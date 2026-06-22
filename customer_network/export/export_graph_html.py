from pathlib import Path
import html
import json

import networkx as nx
import pandas as pd


def clean_value(value: object) -> object:
	if pd.isna(value):
		return None

	return value


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


def build_initial_positions(
	combined_nodes: pd.DataFrame,
	combined_edges: pd.DataFrame,
	width: int,
	height: int,
) -> dict[str, dict[str, float]]:
	graph = nx.Graph()

	for node_id in combined_nodes["node_id"].tolist():
		graph.add_node(node_id)

	for _, row in combined_edges.iterrows():
		graph.add_edge(row["source_node_id"], row["target_node_id"])

	if graph.number_of_nodes() == 1:
		node_id = next(iter(graph.nodes))
		return {
			node_id: {
				"x": width / 2,
				"y": height / 2,
			}
		}

	raw_positions = nx.spring_layout(
		graph,
		seed=42,
		k=1.4,
		iterations=150,
	)

	x_values = [position[0] for position in raw_positions.values()]
	y_values = [position[1] for position in raw_positions.values()]

	min_x = min(x_values)
	max_x = max(x_values)
	min_y = min(y_values)
	max_y = max(y_values)

	x_range = max(max_x - min_x, 0.0001)
	y_range = max(max_y - min_y, 0.0001)

	padding_x = 120
	padding_y = 110

	positions = {}

	for node_id, position in raw_positions.items():
		x = padding_x + ((position[0] - min_x) / x_range) * (width - 2 * padding_x)
		y = padding_y + ((position[1] - min_y) / y_range) * (height - 2 * padding_y)

		positions[node_id] = {
			"x": float(x),
			"y": float(y),
		}

	return positions


def export_graph_html(
	combined_nodes: pd.DataFrame,
	combined_edges: pd.DataFrame,
	output_path: str | Path,
	title: str = "Customer Network Graph",
) -> Path:
	output_path = Path(output_path)
	output_path.parent.mkdir(parents=True, exist_ok=True)

	width = 1500
	height = 850

	initial_positions = build_initial_positions(
		combined_nodes=combined_nodes,
		combined_edges=combined_edges,
		width=width,
		height=height,
	)

	nodes = []

	for _, row in combined_nodes.iterrows():
		position = initial_positions[row["node_id"]]

		nodes.append({
			"id": row["node_id"],
			"label": row["display_label"],
			"title": build_node_title(row),
			"group": get_node_group(row["node_type"], row["node_role"]),
			"nodeType": row["node_type"],
			"nodeRole": row["node_role"],
			"x": position["x"],
			"y": position["y"],
		})

	edges = []

	for index, row in combined_edges.reset_index(drop=True).iterrows():
		edge_group = get_edge_group(row["relationship_layer"])

		edges.append({
			"id": f"edge_{index}",
			"from": row["source_node_id"],
			"to": row["target_node_id"],
			"title": build_edge_title(row),
			"group": edge_group,
			"label": "EID" if edge_group == "identity" else "Account",
		})

	layout_key = "|".join(sorted(combined_nodes["node_id"].astype(str).tolist()))

	html_template = """<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8" />
	<meta name="viewport" content="width=device-width, initial-scale=1" />
	<title>__TITLE_HTML__</title>
	<style>
		body {
			margin: 0;
			font-family: Arial, sans-serif;
			background: #f7f7f7;
			color: #222;
		}

		.header {
			padding: 16px 20px;
			background: white;
			border-bottom: 1px solid #ddd;
		}

		.header h1 {
			margin: 0 0 6px 0;
			font-size: 20px;
		}

		.header p {
			margin: 0;
			font-size: 13px;
			color: #555;
		}

		.toolbar {
			display: flex;
			flex-wrap: wrap;
			align-items: center;
			gap: 10px;
			padding: 10px 20px;
			background: white;
			border-bottom: 1px solid #ddd;
		}

		.toolbar button {
			border: 1px solid #cbd5e1;
			background: #ffffff;
			color: #0f172a;
			border-radius: 10px;
			font-size: 13px;
			font-weight: 700;
			padding: 8px 12px;
			cursor: pointer;
		}

		.toolbar button:hover {
			background: #f1f5f9;
		}

		.toolbar .primary {
			background: #ef4444;
			color: white;
			border-color: #ef4444;
		}

		.toolbar .primary:hover {
			background: #dc2626;
		}

		.status {
			font-size: 12px;
			color: #64748b;
			margin-left: 4px;
		}

		.legend {
			display: flex;
			flex-wrap: wrap;
			gap: 12px;
			padding: 10px 20px;
			background: white;
			border-bottom: 1px solid #ddd;
			font-size: 13px;
		}

		.legend-item {
			display: flex;
			align-items: center;
			gap: 6px;
		}

		.legend-dot {
			width: 12px;
			height: 12px;
			border-radius: 50%;
			display: inline-block;
		}

		.canvas-wrapper {
			overflow: auto;
			height: calc(100vh - 166px);
			background: #fafafa;
		}

		svg {
			background: #fafafa;
			user-select: none;
		}

		.node {
			cursor: grab;
		}

		.node.dragging {
			cursor: grabbing;
		}

		.node-label {
			font-size: 13px;
			font-weight: 700;
			fill: #222;
			pointer-events: none;
		}

		.node-role {
			font-size: 9px;
			fill: #555;
			pointer-events: none;
		}

		.edge-label {
			font-size: 11px;
			fill: #555;
			font-weight: 700;
			paint-order: stroke;
			stroke: #fafafa;
			stroke-width: 4px;
			stroke-linejoin: round;
			pointer-events: none;
		}
	</style>
</head>
<body>
	<div class="header">
		<h1>__TITLE_HTML__</h1>
		<p>Drag nodes to arrange the network. Hover over nodes and edges for details. Use Save layout to keep your arrangement in this browser.</p>
	</div>

	<div class="toolbar">
		<button class="primary" id="saveLayoutButton">Save layout</button>
		<button id="resetLayoutButton">Reset layout</button>
		<button id="downloadLayoutButton">Download layout JSON</button>
		<span class="status" id="layoutStatus">Layout not saved yet.</span>
	</div>

	<div class="legend">
		<div class="legend-item"><span class="legend-dot" style="background:#d62728"></span>Original seed</div>
		<div class="legend-item"><span class="legend-dot" style="background:#ff7f0e"></span>Counterparty expansion start</div>
		<div class="legend-item"><span class="legend-dot" style="background:#1f77b4"></span>Linked customer/entity</div>
		<div class="legend-item"><span class="legend-dot" style="background:#9467bd"></span>Emirates ID connector</div>
		<div class="legend-item"><span class="legend-dot" style="background:#2ca02c"></span>Local counterparty account</div>
	</div>

	<div class="canvas-wrapper">
		<svg id="graphSvg" width="__WIDTH__" height="__HEIGHT__" viewBox="0 0 __WIDTH__ __HEIGHT__"></svg>
	</div>

	<script>
		const svgNamespace = "http://www.w3.org/2000/svg";
		const initialNodes = __NODES_JSON__;
		const edges = __EDGES_JSON__;
		const storageKey = "customer-network-layout:" + __LAYOUT_KEY_JSON__;

		const svg = document.getElementById("graphSvg");
		const layoutStatus = document.getElementById("layoutStatus");

		const nodes = new Map();
		const initialPositions = new Map();
		const nodeElements = new Map();
		const edgeElements = new Map();
		const edgeLabelElements = new Map();

		let draggingNodeId = null;
		let dragOffset = { x: 0, y: 0 };

		function clone(value) {
			return JSON.parse(JSON.stringify(value));
		}

		function createSvgElement(name, attributes = {}) {
			const element = document.createElementNS(svgNamespace, name);

			for (const [key, value] of Object.entries(attributes)) {
				if (value !== null && value !== undefined && value !== "") {
					element.setAttribute(key, value);
				}
			}

			return element;
		}

		function nodeStyle(node) {
			if (node.group === "seed_entity") {
				return { fill: "#d62728", stroke: "#8c1d1d", shape: "circle", radius: 37 };
			}

			if (node.group === "counterparty_expansion_start") {
				return { fill: "#ff7f0e", stroke: "#a85108", shape: "circle", radius: 34 };
			}

			if (node.group === "linked_entity") {
				return { fill: "#1f77b4", stroke: "#15527d", shape: "circle", radius: 32 };
			}

			if (node.group === "emirates_id") {
				return { fill: "#9467bd", stroke: "#5e3f7a", shape: "diamond", radius: 34 };
			}

			if (node.group === "local_counterparty_account") {
				return { fill: "#2ca02c", stroke: "#1d6b1d", shape: "square", radius: 31 };
			}

			return { fill: "#999999", stroke: "#555555", shape: "circle", radius: 30 };
		}

		function edgeStyle(edge) {
			if (edge.group === "identity") {
				return { stroke: "#9467bd", dasharray: "7 5" };
			}

			if (edge.group === "local_counterparty") {
				return { stroke: "#2ca02c", dasharray: "" };
			}

			return { stroke: "#999999", dasharray: "" };
		}

		function loadNodes() {
			const savedLayoutRaw = localStorage.getItem(storageKey);
			let savedLayout = null;

			if (savedLayoutRaw) {
				try {
					savedLayout = JSON.parse(savedLayoutRaw);
				} catch {
					savedLayout = null;
				}
			}

			for (const node of initialNodes) {
				const workingNode = clone(node);
				initialPositions.set(node.id, { x: node.x, y: node.y });

				if (savedLayout && savedLayout[node.id]) {
					workingNode.x = savedLayout[node.id].x;
					workingNode.y = savedLayout[node.id].y;
				}

				nodes.set(node.id, workingNode);
			}

			if (savedLayout) {
				layoutStatus.textContent = "Saved layout loaded from this browser.";
			}
		}

		function getSvgPoint(event) {
			const point = svg.createSVGPoint();
			point.x = event.clientX;
			point.y = event.clientY;
			return point.matrixTransform(svg.getScreenCTM().inverse());
		}

		function renderEdges() {
			for (const edge of edges) {
				const source = nodes.get(edge.from);
				const target = nodes.get(edge.to);
				const style = edgeStyle(edge);

				const group = createSvgElement("g", { class: "edge" });

				const title = createSvgElement("title");
				title.textContent = edge.title;
				group.appendChild(title);

				const line = createSvgElement("line", {
					x1: source.x,
					y1: source.y,
					x2: target.x,
					y2: target.y,
					stroke: style.stroke,
					"stroke-width": 3,
					"stroke-dasharray": style.dasharray,
				});

				const label = createSvgElement("text", {
					x: (source.x + target.x) / 2,
					y: (source.y + target.y) / 2 - 12,
					"text-anchor": "middle",
					class: "edge-label",
				});

				label.textContent = edge.label;

				group.appendChild(line);
				group.appendChild(label);
				svg.appendChild(group);

				edgeElements.set(edge.id, line);
				edgeLabelElements.set(edge.id, label);
			}
		}

		function renderNodeShape(group, node) {
			const style = nodeStyle(node);

			if (style.shape === "diamond") {
				group.appendChild(
					createSvgElement("polygon", {
						points: `0,${-style.radius} ${style.radius},0 0,${style.radius} ${-style.radius},0`,
						fill: style.fill,
						stroke: style.stroke,
						"stroke-width": 3,
					})
				);
				return;
			}

			if (style.shape === "square") {
				group.appendChild(
					createSvgElement("rect", {
						x: -style.radius,
						y: -style.radius,
						width: style.radius * 2,
						height: style.radius * 2,
						rx: 9,
						fill: style.fill,
						stroke: style.stroke,
						"stroke-width": 3,
					})
				);
				return;
			}

			group.appendChild(
				createSvgElement("circle", {
					cx: 0,
					cy: 0,
					r: style.radius,
					fill: style.fill,
					stroke: style.stroke,
					"stroke-width": 3,
				})
			);
		}

		function renderNodes() {
			for (const node of nodes.values()) {
				const group = createSvgElement("g", {
					class: "node",
					transform: `translate(${node.x}, ${node.y})`,
				});

				const title = createSvgElement("title");
				title.textContent = node.title;
				group.appendChild(title);

				renderNodeShape(group, node);

				const label = createSvgElement("text", {
					x: 0,
					y: 56,
					"text-anchor": "middle",
					class: "node-label",
				});
				label.textContent = node.label;
				group.appendChild(label);

				const role = createSvgElement("text", {
					x: 0,
					y: 74,
					"text-anchor": "middle",
					class: "node-role",
				});
				role.textContent = node.nodeRole;
				group.appendChild(role);

				group.addEventListener("pointerdown", (event) => {
					event.preventDefault();
					draggingNodeId = node.id;

					const point = getSvgPoint(event);
					dragOffset.x = node.x - point.x;
					dragOffset.y = node.y - point.y;

					group.classList.add("dragging");
					group.setPointerCapture(event.pointerId);
				});

				group.addEventListener("pointerup", () => {
					group.classList.remove("dragging");
					draggingNodeId = null;
				});

				nodeElements.set(node.id, group);
				svg.appendChild(group);
			}
		}

		function updatePositions() {
			for (const node of nodes.values()) {
				const element = nodeElements.get(node.id);
				element.setAttribute("transform", `translate(${node.x}, ${node.y})`);
			}

			for (const edge of edges) {
				const source = nodes.get(edge.from);
				const target = nodes.get(edge.to);
				const line = edgeElements.get(edge.id);
				const label = edgeLabelElements.get(edge.id);

				line.setAttribute("x1", source.x);
				line.setAttribute("y1", source.y);
				line.setAttribute("x2", target.x);
				line.setAttribute("y2", target.y);

				label.setAttribute("x", (source.x + target.x) / 2);
				label.setAttribute("y", (source.y + target.y) / 2 - 12);
			}
		}

		function saveLayout() {
			const layout = {};

			for (const node of nodes.values()) {
				layout[node.id] = {
					x: Math.round(node.x),
					y: Math.round(node.y),
				};
			}

			localStorage.setItem(storageKey, JSON.stringify(layout, null, 2));
			layoutStatus.textContent = "Layout saved in this browser.";
		}

		function resetLayout() {
			localStorage.removeItem(storageKey);

			for (const node of nodes.values()) {
				const initialPosition = initialPositions.get(node.id);
				node.x = initialPosition.x;
				node.y = initialPosition.y;
			}

			updatePositions();
			layoutStatus.textContent = "Layout reset.";
		}

		function downloadLayout() {
			const layout = {};

			for (const node of nodes.values()) {
				layout[node.id] = {
					label: node.label,
					x: Math.round(node.x),
					y: Math.round(node.y),
				};
			}

			const blob = new Blob([JSON.stringify(layout, null, 2)], {
				type: "application/json",
			});

			const url = URL.createObjectURL(blob);
			const link = document.createElement("a");
			link.href = url;
			link.download = "customer_network_layout.json";
			link.click();

			URL.revokeObjectURL(url);
		}

		svg.addEventListener("pointermove", (event) => {
			if (!draggingNodeId) {
				return;
			}

			const node = nodes.get(draggingNodeId);
			const point = getSvgPoint(event);

			node.x = point.x + dragOffset.x;
			node.y = point.y + dragOffset.y;

			updatePositions();
			layoutStatus.textContent = "Layout changed. Click Save layout to keep it.";
		});

		window.addEventListener("pointerup", () => {
			draggingNodeId = null;

			for (const element of nodeElements.values()) {
				element.classList.remove("dragging");
			}
		});

		document.getElementById("saveLayoutButton").addEventListener("click", saveLayout);
		document.getElementById("resetLayoutButton").addEventListener("click", resetLayout);
		document.getElementById("downloadLayoutButton").addEventListener("click", downloadLayout);

		loadNodes();
		renderEdges();
		renderNodes();
	</script>
</body>
</html>
"""

	html_content = (
		html_template
		.replace("__TITLE_HTML__", html.escape(title))
		.replace("__WIDTH__", str(width))
		.replace("__HEIGHT__", str(height))
		.replace("__NODES_JSON__", json.dumps(nodes, indent=2))
		.replace("__EDGES_JSON__", json.dumps(edges, indent=2))
		.replace("__LAYOUT_KEY_JSON__", json.dumps(layout_key))
	)

	output_path.write_text(html_content, encoding="utf-8")

	return output_path
