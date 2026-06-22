import pandas as pd


def validate_no_duplicate_nodes(eid_nodes: pd.DataFrame) -> list[str]:
	errors = []

	duplicate_node_count = eid_nodes.duplicated(subset=["node_id"]).sum()

	if duplicate_node_count > 0:
		errors.append(f"eid_nodes has {duplicate_node_count} duplicate node_id values")

	return errors


def validate_no_duplicate_edges(eid_edges: pd.DataFrame) -> list[str]:
	errors = []

	duplicate_edge_count = eid_edges.duplicated(
		subset=[
			"source_node_id",
			"target_node_id",
			"relationship_type",
		]
	).sum()

	if duplicate_edge_count > 0:
		errors.append(f"eid_edges has {duplicate_edge_count} duplicate edges")

	return errors


def validate_edge_nodes_exist(
	eid_nodes: pd.DataFrame,
	eid_edges: pd.DataFrame,
) -> list[str]:
	errors = []

	node_ids = set(eid_nodes["node_id"].dropna().astype(str))

	missing_source_count = (~eid_edges["source_node_id"].isin(node_ids)).sum()
	missing_target_count = (~eid_edges["target_node_id"].isin(node_ids)).sum()

	if missing_source_count > 0:
		errors.append(f"eid_edges has {missing_source_count} edges with missing source_node_id")

	if missing_target_count > 0:
		errors.append(f"eid_edges has {missing_target_count} edges with missing target_node_id")

	return errors


def validate_seed_component_mapping(
	eid_seed_entities: pd.DataFrame,
	eid_seed_component_map: pd.DataFrame,
	eid_unmatched_seeds: pd.DataFrame,
) -> list[str]:
	errors = []

	matched_seed_count = eid_seed_entities["seed_entity_key"].nunique()
	mapped_seed_count = eid_seed_component_map["seed_entity_key"].nunique()
	unmatched_seed_count = eid_unmatched_seeds["seed_customer_id"].nunique() if len(eid_unmatched_seeds) > 0 else 0

	if matched_seed_count != mapped_seed_count:
		errors.append(
			f"eid_seed_component_map maps {mapped_seed_count} seeds, but eid_seed_entities has {matched_seed_count} matched seeds"
		)

	if unmatched_seed_count > 0:
		errors.append(f"eid_unmatched_seeds has {unmatched_seed_count} unmatched seed customers")

	return errors


def validate_component_counts(
	eid_nodes: pd.DataFrame,
	eid_edges: pd.DataFrame,
	eid_components: pd.DataFrame,
) -> list[str]:
	errors = []

	node_counts = (
		eid_nodes
		.groupby("component_id", dropna=False)
		.agg(
			actual_graph_node_count=("node_id", "nunique"),
			actual_entity_count=("node_type", lambda values: (values == "ENTITY").sum()),
			actual_eid_node_count=("node_type", lambda values: (values == "EMIRATES_ID").sum()),
		)
		.reset_index()
	)

	edge_counts = (
		eid_edges
		.groupby("component_id", dropna=False)
		.agg(actual_graph_edge_count=("source_node_id", "count"))
		.reset_index()
	)

	component_check = (
		eid_components
		.merge(node_counts, on="component_id", how="left")
		.merge(edge_counts, on="component_id", how="left")
	)

	component_check["actual_graph_node_count"] = component_check["actual_graph_node_count"].fillna(0)
	component_check["actual_entity_count"] = component_check["actual_entity_count"].fillna(0)
	component_check["actual_eid_node_count"] = component_check["actual_eid_node_count"].fillna(0)
	component_check["actual_graph_edge_count"] = component_check["actual_graph_edge_count"].fillna(0)

	if (component_check["graph_node_count"] != component_check["actual_graph_node_count"]).sum() > 0:
		errors.append("eid_components has graph_node_count mismatches")

	if (component_check["component_entity_count"] != component_check["actual_entity_count"]).sum() > 0:
		errors.append("eid_components has component_entity_count mismatches")

	if (component_check["eid_node_count"] != component_check["actual_eid_node_count"]).sum() > 0:
		errors.append("eid_components has eid_node_count mismatches")

	if (component_check["graph_edge_count"] != component_check["actual_graph_edge_count"]).sum() > 0:
		errors.append("eid_components has graph_edge_count mismatches")

	return errors


def validate_eid_graph(eid_graph: dict[str, pd.DataFrame]) -> list[str]:
	errors = []

	errors.extend(validate_no_duplicate_nodes(eid_graph["eid_nodes"]))
	errors.extend(validate_no_duplicate_edges(eid_graph["eid_edges"]))
	errors.extend(validate_edge_nodes_exist(eid_graph["eid_nodes"], eid_graph["eid_edges"]))
	errors.extend(
		validate_seed_component_mapping(
			eid_seed_entities=eid_graph["eid_seed_entities"],
			eid_seed_component_map=eid_graph["eid_seed_component_map"],
			eid_unmatched_seeds=eid_graph["eid_unmatched_seeds"],
		)
	)
	errors.extend(
		validate_component_counts(
			eid_nodes=eid_graph["eid_nodes"],
			eid_edges=eid_graph["eid_edges"],
			eid_components=eid_graph["eid_components"],
		)
	)

	return errors
