import json
import streamlit as st
import streamlit.components.v1 as components


DEMO_DATA = {
    "customers": {
        "RETAIL_1": {
            "segment": "Retail",
            "summary": "Triggered seed customer. Immediate context shows one shared Emirates ID, one common company-like account, and one low-degree account worth expanding.",
            "risk": [],
        },
        "SME_1": {
            "segment": "SME",
            "summary": "Linked through the same Emirates ID as RETAIL_1. No active simulated fraud indicators.",
            "risk": [],
        },
        "RETAIL_2": {
            "segment": "Retail",
            "summary": "Linked through Account ****2202. This customer has multiple simulated fraud indicators and should be reviewed.",
            "risk": [
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
        },
        "VICTIM_SOURCE_1": {
            "segment": "Retail",
            "summary": "Simulated source-of-funds customer. This is not confirmed victim status; it is only investigative context.",
            "risk": [],
        },
        "RETAIL_3": {
            "segment": "Retail",
            "summary": "Isolated seed example with no useful first-level relationship chain in the simulated data.",
            "risk": [],
        },
    },
    "eids": {
        "EID_1": {
            "label": "EID ****1001",
            "linked_customers": ["RETAIL_1", "SME_1"],
            "summary": "Low-degree deterministic identity connector. It links RETAIL_1 and SME_1.",
            "policy": "allow",
        },
        "EID_2": {
            "label": "EID ****2002",
            "linked_customers": ["RETAIL_2"],
            "summary": "Single-customer EID in the simulated data. Useful context, but not group-forming.",
            "policy": "evidence",
        },
    },
    "customer_eids": {
        "RETAIL_1": ["EID_1"],
        "SME_1": ["EID_1"],
        "RETAIL_2": ["EID_2"],
        "VICTIM_SOURCE_1": [],
        "RETAIL_3": [],
    },
    "accounts": {
        "BIG_COMPANY_ACCOUNT": {
            "label": "Account ****9011",
            "name": "Mega Services Collections LLC",
            "linked_customers": ["RETAIL_1"],
            "linked_customer_count": 300,
            "policy": "blocked",
            "summary": "High-degree, company-like account. It is visible as context but blocked from default expansion to avoid graph noise.",
            "patterns": [
                {
                    "title": "Common counterparty control",
                    "summary": "This account has a high customer degree and company-like name. Expanding it would likely create a noisy graph rather than useful relationship evidence.",
                    "guidance": "Keep it visible as context. Only investigate it separately if another signal specifically points to this account.",
                }
            ],
        },
        "ACCOUNT_2": {
            "label": "Account ****2202",
            "name": "Low-degree wallet account",
            "linked_customers": ["RETAIL_1", "RETAIL_2", "VICTIM_SOURCE_1"],
            "linked_customer_count": 3,
            "policy": "allow",
            "summary": "Low-degree account linking the seed to a small number of customers. This is the recommended expansion path.",
            "patterns": [
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
            ],
        },
        "CASHOUT_ACCOUNT": {
            "label": "Account ****7788",
            "name": "Cash-out destination account",
            "linked_customers": ["RETAIL_2"],
            "linked_customer_count": 1,
            "policy": "evidence",
            "summary": "Single-customer account. It is evidence-only context and does not create a group-forming expansion.",
            "patterns": [
                {
                    "title": "Cash-out context",
                    "summary": "This destination is useful for understanding the movement of funds, but it does not link multiple Wio customers.",
                    "guidance": "Review destination ownership, external beneficiary details, and whether this account appears in other alerts.",
                }
            ],
        },
    },
    "customer_accounts": {
        "RETAIL_1": [
            {
                "account": "BIG_COMPANY_ACCOUNT",
                "direction": "Paid to",
                "transaction_count": 2,
                "amount": 420,
            },
            {
                "account": "ACCOUNT_2",
                "direction": "Paid and received",
                "transaction_count": 7,
                "amount": 1250,
            },
        ],
        "RETAIL_2": [
            {
                "account": "ACCOUNT_2",
                "direction": "Paid and received",
                "transaction_count": 7,
                "amount": 17500,
            },
            {
                "account": "CASHOUT_ACCOUNT",
                "direction": "Paid to",
                "transaction_count": 4,
                "amount": 17200,
            },
        ],
        "VICTIM_SOURCE_1": [
            {
                "account": "ACCOUNT_2",
                "direction": "Paid to",
                "transaction_count": 1,
                "amount": 5000,
            },
        ],
        "SME_1": [],
        "RETAIL_3": [],
    },
}


def build_html(seed_customer: str, analyst_id: str) -> str:
    data_json = json.dumps(DEMO_DATA)
    seed_json = json.dumps(seed_customer)
    analyst_json = json.dumps(analyst_id)

    template = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<style>
    :root {
        --bg: #f5f7fb;
        --panel: #ffffff;
        --ink: #0f172a;
        --muted: #64748b;
        --line: #dbe3ef;
        --blue: #2563eb;
        --green: #16a34a;
        --purple: #7c3aed;
        --red: #dc2626;
        --amber: #f59e0b;
        --slate: #94a3b8;
        --shadow: 0 14px 35px rgba(15, 23, 42, 0.10);
    }

    * {
        box-sizing: border-box;
    }

    body {
        margin: 0;
        background: var(--bg);
        color: var(--ink);
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        overflow: hidden;
    }

    .app {
        height: 850px;
        display: grid;
        grid-template-columns: minmax(740px, 1fr) 420px;
        gap: 14px;
        padding: 14px;
    }

    .canvas-shell,
    .side-panel {
        background: var(--panel);
        border: 1px solid #e5e7eb;
        border-radius: 22px;
        box-shadow: var(--shadow);
        overflow: hidden;
    }

    .canvas-header {
        height: 86px;
        padding: 15px 18px;
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    }

    .title {
        font-size: 20px;
        font-weight: 850;
        letter-spacing: -0.03em;
    }

    .subtitle {
        margin-top: 5px;
        font-size: 13px;
        color: var(--muted);
        line-height: 1.35;
    }

    .toolbar {
        display: flex;
        gap: 8px;
        align-items: center;
    }

    button {
        border: 0;
        border-radius: 12px;
        padding: 10px 13px;
        font-weight: 800;
        font-size: 12px;
        cursor: pointer;
        background: #e2e8f0;
        color: #0f172a;
    }

    button.primary {
        background: var(--blue);
        color: white;
    }

    button.ghost {
        background: rgba(255, 255, 255, 0.12);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.18);
    }

    button:hover {
        filter: brightness(0.97);
    }

    .canvas-wrap {
        position: relative;
        height: 764px;
        overflow: auto;
        background:
            radial-gradient(circle at 1px 1px, #e8eef6 1px, transparent 0);
        background-size: 24px 24px;
    }

    .canvas {
        position: relative;
        min-width: 1180px;
        min-height: 720px;
    }

    svg {
        position: absolute;
        left: 0;
        top: 0;
        z-index: 1;
        pointer-events: none;
    }

    .node {
        position: absolute;
        z-index: 2;
        width: 190px;
        min-height: 70px;
        border: 2px solid #cbd5e1;
        background: white;
        border-radius: 16px;
        padding: 10px 12px;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.11);
        cursor: pointer;
        transition: transform 0.14s ease, box-shadow 0.14s ease, border-color 0.14s ease;
    }

    .node:hover {
        transform: translateY(-2px);
        box-shadow: 0 18px 35px rgba(15, 23, 42, 0.15);
    }

    .node.selected {
        outline: 4px solid rgba(37, 99, 235, 0.20);
        box-shadow: 0 18px 38px rgba(37, 99, 235, 0.20);
    }

    .node.seed {
        border-color: var(--red);
        background: #fff1f2;
    }

    .node.customer {
        border-color: var(--blue);
        background: #eff6ff;
    }

    .node.risk {
        border-color: var(--red);
        background: #fee2e2;
    }

    .node.eid {
        border-color: var(--purple);
        background: #f3e8ff;
    }

    .node.account {
        border-color: var(--green);
        background: #f0fdf4;
    }

    .node.blocked {
        border-color: var(--slate);
        background: #f1f5f9;
    }

    .node.evidence {
        border-color: var(--amber);
        background: #fffbeb;
    }

    .node-type {
        font-size: 10px;
        line-height: 1;
        font-weight: 850;
        letter-spacing: 0.09em;
        color: var(--muted);
        text-transform: uppercase;
        margin-bottom: 7px;
    }

    .node-label {
        font-size: 14px;
        line-height: 1.12;
        font-weight: 850;
        color: var(--ink);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .node-status {
        margin-top: 6px;
        font-size: 11px;
        color: #475569;
        display: flex;
        gap: 6px;
        align-items: center;
    }

    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        background: #94a3b8;
    }

    .dot.allow { background: var(--green); }
    .dot.blocked { background: var(--slate); }
    .dot.risk { background: var(--red); }
    .dot.evidence { background: var(--amber); }
    .dot.expanded { background: var(--blue); }

    .side-panel {
        display: flex;
        flex-direction: column;
        height: 850px;
    }

    .side-header {
        padding: 18px;
        border-bottom: 1px solid #e5e7eb;
        background: #0f172a;
        color: white;
    }

    .side-kicker {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 850;
        color: #bfdbfe;
        margin-bottom: 7px;
    }

    .side-title {
        font-size: 20px;
        font-weight: 850;
        line-height: 1.1;
        letter-spacing: -0.03em;
    }

    .side-subtitle {
        margin-top: 8px;
        color: #dbeafe;
        font-size: 13px;
        line-height: 1.4;
    }

    .side-actions {
        margin-top: 14px;
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }

    .side-body {
        padding: 14px;
        overflow: auto;
    }

    .section {
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 14px;
        background: white;
        margin-bottom: 12px;
    }

    .section-title {
        font-size: 14px;
        font-weight: 850;
        margin-bottom: 7px;
        color: var(--ink);
    }

    .section-text {
        font-size: 13px;
        line-height: 1.48;
        color: #475569;
    }

    .status-card {
        border-radius: 16px;
        padding: 13px 14px;
        margin-bottom: 12px;
        font-size: 13px;
        line-height: 1.45;
        border: 1px solid #e5e7eb;
    }

    .status-card.good {
        background: #f0fdf4;
        border-color: #bbf7d0;
        color: #166534;
    }

    .status-card.warn {
        background: #fffbeb;
        border-color: #fde68a;
        color: #92400e;
    }

    .status-card.info {
        background: #eff6ff;
        border-color: #bfdbfe;
        color: #1d4ed8;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 4px 9px;
        font-size: 11px;
        font-weight: 850;
        margin: 0 5px 5px 0;
    }

    .badge.high {
        background: #fee2e2;
        color: #991b1b;
    }

    .badge.medium {
        background: #ffedd5;
        color: #9a3412;
    }

    .badge.info {
        background: #e0f2fe;
        color: #075985;
    }

    .mini-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-bottom: 12px;
    }

    .mini {
        border: 1px solid #e5e7eb;
        border-radius: 15px;
        padding: 12px;
        background: #f8fafc;
    }

    .mini-label {
        font-size: 10px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 850;
        margin-bottom: 5px;
    }

    .mini-value {
        font-size: 18px;
        font-weight: 850;
        color: var(--ink);
    }

    details.section summary {
        cursor: pointer;
        list-style: none;
    }

    details.section summary::-webkit-details-marker {
        display: none;
    }

    .history {
        font-size: 12px;
        color: #475569;
        line-height: 1.45;
        padding-left: 18px;
        margin-top: 8px;
    }

    .legend {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 8px;
    }

    .legend span {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 11px;
        color: #475569;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 999px;
        padding: 5px 9px;
        white-space: nowrap;
    }

    .legend span::before {
        content: "";
        width: 9px;
        height: 9px;
        border-radius: 999px;
        display: inline-block;
        background: #94a3b8;
    }

    .legend .legend-risk::before {
        background: var(--red);
    }

    .legend .legend-account::before {
        background: var(--green);
    }

    .legend .legend-eid::before {
        background: var(--purple);
    }

    .legend .legend-blocked::before {
        background: var(--slate);
    }

    .legend .legend-evidence::before {
        background: var(--amber);
    }

    .storage-pill {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 4px 8px;
        background: rgba(255, 255, 255, 0.12);
        color: #dbeafe;
        font-size: 11px;
        font-weight: 750;
        margin-top: 10px;
    }
</style>
</head>

<body>
<div class="app">
    <div class="canvas-shell">
        <div class="canvas-header">
            <div>
                <div class="title">Investigation canvas</div>
                <div class="subtitle">
                    Click a node to inspect it. If expansion is allowed, the graph expands immediately and the right panel explains what changed.
                </div>
                <div class="legend">
                    <span class="legend-risk">Risk / customer seed</span>
                    <span class="legend-account">Expandable account</span>
                    <span class="legend-eid">Identity connector</span>
                    <span class="legend-blocked">Blocked common connector</span>
                    <span class="legend-evidence">Evidence-only context</span>
                </div>
            </div>
            <div class="toolbar">
                <button onclick="resetGraph()">Reset</button>
                <button class="primary" onclick="startInvestigation()">Start investigation</button>
            </div>
        </div>
        <div class="canvas-wrap">
            <div id="canvas" class="canvas">
                <svg id="edges"></svg>
            </div>
        </div>
    </div>

    <aside class="side-panel">
        <div class="side-header">
            <div class="side-kicker" id="panelKicker">Ready</div>
            <div class="side-title" id="panelTitle">Start the investigation</div>
            <div class="side-subtitle" id="panelSubtitle">
                Click Start to load the seed customer and immediate connectors.
            </div>
            <div class="storage-pill" id="storageStatus">Audit trail: not started</div>
            <div class="side-actions">
                <button class="ghost" onclick="downloadCaseReport()">Export case JSON</button>
                <button class="ghost" onclick="clearSavedCase()">Clear saved case</button>
            </div>
        </div>
        <div class="side-body" id="panelBody"></div>
    </aside>
</div>

<script>
const DATA = __DATA_JSON__;
const SEED = __SEED_JSON__;
const ANALYST_ID = __ANALYST_JSON__;

const state = {
    nodes: {},
    edges: {},
    selectedNodeId: null,
    history: [],
    events: [],
    started: false,
    sessionId: null,
    startedAt: null,
    analystId: ANALYST_ID
};

function nowIso() {
    return new Date().toISOString();
}

function generateSessionId() {
    const datePart = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
    const randomPart = Math.random().toString(36).slice(2, 8).toUpperCase();
    return `CASE-${datePart}-${randomPart}`;
}

function storageKey() {
    return `wio_v2_case_${ANALYST_ID}_${SEED}`;
}

function safeStorageAvailable() {
    try {
        const testKey = "__wio_storage_test__";
        window.localStorage.setItem(testKey, "1");
        window.localStorage.removeItem(testKey);
        return true;
    } catch (error) {
        return false;
    }
}

function setStorageStatus(message) {
    document.getElementById("storageStatus").textContent = message;
}

function saveCaseState() {
    if (!safeStorageAvailable()) {
        setStorageStatus("Audit trail: browser storage unavailable");
        return;
    }

    try {
        window.localStorage.setItem(storageKey(), JSON.stringify(exportPayload()));
        setStorageStatus(`Audit trail: saved locally · ${state.events.length} event(s)`);
    } catch (error) {
        setStorageStatus("Audit trail: save failed");
    }
}

function clearSavedCase() {
    if (safeStorageAvailable()) {
        window.localStorage.removeItem(storageKey());
    }

    resetGraph();
    setStorageStatus("Audit trail: cleared");
}

function visibleRiskIndicators() {
    const indicators = [];

    for (const node of Object.values(state.nodes)) {
        if (node.type === "CUSTOMER") {
            const riskItems = customerRisk(node.key);
            for (const risk of riskItems) {
                indicators.push({
                    customer_id: node.key,
                    indicator_name: risk.name,
                    severity: risk.severity,
                    description: risk.description
                });
            }
        }
    }

    return indicators;
}

function graphSnapshot() {
    return {
        visible_node_count: Object.keys(state.nodes).length,
        visible_edge_count: Object.keys(state.edges).length,
        visible_nodes: Object.values(state.nodes).map(node => ({
            id: node.id,
            type: node.type,
            key: node.key,
            label: node.label,
            role: node.role,
            policy: node.policy,
            expanded: node.expanded,
            risk_count: node.riskCount
        })),
        visible_edges: Object.values(state.edges).map(edge => ({
            id: edge.id,
            source: edge.source,
            target: edge.target,
            label: edge.label,
            relationship_type: edge.relationshipType
        })),
        risk_indicators_visible: visibleRiskIndicators()
    };
}

function recordEvent(actionType, message, node = null, details = {}) {
    if (!state.sessionId) {
        state.sessionId = generateSessionId();
    }

    const timestamp = nowIso();
    const snapshot = graphSnapshot();

    const event = {
        event_id: `${state.sessionId}-${String(state.events.length + 1).padStart(4, "0")}`,
        investigation_session_id: state.sessionId,
        analyst_id: state.analystId,
        timestamp,
        seed_customer_id: SEED,
        action_type: actionType,
        clicked_node_id: node ? node.id : null,
        clicked_node_type: node ? node.type : null,
        clicked_node_key: node ? node.key : null,
        clicked_node_label: node ? node.label : null,
        action_result: message,
        expansion_allowed_flag: details.expansion_allowed_flag ?? null,
        blocked_reason: details.blocked_reason ?? null,
        visible_node_count: snapshot.visible_node_count,
        visible_edge_count: snapshot.visible_edge_count,
        risk_indicator_count_visible: snapshot.risk_indicators_visible.length,
        details
    };

    state.events.push(event);
    state.history.push({
        timestamp,
        action_type: actionType,
        message
    });

    saveCaseState();
}

function exportPayload() {
    return {
        investigation_session_id: state.sessionId,
        analyst_id: state.analystId,
        seed_customer_id: SEED,
        started_at: state.startedAt,
        exported_at: nowIso(),
        app_version: "v2_browser_canvas_demo",
        graph_snapshot: graphSnapshot(),
        investigation_events: state.events,
        investigation_trail: state.history
    };
}

function downloadCaseReport() {
    const payload = exportPayload();

    if (!payload.investigation_session_id) {
        alert("Start an investigation before exporting a case report.");
        return;
    }

    recordEvent("EXPORT_CASE_REPORT", "Exported case activity JSON.", null, {
        export_format: "json"
    });

    const refreshedPayload = exportPayload();
    const blob = new Blob([JSON.stringify(refreshedPayload, null, 2)], {
        type: "application/json"
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${state.sessionId}_case_activity.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
}

function restoreSavedCase() {
    if (!safeStorageAvailable()) {
        setStorageStatus("Audit trail: browser storage unavailable");
        return false;
    }

    const saved = window.localStorage.getItem(storageKey());

    if (!saved) {
        setStorageStatus("Audit trail: no saved case");
        return false;
    }

    try {
        const payload = JSON.parse(saved);

        state.nodes = {};
        state.edges = {};
        state.events = payload.investigation_events || [];
        state.history = payload.investigation_trail || [];
        state.sessionId = payload.investigation_session_id || generateSessionId();
        state.startedAt = payload.started_at || nowIso();
        state.started = true;

        const snapshot = payload.graph_snapshot || {};

        for (const node of snapshot.visible_nodes || []) {
            state.nodes[node.id] = {
                id: node.id,
                type: node.type,
                key: node.key,
                label: node.label,
                role: node.role,
                summary: nodeSummaryFromSnapshot(node),
                expandType: node.type,
                policy: node.policy,
                expanded: node.expanded,
                riskCount: node.risk_count || 0
            };
        }

        for (const edge of snapshot.visible_edges || []) {
            state.edges[edge.id] = {
                id: edge.id,
                source: edge.source,
                target: edge.target,
                label: edge.label,
                relationshipType: edge.relationship_type,
                summary: edge.relationship_type
            };
        }

        const seedNode = nodeId("CUSTOMER", SEED);
        state.selectedNodeId = state.nodes[seedNode] ? seedNode : Object.keys(state.nodes)[0];

        render();

        if (state.selectedNodeId) {
            renderNodePanel(state.nodes[state.selectedNodeId], {
                status: "info",
                message: "Recovered saved investigation state from browser storage."
            });
        }

        setStorageStatus(`Audit trail: restored · ${state.events.length} event(s)`);
        return true;
    } catch (error) {
        setStorageStatus("Audit trail: restore failed");
        return false;
    }
}

function nodeSummaryFromSnapshot(node) {
    if (node.type === "CUSTOMER" && DATA.customers[node.key]) {
        return DATA.customers[node.key].summary;
    }

    if (node.type === "ACCOUNT" && DATA.accounts[node.key]) {
        return DATA.accounts[node.key].summary;
    }

    if (node.type === "EID" && DATA.eids[node.key]) {
        return DATA.eids[node.key].summary;
    }

    return node.label;
}

function nodeId(type, key) {
    return `${type}|${key}`;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function customerRisk(customerId) {
    return DATA.customers[customerId]?.risk || [];
}

function addNode(type, key, label, role, summary, expandType, policy = "allow") {
    const id = nodeId(type, key);
    const existing = state.nodes[id] || {};

    state.nodes[id] = {
        id,
        type,
        key,
        label,
        role,
        summary,
        expandType,
        policy,
        expanded: existing.expanded || false,
        riskCount: type === "CUSTOMER" ? customerRisk(key).length : 0
    };

    return id;
}

function addEdge(source, target, label, relationshipType, summary) {
    const id = `${source}->${target}|${relationshipType}|${label}`;

    state.edges[id] = {
        id,
        source,
        target,
        label,
        relationshipType,
        summary
    };
}

function addCustomer(customerId, role) {
    const customer = DATA.customers[customerId];
    const risks = customerRisk(customerId);
    const riskText = risks.length ? `${risks.length} simulated fraud indicators are active.` : "No active simulated fraud indicators.";

    return addNode(
        "CUSTOMER",
        customerId,
        customerId,
        role,
        `${customerId} is a ${customer.segment} customer. ${customer.summary} ${riskText}`,
        "CUSTOMER",
        "allow"
    );
}

function addCustomerConnectors(customerId) {
    const customerNode = nodeId("CUSTOMER", customerId);

    for (const eidKey of DATA.customer_eids[customerId] || []) {
        const eid = DATA.eids[eidKey];
        const eidNode = addNode(
            "EID",
            eidKey,
            eid.label,
            "IDENTITY_CONNECTOR",
            eid.summary,
            "EID",
            eid.policy
        );

        addEdge(
            customerNode,
            eidNode,
            "Emirates ID",
            "ENTITY_HAS_EID",
            `${customerId} is linked to ${eid.label}.`
        );
    }

    for (const link of DATA.customer_accounts[customerId] || []) {
        const account = DATA.accounts[link.account];
        const accountNode = addNode(
            "ACCOUNT",
            link.account,
            account.label,
            "COUNTERPARTY_CONNECTOR",
            account.summary,
            "ACCOUNT",
            account.policy
        );

        addEdge(
            customerNode,
            accountNode,
            link.direction,
            "ENTITY_USES_ACCOUNT",
            `${customerId} has ${link.transaction_count} simulated transaction(s) with ${account.label} totalling ${link.amount.toLocaleString()}.`
        );
    }
}

function startInvestigation() {
    state.nodes = {};
    state.edges = {};
    state.history = [];
    state.events = [];
    state.started = true;
    state.sessionId = generateSessionId();
    state.startedAt = nowIso();

    const seedNode = addCustomer(SEED, "SEED_CUSTOMER");
    addCustomerConnectors(SEED);

    state.nodes[seedNode].expanded = true;
    state.selectedNodeId = seedNode;

    recordEvent("START_INVESTIGATION", `Started investigation from ${SEED}.`, state.nodes[seedNode], {
        expansion_allowed_flag: true
    });

    render();
    renderNodePanel(state.nodes[seedNode], {
        status: "good",
        message: `Started investigation from ${SEED}. Immediate EID and account connectors are visible.`
    });
}

function resetGraph() {
    state.nodes = {};
    state.edges = {};
    state.selectedNodeId = null;
    state.history = [];
    state.events = [];
    state.started = false;
    state.sessionId = null;
    state.startedAt = null;

    render();
    renderWelcomePanel();
    saveCaseState();
}

function expandNode(id) {
    const node = state.nodes[id];
    if (!node) return null;

    if (node.expanded) {
        return {
            status: "info",
            message: `${node.label} is already expanded.`
        };
    }

    if (node.policy === "blocked") {
        const message = `${node.label} is blocked from default expansion because it appears to be a high-degree/common connector.`;

        recordEvent("BLOCK_COMMON_COUNTERPARTY", message, node, {
            expansion_allowed_flag: false,
            blocked_reason: "HIGH_DEGREE_OR_COMMON_COUNTERPARTY"
        });

        return {
            status: "warn",
            message
        };
    }

    if (node.policy === "evidence") {
        node.expanded = true;

        const message = `${node.label} is evidence-only. It provides context but does not create new group-forming links.`;

        recordEvent("REVIEW_EVIDENCE_ONLY_NODE", message, node, {
            expansion_allowed_flag: false,
            blocked_reason: "EVIDENCE_ONLY_NOT_GROUP_FORMING"
        });

        return {
            status: "info",
            message
        };
    }

    if (node.expandType === "CUSTOMER") {
        addCustomerConnectors(node.key);
        node.expanded = true;

        const message = `Expanded customer context for ${node.label}.`;

        recordEvent("EXPAND_CUSTOMER", message, node, {
            expansion_allowed_flag: true
        });

        return {
            status: "good",
            message
        };
    }

    if (node.expandType === "EID") {
        const eid = DATA.eids[node.key];
        const added = [];

        for (const customerId of eid.linked_customers || []) {
            const customerNode = nodeId("CUSTOMER", customerId);

            if (!state.nodes[customerNode]) {
                addCustomer(customerId, "LINKED_CUSTOMER");
                added.push(customerId);
            }

            addEdge(
                node.id,
                customerNode,
                "Linked entity",
                "EID_LINKS_CUSTOMER",
                `${node.label} links to ${customerId}.`
            );
        }

        node.expanded = true;

        const message = added.length
            ? `Expanded ${node.label} and added ${added.join(", ")}.`
            : `Expanded ${node.label}. No new customers were added.`;

        recordEvent("EXPAND_EID", message, node, {
            expansion_allowed_flag: true,
            added_customers: added
        });

        return {
            status: "good",
            message
        };
    }

    if (node.expandType === "ACCOUNT") {
        const account = DATA.accounts[node.key];
        const added = [];

        for (const customerId of account.linked_customers || []) {
            const customerNode = nodeId("CUSTOMER", customerId);

            if (!state.nodes[customerNode]) {
                addCustomer(customerId, "LINKED_CUSTOMER");
                added.push(customerId);
            }

            addEdge(
                node.id,
                customerNode,
                "Linked customer",
                "ACCOUNT_LINKS_CUSTOMER",
                `${node.label} links to ${customerId}.`
            );
        }

        node.expanded = true;

        const message = added.length
            ? `Expanded ${node.label} and added ${added.join(", ")}.`
            : `Expanded ${node.label}. No new customers were added.`;

        recordEvent("EXPAND_ACCOUNT", message, node, {
            expansion_allowed_flag: true,
            added_customers: added
        });

        return {
            status: "good",
            message
        };
    }

    return {
        status: "info",
        message: `${node.label} has no expansion action.`
    };
}

function selectNode(id, shouldExpand = true) {
    const node = state.nodes[id];
    if (!node) return;

    state.selectedNodeId = id;

    recordEvent("CLICK_NODE", `Clicked ${node.label}.`, node, {
        expansion_allowed_flag: node.policy === "allow"
    });

    let result = null;
    if (shouldExpand) {
        result = expandNode(id);
    }

    render();
    renderNodePanel(node, result);
}

function graphLevels() {
    const ids = Object.keys(state.nodes);
    const seed = nodeId("CUSTOMER", SEED);
    const adjacency = {};

    for (const edge of Object.values(state.edges)) {
        if (!adjacency[edge.source]) adjacency[edge.source] = [];
        if (!adjacency[edge.target]) adjacency[edge.target] = [];
        adjacency[edge.source].push(edge.target);
        adjacency[edge.target].push(edge.source);
    }

    const levels = {};
    const queue = [];

    if (state.nodes[seed]) {
        levels[seed] = 0;
        queue.push(seed);
    }

    while (queue.length) {
        const current = queue.shift();
        for (const linked of adjacency[current] || []) {
            if (levels[linked] === undefined) {
                levels[linked] = levels[current] + 1;
                queue.push(linked);
            }
        }
    }

    let maxLevel = Math.max(0, ...Object.values(levels));
    for (const id of ids) {
        if (levels[id] === undefined) {
            maxLevel += 1;
            levels[id] = maxLevel;
        }
    }

    return levels;
}

function nodeSortValue(node) {
    if (node.role === "SEED_CUSTOMER") return 0;
    if (node.type === "ACCOUNT" && node.policy === "allow") return 1;
    if (node.type === "EID") return 2;
    if (node.type === "CUSTOMER" && node.riskCount > 0) return 3;
    if (node.type === "CUSTOMER") return 4;
    if (node.policy === "blocked") return 5;
    return 6;
}

function computePositions() {
    const levels = graphLevels();
    const grouped = {};

    for (const [id, level] of Object.entries(levels)) {
        if (!grouped[level]) grouped[level] = [];
        grouped[level].push(id);
    }

    const positions = {};

    for (const [levelText, ids] of Object.entries(grouped)) {
        const level = Number(levelText);
        ids.sort((a, b) => {
            const nodeA = state.nodes[a];
            const nodeB = state.nodes[b];
            return nodeSortValue(nodeA) - nodeSortValue(nodeB) || nodeA.label.localeCompare(nodeB.label);
        });

        const x = 62 + level * 275;
        const totalHeight = (ids.length - 1) * 112;
        const startY = Math.max(42, 310 - totalHeight / 2);

        ids.forEach((id, index) => {
            positions[id] = {
                x,
                y: startY + index * 112
            };
        });
    }

    return positions;
}

function nodeCss(node) {
    if (node.role === "SEED_CUSTOMER") return "seed";
    if (node.type === "CUSTOMER" && node.riskCount > 0) return "risk";
    if (node.type === "CUSTOMER") return "customer";
    if (node.type === "EID") return "eid";
    if (node.policy === "blocked") return "blocked";
    if (node.policy === "evidence") return "evidence";
    if (node.type === "ACCOUNT") return "account";
    return "customer";
}

function nodeStatus(node) {
    if (node.riskCount > 0) return {dot: "risk", text: `${node.riskCount} indicator(s)`};
    if (node.expanded) return {dot: "expanded", text: "expanded"};
    if (node.policy === "blocked") return {dot: "blocked", text: "blocked"};
    if (node.policy === "evidence") return {dot: "evidence", text: "evidence only"};
    return {dot: "allow", text: "click to expand"};
}

function render() {
    const canvas = document.getElementById("canvas");
    const svg = document.getElementById("edges");
    const positions = computePositions();

    canvas.querySelectorAll(".node").forEach(el => el.remove());

    const cardW = 190;
    const cardH = 70;
    const maxX = Math.max(1180, ...Object.values(positions).map(p => p.x + cardW + 90));
    const maxY = Math.max(720, ...Object.values(positions).map(p => p.y + cardH + 90));

    canvas.style.width = `${maxX}px`;
    canvas.style.height = `${maxY}px`;
    svg.setAttribute("width", maxX);
    svg.setAttribute("height", maxY);
    svg.innerHTML = "";

    for (const edge of Object.values(state.edges)) {
        const source = positions[edge.source];
        const target = positions[edge.target];
        if (!source || !target) continue;

        let x1 = source.x + cardW;
        let y1 = source.y + cardH / 2;
        let x2 = target.x;
        let y2 = target.y + cardH / 2;

        if (target.x < source.x) {
            x1 = source.x;
            x2 = target.x + cardW;
        }

        const stroke = edge.relationshipType.includes("EID") ? "#7c3aed" : "#16a34a";
        const dash = edge.relationshipType.includes("EID") ? "6 6" : "";

        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", `M ${x1} ${y1} C ${(x1+x2)/2} ${y1}, ${(x1+x2)/2} ${y2}, ${x2} ${y2}`);
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", stroke);
        path.setAttribute("stroke-width", "2.3");
        path.setAttribute("stroke-dasharray", dash);
        path.setAttribute("opacity", "0.50");

        const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
        title.textContent = edge.summary;
        path.appendChild(title);
        svg.appendChild(path);
    }

    for (const node of Object.values(state.nodes)) {
        const position = positions[node.id];
        const status = nodeStatus(node);

        const div = document.createElement("div");
        div.className = `node ${nodeCss(node)}${node.id === state.selectedNodeId ? " selected" : ""}`;
        div.style.left = `${position.x}px`;
        div.style.top = `${position.y}px`;
        div.title = node.summary;

        div.innerHTML = `
            <div class="node-type">${escapeHtml(node.type)}</div>
            <div class="node-label">${escapeHtml(node.label)}</div>
            <div class="node-status">
                <span class="dot ${status.dot}"></span>
                <span>${escapeHtml(status.text)}</span>
            </div>
        `;

        div.addEventListener("click", () => selectNode(node.id, true));
        canvas.appendChild(div);
    }
}

function renderWelcomePanel() {
    document.getElementById("panelKicker").textContent = "Ready";
    document.getElementById("panelTitle").textContent = "Start the investigation";
    document.getElementById("panelSubtitle").textContent = "Click Start to load the seed customer and immediate connectors.";

    document.getElementById("panelBody").innerHTML = `
        <div class="section">
            <div class="section-title">Designed to reduce analyst error</div>
            <div class="section-text">
                The graph reveals relationships step by step and blocks common/high-degree accounts by default, so the analyst is not overloaded with noisy links.
            </div>
        </div>
        <div class="section">
            <div class="section-title">Persistent audit trail</div>
            <div class="section-text">
                Every click and expansion decision is recorded as a structured case event. In this demo it is saved locally in the browser and can be exported as JSON.
            </div>
        </div>
        <div class="section">
            <div class="section-title">Recommended demo path</div>
            <div class="section-text">
                Start RETAIL_1, click Account ****2202, then click RETAIL_2. The right panel explains the selected node, expansion result, and relevant risk context.
            </div>
        </div>
    `;
}

function statusCard(result) {
    if (!result) return "";

    return `
        <div class="status-card ${result.status}">
            <strong>Click result</strong><br>
            ${escapeHtml(result.message)}
        </div>
    `;
}

function renderRiskSection(node) {
    if (node.type !== "CUSTOMER") return "";

    const risks = customerRisk(node.key);

    if (!risks.length) {
        return `
            <div class="section">
                <div class="section-title">Fraud indicator overlay</div>
                <span class="badge info">No active simulated indicators</span>
            </div>
        `;
    }

    return `
        <div class="section">
            <div class="section-title">Fraud indicator overlay</div>
            ${risks.map(risk => `
                <div style="margin-bottom: 12px;">
                    <span class="badge ${risk.severity === "High" ? "high" : "medium"}">${escapeHtml(risk.severity)}</span>
                    <strong>${escapeHtml(risk.name)}</strong>
                    <div class="section-text" style="margin-top: 5px;">${escapeHtml(risk.description)}</div>
                </div>
            `).join("")}
        </div>
    `;
}

function renderAccountSection(node) {
    if (node.type !== "ACCOUNT") return "";

    const account = DATA.accounts[node.key];
    const patterns = account.patterns || [];

    return `
        <div class="mini-grid">
            <div class="mini">
                <div class="mini-label">Linked customers</div>
                <div class="mini-value">${account.linked_customer_count}</div>
            </div>
            <div class="mini">
                <div class="mini-label">Policy</div>
                <div class="mini-value">${account.policy}</div>
            </div>
        </div>

        ${patterns.map(pattern => `
            <div class="section">
                <div class="section-title">${escapeHtml(pattern.title)}</div>
                <div class="section-text">
                    ${escapeHtml(pattern.summary)}
                    <br><br>
                    <strong>Analyst guidance:</strong> ${escapeHtml(pattern.guidance)}
                </div>
            </div>
        `).join("")}
    `;
}

function renderIdentitySection(node) {
    if (node.type !== "EID") return "";

    const eid = DATA.eids[node.key];

    return `
        <div class="mini-grid">
            <div class="mini">
                <div class="mini-label">Linked entities</div>
                <div class="mini-value">${eid.linked_customers.length}</div>
            </div>
            <div class="mini">
                <div class="mini-label">Policy</div>
                <div class="mini-value">${eid.policy}</div>
            </div>
        </div>
    `;
}

function renderAuditTrail() {
    if (!state.history.length) {
        return "";
    }

    return `
        <details class="section" open>
            <summary class="section-title">Case activity timeline</summary>
            <ol class="history">
                ${state.history.slice(-8).map(item => `
                    <li>
                        <strong>${escapeHtml(item.action_type)}</strong><br>
                        ${escapeHtml(item.message)}
                    </li>
                `).join("")}
            </ol>
        </details>
    `;
}

function renderNodePanel(node, result) {
    document.getElementById("panelKicker").textContent = node.type;
    document.getElementById("panelTitle").textContent = node.label;
    document.getElementById("panelSubtitle").textContent = node.summary;

    document.getElementById("panelBody").innerHTML = `
        ${statusCard(result)}

        <div class="section">
            <div class="section-title">What this node means</div>
            <div class="section-text">${escapeHtml(node.summary)}</div>
        </div>

        ${renderRiskSection(node)}
        ${renderAccountSection(node)}
        ${renderIdentitySection(node)}
        ${renderAuditTrail()}
    `;
}

if (!restoreSavedCase()) {
    renderWelcomePanel();
}
</script>
</body>
</html>
"""

    return (
        template
        .replace("__DATA_JSON__", data_json)
        .replace("__SEED_JSON__", seed_json)
        .replace("__ANALYST_JSON__", analyst_json)
    )


def main() -> None:
    st.set_page_config(
        page_title="V2 Investigation Canvas",
        layout="wide",
    )

    st.markdown(
        """
        <style>
            [data-testid="stAppViewContainer"] {
                background: #f5f7fb;
            }

            .block-container {
                max-width: 1800px;
                padding: 1rem 1.2rem 2rem 1.2rem;
            }

            [data-testid="stHeader"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.title("V2 Explorer")
        st.caption("Clean browser-side investigation canvas")

        analyst_id = st.text_input(
            "Analyst ID",
            value="demo_analyst",
            help="Demo placeholder. In production this would come from login/SSO.",
        )

        seed_customer = st.selectbox(
            "Seed customer",
            options=list(DEMO_DATA["customers"].keys()),
            index=list(DEMO_DATA["customers"].keys()).index("RETAIL_1"),
        )

        st.markdown("---")
        st.caption("Demo path")
        st.caption("1. Start RETAIL_1")
        st.caption("2. Click Account ****2202")
        st.caption("3. Click RETAIL_2")
        st.caption("4. Export case JSON")

    components.html(
        build_html(seed_customer, analyst_id),
        height=900,
        scrolling=False,
    )


if __name__ == "__main__":
    main()
