import html
from collections import deque

import streamlit as st
import streamlit.components.v1 as components


CUSTOMERS = {
    "RETAIL_1": {
        "segment": "Retail",
        "summary": "Triggered seed customer. First-level view shows one shared Emirates ID, one common account, and one low-degree account worth expanding.",
    },
    "SME_1": {
        "segment": "SME",
        "summary": "Linked through the same Emirates ID as RETAIL_1. No active simulated fraud indicators.",
    },
    "RETAIL_2": {
        "segment": "Retail",
        "summary": "Linked through Account ****2202. This customer has multiple simulated fraud indicators.",
    },
    "VICTIM_SOURCE_1": {
        "segment": "Retail",
        "summary": "Simulated source-of-funds customer. This is not confirmed victim status; it is only investigative context.",
    },
    "RETAIL_3": {
        "segment": "Retail",
        "summary": "Isolated seed example with no useful first-level relationship chain in the simulated data.",
    },
}

EIDS = {
    "EID_1": {
        "label": "EID ****1001",
        "linked_customers": ["RETAIL_1", "SME_1"],
        "summary": "Low-degree deterministic identity connector. It links RETAIL_1 and SME_1.",
    },
    "EID_2": {
        "label": "EID ****2002",
        "linked_customers": ["RETAIL_2"],
        "summary": "Single-customer EID in the simulated data. Useful context, but not group-forming.",
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
        "policy": "BLOCK_BY_DEFAULT",
        "summary": "High-degree, company-like account. It is visible as context but blocked from default expansion to avoid graph noise.",
    },
    "ACCOUNT_2": {
        "label": "Account ****2202",
        "name": "Low-degree wallet account",
        "linked_customer_count": 3,
        "policy": "ALLOW",
        "summary": "Low-degree account linking the seed to a small number of customers. This is the recommended next expansion.",
    },
    "CASHOUT_ACCOUNT": {
        "label": "Account ****7788",
        "name": "Cash-out destination account",
        "linked_customer_count": 1,
        "policy": "EVIDENCE_ONLY",
        "summary": "Single-customer account. It is evidence-only context and does not create a group-forming expansion.",
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
            "description": "A high share of inbound value is moved onward to another destination account.",
        },
    ],
}

TRANSACTION_PATTERNS = {
    "ACCOUNT_2": [
        {
            "title": "Possible activity simulation",
            "summary": "RETAIL_1 and RETAIL_2 show repeated small-value back-and-forth movement around Account ****2202.",
            "guidance": "Review timestamps, payment direction, counterparties, and whether there is a legitimate explanation.",
        },
        {
            "title": "Large inbound source-of-funds event",
            "summary": "VICTIM_SOURCE_1 sends one larger simulated payment into the same path before value moves onward.",
            "guidance": "Check for disputes, fraud claims, account takeover signals, or unusual onboarding behaviour.",
        },
    ]
}


def apply_style() -> None:
    st.markdown(
        """
        <style>
            [data-testid="stAppViewContainer"] {
                background: #f5f7fb;
            }

            [data-testid="stSidebar"] {
                background: #0f172a;
            }

            [data-testid="stSidebar"] * {
                color: #f8fafc;
            }

            .block-container {
                max-width: 1600px;
                padding-top: 2rem;
                padding-bottom: 3rem;
            }

            .hero {
                background: linear-gradient(135deg, #111827 0%, #263b63 60%, #355c7d 100%);
                color: white;
                border-radius: 22px;
                padding: 28px 32px;
                margin-bottom: 20px;
                box-shadow: 0 16px 35px rgba(15, 23, 42, 0.18);
            }

            .hero-title {
                font-size: 34px;
                font-weight: 850;
                letter-spacing: -0.04em;
                margin-bottom: 8px;
            }

            .hero-text {
                color: #dbeafe;
                font-size: 15px;
                line-height: 1.5;
                max-width: 1050px;
            }

            .panel {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 18px;
                padding: 18px;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
                margin-bottom: 14px;
            }

            .panel-title {
                font-size: 17px;
                font-weight: 850;
                color: #0f172a;
                margin-bottom: 6px;
            }

            .panel-text {
                color: #475569;
                font-size: 13px;
                line-height: 1.5;
            }

            .metric-card {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 16px;
                padding: 16px;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
            }

            .metric-label {
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: #64748b;
                font-weight: 800;
                margin-bottom: 8px;
            }

            .metric-value {
                font-size: 30px;
                line-height: 1;
                color: #0f172a;
                font-weight: 850;
            }

            .badge {
                display: inline-block;
                border-radius: 999px;
                padding: 4px 9px;
                font-size: 11px;
                font-weight: 800;
                margin-right: 5px;
                margin-bottom: 5px;
            }

            .badge-high {
                background: #fee2e2;
                color: #991b1b;
            }

            .badge-medium {
                background: #ffedd5;
                color: #9a3412;
            }

            .badge-info {
                background: #e0f2fe;
                color: #075985;
            }

            .recommendation {
                border-left: 4px solid #2563eb;
                padding-left: 12px;
            }

            .blocked {
                border-left: 4px solid #94a3b8;
                padding-left: 12px;
            }

            .risk {
                border-left: 4px solid #dc2626;
                padding-left: 12px;
            }

            .stButton > button {
                border-radius: 12px;
                font-weight: 800;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def reset_state() -> None:
    st.session_state.v2_nodes = {}
    st.session_state.v2_edges = {}
    st.session_state.v2_seed = None
    st.session_state.v2_history = []
    st.session_state.v2_focus_node_id = None


def ensure_state() -> None:
    if "v2_nodes" not in st.session_state:
        reset_state()


def node_id(node_type: str, key: str) -> str:
    return f"{node_type}|{key}"


def customer_risk_count(customer_id: str) -> int:
    return len(FRAUD_INDICATORS.get(customer_id, []))


def add_node(
    node_type: str,
    key: str,
    label: str,
    role: str,
    summary: str,
    expand_type: str | None,
    policy: str = "ALLOW",
) -> str:
    nid = node_id(node_type, key)
    existing = st.session_state.v2_nodes.get(nid, {})

    st.session_state.v2_nodes[nid] = {
        "id": nid,
        "node_type": node_type,
        "key": key,
        "label": label,
        "role": role,
        "summary": summary,
        "expand_type": expand_type,
        "policy": policy,
        "expanded": existing.get("expanded", False),
        "risk_count": customer_risk_count(key) if node_type == "CUSTOMER" else 0,
    }

    return nid


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


def customer_summary(customer_id: str) -> str:
    customer = CUSTOMERS[customer_id]
    risk_count = customer_risk_count(customer_id)

    if risk_count:
        risk_text = f"{risk_count} simulated fraud indicators are active."
    else:
        risk_text = "No active simulated fraud indicators."

    return f"{customer_id} is a {customer['segment']} customer. {customer['summary']} {risk_text}"


def add_customer_node(customer_id: str, role: str) -> str:
    return add_node(
        node_type="CUSTOMER",
        key=customer_id,
        label=customer_id,
        role=role,
        summary=customer_summary(customer_id),
        expand_type="CUSTOMER",
        policy="ALLOW",
    )


def add_customer_connectors(customer_id: str) -> None:
    customer_node = node_id("CUSTOMER", customer_id)

    for eid_key in CUSTOMER_EIDS.get(customer_id, []):
        eid = EIDS[eid_key]
        eid_node = add_node(
            node_type="EID",
            key=eid_key,
            label=eid["label"],
            role="IDENTITY_CONNECTOR",
            summary=eid["summary"],
            expand_type="EID",
            policy="ALLOW",
        )

        add_edge(
            source=customer_node,
            target=eid_node,
            label="Emirates ID",
            relationship_type="ENTITY_HAS_EID",
            summary=f"{customer_id} is linked to {eid['label']}.",
        )

    for link in CUSTOMER_ACCOUNTS.get(customer_id, []):
        account_key = link["account"]
        account = ACCOUNTS[account_key]

        account_node = add_node(
            node_type="ACCOUNT",
            key=account_key,
            label=account["label"],
            role="COUNTERPARTY_CONNECTOR",
            summary=account["summary"],
            expand_type="ACCOUNT",
            policy=account["policy"],
        )

        add_edge(
            source=customer_node,
            target=account_node,
            label=link["direction"],
            relationship_type="ENTITY_USES_ACCOUNT",
            summary=(
                f"{customer_id} has {link['transaction_count']} simulated transaction(s) "
                f"with {account['label']} totalling {link['amount']:,.0f}."
            ),
        )


def start_investigation(customer_id: str) -> None:
    reset_state()
    st.session_state.v2_seed = customer_id

    seed_node = add_customer_node(customer_id, role="SEED_CUSTOMER")
    add_customer_connectors(customer_id)

    st.session_state.v2_nodes[seed_node]["expanded"] = True
    st.session_state.v2_focus_node_id = seed_node
    st.session_state.v2_history.append(
        f"Started from {customer_id}. The graph shows immediate EID and account connectors only."
    )


def expand_eid(eid_key: str) -> str:
    eid = EIDS[eid_key]
    eid_node = node_id("EID", eid_key)
    added = []

    for customer_id in eid["linked_customers"]:
        customer_node = node_id("CUSTOMER", customer_id)

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
        return f"Expanded {eid['label']} and added {', '.join(added)}."

    return f"Expanded {eid['label']}. No new customers were added."


def expand_account(account_key: str) -> str:
    account = ACCOUNTS[account_key]
    account_node = node_id("ACCOUNT", account_key)
    added = []

    for customer_id in ACCOUNT_CUSTOMERS.get(account_key, []):
        customer_node = node_id("CUSTOMER", customer_id)

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

    if added:
        return f"Expanded {account['label']} and added {', '.join(added)}."

    return f"Expanded {account['label']}. No new customers were added."


def expand_customer(customer_id: str) -> str:
    add_customer_connectors(customer_id)
    st.session_state.v2_nodes[node_id("CUSTOMER", customer_id)]["expanded"] = True
    return f"Expanded customer context for {customer_id}."


def expand_node(nid: str) -> None:
    node = st.session_state.v2_nodes[nid]
    st.session_state.v2_focus_node_id = nid

    if node["expanded"]:
        st.session_state.v2_history.append(f"{node['label']} was already expanded.")
        return

    if node["policy"] == "BLOCK_BY_DEFAULT":
        st.session_state.v2_history.append(
            f"{node['label']} was blocked from default expansion because it appears high-degree/common."
        )
        return

    if node["policy"] == "EVIDENCE_ONLY":
        node["expanded"] = True
        st.session_state.v2_history.append(
            f"{node['label']} was marked as reviewed evidence-only context."
        )
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


def visible_customer_nodes() -> list[dict]:
    return [
        node
        for node in st.session_state.v2_nodes.values()
        if node["node_type"] == "CUSTOMER"
    ]


def recommendation_score(node: dict) -> tuple[int, str]:
    if node["expanded"]:
        return (99, node["label"])

    if node["policy"] == "BLOCK_BY_DEFAULT":
        return (50, node["label"])

    if node["policy"] == "EVIDENCE_ONLY":
        return (40, node["label"])

    if node["node_type"] == "ACCOUNT" and node["policy"] == "ALLOW":
        return (1, node["label"])

    if node["node_type"] == "CUSTOMER" and node["risk_count"] > 0:
        return (2, node["label"])

    if node["node_type"] == "EID":
        return (3, node["label"])

    if node["node_type"] == "CUSTOMER":
        return (4, node["label"])

    return (10, node["label"])


def open_recommendations() -> list[dict]:
    candidates = [
        node
        for node in st.session_state.v2_nodes.values()
        if node["expand_type"] is not None and not node["expanded"]
    ]

    return sorted(candidates, key=recommendation_score)


def metric_card(label: str, value: int | str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{html.escape(label)}</div>
            <div class="metric-value">{html.escape(str(value))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def graph_positions() -> dict[str, tuple[int, int]]:
    nodes = st.session_state.v2_nodes
    edges = st.session_state.v2_edges
    seed = node_id("CUSTOMER", st.session_state.v2_seed) if st.session_state.v2_seed else None

    adjacency = {}

    for edge in edges.values():
        adjacency.setdefault(edge["source"], set()).add(edge["target"])
        adjacency.setdefault(edge["target"], set()).add(edge["source"])

    levels = {}

    if seed in nodes:
        levels[seed] = 0
        queue = deque([seed])
    else:
        queue = deque()

    while queue:
        current = queue.popleft()

        for linked in adjacency.get(current, set()):
            if linked not in levels:
                levels[linked] = levels[current] + 1
                queue.append(linked)

    for nid in nodes:
        if nid not in levels:
            levels[nid] = max(levels.values(), default=0) + 1

    grouped = {}

    def sort_key(nid: str) -> tuple[int, str]:
        node = nodes[nid]
        type_rank = {"CUSTOMER": 1, "EID": 2, "ACCOUNT": 3}.get(node["node_type"], 9)
        if node["role"] == "SEED_CUSTOMER":
            type_rank = 0
        return type_rank, node["label"]

    for nid, level in levels.items():
        grouped.setdefault(level, []).append(nid)

    positions = {}

    for level, ids in grouped.items():
        ids = sorted(ids, key=sort_key)
        x = 70 + level * 300
        total_height = (len(ids) - 1) * 125
        start_y = max(40, 285 - total_height // 2)

        for index, nid in enumerate(ids):
            positions[nid] = (x, start_y + index * 125)

    return positions


def node_class(node: dict) -> str:
    if node["role"] == "SEED_CUSTOMER":
        return "seed"

    if node["node_type"] == "CUSTOMER" and node["risk_count"] > 0:
        return "risk-node"

    if node["node_type"] == "CUSTOMER":
        return "customer"

    if node["node_type"] == "EID":
        return "eid"

    if node["policy"] == "BLOCK_BY_DEFAULT":
        return "blocked-node"

    if node["policy"] == "EVIDENCE_ONLY":
        return "evidence"

    if node["node_type"] == "ACCOUNT":
        return "account"

    return "customer"


def node_status(node: dict) -> str:
    if node["risk_count"] > 0:
        return f"{node['risk_count']} indicators"

    if node["expanded"]:
        return "expanded"

    if node["policy"] == "BLOCK_BY_DEFAULT":
        return "blocked"

    if node["policy"] == "EVIDENCE_ONLY":
        return "evidence only"

    return "available"


def render_graph_html() -> str:
    positions = graph_positions()
    nodes = st.session_state.v2_nodes
    edges = st.session_state.v2_edges

    card_w = 210
    card_h = 74

    max_x = max((x for x, _ in positions.values()), default=600) + card_w + 80
    max_y = max((y for _, y in positions.values()), default=450) + card_h + 80

    edge_parts = []

    for edge in edges.values():
        if edge["source"] not in positions or edge["target"] not in positions:
            continue

        sx, sy = positions[edge["source"]]
        tx, ty = positions[edge["target"]]

        x1 = sx + card_w
        y1 = sy + card_h / 2
        x2 = tx
        y2 = ty + card_h / 2

        if tx < sx:
            x1 = sx
            x2 = tx + card_w

        stroke = "#7c3aed" if "EID" in edge["relationship_type"] else "#16a34a"
        dash = "6 6" if "EID" in edge["relationship_type"] else ""

        edge_parts.append(
            f"""
            <path d="M {x1} {y1} C {(x1+x2)/2} {y1}, {(x1+x2)/2} {y2}, {x2} {y2}"
                  fill="none"
                  stroke="{stroke}"
                  stroke-width="2.2"
                  stroke-dasharray="{dash}"
                  opacity="0.55">
                <title>{html.escape(edge["summary"])}</title>
            </path>
            """
        )

    node_parts = []

    for nid, node in nodes.items():
        x, y = positions[nid]

        node_parts.append(
            f"""
            <div class="node-card {node_class(node)}" style="left:{x}px; top:{y}px;" title="{html.escape(node["summary"])}">
                <div class="node-type">{html.escape(node["node_type"])}</div>
                <div class="node-label">{html.escape(node["label"])}</div>
                <div class="node-status">{html.escape(node_status(node))}</div>
            </div>
            """
        )

    return f"""
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                background: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }}

            .canvas {{
                position: relative;
                width: {max_x}px;
                height: {max_y}px;
                background:
                    radial-gradient(circle at 1px 1px, #e5e7eb 1px, transparent 0);
                background-size: 22px 22px;
                border: 1px solid #e5e7eb;
                border-radius: 18px;
                overflow: auto;
            }}

            svg {{
                position: absolute;
                left: 0;
                top: 0;
                z-index: 1;
            }}

            .node-card {{
                position: absolute;
                width: {card_w}px;
                height: {card_h}px;
                z-index: 2;
                background: #ffffff;
                border: 2px solid #cbd5e1;
                border-radius: 16px;
                box-sizing: border-box;
                padding: 10px 12px;
                box-shadow: 0 10px 22px rgba(15, 23, 42, 0.10);
            }}

            .node-type {{
                font-size: 10px;
                font-weight: 850;
                letter-spacing: 0.08em;
                color: #64748b;
                margin-bottom: 4px;
            }}

            .node-label {{
                font-size: 15px;
                font-weight: 850;
                color: #0f172a;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}

            .node-status {{
                font-size: 11px;
                color: #475569;
                margin-top: 4px;
            }}

            .seed {{
                border-color: #dc2626;
                background: #fff1f2;
            }}

            .customer {{
                border-color: #2563eb;
                background: #eff6ff;
            }}

            .risk-node {{
                border-color: #dc2626;
                background: #fee2e2;
            }}

            .eid {{
                border-color: #7c3aed;
                background: #f3e8ff;
            }}

            .account {{
                border-color: #16a34a;
                background: #f0fdf4;
            }}

            .blocked-node {{
                border-color: #94a3b8;
                background: #f1f5f9;
            }}

            .evidence {{
                border-color: #f59e0b;
                background: #fffbeb;
            }}
        </style>
    </head>
    <body>
        <div class="canvas">
            <svg width="{max_x}" height="{max_y}">
                {''.join(edge_parts)}
            </svg>
            {''.join(node_parts)}
        </div>
    </body>
    </html>
    """


def render_node_details(node: dict) -> None:
    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">{html.escape(node["label"])}</div>
            <div class="panel-text">{html.escape(node["summary"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if node["node_type"] == "CUSTOMER":
        indicators = FRAUD_INDICATORS.get(node["key"], [])

        if indicators:
            st.markdown("##### Fraud indicator overlay")

            for indicator in indicators:
                badge_class = "badge-high" if indicator["severity"] == "High" else "badge-medium"
                st.markdown(
                    f"""
                    <div class="panel risk">
                        <span class="badge {badge_class}">{html.escape(indicator["severity"])}</span>
                        <strong>{html.escape(indicator["name"])}</strong>
                        <div class="panel-text">{html.escape(indicator["description"])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown('<span class="badge badge-info">No active simulated indicators</span>', unsafe_allow_html=True)

    if node["node_type"] == "ACCOUNT":
        for pattern in TRANSACTION_PATTERNS.get(node["key"], []):
            st.markdown(
                f"""
                <div class="panel">
                    <div class="panel-title">{html.escape(pattern["title"])}</div>
                    <div class="panel-text">
                        {html.escape(pattern["summary"])}
                        <br><br>
                        <strong>Analyst guidance:</strong> {html.escape(pattern["guidance"])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_focus_panel() -> None:
    nodes = list(st.session_state.v2_nodes.values())

    if not nodes:
        return

    labels = {f"{node['label']} · {node['node_type']}": node["id"] for node in nodes}
    current = st.session_state.get("v2_focus_node_id")

    if current not in st.session_state.v2_nodes:
        current = nodes[0]["id"]

    current_label = next(label for label, nid in labels.items() if nid == current)

    selected_label = st.selectbox(
        "Inspect visible node",
        options=list(labels.keys()),
        index=list(labels.keys()).index(current_label),
    )

    st.session_state.v2_focus_node_id = labels[selected_label]
    render_node_details(st.session_state.v2_nodes[labels[selected_label]])


def render_recommendations() -> None:
    recommendations = open_recommendations()

    if not recommendations:
        st.success("No recommended expansion remains for the current graph.")
        return

    st.markdown("##### Recommended next actions")

    for index, node in enumerate(recommendations[:5], start=1):
        if node["policy"] == "BLOCK_BY_DEFAULT":
            css_class = "blocked"
            action_label = "Blocked by default"
        elif node["policy"] == "EVIDENCE_ONLY":
            css_class = "blocked"
            action_label = "Mark as reviewed"
        elif node["node_type"] == "ACCOUNT":
            css_class = "recommendation"
            action_label = "Expand account"
        elif node["node_type"] == "CUSTOMER":
            css_class = "recommendation"
            action_label = "Expand customer context"
        else:
            css_class = "recommendation"
            action_label = "Expand connector"

        st.markdown(
            f"""
            <div class="panel {css_class}">
                <div class="panel-title">{index}. {html.escape(node["label"])}</div>
                <div class="panel-text">{html.escape(node["summary"])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns([1, 1])

        with col_a:
            if st.button("Inspect", key=f"inspect_{node['id']}"):
                st.session_state.v2_focus_node_id = node["id"]
                st.rerun()

        with col_b:
            disabled = node["policy"] == "BLOCK_BY_DEFAULT"

            if st.button(action_label, key=f"expand_{node['id']}", disabled=disabled):
                expand_node(node["id"])
                st.rerun()


def render_summary() -> None:
    nodes = list(st.session_state.v2_nodes.values())
    customer_nodes = visible_customer_nodes()
    risk_nodes = [node for node in customer_nodes if node["risk_count"] > 0]
    blocked_nodes = [node for node in nodes if node["policy"] == "BLOCK_BY_DEFAULT"]

    cols = st.columns(4)

    with cols[0]:
        metric_card("Visible nodes", len(nodes))

    with cols[1]:
        metric_card("Relationships", len(st.session_state.v2_edges))

    with cols[2]:
        metric_card("Customers", len(customer_nodes))

    with cols[3]:
        metric_card("Risk nodes", len(risk_nodes))

    if blocked_nodes:
        st.markdown(
            """
            <div class="panel blocked">
                <div class="panel-title">Common connector control</div>
                <div class="panel-text">
                    High-degree/company-like counterparties are shown as context but blocked from default expansion.
                    This prevents graph explosion and keeps the investigation focused.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(
        page_title="V2 Analyst Investigation Graph",
        layout="wide",
    )

    apply_style()
    ensure_state()

    with st.sidebar:
        st.markdown("## V2 Explorer")
        st.caption("Analyst-led relationship expansion")

        selected_customer = st.selectbox(
            "Seed customer",
            options=list(CUSTOMERS.keys()),
            index=list(CUSTOMERS.keys()).index("RETAIL_1"),
        )

        if st.button("Start investigation", type="primary"):
            start_investigation(selected_customer)
            st.rerun()

        if st.button("Reset"):
            reset_state()
            st.rerun()

        st.markdown("---")
        st.caption("Recommended demo path")
        st.caption("Start RETAIL_1")
        st.caption("Expand Account ****2202")
        st.caption("Inspect RETAIL_2")
        st.caption("Expand RETAIL_2")
        st.caption("Review cash-out context")

    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">AI-Assisted Investigation Graph</div>
            <div class="hero-text">
                The graph maps relationships around a triggered customer. Fraud indicators are shown as overlays.
                The system recommends useful expansion paths, but the analyst decides what to expand.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.v2_nodes:
        st.markdown(
            """
            <div class="panel">
                <div class="panel-title">Start an investigation</div>
                <div class="panel-text">
                    Use the sidebar to start from RETAIL_1. The first view will show immediate EID and account connectors only.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    render_summary()

    workspace_tab, history_tab = st.tabs(["Investigation workspace", "History"])

    with workspace_tab:
        graph_col, control_col = st.columns([2.2, 1])

        with graph_col:
            st.markdown(
                """
                <div class="panel">
                    <div class="panel-title">Relationship graph</div>
                    <div class="panel-text">
                        This is a controlled visual map. Expansion is managed from the recommendation panel to avoid unstable graph behaviour.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            components.html(render_graph_html(), height=650, scrolling=True)

        with control_col:
            render_recommendations()
            render_focus_panel()

    with history_tab:
        for item in st.session_state.v2_history:
            st.markdown(
                f"""
                <div class="panel">
                    <div class="panel-title">Step</div>
                    <div class="panel-text">{html.escape(item)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
