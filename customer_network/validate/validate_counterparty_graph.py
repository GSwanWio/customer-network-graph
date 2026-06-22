import pandas as pd


def validate_required_columns(
	df: pd.DataFrame,
	required_columns: list[str],
	dataset_name: str,
) -> list[str]:
	errors = []

	missing_columns = [
		column
		for column in required_columns
		if column not in df.columns
	]

	if missing_columns:
		errors.append(f"{dataset_name} missing columns: {missing_columns}")

	return errors


def validate_counterparty_graph(
	counterparty_graph: dict[str, pd.DataFrame],
	graph_rules: dict,
) -> list[str]:
	errors = []

	account_profile = counterparty_graph["counterparty_account_profile"]
	bridge_profile = counterparty_graph["counterparty_entity_bridge_profile"]
	counterparty_nodes = counterparty_graph["counterparty_nodes"]
	counterparty_edges = counterparty_graph["counterparty_edges"]
	counterparty_groups = counterparty_graph["counterparty_groups"]
	seed_group_map = counterparty_graph["counterparty_seed_group_map"]

	errors.extend(
		validate_required_columns(
			counterparty_nodes,
			[
				"counterparty_group_id",
				"node_id",
				"node_type",
				"seed_entity_flag",
			],
			"counterparty_nodes",
		)
	)

	errors.extend(
		validate_required_columns(
			counterparty_edges,
			[
				"counterparty_group_id",
				"source_node_id",
				"target_node_id",
				"relationship_type",
				"relationship_layer",
				"edge_role",
				"transaction_count",
				"transaction_amount",
				"counterparty_linked_entity_count",
			],
			"counterparty_edges",
		)
	)

	if errors:
		return errors

	if not counterparty_nodes.empty:
		duplicate_node_count = counterparty_nodes.duplicated(subset=["node_id"]).sum()

		if duplicate_node_count > 0:
			errors.append(f"counterparty_nodes has {duplicate_node_count} duplicate node_id values")

	if not counterparty_edges.empty:
		duplicate_edge_count = counterparty_edges.duplicated(
			subset=[
				"source_node_id",
				"target_node_id",
				"relationship_type",
			]
		).sum()

		if duplicate_edge_count > 0:
			errors.append(f"counterparty_edges has {duplicate_edge_count} duplicate core edges")

		node_ids = set(counterparty_nodes["node_id"].dropna().astype(str))

		missing_source_count = (~counterparty_edges["source_node_id"].isin(node_ids)).sum()
		missing_target_count = (~counterparty_edges["target_node_id"].isin(node_ids)).sum()

		if missing_source_count > 0:
			errors.append(f"counterparty_edges has {missing_source_count} edges with missing source_node_id")

		if missing_target_count > 0:
			errors.append(f"counterparty_edges has {missing_target_count} edges with missing target_node_id")

		invalid_relationship_count = (
			counterparty_edges["relationship_type"] != "ENTITY_USES_LOCAL_COUNTERPARTY_ACCOUNT"
		).sum()

		invalid_layer_count = (
			counterparty_edges["relationship_layer"] != "LOCAL_COUNTERPARTY_CORE"
		).sum()

		invalid_edge_role_count = (
			counterparty_edges["edge_role"] != "GROUP_FORMING"
		).sum()

		if invalid_relationship_count > 0:
			errors.append(f"counterparty_edges has {invalid_relationship_count} invalid relationship_type values")

		if invalid_layer_count > 0:
			errors.append(f"counterparty_edges has {invalid_layer_count} invalid relationship_layer values")

		if invalid_edge_role_count > 0:
			errors.append(f"counterparty_edges has {invalid_edge_role_count} invalid edge_role values")

	if not account_profile.empty:
		counterparty_rules = graph_rules["counterparty"]

		group_forming_min = counterparty_rules["group_forming_min_linked_entities"]
		group_forming_max = counterparty_rules["group_forming_max_linked_entities"]
		stopped_min = counterparty_rules["stopped_min_linked_entities"]

		expected_group_forming_flag = (
			(account_profile["linked_entity_count"] >= group_forming_min)
			& (account_profile["linked_entity_count"] <= group_forming_max)
		).astype(int)

		expected_single_entity_flag = (
			account_profile["linked_entity_count"] == 1
		).astype(int)

		expected_stopped_flag = (
			account_profile["linked_entity_count"] >= stopped_min
		).astype(int)

		if (account_profile["group_forming_counterparty_flag"] != expected_group_forming_flag).sum() > 0:
			errors.append("counterparty_account_profile has group_forming flag mismatches")

		if (account_profile["single_entity_counterparty_flag"] != expected_single_entity_flag).sum() > 0:
			errors.append("counterparty_account_profile has single_entity flag mismatches")

		if (account_profile["stopped_counterparty_flag"] != expected_stopped_flag).sum() > 0:
			errors.append("counterparty_account_profile has stopped flag mismatches")

	if not bridge_profile.empty:
		counterparty_rules = graph_rules["counterparty"]

		seed_bridge_max = counterparty_rules["seed_bridge_max_group_forming_counterparties"]
		non_seed_bridge_max = counterparty_rules["non_seed_bridge_max_group_forming_counterparties"]

		invalid_allowed_seed_count = (
			(bridge_profile["seed_entity_flag"] == 1)
			& (bridge_profile["group_merging_entity_flag"] == 1)
			& (bridge_profile["group_forming_counterparty_count"] > seed_bridge_max)
		).sum()

		invalid_allowed_non_seed_count = (
			(bridge_profile["seed_entity_flag"] == 0)
			& (bridge_profile["group_merging_entity_flag"] == 1)
			& (bridge_profile["group_forming_counterparty_count"] > non_seed_bridge_max)
		).sum()

		if invalid_allowed_seed_count > 0:
			errors.append(f"counterparty bridge rules allowed {invalid_allowed_seed_count} seed entities above threshold")

		if invalid_allowed_non_seed_count > 0:
			errors.append(f"counterparty bridge rules allowed {invalid_allowed_non_seed_count} non-seed entities above threshold")

	if not counterparty_groups.empty:
		group_ids = set(counterparty_groups["counterparty_group_id"].dropna().astype(str))
		node_group_ids = set(counterparty_nodes["counterparty_group_id"].dropna().astype(str))
		edge_group_ids = set(counterparty_edges["counterparty_group_id"].dropna().astype(str))

		unknown_node_group_count = len(node_group_ids - group_ids)
		unknown_edge_group_count = len(edge_group_ids - group_ids)

		if unknown_node_group_count > 0:
			errors.append(f"counterparty_nodes has {unknown_node_group_count} group ids not found in counterparty_groups")

		if unknown_edge_group_count > 0:
			errors.append(f"counterparty_edges has {unknown_edge_group_count} group ids not found in counterparty_groups")

	if not seed_group_map.empty and not counterparty_groups.empty:
		group_ids = set(counterparty_groups["counterparty_group_id"].dropna().astype(str))

		in_group = seed_group_map["seed_group_status"] == "IN_COUNTERPARTY_CORE_GROUP"
		no_group = seed_group_map["seed_group_status"] == "NO_COUNTERPARTY_CORE_GROUP"

		missing_group_id_count = (
			in_group
			& seed_group_map["counterparty_group_id"].isna()
		).sum()

		invalid_no_group_id_count = (
			no_group
			& seed_group_map["counterparty_group_id"].notna()
		).sum()

		unknown_group_id_count = (
			in_group
			& ~seed_group_map["counterparty_group_id"].isin(group_ids)
		).sum()

		if missing_group_id_count > 0:
			errors.append(f"counterparty_seed_group_map has {missing_group_id_count} in-group seeds with missing counterparty_group_id")

		if invalid_no_group_id_count > 0:
			errors.append(f"counterparty_seed_group_map has {invalid_no_group_id_count} no-group seeds with populated counterparty_group_id")

		if unknown_group_id_count > 0:
			errors.append(f"counterparty_seed_group_map has {unknown_group_id_count} in-group seeds mapped to unknown counterparty_group_id")

	return errors
