from collections import defaultdict, deque
import hashlib

import pandas as pd
import networkx as nx


def make_entity_node_id(entity_key: str) -> str:
	return f"ENTITY|{entity_key}"


def make_counterparty_node_id(counterparty_account_number: str) -> str:
	hash_value = hashlib.sha256(counterparty_account_number.encode("utf-8")).hexdigest().upper()
	return f"LOCAL_COUNTERPARTY_ACCOUNT|{hash_value}"


def make_counterparty_group_id(component_root_node_id: str) -> str:
	hash_value = hashlib.sha256(component_root_node_id.encode("utf-8")).hexdigest()[:16].upper()
	return f"LCACG_{hash_value}"


def mask_counterparty(counterparty_account_number: str | None) -> str | None:
	if counterparty_account_number is None:
		return None

	if len(counterparty_account_number) <= 4:
		return "****"

	return "****" + counterparty_account_number[-4:]


def empty_df(columns: list[str]) -> pd.DataFrame:
	return pd.DataFrame([], columns=columns)


def build_counterparty_graph(
	seed_customers: pd.DataFrame,
	identity_entities: pd.DataFrame,
	local_counterparty_flows: pd.DataFrame,
	graph_rules: dict,
) -> dict[str, pd.DataFrame]:
	counterparty_rules = graph_rules["counterparty"]

	group_forming_min = counterparty_rules["group_forming_min_linked_entities"]
	group_forming_max = counterparty_rules["group_forming_max_linked_entities"]
	stopped_min = counterparty_rules["stopped_min_linked_entities"]
	seed_bridge_max = counterparty_rules["seed_bridge_max_group_forming_counterparties"]
	non_seed_bridge_max = counterparty_rules["non_seed_bridge_max_group_forming_counterparties"]

	seed_customer_ids = set(
		seed_customers["seed_customer_id"]
		.dropna()
		.astype(str)
		.tolist()
	)

	identity = identity_entities.copy()
	identity["entity_node_id"] = identity["entity_key"].apply(make_entity_node_id)
	identity["seed_entity_flag"] = identity["lookup_customer_id"].isin(seed_customer_ids).astype(int)

	seed_entity_keys = set(
		identity.loc[
			identity["seed_entity_flag"] == 1,
			"entity_key",
		].astype(str)
	)

	flows_with_identity = local_counterparty_flows.merge(
		identity[
			[
				"entity_type",
				"entity_id",
				"entity_key",
				"entity_node_id",
				"lookup_customer_id",
				"entity_created_at",
				"seed_entity_flag",
			]
		],
		on="lookup_customer_id",
		how="inner",
	)

	link_columns = [
		"entity_type",
		"entity_id",
		"entity_key",
		"entity_node_id",
		"lookup_customer_id",
		"entity_created_at",
		"seed_entity_flag",
		"counterparty_account_number",
		"counterparty_account_node_id",
		"counterparty_account_masked",
		"transaction_count",
		"outbound_transaction_count",
		"inbound_transaction_count",
		"transaction_amount",
		"first_seen_at",
		"last_seen_at",
		"entity_counterparty_direction",
	]

	if flows_with_identity.empty:
		return {
			"counterparty_entity_account_links": empty_df(link_columns),
			"counterparty_account_profile": empty_df([]),
			"counterparty_entity_bridge_profile": empty_df([]),
			"counterparty_nodes": empty_df([]),
			"counterparty_edges": empty_df([]),
			"counterparty_groups": empty_df([]),
			"counterparty_blocked_bridge_edges": empty_df([]),
			"counterparty_stopped_edges": empty_df([]),
			"counterparty_seed_group_map": empty_df([]),
		}

	flows_with_identity["outbound_transaction_flag"] = (
		flows_with_identity["flow_direction"] == "OUTBOUND"
	).astype(int)
	flows_with_identity["inbound_transaction_flag"] = (
		flows_with_identity["flow_direction"] == "INBOUND"
	).astype(int)

	links = (
		flows_with_identity
		.groupby(
			[
				"entity_type",
				"entity_id",
				"entity_key",
				"entity_node_id",
				"lookup_customer_id",
				"entity_created_at",
				"seed_entity_flag",
				"counterparty_account_number",
			],
			dropna=False,
		)
		.agg(
			transaction_count=("transaction_id", "nunique"),
			outbound_transaction_count=("outbound_transaction_flag", "sum"),
			inbound_transaction_count=("inbound_transaction_flag", "sum"),
			transaction_amount=("transaction_amount", "sum"),
			first_seen_at=("transaction_timestamp", "min"),
			last_seen_at=("transaction_timestamp", "max"),
		)
		.reset_index()
	)

	links["counterparty_account_node_id"] = links["counterparty_account_number"].apply(make_counterparty_node_id)
	links["counterparty_account_masked"] = links["counterparty_account_number"].apply(mask_counterparty)

	links["entity_counterparty_direction"] = links.apply(
		lambda row: "BOTH_DIRECTIONS"
		if row["outbound_transaction_count"] > 0 and row["inbound_transaction_count"] > 0
		else "OUTBOUND_ONLY"
		if row["outbound_transaction_count"] > 0
		else "INBOUND_ONLY"
		if row["inbound_transaction_count"] > 0
		else "UNKNOWN",
		axis=1,
	)

	links = links[link_columns].copy()

	account_profile = (
		links
		.groupby(
			[
				"counterparty_account_number",
				"counterparty_account_node_id",
				"counterparty_account_masked",
			],
			dropna=False,
		)
		.agg(
			linked_entity_count=("entity_key", "nunique"),
			linked_seed_entity_count=("seed_entity_flag", "sum"),
			transaction_count=("transaction_count", "sum"),
			outbound_transaction_count=("outbound_transaction_count", "sum"),
			inbound_transaction_count=("inbound_transaction_count", "sum"),
			transaction_amount=("transaction_amount", "sum"),
			first_seen_at=("first_seen_at", "min"),
			last_seen_at=("last_seen_at", "max"),
		)
		.reset_index()
	)

	account_profile["linked_non_seed_entity_count"] = (
		account_profile["linked_entity_count"] - account_profile["linked_seed_entity_count"]
	)

	account_profile["counterparty_degree_profile"] = account_profile["linked_entity_count"].apply(
		lambda value: "SINGLE_ENTITY_COUNTERPARTY"
		if value == 1
		else "LOW_DEGREE_SHARED_COUNTERPARTY"
		if group_forming_min <= value <= group_forming_max
		else "MEDIUM_DEGREE_COUNTERPARTY"
		if stopped_min <= value <= 24
		else "HIGH_DEGREE_COUNTERPARTY"
		if 25 <= value <= 99
		else "VERY_HIGH_DEGREE_COUNTERPARTY"
		if value >= 100
		else "UNKNOWN"
	)

	account_profile["group_forming_counterparty_flag"] = (
		(account_profile["linked_entity_count"] >= group_forming_min)
		& (account_profile["linked_entity_count"] <= group_forming_max)
	).astype(int)

	account_profile["single_entity_counterparty_flag"] = (
		account_profile["linked_entity_count"] == 1
	).astype(int)

	account_profile["stopped_counterparty_flag"] = (
		account_profile["linked_entity_count"] >= stopped_min
	).astype(int)

	candidate_edges = links.merge(
		account_profile[
			[
				"counterparty_account_number",
				"counterparty_degree_profile",
				"linked_entity_count",
				"linked_seed_entity_count",
				"linked_non_seed_entity_count",
				"group_forming_counterparty_flag",
				"single_entity_counterparty_flag",
				"stopped_counterparty_flag",
			]
		],
		on="counterparty_account_number",
		how="inner",
	)

	group_forming_edges = candidate_edges[
		candidate_edges["group_forming_counterparty_flag"] == 1
	].copy()

	if group_forming_edges.empty:
		return {
			"counterparty_entity_account_links": links,
			"counterparty_account_profile": account_profile,
			"counterparty_entity_bridge_profile": empty_df([]),
			"counterparty_nodes": empty_df([]),
			"counterparty_edges": empty_df([]),
			"counterparty_groups": empty_df([]),
			"counterparty_blocked_bridge_edges": empty_df([]),
			"counterparty_stopped_edges": empty_df([]),
			"counterparty_seed_group_map": empty_df([]),
		}

	bridge_profile = (
		group_forming_edges
		.groupby(
			[
				"entity_key",
				"entity_node_id",
				"entity_type",
				"entity_id",
				"lookup_customer_id",
				"seed_entity_flag",
			],
			dropna=False,
		)
		.agg(
			group_forming_counterparty_count=("counterparty_account_number", "nunique"),
			transaction_count=("transaction_count", "sum"),
			transaction_amount=("transaction_amount", "sum"),
		)
		.reset_index()
	)

	def get_group_merging_flag(row: pd.Series) -> int:
		if row["seed_entity_flag"] == 1:
			return int(row["group_forming_counterparty_count"] <= seed_bridge_max)

		return int(row["group_forming_counterparty_count"] <= non_seed_bridge_max)

	def get_bridge_rule(row: pd.Series) -> str:
		if row["seed_entity_flag"] == 1 and row["group_forming_counterparty_count"] <= seed_bridge_max:
			return "SEED_ALLOWED_BRIDGE_WITHIN_THRESHOLD"

		if row["seed_entity_flag"] == 1 and row["group_forming_counterparty_count"] > seed_bridge_max:
			return "SEED_BLOCKED_HIGH_ACTIVITY_BRIDGE"

		if row["seed_entity_flag"] == 0 and row["group_forming_counterparty_count"] <= non_seed_bridge_max:
			return "NON_SEED_ALLOWED_BRIDGE_WITHIN_THRESHOLD"

		return "NON_SEED_BLOCKED_HIGH_CONNECTOR_BRIDGE"

	bridge_profile["group_merging_entity_flag"] = bridge_profile.apply(get_group_merging_flag, axis=1)
	bridge_profile["blocked_bridge_entity_flag"] = 1 - bridge_profile["group_merging_entity_flag"]
	bridge_profile["bridge_rule"] = bridge_profile.apply(get_bridge_rule, axis=1)

	group_forming_edges = group_forming_edges.merge(
		bridge_profile[
			[
				"entity_key",
				"group_forming_counterparty_count",
				"group_merging_entity_flag",
				"blocked_bridge_entity_flag",
				"bridge_rule",
			]
		],
		on="entity_key",
		how="left",
	)

	allowed_edges = group_forming_edges[
		group_forming_edges["group_merging_entity_flag"] == 1
	].copy()

	blocked_edges = group_forming_edges[
		group_forming_edges["blocked_bridge_entity_flag"] == 1
	].copy()

	adjacency: dict[str, set[str]] = defaultdict(set)

	for _, row in allowed_edges.iterrows():
		source_node_id = row["entity_node_id"]
		target_node_id = row["counterparty_account_node_id"]

		adjacency[source_node_id].add(target_node_id)
		adjacency[target_node_id].add(source_node_id)

	seed_node_ids = {
		make_entity_node_id(entity_key)
		for entity_key in seed_entity_keys
	}

	reached_nodes: set[str] = set()
	queue = deque()

	for seed_node_id in sorted(seed_node_ids):
		if seed_node_id in adjacency:
			reached_nodes.add(seed_node_id)
			queue.append(seed_node_id)

	while queue:
		current_node_id = queue.popleft()

		for linked_node_id in adjacency.get(current_node_id, set()):
			if linked_node_id not in reached_nodes:
				reached_nodes.add(linked_node_id)
				queue.append(linked_node_id)

	reached_allowed_edges = allowed_edges[
		allowed_edges["entity_node_id"].isin(reached_nodes)
		& allowed_edges["counterparty_account_node_id"].isin(reached_nodes)
	].copy()

	reached_account_node_ids = set(reached_allowed_edges["counterparty_account_node_id"].dropna().astype(str))
	reached_entity_node_ids = set(reached_allowed_edges["entity_node_id"].dropna().astype(str))

	graph = nx.Graph()

	for _, row in reached_allowed_edges.iterrows():
		graph.add_edge(
			row["entity_node_id"],
			row["counterparty_account_node_id"],
		)

	node_group_map = {}

	for component_nodes in nx.connected_components(graph):
		component_root_node_id = min(component_nodes)
		counterparty_group_id = make_counterparty_group_id(component_root_node_id)

		for node_id in component_nodes:
			node_group_map[node_id] = {
				"component_id": counterparty_group_id,
				"counterparty_group_id": counterparty_group_id,
				"component_root_node_id": component_root_node_id,
			}

	node_rows = []

	reached_entities = identity[
		identity["entity_node_id"].isin(reached_entity_node_ids)
	].copy()

	for _, row in reached_entities.iterrows():
		group_info = node_group_map[row["entity_node_id"]]

		node_rows.append({
			"component_id": group_info["component_id"],
			"counterparty_group_id": group_info["counterparty_group_id"],
			"component_root_node_id": group_info["component_root_node_id"],
			"node_id": row["entity_node_id"],
			"node_type": "ENTITY",
			"entity_key": row["entity_key"],
			"entity_type": row["entity_type"],
			"entity_id": row["entity_id"],
			"lookup_customer_id": row["lookup_customer_id"],
			"display_label": row["lookup_customer_id"],
			"network_layer": "LOCAL_COUNTERPARTY",
			"seed_entity_flag": int(row["seed_entity_flag"]),
			"node_role": "SEED_ENTITY" if int(row["seed_entity_flag"]) == 1 else "LINKED_ENTITY",
			"counterparty_account_number": None,
			"counterparty_account_masked": None,
			"counterparty_linked_entity_count": None,
		})

	reached_accounts = account_profile[
		account_profile["counterparty_account_node_id"].isin(reached_account_node_ids)
	].copy()

	for _, row in reached_accounts.iterrows():
		group_info = node_group_map[row["counterparty_account_node_id"]]

		node_rows.append({
			"component_id": group_info["component_id"],
			"counterparty_group_id": group_info["counterparty_group_id"],
			"component_root_node_id": group_info["component_root_node_id"],
			"node_id": row["counterparty_account_node_id"],
			"node_type": "LOCAL_COUNTERPARTY_ACCOUNT",
			"entity_key": None,
			"entity_type": None,
			"entity_id": None,
			"lookup_customer_id": None,
			"display_label": f"Account {row['counterparty_account_masked']}",
			"network_layer": "LOCAL_COUNTERPARTY",
			"seed_entity_flag": 0,
			"node_role": "COUNTERPARTY_CONNECTOR",
			"counterparty_account_number": row["counterparty_account_number"],
			"counterparty_account_masked": row["counterparty_account_masked"],
			"counterparty_linked_entity_count": int(row["linked_entity_count"]),
		})

	counterparty_nodes = pd.DataFrame(node_rows)

	edge_rows = []

	for _, row in reached_allowed_edges.iterrows():
		group_info = node_group_map[row["entity_node_id"]]

		edge_rows.append({
			"component_id": group_info["component_id"],
			"counterparty_group_id": group_info["counterparty_group_id"],
			"component_root_node_id": group_info["component_root_node_id"],
			"source_node_id": row["entity_node_id"],
			"source_node_type": "ENTITY",
			"source_entity_key": row["entity_key"],
			"source_entity_type": row["entity_type"],
			"source_entity_id": row["entity_id"],
			"source_customer_id": row["lookup_customer_id"],
			"target_node_id": row["counterparty_account_node_id"],
			"target_node_type": "LOCAL_COUNTERPARTY_ACCOUNT",
			"counterparty_account_number": row["counterparty_account_number"],
			"counterparty_account_masked": row["counterparty_account_masked"],
			"relationship_type": "ENTITY_USES_LOCAL_COUNTERPARTY_ACCOUNT",
			"relationship_layer": "LOCAL_COUNTERPARTY_CORE",
			"edge_role": "GROUP_FORMING",
			"group_forming_edge_flag": 1,
			"evidence_only_edge_flag": 0,
			"entity_counterparty_direction": row["entity_counterparty_direction"],
			"transaction_count": row["transaction_count"],
			"outbound_transaction_count": row["outbound_transaction_count"],
			"inbound_transaction_count": row["inbound_transaction_count"],
			"transaction_amount": row["transaction_amount"],
			"first_seen_at": row["first_seen_at"],
			"last_seen_at": row["last_seen_at"],
			"counterparty_linked_entity_count": row["linked_entity_count"],
			"source_group_forming_counterparty_count": row["group_forming_counterparty_count"],
			"bridge_rule": row["bridge_rule"],
		})

	counterparty_edges = pd.DataFrame(edge_rows)

	group_rows = []

	if not counterparty_nodes.empty:
		node_counts = (
			counterparty_nodes
			.groupby("counterparty_group_id")
			.agg(
				group_node_count=("node_id", "nunique"),
				group_entity_count=("node_type", lambda values: (values == "ENTITY").sum()),
				group_counterparty_account_count=("node_type", lambda values: (values == "LOCAL_COUNTERPARTY_ACCOUNT").sum()),
				group_seed_entity_count=("seed_entity_flag", "sum"),
			)
			.reset_index()
		)

		edge_counts = (
			counterparty_edges
			.groupby("counterparty_group_id")
			.agg(
				group_edge_count=("source_node_id", "count"),
				total_transaction_count=("transaction_count", "sum"),
				total_transaction_amount=("transaction_amount", "sum"),
				first_seen_at=("first_seen_at", "min"),
				last_seen_at=("last_seen_at", "max"),
				max_counterparty_linked_entity_count=("counterparty_linked_entity_count", "max"),
				max_source_group_forming_counterparty_count=("source_group_forming_counterparty_count", "max"),
			)
			.reset_index()
		)

		groups = node_counts.merge(edge_counts, on="counterparty_group_id", how="left")
		groups["group_non_seed_entity_count"] = (
			groups["group_entity_count"] - groups["group_seed_entity_count"]
		)
		groups["group_profile"] = groups.apply(
			lambda row: "MULTI_SEED_COUNTERPARTY_CORE_GROUP"
			if row["group_seed_entity_count"] >= 2
			else "SEED_TO_NON_SEED_COUNTERPARTY_CORE_GROUP"
			if row["group_non_seed_entity_count"] >= 1
			else "SEED_ONLY_COUNTERPARTY_CORE_GROUP",
			axis=1,
		)

		group_rows = groups.to_dict("records")

	counterparty_groups = pd.DataFrame(group_rows)

	stopped_edges = candidate_edges[
		candidate_edges["stopped_counterparty_flag"] == 1
	].copy()

	blocked_bridge_edges = blocked_edges.copy()

	seed_group_rows = []

	for seed_entity_key in sorted(seed_entity_keys):
		seed_node_id = make_entity_node_id(seed_entity_key)
		group_info = node_group_map.get(seed_node_id)

		seed_meta = identity.loc[
			identity["entity_key"] == seed_entity_key
		].iloc[0].to_dict()

		seed_group_rows.append({
			"seed_customer_id": seed_meta["lookup_customer_id"],
			"seed_entity_type": seed_meta["entity_type"],
			"seed_entity_id": seed_meta["entity_id"],
			"seed_entity_key": seed_entity_key,
			"seed_entity_node_id": seed_node_id,
			"counterparty_group_id": group_info["counterparty_group_id"] if group_info else None,
			"seed_group_status": "IN_COUNTERPARTY_CORE_GROUP" if group_info else "NO_COUNTERPARTY_CORE_GROUP",
		})

	seed_group_map = pd.DataFrame(seed_group_rows)

	return {
		"counterparty_entity_account_links": links,
		"counterparty_account_profile": account_profile,
		"counterparty_entity_bridge_profile": bridge_profile,
		"counterparty_nodes": counterparty_nodes,
		"counterparty_edges": counterparty_edges,
		"counterparty_groups": counterparty_groups,
		"counterparty_blocked_bridge_edges": blocked_bridge_edges,
		"counterparty_stopped_edges": stopped_edges,
		"counterparty_seed_group_map": seed_group_map,
	}
