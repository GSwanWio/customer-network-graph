from pathlib import Path
import html

import pandas as pd


def clean_value(value: object) -> object:
	if pd.isna(value):
		return None

	return value


def get_node_style(node_type: str, node_role: str) -> dict[str, str]:
	if node_role == "SEED_ENTITY":
		return {
			"fill": "#d62728",
			"stroke": "#8c1d1d",
			"shape": "circle",
		}

	if node_role == "COUNTERPARTY_EXPANSION_START_ENTITY":
		return {
			"fill": "#ff7f0e",
			"stroke": "#a85108",
			"shape": "circle",
		}

	if node_type == "ENTITY":
		return {
			"fill": "#1f77b4",
			"stroke": "#15527d",
			"shape": "circle",
		}

	if node_type == "EMIRATES_ID":
		return {
			"fill": "#9467bd",
			"stroke": "#5e3f7a",
			"shape": "diamond",
		}

	if node_type == "LOCAL_COUNTERPARTY_ACCOUNT":
		return {
			"fill": "#2ca02c",
			"stroke": "#1d6b1d",
			"shape": "square",
		}

	return {
		"fill": "#999999",
		"stroke": "#555555",
		"shape": "circle",
	}


def get_edge_style(relationship_layer: str) -> dict[str, str]:
	if relationship_layer == "IDENTITY":
		return {
			"stroke": "#9467bd",
			"dasharray": "6 4",
			"label": "EID",
		}

	if relationship_layer == "LOCAL_COUNTERPARTY_CORE":
		return {
			"stroke": "#2ca02c",
			"dasharray": "",
			"label": "Account",
		}

	return {
		"stroke": "#999999",
		"dasharray": "",
		"label": "",
	}


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

	return "\n".join(lines)


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

	return "\n".join(lines)


def export_graph_html(
	combined_nodes: pd.DataFrame,
	combined_edges: pd.DataFrame,
	output_path: str | Path,
	title: str = "Customer Network Graph",
) -> Path:
	output_path = Path(output_path)
	output_path.parent.mkdir(parents=True, exist_ok=True)

	display_order = [
		"ENTITY|SME|CUST_1",
		"EID|43C41990C303B9D7FE501AE51203229235F27F191B3187FB962CCF70EE76C181",
		"ENTITY|RETAIL|CUST_2",
		"LOCAL_COUNTERPARTY_ACCOUNT|1D1D8D1FC1BB7CD46F9F3B92FB26547122D480C9F85BEE5DADB5AAB80C77DE20",
		"ENTITY|SME|CUST_3",
		"LOCAL_COUNTERPARTY_ACCOUNT|7266EE5B3812D9C647CA459B3A040269EDD709A412F602D1714CF35E8E24C82B",
		"ENTITY|RETAIL|CUST_4",
		"LOCAL_COUNTERPARTY_ACCOUNT|3395DBCB7506478D1F75DFDBC0F45CA8DC110CE4AD672CFCB2B96056D26F73D4",
		"ENTITY|SME|CUST_5",
	]

	nodes_by_id = {
		row["node_id"]: row
		for _, row in combined_nodes.iterrows()
	}

	ordered_node_ids = [
		node_id
		for node_id in display_order
		if node_id in nodes_by_id
	]

	for node_id in combined_nodes["node_id"].tolist():
		if node_id not in ordered_node_ids:
			ordered_node_ids.append(node_id)

	positions = {}
	start_x = 110
	start_y = 220
	step_x = 220
	step_y = 230
	nodes_per_row = 5

	for index, node_id in enumerate(ordered_node_ids):
		row_index = index // nodes_per_row
		column_index = index % nodes_per_row

		if row_index % 2 == 1:
			column_index = nodes_per_row - 1 - column_index

		positions[node_id] = {
			"x": start_x + column_index * step_x,
			"y": start_y + row_index * step_y,
		}

	width = max(1180, start_x * 2 + step_x * (nodes_per_row - 1))
	height = max(620, start_y * 2 + step_y * ((len(ordered_node_ids) - 1) // nodes_per_row))

	edge_elements = []

	for _, row in combined_edges.iterrows():
		source_node_id = row["source_node_id"]
		target_node_id = row["target_node_id"]

		if source_node_id not in positions or target_node_id not in positions:
			continue

		source = positions[source_node_id]
		target = positions[target_node_id]
		style = get_edge_style(row["relationship_layer"])

		label_x = (source["x"] + target["x"]) / 2
		label_y = (source["y"] + target["y"]) / 2 - 14

		edge_elements.append(f'''
			<g class="edge">
				<title>{html.escape(build_edge_title(row))}</title>
				<line
					x1="{source["x"]}"
					y1="{source["y"]}"
					x2="{target["x"]}"
					y2="{target["y"]}"
					stroke="{style["stroke"]}"
					stroke-width="3"
					stroke-dasharray="{style["dasharray"]}"
				/>
				<text x="{label_x}" y="{label_y}" text-anchor="middle" class="edge-label">{html.escape(style["label"])}</text>
			</g>
		''')

	node_elements = []

	for node_id in ordered_node_ids:
		row = nodes_by_id[node_id]
		position = positions[node_id]
		style = get_node_style(row["node_type"], row["node_role"])
		label = html.escape(str(row["display_label"]))

		if style["shape"] == "diamond":
			shape = f'''
				<polygon
					points="{position["x"]},{position["y"] - 34} {position["x"] + 34},{position["y"]} {position["x"]},{position["y"] + 34} {position["x"] - 34},{position["y"]}"
					fill="{style["fill"]}"
					stroke="{style["stroke"]}"
					stroke-width="3"
				/>
			'''
		elif style["shape"] == "square":
			shape = f'''
				<rect
					x="{position["x"] - 30}"
					y="{position["y"] - 30}"
					width="60"
					height="60"
					rx="8"
					fill="{style["fill"]}"
					stroke="{style["stroke"]}"
					stroke-width="3"
				/>
			'''
		else:
			radius = 36 if row["node_role"] == "SEED_ENTITY" else 32
			shape = f'''
				<circle
					cx="{position["x"]}"
					cy="{position["y"]}"
					r="{radius}"
					fill="{style["fill"]}"
					stroke="{style["stroke"]}"
					stroke-width="3"
				/>
			'''

		node_elements.append(f'''
			<g class="node">
				<title>{html.escape(build_node_title(row))}</title>
				{shape}
				<text x="{position["x"]}" y="{position["y"] + 56}" text-anchor="middle" class="node-label">{label}</text>
				<text x="{position["x"]}" y="{position["y"] + 74}" text-anchor="middle" class="node-role">{html.escape(str(row["node_role"]))}</text>
			</g>
		''')

	html_content = f"""<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8" />
	<meta name="viewport" content="width=device-width, initial-scale=1" />
	<title>{html.escape(title)}</title>
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

		.canvas-wrapper {{
			overflow: auto;
			height: calc(100vh - 116px);
			background: #fafafa;
		}}

		svg {{
			min-width: 100%;
			background: #fafafa;
		}}

		.node-label {{
			font-size: 13px;
			font-weight: 700;
			fill: #222;
		}}

		.node-role {{
			font-size: 9px;
			fill: #555;
		}}

		.edge-label {{
			font-size: 11px;
			fill: #555;
			font-weight: 700;
			paint-order: stroke;
			stroke: #fafafa;
			stroke-width: 4px;
			stroke-linejoin: round;
		}}

		.node:hover,
		.edge:hover {{
			cursor: pointer;
			filter: brightness(1.05);
		}}
	</style>
</head>
<body>
	<div class="header">
		<h1>{html.escape(title)}</h1>
		<p>Self-contained visual. Hover over nodes and edges for details. No external JavaScript is required.</p>
	</div>

	<div class="legend">
		<div class="legend-item"><span class="legend-dot" style="background:#d62728"></span>Original seed</div>
		<div class="legend-item"><span class="legend-dot" style="background:#ff7f0e"></span>Counterparty expansion start</div>
		<div class="legend-item"><span class="legend-dot" style="background:#1f77b4"></span>Linked customer/entity</div>
		<div class="legend-item"><span class="legend-dot" style="background:#9467bd"></span>Emirates ID connector</div>
		<div class="legend-item"><span class="legend-dot" style="background:#2ca02c"></span>Local counterparty account</div>
	</div>

	<div class="canvas-wrapper">
		<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
			{''.join(edge_elements)}
			{''.join(node_elements)}
		</svg>
	</div>
</body>
</html>
"""

	output_path.write_text(html_content, encoding="utf-8")

	return output_path
