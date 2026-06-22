from collections import deque

import pandas as pd


def _node_label_map(combined_nodes: pd.DataFrame) -> dict[str, str]:
	return {
		row["node_id"]: str(row["display_label"])
		for _, row in combined_nodes.iterrows()
	}


def _build_adjacency(combined_edges: pd.DataFrame) -> dict[str, set[str]]:
	adjacency: dict[str, set[str]] = {}

	for _, row in combined_edges.iterrows():
		source = row["source_node_id"]
		target = row["target_node_id"]

		adjacency.setdefault(source, set()).add(target)
		adjacency.setdefault(target, set()).add(source)

	return adjacency


def _shortest_paths_from_seeds(
	combined_nodes: pd.DataFrame,
	combined_edges: pd.DataFrame,
) -> pd.DataFrame:
	labels = _node_label_map(combined_nodes)
	adjacency = _build_adjacency(combined_edges)

	seed_node_ids = (
		combined_nodes
		.loc[
			combined_nodes["seed_entity_flag"] == 1,
			"node_id",
		]
		.tolist()
	)

	if not seed_node_ids:
		return pd.DataFrame([])

	queue = deque()
	visited = {}

	for seed_node_id in seed_node_ids:
		queue.append(seed_node_id)
		visited[seed_node_id] = {
			"distance": 0,
			"path": [seed_node_id],
		}

	while queue:
		current_node_id = queue.popleft()

		for linked_node_id in adjacency.get(current_node_id, set()):
			if linked_node_id not in visited:
				visited[linked_node_id] = {
					"distance": visited[current_node_id]["distance"] + 1,
					"path": visited[current_node_id]["path"] + [linked_node_id],
				}
				queue.append(linked_node_id)

	entity_nodes = combined_nodes[
		combined_nodes["node_type"] == "ENTITY"
	].copy()

	rows = []

	for _, row in entity_nodes.iterrows():
		node_id = row["node_id"]

		if node_id not in visited:
			continue

		path_labels = [
			labels.get(path_node_id, path_node_id)
			for path_node_id in visited[node_id]["path"]
		]

		rows.append({
			"customer_id": row["lookup_customer_id"],
			"entity_type": row["entity_type"],
			"node_role": row["node_role"],
			"distance_from_seed": visited[node_id]["distance"],
			"path": " → ".join(path_labels),
		})

	return (
		pd.DataFrame(rows)
		.sort_values(["distance_from_seed", "customer_id"])
		.reset_index(drop=True)
	)


def _relationship_summary(
	combined_nodes: pd.DataFrame,
	combined_edges: pd.DataFrame,
) -> pd.DataFrame:
	node_lookup = (
		combined_nodes
		.set_index("node_id")
		.to_dict("index")
	)

	rows = []

	for _, edge in combined_edges.iterrows():
		source = node_lookup.get(edge["source_node_id"], {})
		target = node_lookup.get(edge["target_node_id"], {})

		if edge["relationship_layer"] == "IDENTITY":
			rows.append({
				"relationship": "Shared Emirates ID",
				"source": source.get("display_label"),
				"connector": target.get("display_label"),
				"transaction_count": None,
				"transaction_amount": None,
				"interpretation": f"{source.get('display_label')} is linked to {target.get('display_label')} through Emirates ID evidence.",
			})

		elif edge["relationship_layer"] == "LOCAL_COUNTERPARTY_CORE":
			rows.append({
				"relationship": "Shared local counterparty account",
				"source": source.get("display_label"),
				"connector": target.get("display_label"),
				"transaction_count": int(edge.get("transaction_count", 0) or 0),
				"transaction_amount": float(edge.get("transaction_amount", 0) or 0),
				"interpretation": f"{source.get('display_label')} is connected to a shared local counterparty account used by other entities in the graph.",
			})

	return pd.DataFrame(rows)


def interpret_combined_graph(combined_graph: dict[str, pd.DataFrame]) -> dict:
	combined_nodes = combined_graph["combined_nodes"]
	combined_edges = combined_graph["combined_edges"]
	combined_components = combined_graph["combined_components"]

	component = combined_components.iloc[0]

	seed_customers = (
		combined_nodes
		.loc[
			combined_nodes["seed_entity_flag"] == 1,
			"lookup_customer_id",
		]
		.dropna()
		.astype(str)
		.tolist()
	)

	expansion_start_customers = (
		combined_nodes
		.loc[
			combined_nodes["counterparty_expansion_seed_flag"] == 1,
			"lookup_customer_id",
		]
		.dropna()
		.astype(str)
		.tolist()
	)

	linked_customers = (
		combined_nodes
		.loc[
			(combined_nodes["node_type"] == "ENTITY")
			& (combined_nodes["seed_entity_flag"] == 0)
			& (combined_nodes["counterparty_expansion_seed_flag"] == 0),
			"lookup_customer_id",
		]
		.dropna()
		.astype(str)
		.tolist()
	)

	path_summary = _shortest_paths_from_seeds(
		combined_nodes=combined_nodes,
		combined_edges=combined_edges,
	)

	relationship_summary = _relationship_summary(
		combined_nodes=combined_nodes,
		combined_edges=combined_edges,
	)

	identity_edge_count = int(component["identity_edge_count"])
	counterparty_edge_count = int(component["counterparty_core_edge_count"])
	entity_count = int(component["entity_node_count"])
	account_count = int(component["counterparty_account_node_count"])
	transaction_count = int(component["total_transaction_count"])
	transaction_amount = float(component["total_transaction_amount"])

	if identity_edge_count > 0 and counterparty_edge_count > 0:
		network_profile = "Identity-to-counterparty expansion"
		overview = (
			f"The triggered customer expands through an identity relationship first, then reaches a wider local counterparty network. "
			f"The graph contains {entity_count} customer/entity nodes, {account_count} shared local counterparty accounts, "
			f"and {transaction_count} counterparty transactions with total simulated value {transaction_amount:,.0f}."
		)
	elif identity_edge_count > 0:
		network_profile = "Identity-only expansion"
		overview = (
			f"The triggered customer expands through Emirates ID evidence, but the linked entities do not lead to a group-forming local counterparty chain."
		)
	elif counterparty_edge_count > 0:
		network_profile = "Counterparty-only expansion"
		overview = (
			f"The triggered customer expands through shared local counterparty accounts without an identity-link expansion."
		)
	else:
		network_profile = "No material expansion"
		overview = (
			"The triggered customer is present as a seed node, but no shared Emirates ID or group-forming local counterparty chain was found."
		)

	key_findings = []

	if seed_customers:
		key_findings.append({
			"title": "Triggered customer",
			"text": f"The graph was initiated from {', '.join(seed_customers)}.",
			"severity": "info",
		})

	if expansion_start_customers:
		key_findings.append({
			"title": "Expansion handoff",
			"text": (
				f"{', '.join(expansion_start_customers)} was reached through identity evidence and then used to start the local counterparty expansion."
			),
			"severity": "medium",
		})

	if linked_customers:
		key_findings.append({
			"title": "Additional linked entities",
			"text": (
				f"The graph identified {len(linked_customers)} additional linked customer/entity nodes: {', '.join(linked_customers)}."
			),
			"severity": "medium",
		})

	if account_count > 0:
		key_findings.append({
			"title": "Shared counterparty accounts",
			"text": (
				f"{account_count} shared local counterparty account connector(s) were found. These accounts explain how the counterparty portion of the graph expands."
			),
			"severity": "medium",
		})

	if identity_edge_count == 0 and counterparty_edge_count == 0:
		key_findings.append({
			"title": "No expansion found",
			"text": "The seed customer should still be displayed, but there is no additional deterministic relationship chain in the current data.",
			"severity": "low",
		})

	recommended_actions = []

	if identity_edge_count > 0:
		recommended_actions.append("Review the Emirates ID linkage to confirm whether the connected entities represent the same individual or a legitimate shared identity relationship.")

	if counterparty_edge_count > 0:
		recommended_actions.append("Review the shared local counterparty accounts and transaction directions to understand whether the flow pattern is expected or unusual.")

	if len(linked_customers) >= 3:
		recommended_actions.append("Prioritize the highest-connector entities and accounts first, because they explain most of the network expansion.")

	if identity_edge_count == 0 and counterparty_edge_count == 0:
		recommended_actions.append("Treat this as a non-expanding seed in the current relationship layer. Continue with other risk evidence outside the graph.")

	return {
		"network_profile": network_profile,
		"overview": overview,
		"key_findings": key_findings,
		"recommended_actions": recommended_actions,
		"path_summary": path_summary,
		"relationship_summary": relationship_summary,
	}
