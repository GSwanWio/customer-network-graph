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


def validate_combined_graph(combined_graph: dict[str, pd.DataFrame]) -> list[str]:
	errors = []

	combined_nodes = combined_graph["combined_nodes"]
	combined_edges = combined_graph["combined_edges"]
	combined_components = combined_graph["combined_components"]

	errors.extend(
		validate_required_columns(
			combined_nodes,
			[
				"combined_component_id",
				"node_id",
				"node_type",
				"display_label",
				"seed_entity_flag",
				"counterparty_expansion_seed_flag",
				"node_role",
			],
			"combined_nodes",
		)
	)

	errors.extend(
		validate_required_columns(
			combined_edges,
			[
				"combined_component_id",
				"source_node_id",
				"target_node_id",
				"relationship_type",
				"relationship_layer",
				"same_component_flag",
			],
			"combined_edges",
		)
	)

	errors.extend(
		validate_required_columns(
			combined_components,
			[
				"combined_component_id",
				"graph_node_count",
				"entity_node_count",
				"eid_node_count",
				"counterparty_account_node_count",
				"seed_entity_count",
				"counterparty_expansion_seed_entity_count",
				"graph_edge_count",
				"identity_edge_count",
				"counterparty_core_edge_count",
				"component_profile",
			],
			"combined_components",
		)
	)

	if errors:
		return errors

	duplicate_node_count = combined_nodes.duplicated(subset=["node_id"]).sum()

	if duplicate_node_count > 0:
		errors.append(f"combined_nodes has {duplicate_node_count} duplicate node_id values")

	duplicate_edge_count = combined_edges.duplicated(
		subset=[
			"source_node_id",
			"target_node_id",
			"relationship_type",
		]
	).sum()

	if duplicate_edge_count > 0:
		errors.append(f"combined_edges has {duplicate_edge_count} duplicate edges")

	node_ids = set(combined_nodes["node_id"].dropna().astype(str))

	missing_source_count = (~combined_edges["source_node_id"].isin(node_ids)).sum()
	missing_target_count = (~combined_edges["target_node_id"].isin(node_ids)).sum()

	if missing_source_count > 0:
		errors.append(f"combined_edges has {missing_source_count} edges with missing source_node_id")

	if missing_target_count > 0:
		errors.append(f"combined_edges has {missing_target_count} edges with missing target_node_id")

	cross_component_edge_count = (combined_edges["same_component_flag"] != 1).sum()

	if cross_component_edge_count > 0:
		errors.append(f"combined_edges has {cross_component_edge_count} edges crossing combined components")

	node_counts = (
		combined_nodes
		.groupby("combined_component_id", dropna=False)
		.agg(
			actual_graph_node_count=("node_id", "nunique"),
			actual_entity_node_count=("node_type", lambda values: (values == "ENTITY").sum()),
			actual_eid_node_count=("node_type", lambda values: (values == "EMIRATES_ID").sum()),
			actual_counterparty_account_node_count=("node_type", lambda values: (values == "LOCAL_COUNTERPARTY_ACCOUNT").sum()),
			actual_seed_entity_count=("seed_entity_flag", "sum"),
			actual_counterparty_expansion_seed_entity_count=("counterparty_expansion_seed_flag", "sum"),
		)
		.reset_index()
	)

	edge_counts = (
		combined_edges
		.groupby("combined_component_id", dropna=False)
		.agg(
			actual_graph_edge_count=("source_node_id", "count"),
			actual_identity_edge_count=("relationship_layer", lambda values: (values == "IDENTITY").sum()),
			actual_counterparty_core_edge_count=("relationship_layer", lambda values: (values == "LOCAL_COUNTERPARTY_CORE").sum()),
		)
		.reset_index()
	)

	component_check = (
		combined_components
		.merge(node_counts, on="combined_component_id", how="left")
		.merge(edge_counts, on="combined_component_id", how="left")
	)

	for column in component_check.columns:
		if column.startswith("actual_"):
			component_check[column] = component_check[column].fillna(0)

	checks = [
		("graph_node_count", "actual_graph_node_count"),
		("entity_node_count", "actual_entity_node_count"),
		("eid_node_count", "actual_eid_node_count"),
		("counterparty_account_node_count", "actual_counterparty_account_node_count"),
		("seed_entity_count", "actual_seed_entity_count"),
		("counterparty_expansion_seed_entity_count", "actual_counterparty_expansion_seed_entity_count"),
		("graph_edge_count", "actual_graph_edge_count"),
		("identity_edge_count", "actual_identity_edge_count"),
		("counterparty_core_edge_count", "actual_counterparty_core_edge_count"),
	]

	for expected_column, actual_column in checks:
		mismatch_count = (
			component_check[expected_column] != component_check[actual_column]
		).sum()

		if mismatch_count > 0:
			errors.append(f"combined_components has {mismatch_count} {expected_column} mismatches")

	return errors
