import html
import json
from collections import deque

import streamlit as st
import streamlit.components.v1 as components
from streamlit_agraph import agraph, Config, Edge, Node


CUSTOMERS = {
    "RETAIL_1": {
        "segment": "Retail",
        "summary": "Triggered seed customer. First-level view shows one shared Emirates ID, one common company-like account, and one low-degree account worth expanding.",
    },
    "SME_1": {
        "segment": "SME",
        "summary": "Linked through the same Emirates ID as RETAIL_1. No active simulated fraud indicators.",
    },
    "RETAIL_2": {
        "segment": "Retail",
        "summary": "Linked through ACCOUNT_2. This customer has multiple simulated fraud indicators and should be reviewed.",
    },
    "VICTIM_SOURCE_1": {
        "segment": "Retail",
        "summary": "Simulated source-of-funds customer that sent one large payment into the ACCOUNT_2 path. This is not confirmed victim status.",
    },
    "RETAIL_3": {
        "segment": "Retail",
        "summary": "Isolated seed example. No useful first-level relationship chain is found in the simulated data.",
    },
}

EIDS = {
    "EID_1": {
        "label": "EID ****1001",
        "linked_customers": ["RETAIL_1", "SME_1"],
        "summary": "This Emirates ID is linked to 2 customer entities: RETAIL_1 and SME_1. This is a low-degree deterministic identity connector, so expansion is allowed.",
    },
    "EID_2": {
        "label": "EID ****2002",
        "linked_customers": ["RETAIL_2"],
        "summary": "This Emirates ID is linked to one visible customer only in the simulated data. It is useful as context but does not expand further.",
    },
}

CUSTOMER_EIDS = {
    "RETAIL_1": ["EID_1"],
    "SME_1": ["EID_1"],
    "RETAIL_2": ["EID_2"],
    "VICTIM_SOURCE_1": [],
    "RETAIL_3": [],
}

ACCOUNTS = {
    "BIG_COMPANY_ACCOUNT": {
        "label": "Account ****9011",
        "name": "Mega Services Collections LLC",
        "linked_customer_count": 300,
        "transaction_count": 920,
        "total_amount": 1845000,
        "policy": "BLOCK_BY_DEFAULT",
        "summary": "This account has high transaction volume and approximately 300 linked customers. The name appears company-like, so it may be a legitimate merchant, utility, collections account, payroll provider, or common recipient. Expansion is blocked by default to avoid graph noise.",
    },
    "ACCOUNT_2": {
        "label": "Account ****2202",
        "name": "Low-degree wallet account",
        "linked_customer_count": 3,
        "transaction_count": 15,
        "total_amount": 23750,
        "policy": "ALLOW",
        "summary": "This account is low-degree and group-forming. It links the seed customer to a small number of other customers, so it is a useful path to expand.",
    },
    "CASHOUT_ACCOUNT": {
        "label": "Account ****7788",
        "name": "Cash-out destination account",
        "linked_customer_count": 1,
        "transaction_count": 4,
        "total_amount": 17200,
        "policy": "EVIDENCE_ONLY",
        "summary": "This account is used by one customer only in the simulated data. It does not create a group-forming relationship but provides cash-out context.",
    },
}

CUSTOMER_ACCOUNTS = {
    "RETAIL_1": [
        {"account": "BIG_COMPANY_ACCOUNT", "direction": "Paid to", "transaction_count": 2, "amount": 420},
        {"account": "ACCOUNT_2", "direction": "Paid and received", "transaction_count": 7, "amount": 1250},
    ],
    "RETAIL_2": [
        {"account": "ACCOUNT_2", "direction": "Paid and received", "transaction_count": 7, "amount": 17500},
        {"account": "CASHOUT_ACCOUNT", "direction": "Paid to", "transaction_count": 4, "amount": 17200},
    ],
    "VICTIM_SOURCE_1": [
        {"account": "ACCOUNT_2", "direction": "Paid to", "transaction_count": 1, "amount": 5000},
    ],
    "SME_1": [],
    "RETAIL_3": [],
}

ACCOUNT_CUSTOMERS = {
    "BIG_COMPANY_ACCOUNT": ["RETAIL_1"],
    "ACCOUNT_2": ["RETAIL_1", "RETAIL_2", "VICTIM_SOURCE_1"],
    "CASHOUT_ACCOUNT": ["RETAIL_2"],
}

FRAUD_INDICATORS = {
    "RETAIL_2": [
        {
            "name": "Rapid fund movement",
            "severity": "High",
            "description": "Funds are received and moved onward within a short simulated time window.",
        },
        {
            "name": "Small-value reciprocal activity",
            "severity": "Medium",
            "description": "Repeated small payments move back and forth, which can be consistent with activity simulation.",
        },
        {
            "name": "Flow-through behaviour",
            "severity": "High",
            "description": "A high share of inbound value is moved to another destination account.",
        },
    ],
}

TRANSACTION_PATTERNS = {
    "ACCOUNT_2": [
        {
            "title": "Possible activity simulation",
            "summary": "RETAIL_1 and RETAIL_2 show repeated small-value back-and-forth movement around ACCOUNT_2. This does not prove fraud, but it is useful investigative context.",
            "guidance": "Review timestamps, payment direction, counterparties, and whether there is a legitimate commercial explanation.",
        },
        {
            "title": "Large inbound source-of-funds event",
            "summary": "VICTIM_SOURCE_1 sends one larger simulated payment into the same path before value moves onward. This may represent a source-of-funds event worth checking against fraud reports or dispute activity.",
            "guidance": "Check whether the source account has fraud claims, disputes, account takeover signals, or unusual recent onboarding behaviour.",
        },
    ],
    "BIG_COMPANY_ACCOUNT": [
        {
            "title": "Likely common counterparty",
            "summary": "The account has high customer degree and a company-like name. This is more likely to create noise than a useful small relationship group.",
            "guidance": "Keep visible as context, but do not expand by default unless there is a specific reason.",
        },
    ],
}


def apply_style() -> None:
    st.markdown(
        """
        <style>
            [data-testid="stAppViewContainer"] {
                background: #f5f7fb;
            }

            [data-testid="stSidebar"] {
                background: #101827;
            }

            [data-testid="stSidebar"] * {
                color: #f8fafc;
            }

            .block-container {
                max-width: 1550px;
                padding-top: 2rem;
                padding-bottom: 3rem;
            }

            .hero-card {
                background: linear-gradient(135deg, #111827 0%, #263b63 55%, #355c7d 100%);
                color: white;
                border-radius: 22px;
                padding: 28px 32px;
                margin-bottom: 22px;
                box-shadow: 0 16px 35px rgba(17, 24, 39, 0.18);
            }

            .hero-title {
                font-size: 34px;
                font-weight: 800;
                margin: 0 0 8px 0;
                letter-spacing: -0.03em;
            }

            .hero-subtitle {
                font-size: 15px;
                color: #dbeafe;
                margin: 0;
                max-width: 1000px;
                line-height: 1.5;
            }

            .status-pill {
                display: inline-flex;
                align-items: center;
                border-radius: 999px;
                padding: 6px 12px;
                background: rgba(255,255,255,0.14);
                border: 1px solid rgba(255,255,255,0.22);
                font-size: 12px;
                font-weight: 700;
                color: #ffffff;
                margin-bottom: 14px;
            }

            .panel {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 20px;
                padding: 20px;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
                margin-bottom: 16px;
            }

            .panel-title {
                font-size: 18px;
                font-weight: 800;
                color: #0f172a;
                margin-bottom: 6px;
            }

            .panel-caption {
                font-size: 13px;
                color: #64748b;
                line-height: 1.5;
            }

            .metric-card {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 18px;
                padding: 18px 20px;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
                min-height: 105px;
            }

            .metric-label {
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: #64748b;
                font-weight: 800;
                margin-bottom: 8px;
            }

            .metric-value {
                font-size: 32px;
                line-height: 1;
                color: #0f172a;
                font-weight: 800;
                letter-spacing: -0.04em;
            }

            .metric-helper {
                font-size: 12px;
                color: #64748b;
                margin-top: 8px;
            }

            .insight-box {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                padding: 16px 18px;
                margin-bottom: 12px;
                box-shadow: 0 5px 16px rgba(15, 23, 42, 0.04);
            }

            .insight-title {
                font-weight: 800;
                color: #0f172a;
                margin-bottom: 5px;
            }

            .insight-text {
                color: #475569;
                font-size: 13px;
                line-height: 1.5;
            }

            .badge {
                display: inline-block;
                padding: 4px 9px;
                border-radius: 999px;
                font-size: 11px;
                font-weight: 800;
                margin-right: 6px;
                margin-bottom: 6px;
            }

            .badge-high {
                background: #fee2e2;
                color: #991b1b;
            }

            .badge-medium {
                background: #ffedd5;
                color: #9a3412;
            }

            .badge-low {
                background: #e0f2fe;
                color: #075985;
            }

            .stButton > button {
                border-radius: 13px;
                font-weight: 800;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def ntype_key(node_type: str, key: str) -> str:
    return f"{node_type}|{key}"


def reset_state() -> None:
    st.session_state.v2_nodes = {}
    st.session_state.v2_edges = {}
    st.session_state.v2_history = []
    st.session_state.v2_seed = None
    st.session_state.v2_last_selected_node = None
    st.session_state.v2_selected_node_id = None


def ensure_state() -> None:
    if "v2_nodes" not in st.session_state:
        reset_state()


def customer_risk_count(customer_id: str) -> int:
    return len(FRAUD_INDICATORS.get(customer_id, []))


def add_node(
    node_id: str,
    label: str,
    node_type: str,
    role: str,
    key: str,
    summary: str,
    expand_type: str | None,
    policy: str = "ALLOW",
) -> None:
    existing = st.session_state.v2_nodes.get(node_id, {})
    st.session_state.v2_nodes[node_id] = {
        "id": node_id,
        "label": label,
        "node_type": node_type,
        "role": role,
        "key": key,
        "summary": summary,
        "expand_type": expand_type,
        "policy": policy,
        "expanded": existing.get("expanded", False),
        "risk_count": customer_risk_count(key) if node_type == "CUSTOMER" else 0,
    }


def add_edge(source: str, target: str, label: str, relationship_type: str, summary: str) -> None:
    edge_id = f"{source}->{target}|{relationship_type}|{label}"
    st.session_state.v2_edges[edge_id] = {
        "id": edge_id,
        "source": source,
        "target": target,
        "label": label,
        "relationship_type": relationship_type,
        "summary": summary,
    }


def build_customer_summary(customer_id: str) -> str:
    customer = CUSTOMERS[customer_id]
    eid_count = len(CUSTOMER_EIDS.get(customer_id, []))
    account_count = len(CUSTOMER_ACCOUNTS.get(customer_id, []))
    risk_count = customer_risk_count(customer_id)

    risk_text = (
        f"{risk_count} simulated fraud indicator(s) are active."
        if risk_count > 0
        else "No active simulated fraud indicators."
    )

    return (
        f"{customer_id} is a {customer['segment']} customer. "
        f"{customer['summary']} "
        f"First-level context: {eid_count} EID connector(s), {account_count} account connector(s). "
        f"{risk_text}"
    )


def add_customer_node(customer_id: str, role: str) -> None:
    add_node(
        node_id=ntype_key("CUSTOMER", customer_id),
        label=customer_id,
        node_type="CUSTOMER",
        role=role,
        key=customer_id,
        summary=build_customer_summary(customer_id),
        expand_type="CUSTOMER",
        policy="ALLOW",
    )


def add_customer_connectors(customer_id: str) -> None:
    customer_node = ntype_key("CUSTOMER", customer_id)

    for eid_key in CUSTOMER_EIDS.get(customer_id, []):
        eid = EIDS[eid_key]
        eid_node = ntype_key("EID", eid_key)

        add_node(
            node_id=eid_node,
            label=eid["label"],
            node_type="EID",
            role="IDENTITY_CONNECTOR",
            key=eid_key,
            summary=eid["summary"],
            expand_type="EID",
            policy="ALLOW",
        )

        add_edge(
            source=customer_node,
            target=eid_node,
            label="EID",
            relationship_type="ENTITY_HAS_EMIRATES_ID",
            summary=f"{customer_id} is linked to {eid['label']}.",
        )

    for account_link in CUSTOMER_ACCOUNTS.get(customer_id, []):
        account_key = account_link["account"]
        account = ACCOUNTS[account_key]
        account_node = ntype_key("ACCOUNT", account_key)

        add_node(
            node_id=account_node,
            label=account["label"],
            node_type="ACCOUNT",
            role="COUNTERPARTY_CONNECTOR",
            key=account_key,
            summary=account["summary"],
            expand_type="ACCOUNT",
            policy=account["policy"],
        )

        add_edge(
            source=customer_node,
            target=account_node,
            label=account_link["direction"],
            relationship_type="ENTITY_USES_COUNTERPARTY_ACCOUNT",
            summary=(
                f"{customer_id} has {account_link['transaction_count']} simulated transaction(s) "
                f"with {account['label']} totalling {account_link['amount']:,.0f}."
            ),
        )


def start_investigation(customer_id: str) -> None:
    reset_state()
    st.session_state.v2_seed = customer_id

    add_customer_node(customer_id, role="SEED_CUSTOMER")
    add_customer_connectors(customer_id)

    seed_node = ntype_key("CUSTOMER", customer_id)
    st.session_state.v2_nodes[seed_node]["expanded"] = True

    st.session_state.v2_history.append(
        f"Started investigation from {customer_id}. The first view shows only immediate EID and account connectors."
    )


def expand_eid(eid_key: str) -> str:
    eid = EIDS[eid_key]
    eid_node = ntype_key("EID", eid_key)
    added = []

    for customer_id in eid["linked_customers"]:
        customer_node = ntype_key("CUSTOMER", customer_id)

        if customer_node not in st.session_state.v2_nodes:
            add_customer_node(customer_id, role="LINKED_CUSTOMER")
            added.append(customer_id)

        add_edge(
            source=eid_node,
            target=customer_node,
            label="Linked entity",
            relationship_type="EID_LINKS_CUSTOMER",
            summary=f"{eid['label']} links to {customer_id}.",
        )

    st.session_state.v2_nodes[eid_node]["expanded"] = True

    if added:
        return f"Expanded {eid['label']} and added linked customer(s): {', '.join(added)}."

    return f"Expanded {eid['label']}. No new customer nodes were added."


def expand_account(account_key: str) -> str:
    account = ACCOUNTS[account_key]
    account_node = ntype_key("ACCOUNT", account_key)
    added = []

    for customer_id in ACCOUNT_CUSTOMERS.get(account_key, []):
        customer_node = ntype_key("CUSTOMER", customer_id)

        if customer_node not in st.session_state.v2_nodes:
            add_customer_node(customer_id, role="LINKED_CUSTOMER")
            added.append(customer_id)

        add_edge(
            source=account_node,
            target=customer_node,
            label="Linked customer",
            relationship_type="ACCOUNT_LINKS_CUSTOMER",
            summary=f"{account['label']} links to {customer_id}.",
        )

    st.session_state.v2_nodes[account_node]["expanded"] = True

    pattern_text = " ".join(
        pattern["summary"]
        for pattern in TRANSACTION_PATTERNS.get(account_key, [])
    )

    if added:
        return f"Expanded {account['label']} and added linked customer(s): {', '.join(added)}. {pattern_text}"

    return f"Expanded {account['label']}. No new customers were added. {pattern_text}"


def expand_customer(customer_id: str) -> str:
    add_customer_connectors(customer_id)
    st.session_state.v2_nodes[ntype_key("CUSTOMER", customer_id)]["expanded"] = True
    return f"Expanded customer context for {customer_id}. Added first-level EID and account connectors where available."


def expand_node(node_id: str) -> None:
    node = st.session_state.v2_nodes[node_id]

    if node["expanded"]:
        st.session_state.v2_history.append(f"{node['label']} was already expanded.")
        return

    if node["policy"] == "BLOCK_BY_DEFAULT":
        st.session_state.v2_history.append(
            f"{node['label']} was not expanded because it is a high-degree/common connector blocked by default."
        )
        return

    if node["policy"] == "EVIDENCE_ONLY":
        st.session_state.v2_history.append(
            f"{node['label']} is evidence-only. It is visible as context but does not create a group-forming expansion."
        )
        st.session_state.v2_nodes[node_id]["expanded"] = True
        return

    if node["expand_type"] == "EID":
        message = expand_eid(node["key"])
    elif node["expand_type"] == "ACCOUNT":
        message = expand_account(node["key"])
    elif node["expand_type"] == "CUSTOMER":
        message = expand_customer(node["key"])
    else:
        message = f"{node['label']} has no expansion action."

    st.session_state.v2_history.append(message)


def metric_card(label: str, value: str | int, helper: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-helper">{helper}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def calculate_positions(nodes: list[dict], edges: list[dict]) -> dict[str, dict[str, int]]:
    adjacency: dict[str, set[str]] = {}

    for edge in edges:
        adjacency.setdefault(edge["source"], set()).add(edge["target"])
        adjacency.setdefault(edge["target"], set()).add(edge["source"])

    seed_nodes = [node["id"] for node in nodes if node["role"] == "SEED_CUSTOMER"]
    if not seed_nodes and nodes:
        seed_nodes = [nodes[0]["id"]]

    levels = {}
    queue = deque()

    for seed in seed_nodes:
        levels[seed] = 0
        queue.append(seed)

    while queue:
        current = queue.popleft()
        for linked in adjacency.get(current, set()):
            if linked not in levels:
                levels[linked] = levels[current] + 1
                queue.append(linked)

    for node in nodes:
        if node["id"] not in levels:
            levels[node["id"]] = max(levels.values(), default=0) + 1

    grouped: dict[int, list[dict]] = {}
    for node in nodes:
        grouped.setdefault(levels[node["id"]], []).append(node)

    positions = {}

    for level, level_nodes in grouped.items():
        level_nodes = sorted(level_nodes, key=lambda item: (item["node_type"], item["label"]))
        x = 130 + level * 265

        for index, node in enumerate(level_nodes):
            positions[node["id"]] = {
                "x": x,
                "y": 110 + index * 135,
            }

    return positions


def render_graph_html() -> str:
    nodes = list(st.session_state.v2_nodes.values())
    edges = list(st.session_state.v2_edges.values())
    positions = calculate_positions(nodes, edges)

    for node in nodes:
        node["x"] = positions[node["id"]]["x"]
        node["y"] = positions[node["id"]]["y"]

    width = max(1200, max([node["x"] for node in nodes], default=800) + 220)
    height = max(720, max([node["y"] for node in nodes], default=500) + 180)

    template = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8" />
    <style>
        body { margin: 0; background: #ffffff; font-family: Arial, sans-serif; }
        .graph-header { padding: 12px 14px; border-bottom: 1px solid #e5e7eb; font-size: 13px; color: #64748b; }
        .graph-wrap { overflow: auto; height: 700px; background: #ffffff; }
        svg { background: #ffffff; user-select: none; }
        .node { cursor: grab; }
        .node.dragging { cursor: grabbing; }
        .label { font-size: 12px; font-weight: 800; fill: #0f172a; pointer-events: none; }
        .sub-label { font-size: 9px; fill: #64748b; pointer-events: none; }
        .edge-label { font-size: 10px; fill: #64748b; font-weight: 700; paint-order: stroke; stroke: #ffffff; stroke-width: 4px; pointer-events: none; }
    </style>
</head>
<body>
    <div class="graph-header">
        Drag nodes to arrange the view. Hover over nodes and edges for summaries. Use the Expand next tab to add the next layer.
    </div>
    <div class="graph-wrap">
        <svg id="graph" width="__WIDTH__" height="__HEIGHT__" viewBox="0 0 __WIDTH__ __HEIGHT__"></svg>
    </div>

    <script>
        const ns = "http://www.w3.org/2000/svg";
        const nodes = __NODES_JSON__;
        const edges = __EDGES_JSON__;

        const svg = document.getElementById("graph");
        const nodeMap = new Map(nodes.map(node => [node.id, node]));
        const nodeElements = new Map();
        const edgeElements = new Map();
        const edgeLabelElements = new Map();

        let dragging = null;
        let offset = { x: 0, y: 0 };

        function createSvg(name, attrs) {
            const el = document.createElementNS(ns, name);
            for (const [key, value] of Object.entries(attrs || {})) {
                if (value !== undefined && value !== null) {
                    el.setAttribute(key, value);
                }
            }
            return el;
        }

        function nodeStyle(node) {
            if (node.role === "SEED_CUSTOMER") {
                return { fill: "#d62728", stroke: "#7f1d1d", shape: "circle", size: 34 };
            }
            if (node.node_type === "CUSTOMER" && node.risk_count >= 2) {
                return { fill: "#ef4444", stroke: "#7f1d1d", shape: "circle", size: 34 };
            }
            if (node.node_type === "CUSTOMER") {
                return { fill: "#1f77b4", stroke: "#15527d", shape: "circle", size: 32 };
            }
            if (node.node_type === "EID") {
                return { fill: "#9467bd", stroke: "#5e3f7a", shape: "diamond", size: 34 };
            }
            if (node.policy === "BLOCK_BY_DEFAULT") {
                return { fill: "#94a3b8", stroke: "#475569", shape: "square", size: 31 };
            }
            if (node.node_type === "ACCOUNT") {
                return { fill: "#2ca02c", stroke: "#1d6b1d", shape: "square", size: 31 };
            }
            return { fill: "#999999", stroke: "#555555", shape: "circle", size: 30 };
        }

        function edgeStyle(edge) {
            if (edge.relationship_type.includes("EID")) {
                return { stroke: "#9467bd", dash: "7 5" };
            }
            if (edge.relationship_type.includes("ACCOUNT") || edge.relationship_type.includes("COUNTERPARTY")) {
                return { stroke: "#2ca02c", dash: "" };
            }
            return { stroke: "#94a3b8", dash: "" };
        }

        function point(evt) {
            const pt = svg.createSVGPoint();
            pt.x = evt.clientX;
            pt.y = evt.clientY;
            return pt.matrixTransform(svg.getScreenCTM().inverse());
        }

        function drawEdges() {
            for (const edge of edges) {
                const source = nodeMap.get(edge.source);
                const target = nodeMap.get(edge.target);
                const style = edgeStyle(edge);
                const group = createSvg("g", {});

                const title = createSvg("title", {});
                title.textContent = edge.summary;
                group.appendChild(title);

                const line = createSvg("line", {
                    x1: source.x,
                    y1: source.y,
                    x2: target.x,
                    y2: target.y,
                    stroke: style.stroke,
                    "stroke-width": 3,
                    "stroke-dasharray": style.dash,
                });

                const label = createSvg("text", {
                    x: (source.x + target.x) / 2,
                    y: (source.y + target.y) / 2 - 10,
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

        function drawShape(group, node) {
            const style = nodeStyle(node);

            if (style.shape === "diamond") {
                group.appendChild(createSvg("polygon", {
                    points: `0,${-style.size} ${style.size},0 0,${style.size} ${-style.size},0`,
                    fill: style.fill,
                    stroke: style.stroke,
                    "stroke-width": 3,
                }));
                return;
            }

            if (style.shape === "square") {
                group.appendChild(createSvg("rect", {
                    x: -style.size,
                    y: -style.size,
                    width: style.size * 2,
                    height: style.size * 2,
                    rx: 9,
                    fill: style.fill,
                    stroke: style.stroke,
                    "stroke-width": 3,
                }));
                return;
            }

            group.appendChild(createSvg("circle", {
                cx: 0,
                cy: 0,
                r: style.size,
                fill: style.fill,
                stroke: style.stroke,
                "stroke-width": 3,
            }));
        }

        function drawNodes() {
            for (const node of nodes) {
                const group = createSvg("g", {
                    class: "node",
                    transform: `translate(${node.x}, ${node.y})`,
                });

                const title = createSvg("title", {});
                title.textContent = node.summary;
                group.appendChild(title);

                drawShape(group, node);

                const label = createSvg("text", {
                    x: 0,
                    y: 52,
                    "text-anchor": "middle",
                    class: "label",
                });
                label.textContent = node.label;
                group.appendChild(label);

                const subLabel = createSvg("text", {
                    x: 0,
                    y: 68,
                    "text-anchor": "middle",
                    class: "sub-label",
                });

                if (node.risk_count > 0) {
                    subLabel.textContent = `${node.risk_count} risk indicator(s)`;
                } else if (node.expanded) {
                    subLabel.textContent = "expanded";
                } else if (node.policy === "BLOCK_BY_DEFAULT") {
                    subLabel.textContent = "blocked common connector";
                } else if (node.policy === "EVIDENCE_ONLY") {
                    subLabel.textContent = "evidence only";
                } else {
                    subLabel.textContent = "expandable";
                }

                group.appendChild(subLabel);

                group.addEventListener("pointerdown", (evt) => {
                    evt.preventDefault();
                    dragging = node.id;
                    const p = point(evt);
                    offset.x = node.x - p.x;
                    offset.y = node.y - p.y;
                    group.classList.add("dragging");
                    group.setPointerCapture(evt.pointerId);
                });

                group.addEventListener("pointerup", () => {
                    dragging = null;
                    group.classList.remove("dragging");
                });

                nodeElements.set(node.id, group);
                svg.appendChild(group);
            }
        }

        function update() {
            for (const node of nodes) {
                const el = nodeElements.get(node.id);
                el.setAttribute("transform", `translate(${node.x}, ${node.y})`);
            }

            for (const edge of edges) {
                const source = nodeMap.get(edge.source);
                const target = nodeMap.get(edge.target);
                const line = edgeElements.get(edge.id);
                const label = edgeLabelElements.get(edge.id);

                line.setAttribute("x1", source.x);
                line.setAttribute("y1", source.y);
                line.setAttribute("x2", target.x);
                line.setAttribute("y2", target.y);

                label.setAttribute("x", (source.x + target.x) / 2);
                label.setAttribute("y", (source.y + target.y) / 2 - 10);
            }
        }

        svg.addEventListener("pointermove", (evt) => {
            if (!dragging) {
                return;
            }
            const p = point(evt);
            const node = nodeMap.get(dragging);
            node.x = p.x + offset.x;
            node.y = p.y + offset.y;
            update();
        });

        window.addEventListener("pointerup", () => {
            dragging = null;
            for (const el of nodeElements.values()) {
                el.classList.remove("dragging");
            }
        });

        drawEdges();
        drawNodes();
    </script>
</body>
</html>
"""

    return (
        template
        .replace("__WIDTH__", str(width))
        .replace("__HEIGHT__", str(height))
        .replace("__NODES_JSON__", json.dumps(nodes))
        .replace("__EDGES_JSON__", json.dumps(edges))
    )


def render_badges(customer_id: str) -> None:
    indicators = FRAUD_INDICATORS.get(customer_id, [])

    if not indicators:
        st.markdown(
            '<span class="badge badge-low">No active simulated indicators</span>',
            unsafe_allow_html=True,
        )
        return

    for indicator in indicators:
        css_class = "badge-high" if indicator["severity"] == "High" else "badge-medium"
        st.markdown(
            f'<span class="badge {css_class}">{html.escape(indicator["name"])}</span>',
            unsafe_allow_html=True,
        )


def render_ai_summary() -> None:
    nodes = list(st.session_state.v2_nodes.values())
    customer_nodes = [node for node in nodes if node["node_type"] == "CUSTOMER"]
    risk_nodes = [node for node in customer_nodes if node["risk_count"] > 0]
    blocked_nodes = [node for node in nodes if node["policy"] == "BLOCK_BY_DEFAULT"]

    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">AI investigation summary</div>
            <div class="panel-caption">
                The graph currently contains {len(nodes)} visible node(s), {len(st.session_state.v2_edges)} relationship edge(s), 
                and {len(risk_nodes)} customer node(s) with simulated fraud indicators.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if blocked_nodes:
        for node in blocked_nodes:
            st.markdown(
                f"""
                <div class="insight-box">
                    <div class="insight-title">Common connector identified</div>
                    <div class="insight-text">
                        {html.escape(node["label"])} is visible as first-level context, but expansion is blocked by default because it appears to be a high-degree/common counterparty.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if risk_nodes:
        for node in risk_nodes:
            st.markdown(
                f"""
                <div class="insight-box">
                    <div class="insight-title">Risk-bearing linked customer</div>
                    <div class="insight-text">
                        {html.escape(node["label"])} has {node["risk_count"]} simulated fraud indicator(s). 
                        Review this node before expanding wider low-confidence paths.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if not risk_nodes:
        st.markdown(
            """
            <div class="insight-box">
                <div class="insight-title">Suggested next action</div>
                <div class="insight-text">
                    Review low-degree connectors first. In this demo, Account ****2202 is the useful expandable counterparty path, while Account ****9011 is intentionally blocked as a common connector.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_expansion_cards() -> None:
    candidates = [
        node
        for node in st.session_state.v2_nodes.values()
        if node["expand_type"] is not None and not node["expanded"]
    ]

    if not candidates:
        st.info("No expandable nodes remain in the current graph.")
        return

    for node in candidates:
        st.markdown(
            f"""
            <div class="insight-box">
                <div class="insight-title">{html.escape(node["label"])}</div>
                <div class="insight-text">{html.escape(node["summary"])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        disabled = node["policy"] in ["BLOCK_BY_DEFAULT", "EVIDENCE_ONLY"]

        if node["policy"] == "BLOCK_BY_DEFAULT":
            label = "Expansion blocked by default"
        elif node["policy"] == "EVIDENCE_ONLY":
            label = "Evidence-only node"
        elif node["expand_type"] == "ACCOUNT":
            label = "Expand account"
        elif node["expand_type"] == "EID":
            label = "Expand EID"
        else:
            label = "Expand customer context"

        if st.button(label, key=f"expand_{node['id']}", disabled=disabled):
            expand_node(node["id"])
            st.rerun()


def render_node_intelligence() -> None:
    nodes = list(st.session_state.v2_nodes.values())
    labels = {f"{node['label']} · {node['node_type']}": node["id"] for node in nodes}

    selected_label = st.selectbox("Select visible node", options=list(labels.keys()))
    node = st.session_state.v2_nodes[labels[selected_label]]

    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">{html.escape(node["label"])}</div>
            <div class="panel-caption">{html.escape(node["summary"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if node["node_type"] == "CUSTOMER":
        st.markdown("### Simulated fraud indicators")
        render_badges(node["key"])

        for indicator in FRAUD_INDICATORS.get(node["key"], []):
            st.markdown(
                f"""
                <div class="insight-box">
                    <div class="insight-title">{html.escape(indicator["name"])} · {html.escape(indicator["severity"])}</div>
                    <div class="insight-text">{html.escape(indicator["description"])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if node["node_type"] == "ACCOUNT":
        patterns = TRANSACTION_PATTERNS.get(node["key"], [])

        if patterns:
            st.markdown("### Transaction-pattern interpretation")

            for pattern in patterns:
                st.markdown(
                    f"""
                    <div class="insight-box">
                        <div class="insight-title">{html.escape(pattern["title"])}</div>
                        <div class="insight-text">
                            {html.escape(pattern["summary"])}
                            <br><br>
                            <strong>Analyst guidance:</strong> {html.escape(pattern["guidance"])}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )




def node_visual_style(node: dict) -> dict:
    if node["role"] == "SEED_CUSTOMER":
        return {"color": "#dc2626", "size": 42, "shape": "dot"}

    if node["node_type"] == "CUSTOMER" and node["risk_count"] >= 2:
        return {"color": "#ef4444", "size": 40, "shape": "dot"}

    if node["node_type"] == "CUSTOMER":
        return {"color": "#2563eb", "size": 34, "shape": "dot"}

    if node["node_type"] == "EID":
        return {"color": "#7c3aed", "size": 32, "shape": "diamond"}

    if node["policy"] == "BLOCK_BY_DEFAULT":
        return {"color": "#94a3b8", "size": 34, "shape": "box"}

    if node["policy"] == "EVIDENCE_ONLY":
        return {"color": "#f59e0b", "size": 32, "shape": "box"}

    if node["node_type"] == "ACCOUNT":
        return {"color": "#16a34a", "size": 34, "shape": "box"}

    return {"color": "#64748b", "size": 28, "shape": "dot"}


def normalise_agraph_selection(selection) -> str | None:
    if isinstance(selection, str):
        return selection

    if isinstance(selection, dict):
        for key in ["id", "node", "selected_node", "selectedNode"]:
            value = selection.get(key)
            if isinstance(value, str):
                return value

        nodes = selection.get("nodes")
        if isinstance(nodes, list) and nodes:
            return nodes[0]

    return None


def render_interactive_agraph() -> None:
    graph_nodes = []

    for node in st.session_state.v2_nodes.values():
        style = node_visual_style(node)

        graph_nodes.append(
            Node(
                id=node["id"],
                label=node["label"],
                size=style["size"],
                color=style["color"],
                shape=style["shape"],
            )
        )

    graph_edges = []

    for edge in st.session_state.v2_edges.values():
        graph_edges.append(
            Edge(
                source=edge["source"],
                target=edge["target"],
                label="",
            )
        )

    config = Config(
        width=1000,
        height=620,
        directed=False,
        physics=False,
        hierarchical=True,
        nodeHighlightBehavior=True,
        highlightColor="#f59e0b",
        collapsible=False,
    )

    selected = agraph(
        nodes=graph_nodes,
        edges=graph_edges,
        config=config,
    )

    selected_node_id = normalise_agraph_selection(selected)

    if selected_node_id and selected_node_id in st.session_state.v2_nodes:
        st.session_state.v2_selected_node_id = selected_node_id


def render_selected_graph_node_panel() -> None:
    selected_node_id = st.session_state.get("v2_selected_node_id")

    if not selected_node_id or selected_node_id not in st.session_state.v2_nodes:
        st.markdown(
            """
            <div class="panel">
                <div class="panel-title">Selected node</div>
                <div class="panel-caption">
                    Click a node in the graph to inspect it. Expansion happens from this panel, not automatically.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    node = st.session_state.v2_nodes[selected_node_id]

    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">{html.escape(node["label"])}</div>
            <div class="panel-caption">{html.escape(node["summary"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if node["expanded"]:
        st.success("This node is already expanded.")
        return

    if node["policy"] == "BLOCK_BY_DEFAULT":
        st.warning("This is a high-degree/common connector. It is visible as context but blocked from default expansion.")
        return

    if node["policy"] == "EVIDENCE_ONLY":
        if st.button("Mark evidence-only node as reviewed", key=f"review_{node['id']}"):
            expand_node(node["id"])
            st.rerun()
        return

    if st.button("Expand selected node", type="primary", key=f"expand_selected_{node['id']}"):
        expand_node(node["id"])
        st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="V2 Interactive Investigation Graph",
        layout="wide",
    )

    apply_style()
    ensure_state()

    with st.sidebar:
        st.markdown("## V2 Explorer")
        st.caption("Interactive layer-by-layer investigation demo")

        selected_customer = st.selectbox(
            "Search customer",
            options=list(CUSTOMERS.keys()),
            index=list(CUSTOMERS.keys()).index("RETAIL_1"),
        )

        if st.button("Start investigation", type="primary"):
            start_investigation(selected_customer)
            st.rerun()

        if st.button("Reset graph"):
            reset_state()
            st.rerun()

        st.markdown("---")
        st.caption("Suggested demo path")
        st.caption("1. Start RETAIL_1")
        st.caption("2. Review the common account")
        st.caption("3. Expand Account ****2202")
        st.caption("4. Select RETAIL_2")
        st.caption("5. Review indicators and transaction pattern")

    st.markdown(
        """
        <div class="hero-card">
            <div class="status-pill">Version 2 concept · Interactive expansion</div>
            <div class="hero-title">AI-Assisted Investigation Graph</div>
            <p class="hero-subtitle">
                Start from a triggered customer, review first-level identity and counterparty connectors, then expand only the paths that look useful.
                Fraud indicators and transaction-pattern interpretation are shown as an overlay, not as a replacement for analyst judgement.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.v2_nodes:
        st.markdown(
            """
            <div class="panel">
                <div class="panel-title">Start a new investigation</div>
                <div class="panel-caption">
                    Select RETAIL_1 in the sidebar and click Start investigation. The app will show only first-level connectors first.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    nodes = list(st.session_state.v2_nodes.values())
    customer_nodes = [node for node in nodes if node["node_type"] == "CUSTOMER"]
    risk_nodes = [node for node in customer_nodes if node["risk_count"] > 0]
    blocked_nodes = [node for node in nodes if node["policy"] == "BLOCK_BY_DEFAULT"]

    cols = st.columns(5)

    with cols[0]:
        metric_card("Visible nodes", len(nodes), "Current graph state")

    with cols[1]:
        metric_card("Edges", len(st.session_state.v2_edges), "Visible relationships")

    with cols[2]:
        metric_card("Customers", len(customer_nodes), "Visible customer nodes")

    with cols[3]:
        metric_card("Risk nodes", len(risk_nodes), "Customers with indicators")

    with cols[4]:
        metric_card("Blocked", len(blocked_nodes), "Common/noisy connectors")

    tab_graph, tab_expand, tab_intelligence, tab_history = st.tabs(
        [
            "Investigation graph",
            "Expand next",
            "Node intelligence",
            "Investigation history",
        ]
    )

    with tab_graph:
        st.markdown(
            """
            <div class="panel">
                <div class="panel-title">Investigation graph</div>
                <div class="panel-caption">
                    Click a node to inspect it. Use the panel on the right to expand the selected node.
                    This avoids uncontrolled graph jumps and keeps the investigation flow explicit.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        graph_col, detail_col = st.columns([2, 1])

        with graph_col:
            render_interactive_agraph()

        with detail_col:
            render_selected_graph_node_panel()

        render_ai_summary()

    with tab_expand:
        st.markdown(
            """
            <div class="panel">
                <div class="panel-title">Expansion choices</div>
                <div class="panel-caption">
                    The system summarises each visible connector. The analyst chooses which path to expand.
                    High-degree/common accounts are visible but blocked by default to reduce graph explosion.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_expansion_cards()

    with tab_intelligence:
        render_node_intelligence()

    with tab_history:
        for item in st.session_state.v2_history:
            st.markdown(
                f"""
                <div class="insight-box">
                    <div class="insight-title">Step</div>
                    <div class="insight-text">{html.escape(item)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
