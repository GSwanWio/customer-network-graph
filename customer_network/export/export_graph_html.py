from pathlib import Path
import json

import pandas as pd


def get_node_group(node_type: str, node_role: str) -> str:
	if node_role == "SEED_ENTITY":
		return "seed_entity"

	if node_role == "COUNTERPARTY_EXPANSION_START_ENTITY":
		return "counterparty_expansion_start"

	if node_type == "ENTITY":
		return "linked_entity"

	if node_type == "EMIRATES_ID":
		return "emirates_id"

	if node_type == "LOCAL_COUNTERPARTY_ACCOUNT":
		return "local_counterparty_account"

	return "default"


def get_edge_group(relationship_layer: str) -> str:
	if relationship_layer == "IDENTITY":
		return "identity"

	if relationship_layer == "LOCAL_COUNTERPARTY_CORE":
		return "local_counterparty"

	return "default"


def clean_value(value: object) -> object:
	if pd.isna(value):
		return None

	return value


def build_node_title(row: pd.Series) -> str:
	lines = [
		f"Node ID: {row['node_id']}",
		f"Type: {row['node_type']}",
		f"Role: {row['node_role']}",
		f"Layers: {row['network_layers']}",
	]

	if clean_value(row.get("entity_type")) is not None:
		lines.append(f"Entity type: {row['entity_type']}")

	if clean_value(row.get("lookup_customer_id")) is not None:
		lines.append(f"Customer ID: {row['lookup_customer_id']}")

	if clean_value(row.get("emirates_id_masked")) is not None:
		lines.append(f"Emirates ID: {row['emirates_id_masked']}")

	if clean_value(row.get("counterparty_account_masked")) is not None:
		lines.append(f"Counterparty account: {row['counterparty_account_masked']}")

	return "\\n".join(lines)


def build_edge_title(row: pd.Series) -> str:
	lines = [
		f"Relationship: {row['relationship_type']}",
		f"Layer: {row['relationship_layer']}",
		f"Role: {row['edge_role']}",
	]

	if row["relationship_layer"] == "LOCAL_COUNTERPARTY_CORE":
		lines.extend([
			f"Direction: {clean_value(row.get('entity_counterparty_direction'))}",
			f"Transaction count: {row.get('transaction_count', 0)}",
			f"Transaction amount: {row.get('transaction_amount', 0)}",
			f"First seen: {clean_value(row.get('first_seen_at'))}",
			f"Last seen: {clean_value(row.get('last_seen_at'))}",
		])

	if row["relationship_layer"] == "IDENTITY":
		lines.append(f"Emirates ID: {clean_value(row.get('emirates_id_masked'))}")

	return "\\n".join(lines)


def export_graph_html(
	combined_nodes: pd.DataFrame,
	combined_edges: pd.DataFrame,
	output_path: str | Path,
	title: str = "Customer Network Graph",
) -> Path:
	output_path = Path(output_path)
	output_path.parent.mkdir(parents=True, exist_ok=True)

	nodes = []

	for _, row in combined_nodes.iterrows():
		nodes.append({
			"id": row["node_id"],
			"label": row["display_label"],
			"title": build_node_title(row),
			"group": get_node_group(row["node_type"], row["node_role"]),
		})

	edges = []

	for _, row in combined_edges.iterrows():
		edges.append({
			"from": row["source_node_id"],
			"to": row["target_node_id"],
			"title": build_edge_title(row),
			"group": get_edge_group(row["relationship_layer"]),
			"label": "EID" if row["relationship_layer"] == "IDENTITY" else "Account",
		})

	html = f"""<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8" />
	<meta name="viewport" content="width=device-width, initial-scale=1" />
	<title>{title}</title>
	<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
	<style>
		body {{
			margin: 0;
			font-family: Arial, sans-serif;
			background: #f7f7f7;
			color: #222;
		}}

		.header {{
			padding: 16px 20px;
			background: white;
			border-bottom: 1px solid #ddd;
		}}

		.header h1 {{
			margin: 0 0 6px 0;
			font-size: 20px;
		}}

		.header p {{
			margin: 0;
			font-size: 13px;
			color: #555;
		}}

		.legend {{
			display: flex;
			flex-wrap: wrap;
			gap: 12px;
			padding: 10px 20px;
			background: white;
			border-bottom: 1px solid #ddd;
			font-size: 13px;
		}}

		.legend-item {{
			display: flex;
			align-items: center;
			gap: 6px;
		}}

		.legend-dot {{
			width: 12px;
			height: 12px;
			border-radius: 50%;
			display: inline-block;
		}}

		#network {{
			width: 100vw;
			height: calc(100vh - 112px);
			background: #fafafa;
		}}
	</style>
</head>
<body>
	<div class="header">
		<h1>{title}</h1>
		<p>Interactive combined customer relationship graph. Hover over nodes and edges for details. Drag nodes to rearrange the view.</p>
	</div>

	<div class="legend">
		<div class="legend-item"><span class="legend-dot" style="background:#d62728"></span>Original seed</div>
		<div class="legend-item"><span class="legend-dot" style="background:#ff7f0e"></span>Counterparty expansion start</div>
		<div class="legend-item"><span class="legend-dot" style="background:#1f77b4"></span>Linked customer/entity</div>
		<div class="legend-item"><span class="legend-dot" style="background:#9467bd"></span>Emirates ID connector</div>
		<div class="legend-item"><span class="legend-dot" style="background:#2ca02c"></span>Local counterparty account</div>
	</div>

	<div id="network"></div>

	<script>
		const nodes = new vis.DataSet({json.dumps(nodes, indent=2)});
		const edges = new vis.DataSet({json.dumps(edges, indent=2)});

		const container = document.getElementById("network");

		const data = {{
			nodes: nodes,
			edges: edges
		}};

		const options = {{
			nodes: {{
				shape: "dot",
				size: 22,
				font: {{
					size: 14,
					face: "Arial"
				}},
				borderWidth: 2
			}},
			edges: {{
				width: 2,
				smooth: {{
					type: "continuous"
				}},
				font: {{
					size: 11,
					align: "middle"
				}}
			}},
			groups: {{
				seed_entity: {{
					color: {{
						background: "#d62728",
						border: "#8c1d1d"
					}},
					size: 30
				}},
				counterparty_expansion_start: {{
					color: {{
						background: "#ff7f0e",
						border: "#a85108"
					}},
					size: 28
				}},
				linked_entity: {{
					color: {{
						background: "#1f77b4",
						border: "#15527d"
					}}
				}},
				emirates_id: {{
					color: {{
						background: "#9467bd",
						border: "#5e3f7a"
					}},
					shape: "diamond",
					size: 24
				}},
				local_counterparty_account: {{
					color: {{
						background: "#2ca02c",
						border: "#1d6b1d"
					}},
					shape: "square",
					size: 22
				}}
			}},
			physics: {{
				enabled: true,
				solver: "forceAtlas2Based",
				forceAtlas2Based: {{
					gravitationalConstant: -60,
					centralGravity: 0.01,
					springLength: 120,
					springConstant: 0.08
				}},
				stabilization: {{
					iterations: 200
				}}
			}},
			interaction: {{
				hover: true,
				tooltipDelay: 150,
				navigationButtons: true,
				keyboard: true
			}}
		}};

		new vis.Network(container, data, options);
	</script>
</body>
</html>
"""

	output_path.write_text(html, encoding="utf-8")

	return output_path
