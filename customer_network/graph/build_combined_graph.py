import hashlib

import networkx as nx
import pandas as pd


def make_combined_component_id(component_root_node_id: str) -> str:
	hash_value = hashlib.sha256(component_root_node_id.encode("utf-8")).hexdigest()[:16].upper()
	return f"CCG_{hash_value}"


def clean_value(value: object) -> object:
	if pd.isna(value):
		return None

	return value


def build_combined_graph(
	eid_graph: dict[str, pd.DataFrame],
	counterparty_graph: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
	node_records_by_id: dict[str, dict] = {}
	edge_rows = []

	def upsert_node(row: pd.Series, source_layer: str) -> None:
		node_id = row["node_id"]

		if node_id not in node_records_by_id:
			node_records_by_id[node_id] = {
				"node_id": node_id,
				"node_type": clean_value(row.get("node_type")),
				"display_label": clean_value(row.get("display_label")),
				"entity_key": clean_value(row.get("entity_key")),
				"entity_type": clean_value(row.get("entity_type")),
				"entity_id": clean_value(row.get("entity_id")),
				"lookup_customer_id": clean_value(row.get("lookup_customer_id")),
				"emirates_id_masked": clean_value(row.get("emirates_id_masked")),
				"counterparty_account_masked": clean_value(row.get("counterparty_account_masked")),
				"counterparty_account_number": clean_value(row.get("counterparty_account_number")),
				"seed_entity_flag": int(row.get("seed_entity_flag", 0) or 0),
				"node_role_values": set(),
				"network_layer_values": set(),
				"eid_component_id": clean_value(row.get("eid_component_id")),
				"counterparty_group_id": clean_value(row.get("counterparty_group_id")),
			}

		record = node_records_by_id[node_id]

		record["seed_entity_flag"] = max(
			record["seed_entity_flag"],
			int(row.get("seed_entity_flag", 0) or 0),
		)

		node_role = clean_value(row.get("node_role"))

		if node_role is not None:
			record["node_role_values"].add(str(node_role))

		network_layer = clean_value(row.get("network_layer"))

		if network_layer is not None:
			record["network_layer_values"].add(str(network_layer))

		record["network_layer_values"].add(source_layer)

		for column in [
			"display_label",
			"entity_key",
			"entity_type",
			"entity_id",
			"lookup_customer_id",
			"emirates_id_masked",
			"counterparty_account_masked",
			"counterparty_account_number",
			"eid_component_id",
			"counterparty_group_id",
		]:
			if record.get(column) is None and clean_value(row.get(column)) is not None:
				record[column] = clean_value(row.get(column))

	eid_nodes = eid_graph["eid_nodes"].copy()
	counterparty_nodes = counterparty_graph["counterparty_nodes"].copy()

	for _, row in eid_nodes.iterrows():
		upsert_node(row, "IDENTITY")

	for _, row in counterparty_nodes.iterrows():
		upsert_node(row, "LOCAL_COUNTERPARTY")

	eid_edges = eid_graph["eid_edges"].copy()

	for _, row in eid_edges.iterrows():
		edge_rows.append({
			"source_node_id": row["source_node_id"],
			"target_node_id": row["target_node_id"],
			"source_node_type": row["source_node_type"],
			"target_node_type": row["target_node_type"],
			"relationship_type": row["relationship_type"],
			"relationship_layer": row["relationship_layer"],
			"edge_role": row["edge_role"],
			"group_forming_edge_flag": int(row["group_forming_edge_flag"]),
			"evidence_only_edge_flag": int(row["evidence_only_edge_flag"]),
			"source_entity_key": clean_value(row.get("source_entity_key")),
			"source_customer_id": clean_value(row.get("source_customer_id")),
			"counterparty_account_masked": None,
			"emirates_id_masked": clean_value(row.get("emirates_id_masked")),
			"entity_counterparty_direction": None,
			"transaction_count": 0,
			"outbound_transaction_count": 0,
			"inbound_transaction_count": 0,
			"transaction_amount": 0.0,
			"first_seen_at": None,
			"last_seen_at": None,
			"source_graph": "EID",
		})

	counterparty_edges = counterparty_graph["counterparty_edges"].copy()

	for _, row in counterparty_edges.iterrows():
		edge_rows.append({
			"source_node_id": row["source_node_id"],
			"target_node_id": row["target_node_id"],
			"source_node_type": row["source_node_type"],
			"target_node_type": row["target_node_type"],
			"relationship_type": row["relationship_type"],
			"relationship_layer": row["relationship_layer"],
			"edge_role": row["edge_role"],
			"group_forming_edge_flag": int(row["group_forming_edge_flag"]),
			"evidence_only_edge_flag": int(row["evidence_only_edge_flag"]),
			"source_entity_key": clean_value(row.get("source_entity_key")),
			"source_customer_id": clean_value(row.get("source_customer_id")),
			"counterparty_account_masked": clean_value(row.get("counterparty_account_masked")),
			"emirates_id_masked": None,
			"entity_counterparty_direction": clean_value(row.get("entity_counterparty_direction")),
			"transaction_count": int(row.get("transaction_count", 0) or 0),
			"outbound_transaction_count": int(row.get("outbound_transaction_count", 0) or 0),
			"inbound_transaction_count": int(row.get("inbound_transaction_count", 0) or 0),
			"transaction_amount": float(row.get("transaction_amount", 0) or 0),
			"first_seen_at": clean_value(row.get("first_seen_at")),
			"last_seen_at": clean_value(row.get("last_seen_at")),
			"source_graph": "COUNTERPARTY",
		})

	combined_edges = pd.DataFrame(edge_rows)

	graph = nx.Graph()

	for node_id in node_records_by_id:
		graph.add_node(node_id)

	for _, row in combined_edges.iterrows():
		graph.add_edge(row["source_node_id"], row["target_node_id"])

	node_component_map = {}

	for component_nodes in nx.connected_components(graph):
		component_root_node_id = min(component_nodes)
		combined_component_id = make_combined_component_id(component_root_node_id)

		for node_id in component_nodes:
			node_component_map[node_id] = {
				"combined_component_id": combined_component_id,
				"component_root_node_id": component_root_node_id,
			}

	node_rows = []

	for node_id, record in node_records_by_id.items():
		component_info = node_component_map[node_id]

		node_role_values = record["node_role_values"]

		if record["seed_entity_flag"] == 1:
			node_role = "SEED_ENTITY"
		elif "EMIRATES_ID_CONNECTOR" in node_role_values:
			node_role = "EMIRATES_ID_CONNECTOR"
		elif "COUNTERPARTY_CONNECTOR" in node_role_values:
			node_role = "COUNTERPARTY_CONNECTOR"
		else:
			node_role = "LINKED_ENTITY"

		node_rows.append({
			"combined_component_id": component_info["combined_component_id"],
			"component_root_node_id": component_info["component_root_node_id"],
			"node_id": node_id,
			"node_type": record["node_type"],
			"display_label": record["display_label"],
			"entity_key": record["entity_key"],
			"entity_type": record["entity_type"],
			"entity_id": record["entity_id"],
			"lookup_customer_id": record["lookup_customer_id"],
			"emirates_id_masked": record["emirates_id_masked"],
			"counterparty_account_masked": record["counterparty_account_masked"],
			"counterparty_account_number": record["counterparty_account_number"],
			"seed_entity_flag": record["seed_entity_flag"],
			"node_role": node_role,
			"network_layers": "|".join(sorted(record["network_layer_values"])),
			"eid_component_id": record["eid_component_id"],
			"counterparty_group_id": record["counterparty_group_id"],
		})

	combined_nodes = pd.DataFrame(node_rows)

	combined_edges = combined_edges.merge(
		combined_nodes[
			[
				"node_id",
				"combined_component_id",
			]
		].rename(columns={"node_id": "source_node_id"}),
		on="source_node_id",
		how="left",
	)

	combined_edges = combined_edges.merge(
		combined_nodes[
			[
				"node_id",
				"combined_component_id",
			]
		].rename(columns={
			"node_id": "target_node_id",
			"combined_component_id": "target_combined_component_id",
		}),
		on="target_node_id",
		how="left",
	)

	combined_edges["same_component_flag"] = (
		combined_edges["combined_component_id"] == combined_edges["target_combined_component_id"]
	).astype(int)

	component_node_counts = (
		combined_nodes
		.groupby("combined_component_id", dropna=False)
		.agg(
			component_root_node_id=("component_root_node_id", "min"),
			graph_node_count=("node_id", "nunique"),
			entity_node_count=("node_type", lambda values: (values == "ENTITY").sum()),
			eid_node_count=("node_type", lambda values: (values == "EMIRATES_ID").sum()),
			counterparty_account_node_count=("node_type", lambda values: (values == "LOCAL_COUNTERPARTY_ACCOUNT").sum()),
			seed_entity_count=("seed_entity_flag", "sum"),
		)
		.reset_index()
	)

	component_edge_counts = (
		combined_edges
		.groupby("combined_component_id", dropna=False)
		.agg(
			graph_edge_count=("source_node_id", "count"),
			identity_edge_count=("relationship_layer", lambda values: (values == "IDENTITY").sum()),
			counterparty_core_edge_count=("relationship_layer", lambda values: (values == "LOCAL_COUNTERPARTY_CORE").sum()),
			total_transaction_count=("transaction_count", "sum"),
			total_transaction_amount=("transaction_amount", "sum"),
		)
		.reset_index()
	)

	combined_components = component_node_counts.merge(
		component_edge_counts,
		on="combined_component_id",
		how="left",
	)

	for column in [
		"graph_edge_count",
		"identity_edge_count",
		"counterparty_core_edge_count",
		"total_transaction_count",
		"total_transaction_amount",
	]:
		combined_components[column] = combined_components[column].fillna(0)

	combined_components["component_profile"] = combined_components.apply(
		lambda row: "IDENTITY_AND_COUNTERPARTY_NETWORK"
		if row["identity_edge_count"] > 0 and row["counterparty_core_edge_count"] > 0
		else "IDENTITY_ONLY_NETWORK"
		if row["identity_edge_count"] > 0
		else "COUNTERPARTY_ONLY_NETWORK"
		if row["counterparty_core_edge_count"] > 0
		else "ISOLATED_NODE",
		axis=1,
	)

	combined_nodes = combined_nodes.sort_values(
		[
			"combined_component_id",
			"node_type",
			"display_label",
			"node_id",
		]
	).reset_index(drop=True)

	combined_edges = combined_edges.sort_values(
		[
			"combined_component_id",
			"relationship_layer",
			"source_node_id",
			"target_node_id",
		]
	).reset_index(drop=True)

	combined_components = combined_components.sort_values(
		[
			"graph_node_count",
			"graph_edge_count",
		],
		ascending=[False, False],
	).reset_index(drop=True)

	return {
		"combined_nodes": combined_nodes,
		"combined_edges": combined_edges,
		"combined_components": combined_components,
	}
