from collections import defaultdict, deque
import hashlib

import pandas as pd


def make_entity_node_id(entity_key: str) -> str:
	return f"ENTITY|{entity_key}"


def make_eid_node_id(emirates_id_number: str) -> str:
	hash_value = hashlib.sha256(emirates_id_number.encode("utf-8")).hexdigest().upper()
	return f"EID|{hash_value}"


def mask_eid(emirates_id_number: str | None) -> str | None:
	if emirates_id_number is None:
		return None

	if len(emirates_id_number) <= 4:
		return "****"

	return "****" + emirates_id_number[-4:]


def make_eid_component_id(component_root_entity_key: str) -> str:
	hash_value = hashlib.sha256(component_root_entity_key.encode("utf-8")).hexdigest()[:16].upper()
	return f"EIDCG_{hash_value}"


def build_eid_graph(
	seed_customers: pd.DataFrame,
	identity_entities: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
	seed_customer_ids = set(
		seed_customers["seed_customer_id"]
		.dropna()
		.astype(str)
		.tolist()
	)

	entity_meta: dict[str, dict] = {}
	entity_to_eids: dict[str, set[str]] = defaultdict(set)
	eid_to_entities: dict[str, set[str]] = defaultdict(set)
	customer_id_to_entities: dict[str, set[str]] = defaultdict(set)

	for _, row in identity_entities.iterrows():
		entity_key = str(row["entity_key"])
		lookup_customer_id = str(row["lookup_customer_id"])
		emirates_id_number = row["emirates_id_number"]

		entity_meta[entity_key] = {
			"entity_type": row["entity_type"],
			"entity_id": row["entity_id"],
			"lookup_customer_id": lookup_customer_id,
			"entity_created_at": row["entity_created_at"],
		}

		customer_id_to_entities[lookup_customer_id].add(entity_key)

		if pd.notna(emirates_id_number):
			emirates_id_number = str(emirates_id_number)
			entity_to_eids[entity_key].add(emirates_id_number)
			eid_to_entities[emirates_id_number].add(entity_key)

	seed_entity_keys: set[str] = set()

	for seed_customer_id in seed_customer_ids:
		for entity_key in customer_id_to_entities.get(seed_customer_id, set()):
			seed_entity_keys.add(entity_key)

	matched_seed_customer_ids = {
		entity_meta[entity_key]["lookup_customer_id"]
		for entity_key in seed_entity_keys
		if entity_meta[entity_key]["lookup_customer_id"] is not None
	}

	unmatched_seed_customer_ids = sorted(seed_customer_ids - matched_seed_customer_ids)

	visited_seed_entities: set[str] = set()

	seed_entity_rows = []
	unmatched_seed_rows = []
	node_rows = []
	edge_rows = []
	component_rows = []
	seed_component_rows = []

	for seed_entity_key in sorted(seed_entity_keys):
		seed_meta = entity_meta[seed_entity_key]
		seed_eids = entity_to_eids.get(seed_entity_key, set())

		seed_entity_rows.append({
			"seed_customer_id": seed_meta["lookup_customer_id"],
			"seed_entity_type": seed_meta["entity_type"],
			"seed_entity_id": seed_meta["entity_id"],
			"seed_entity_key": seed_entity_key,
			"seed_entity_node_id": make_entity_node_id(seed_entity_key),
			"seed_emirates_id_count": len(seed_eids),
		})

		if seed_entity_key in visited_seed_entities:
			continue

		component_entity_keys: set[str] = set()
		component_eids: set[str] = set()
		entity_depth: dict[str, int] = {}
		eid_depth: dict[str, int] = {}

		queue = deque()

		component_entity_keys.add(seed_entity_key)
		entity_depth[seed_entity_key] = 0
		queue.append(("ENTITY", seed_entity_key))

		while queue:
			node_type, node_value = queue.popleft()

			if node_type == "ENTITY":
				current_entity_key = node_value
				current_depth = entity_depth[current_entity_key]

				for emirates_id_number in entity_to_eids.get(current_entity_key, set()):
					if emirates_id_number not in component_eids:
						component_eids.add(emirates_id_number)
						eid_depth[emirates_id_number] = current_depth + 1
						queue.append(("EID", emirates_id_number))

			else:
				emirates_id_number = node_value
				current_depth = eid_depth[emirates_id_number]

				for linked_entity_key in eid_to_entities.get(emirates_id_number, set()):
					if linked_entity_key not in component_entity_keys:
						component_entity_keys.add(linked_entity_key)
						entity_depth[linked_entity_key] = current_depth + 1
						queue.append(("ENTITY", linked_entity_key))

		component_seed_entity_keys = sorted(component_entity_keys.intersection(seed_entity_keys))
		visited_seed_entities.update(component_seed_entity_keys)

		component_root_entity_key = min(component_entity_keys)
		eid_component_id = make_eid_component_id(component_root_entity_key)

		for component_seed_entity_key in component_seed_entity_keys:
			seed_component_rows.append({
				"seed_customer_id": entity_meta[component_seed_entity_key]["lookup_customer_id"],
				"seed_entity_type": entity_meta[component_seed_entity_key]["entity_type"],
				"seed_entity_id": entity_meta[component_seed_entity_key]["entity_id"],
				"seed_entity_key": component_seed_entity_key,
				"seed_entity_node_id": make_entity_node_id(component_seed_entity_key),
				"eid_component_id": eid_component_id,
				"component_root_entity_key": component_root_entity_key,
				"component_root_node_id": make_entity_node_id(component_root_entity_key),
			})

		for entity_key in sorted(component_entity_keys):
			meta = entity_meta[entity_key]
			entity_eids = entity_to_eids.get(entity_key, set())

			node_rows.append({
				"component_id": eid_component_id,
				"eid_component_id": eid_component_id,
				"component_root_entity_key": component_root_entity_key,
				"component_root_node_id": make_entity_node_id(component_root_entity_key),
				"node_id": make_entity_node_id(entity_key),
				"node_type": "ENTITY",
				"entity_key": entity_key,
				"entity_type": meta["entity_type"],
				"entity_id": meta["entity_id"],
				"lookup_customer_id": meta["lookup_customer_id"],
				"entity_created_at": meta["entity_created_at"],
				"eid_node_id": None,
				"emirates_id_masked": None,
				"display_label": meta["lookup_customer_id"],
				"network_layer": "IDENTITY",
				"network_depth": int(entity_depth.get(entity_key, 0)),
				"seed_entity_flag": 1 if entity_key in component_seed_entity_keys else 0,
				"node_role": "SEED_ENTITY" if entity_key in component_seed_entity_keys else "LINKED_ENTITY",
				"entity_emirates_id_count": len(entity_eids),
				"eid_linked_entity_count": None,
			})

		for emirates_id_number in sorted(component_eids):
			eid_node_id = make_eid_node_id(emirates_id_number)
			linked_entities = eid_to_entities.get(emirates_id_number, set()).intersection(component_entity_keys)

			node_rows.append({
				"component_id": eid_component_id,
				"eid_component_id": eid_component_id,
				"component_root_entity_key": component_root_entity_key,
				"component_root_node_id": make_entity_node_id(component_root_entity_key),
				"node_id": eid_node_id,
				"node_type": "EMIRATES_ID",
				"entity_key": None,
				"entity_type": None,
				"entity_id": None,
				"lookup_customer_id": None,
				"entity_created_at": None,
				"eid_node_id": eid_node_id,
				"emirates_id_masked": mask_eid(emirates_id_number),
				"display_label": f"EID {mask_eid(emirates_id_number)}",
				"network_layer": "IDENTITY",
				"network_depth": int(eid_depth.get(emirates_id_number, 0)),
				"seed_entity_flag": 0,
				"node_role": "EMIRATES_ID_CONNECTOR",
				"entity_emirates_id_count": None,
				"eid_linked_entity_count": len(linked_entities),
			})

			for entity_key in sorted(linked_entities):
				meta = entity_meta[entity_key]

				edge_rows.append({
					"component_id": eid_component_id,
					"eid_component_id": eid_component_id,
					"component_root_entity_key": component_root_entity_key,
					"component_root_node_id": make_entity_node_id(component_root_entity_key),
					"source_node_id": make_entity_node_id(entity_key),
					"source_node_type": "ENTITY",
					"source_entity_key": entity_key,
					"source_entity_type": meta["entity_type"],
					"source_entity_id": meta["entity_id"],
					"source_customer_id": meta["lookup_customer_id"],
					"target_node_id": eid_node_id,
					"target_node_type": "EMIRATES_ID",
					"eid_node_id": eid_node_id,
					"emirates_id_masked": mask_eid(emirates_id_number),
					"relationship_type": "ENTITY_HAS_EMIRATES_ID",
					"relationship_layer": "IDENTITY",
					"edge_role": "GROUP_FORMING",
					"group_forming_edge_flag": 1,
					"evidence_only_edge_flag": 0,
					"source_network_depth": int(entity_depth.get(entity_key, 0)),
					"target_network_depth": int(eid_depth.get(emirates_id_number, 0)),
					"eid_linked_entity_count": len(linked_entities),
				})

		component_rows.append({
			"component_id": eid_component_id,
			"eid_component_id": eid_component_id,
			"component_root_entity_key": component_root_entity_key,
			"component_root_node_id": make_entity_node_id(component_root_entity_key),
			"seed_entity_count": len(component_seed_entity_keys),
			"component_entity_count": len(component_entity_keys),
			"linked_entity_count": len(component_entity_keys) - len(component_seed_entity_keys),
			"eid_node_count": len(component_eids),
			"graph_node_count": len(component_entity_keys) + len(component_eids),
			"graph_edge_count": sum(
				len(eid_to_entities.get(emirates_id_number, set()).intersection(component_entity_keys))
				for emirates_id_number in component_eids
			),
			"sme_entity_count": sum(
				1
				for entity_key in component_entity_keys
				if entity_meta[entity_key]["entity_type"] == "SME"
			),
			"retail_entity_count": sum(
				1
				for entity_key in component_entity_keys
				if entity_meta[entity_key]["entity_type"] == "RETAIL"
			),
			"max_network_depth": max(
				list(entity_depth.values()) + list(eid_depth.values())
			) if component_entity_keys else 0,
			"max_eid_linked_entity_count": max(
				(
					len(eid_to_entities.get(emirates_id_number, set()).intersection(component_entity_keys))
					for emirates_id_number in component_eids
				),
				default=0,
			),
			"component_profile": (
				"SEED_WITHOUT_EID"
				if len(component_eids) == 0
				else "SINGLE_ENTITY_EID_ONLY"
				if len(component_entity_keys) == len(component_seed_entity_keys)
				else "SHARED_EID_NETWORK"
			),
		})

	for seed_customer_id in unmatched_seed_customer_ids:
		unmatched_seed_rows.append({
			"seed_customer_id": seed_customer_id,
			"unmatched_reason": "CUSTOMER_ID_NOT_FOUND_IN_IDENTITY_ENTITIES",
		})

	return {
		"eid_seed_entities": pd.DataFrame(seed_entity_rows),
		"eid_unmatched_seeds": pd.DataFrame(unmatched_seed_rows),
		"eid_nodes": pd.DataFrame(node_rows),
		"eid_edges": pd.DataFrame(edge_rows),
		"eid_components": pd.DataFrame(component_rows),
		"eid_seed_component_map": pd.DataFrame(seed_component_rows),
	}