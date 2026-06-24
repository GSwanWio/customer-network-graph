from pathlib import Path
import json
import streamlit as st
import streamlit.components.v1 as components


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "real_demo" / "customer_network_demo_data.json"

with DATA_PATH.open("r", encoding="utf-8") as f:
    DEMO_DATA = json.load(f)


def build_html() -> str:
    data_json = json.dumps(DEMO_DATA)

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

        /* Single source of truth for graph risk colors */
        --high-risk-border: #dc2626;
        --high-risk-bg: #fee2e2;
        --high-risk-text: #991b1b;

        --flagged-border: #f97316;
        --flagged-bg: #fff7ed;
        --flagged-text: #9a3412;

        --exposed-border: #f59e0b;
        --exposed-bg: #fffbeb;
        --exposed-text: #92400e;

        --account-standard-border: #16a34a;
        --account-standard-bg: #f0fdf4;
        --account-standard-text: #166534;

        --identity-border: #7c3aed;
        --identity-bg: #f3e8ff;
        --identity-text: #5b21b6;

        --controlled-border: #94a3b8;
        --controlled-bg: #f1f5f9;
        --controlled-text: #475569;
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
        height: 940px;
        display: grid;
        grid-template-columns: minmax(740px, 1fr) 420px;
        grid-template-rows: 104px 1fr;
        gap: 14px;
        padding: 14px;
    }

    .top-bar {
        grid-column: 1 / -1;
        grid-row: 1;
        background: var(--panel);
        border: 1px solid #e5e7eb;
        border-radius: 22px;
        box-shadow: var(--shadow);
        display: grid;
        grid-template-columns: minmax(260px, 1fr) 220px 260px 156px;
        gap: 14px;
        align-items: center;
        padding: 12px 16px;
    }

    .top-brand {
        font-size: 26px;
        font-weight: 900;
        letter-spacing: -0.04em;
        color: var(--ink);
        white-space: nowrap;
    }

    .top-control label {
        display: block;
        font-size: 11px;
        font-weight: 850;
        color: #475569;
        margin-bottom: 5px;
    }

    .top-control input,
    .top-control select {
        width: 100%;
        height: 38px;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        background: #f8fafc;
        color: var(--ink);
        padding: 0 11px;
        font-size: 13px;
        font-weight: 650;
        outline: none;
    }

    .top-control input:focus,
    .top-control select:focus {
        border-color: var(--blue);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.14);
        background: white;
    }

    .top-actions {
        display: grid;
        grid-template-rows: 1fr 1fr;
        gap: 7px;
    }

    .top-actions button {
        width: 100%;
        height: 32px;
        padding: 0 10px;
        border-radius: 11px;
    }

    .canvas-shell,
    .side-panel {
        background: var(--panel);
        border: 1px solid #e5e7eb;
        border-radius: 22px;
        box-shadow: var(--shadow);
        overflow: hidden;
        min-height: 0;
    }

    .canvas-shell {
        grid-column: 1;
        grid-row: 2;
    }

    .side-panel {
        grid-column: 2;
        grid-row: 2;
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
        height: 100%;
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
        border-color: var(--high-risk-border);
        background: var(--high-risk-bg);
    }

    .node.customer {
        border-color: var(--blue);
        background: #eff6ff;
    }

    .node.risk,
    .node.highrisk {
        border-color: var(--high-risk-border);
        background: var(--high-risk-bg);
    }

    .node.mediumrisk {
        border-color: var(--flagged-border);
        background: var(--flagged-bg);
    }

    .node.exposed {
        border-color: var(--exposed-border);
        background: var(--exposed-bg);
    }

    .node.eid {
        border-color: var(--identity-border);
        background: var(--identity-bg);
    }

    .node.account {
        border-color: var(--account-standard-border);
        background: var(--account-standard-bg);
    }

    .node.suspicious-account {
        border-color: var(--flagged-border);
        background: var(--flagged-bg);
    }

    .node.blocked,
    .node.safe-account {
        border-color: var(--controlled-border);
        background: var(--controlled-bg);
    }

    .node.evidence {
        border-color: var(--exposed-border);
        background: var(--exposed-bg);
    }

    .node-icon {
        position: absolute;
        top: 7px;
        right: 9px;
        min-width: 23px;
        height: 23px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.78);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 15px;
        line-height: 1;
        box-shadow: 0 4px 10px rgba(15, 23, 42, 0.10);
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

    .dot.allow { background: var(--account-standard-border); }
    .dot.blocked { background: var(--controlled-border); }
    .dot.high { background: var(--high-risk-border); }
    .dot.flagged { background: var(--flagged-border); }
    .dot.risk { background: var(--high-risk-border); }
    .dot.suspicious { background: var(--flagged-border); }
    .dot.evidence { background: var(--exposed-border); }
    .dot.exposed { background: var(--exposed-border); }
    .dot.expanded { background: var(--blue); }

    .side-panel {
        display: flex;
        flex-direction: column;
        height: 100%;
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

    .badge.low {
        background: #fef9c3;
        color: #854d0e;
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

    .legend-pill {
        position: absolute;
        top: 14px;
        left: 14px;
        z-index: 6;
        height: 36px;
        border-radius: 999px;
        padding: 0 14px;
        border: 1px solid #dbe3ef;
        background: rgba(255, 255, 255, 0.92);
        color: #334155;
        font-weight: 850;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.10);
        backdrop-filter: blur(8px);
    }

    .legend-flyout {
        position: absolute;
        top: 58px;
        left: 14px;
        z-index: 7;
        width: 342px;
        padding: 12px;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.97);
        border: 1px solid #e5e7eb;
        box-shadow: 0 20px 50px rgba(15, 23, 42, 0.18);
        backdrop-filter: blur(10px);
    }

    .legend-flyout.hidden {
        display: none;
    }

    .legend-title {
        font-size: 13px;
        font-weight: 900;
        color: var(--ink);
        margin: 2px 2px 10px 2px;
    }

    .legend-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 7px;
    }

    .legend-chip {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        font-size: 12px;
        font-weight: 800;
        border-radius: 14px;
        padding: 8px 10px;
        border: 2px solid #e5e7eb;
    }

    .legend-chip .legend-left {
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }

    .legend-chip .legend-swatch {
        width: 24px;
        height: 18px;
        border-radius: 8px;
        border: 2px solid currentColor;
        background: currentColor;
        opacity: 0.16;
    }

    .legend-high {
        background: var(--high-risk-bg);
        border-color: var(--high-risk-border) !important;
        color: var(--high-risk-text);
    }

    .legend-medium {
        background: var(--flagged-bg);
        border-color: var(--flagged-border) !important;
        color: var(--flagged-text);
    }

    .legend-exposed {
        background: var(--exposed-bg);
        border-color: var(--exposed-border) !important;
        color: var(--exposed-text);
    }

    .legend-suspicious-account {
        background: var(--flagged-bg);
        border-color: var(--flagged-border) !important;
        color: var(--flagged-text);
    }

    .legend-expandable-account {
        background: var(--account-standard-bg);
        border-color: var(--account-standard-border) !important;
        color: var(--account-standard-text);
    }

    .legend-eid {
        background: var(--identity-bg);
        border-color: var(--identity-border) !important;
        color: var(--identity-text);
    }

    .legend-blocked {
        background: var(--controlled-bg);
        border-color: var(--controlled-border) !important;
        color: var(--controlled-text);
    }

    .legend-evidence {
        background: var(--exposed-bg);
        border-color: var(--exposed-border) !important;
        color: var(--exposed-text);
    }


    .guidance-card {
        border-radius: 18px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid #dbeafe;
        background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
    }

    .guidance-kicker {
        font-size: 10px;
        font-weight: 900;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        color: #2563eb;
        margin-bottom: 6px;
    }

    .guidance-main {
        font-size: 18px;
        line-height: 1.25;
        font-weight: 900;
        color: #0f172a;
    }

    .observation-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-bottom: 12px;
    }

    .observation-card {
        border: 1px solid #e5e7eb;
        border-radius: 15px;
        padding: 12px;
        background: #f8fafc;
    }

    .observation-label {
        font-size: 10px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 850;
        margin-bottom: 5px;
    }

    .observation-value {
        font-size: 16px;
        font-weight: 850;
        color: var(--ink);
        line-height: 1.25;
    }

    .next-steps {
        margin: 8px 0 0 18px;
        padding: 0;
        color: #475569;
        font-size: 13px;
        line-height: 1.5;
    }

    .next-steps li {
        margin-bottom: 6px;
    }

    .risk-flag {
        border-left: 4px solid #e5e7eb;
        padding: 8px 10px;
        margin-bottom: 10px;
        border-radius: 10px;
        background: #f8fafc;
    }

    .risk-flag.high {
        border-left-color: var(--high-risk-border);
        background: #fff1f2;
    }

    .risk-flag.medium {
        border-left-color: var(--flagged-border);
        background: #fff7ed;
    }

    .risk-flag.low {
        border-left-color: var(--exposed-border);
        background: #fffbeb;
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
    <header class="top-bar">
        <div class="top-brand">Wio Network Graphing</div>
        <div class="top-control">
            <label for="analystInput">Analyst ID</label>
            <input id="analystInput" type="text" value="analyst_001" oninput="handleAnalystChange()" />
        </div>
        <div class="top-control">
            <label for="seedSelect">Seed customer</label>
            <select id="seedSelect" onchange="handleSeedChange()"></select>
        </div>
        <div class="top-actions">
            <button class="primary" onclick="startInvestigation()">Start investigation</button>
            <button onclick="resetGraph()">Reset</button>
        </div>
    </header>

    <div class="canvas-shell">
        <div class="canvas-wrap">
            <button class="legend-pill" onclick="toggleLegend()">Risk legend</button>
            <div id="legendFlyout" class="legend-flyout hidden">
                <div class="legend-title">Visual risk legend</div>
                <div class="legend-grid">
                    <div class="legend-chip legend-high"><span class="legend-left">☠️ High-risk customer</span><span class="legend-swatch"></span></div>
                    <div class="legend-chip legend-medium"><span class="legend-left">⚠️ Flagged customer</span><span class="legend-swatch"></span></div>
                    <div class="legend-chip legend-exposed"><span class="legend-left">😟 Network-exposed customer</span><span class="legend-swatch"></span></div>
                    <div class="legend-chip legend-suspicious-account"><span class="legend-left">🚩 Suspicious account / link</span><span class="legend-swatch"></span></div>
                    <div class="legend-chip legend-expandable-account"><span class="legend-left">✅ Standard expandable account / link</span><span class="legend-swatch"></span></div>
                    <div class="legend-chip legend-eid"><span class="legend-left">🔗 Identity connector / link</span><span class="legend-swatch"></span></div>
                    <div class="legend-chip legend-blocked"><span class="legend-left">🛡️ Controlled context connector / link</span><span class="legend-swatch"></span></div>
                    <div class="legend-chip legend-evidence"><span class="legend-left">🧾 Evidence-only connector / link</span><span class="legend-swatch"></span></div>
                </div>
            </div>
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
                Click Start to load the selected customer and immediate connections.
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
let SEED = "";
let ANALYST_ID = "analyst_001";

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

function customerKeys() {
    return Object.keys(DATA.customers || {}).sort();
}

function populateSeedSelect() {
    const select = document.getElementById("seedSelect");
    if (!select || select.options.length) return;

    for (const customerId of customerKeys()) {
        const option = document.createElement("option");
        option.value = customerId;
        option.textContent = customerId;
        select.appendChild(option);
    }
}

function syncControlsFromInputs() {
    const analystInput = document.getElementById("analystInput");
    const seedSelect = document.getElementById("seedSelect");

    ANALYST_ID = analystInput && analystInput.value.trim() ? analystInput.value.trim() : "analyst_001";
    SEED = seedSelect && seedSelect.value ? seedSelect.value : customerKeys()[0];
    state.analystId = ANALYST_ID;
}

function resetStateOnly() {
    state.nodes = {};
    state.edges = {};
    state.selectedNodeId = null;
    state.history = [];
    state.events = [];
    state.started = false;
    state.sessionId = null;
    state.startedAt = null;
}

function handleSeedChange() {
    syncControlsFromInputs();
    resetStateOnly();
    render();

    if (!restoreSavedCase()) {
        renderWelcomePanel();
    }
}

function handleAnalystChange() {
    syncControlsFromInputs();
    setStorageStatus(state.sessionId ? `Audit trail: ${state.events.length} event(s)` : "Audit trail: not started");
}

function toggleLegend() {
    const legend = document.getElementById("legendFlyout");
    if (legend) legend.classList.toggle("hidden");
}

function initApp() {
    populateSeedSelect();
    syncControlsFromInputs();
    render();

    if (!restoreSavedCase()) {
        renderWelcomePanel();
    }
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
    syncControlsFromInputs();

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
        app_version: "wio_network_graphing_v2",
        graph_snapshot: graphSnapshot(),
        investigation_events: state.events,
        investigation_trail: state.history
    };
}

function downloadCaseReport() {
    syncControlsFromInputs();
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

function severityRank(severity) {
    if (severity === "High") return 3;
    if (severity === "Medium") return 2;
    if (severity === "Low") return 1;
    return 0;
}

function customerMaxSeverity(customerId) {
    const risks = customerRisk(customerId);
    if (!risks.length) return 0;
    return Math.max(...risks.map(risk => severityRank(risk.severity)));
}

function customerIsFraudFlagged(customerId) {
    return customerMaxSeverity(customerId) > 0;
}

function accountRiskCustomerCount(accountId) {
    const account = DATA.accounts[accountId];
    if (!account) return 0;

    return new Set((account.linked_customers || [])
        .filter(customerId => customerIsFraudFlagged(customerId))).size;
}

function customerRelatedRiskCount(customerId) {
    if (customerIsFraudFlagged(customerId)) return 0;

    const relatedCustomers = new Set();

    for (const eidKey of DATA.customer_eids[customerId] || []) {
        for (const linkedCustomer of DATA.eids[eidKey]?.linked_customers || []) {
            if (linkedCustomer !== customerId) relatedCustomers.add(linkedCustomer);
        }
    }

    for (const accountLink of DATA.customer_accounts[customerId] || []) {
        for (const linkedCustomer of DATA.accounts[accountLink.account]?.linked_customers || []) {
            if (linkedCustomer !== customerId) relatedCustomers.add(linkedCustomer);
        }
    }

    return [...relatedCustomers].filter(linkedCustomer => customerIsFraudFlagged(linkedCustomer)).length;
}

function visualMarker(node) {
    if (node.type === "CUSTOMER") {
        const maxSeverity = customerMaxSeverity(node.key);
        const exposureCount = customerRelatedRiskCount(node.key);

        if (maxSeverity === 3) {
            return {
                emoji: "☠️",
                title: "High-risk customer: high-severity fraud indicator present"
            };
        }

        if (maxSeverity === 2) {
            return {
                emoji: "⚠️",
                title: "Medium-risk customer: fraud indicator present"
            };
        }

        if (maxSeverity === 1) {
            return {
                emoji: "⚠️",
                title: "Low-risk customer: low-severity fraud indicator present"
            };
        }

        if (exposureCount > 0) {
            return {
                emoji: "😟",
                title: `Potential victim / exposed customer: linked to ${exposureCount} fraud-flagged customer(s)`
            };
        }
    }

    if (node.type === "ACCOUNT") {
        const riskyLinkedCustomers = accountRiskCustomerCount(node.key);

        if (node.policy === "allow" && riskyLinkedCustomers > 0) {
            return {
                emoji: "🚩",
                title: `Suspicious shared account: linked to ${riskyLinkedCustomers} fraud-flagged customer(s)`
            };
        }

        if (node.policy === "evidence") {
            return {
                emoji: "🧾",
                title: "Evidence-only account: review context but do not expand by default"
            };
        }

        if (node.policy === "blocked") {
            return {
                emoji: "🛡️",
                title: "Controlled/common connector: expansion is blocked to prevent graph noise"
            };
        }
    }

    if (node.type === "EID") {
        return {
            emoji: "🔗",
            title: "Identity connector"
        };
    }

    return {
        emoji: "",
        title: ""
    };
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
    const exposureCount = customerRelatedRiskCount(customerId);
    const riskText = risks.length
        ? `${risks.length} fraud indicator(s) are active.`
        : exposureCount > 0
            ? `No direct fraud indicator is active, but this customer is linked to ${exposureCount} fraud-flagged customer(s).`
            : "No active fraud indicators.";

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
            `${customerId} has ${link.transaction_count} transaction(s) with ${account.label} totalling ${link.amount.toLocaleString()}.`
        );
    }
}

function startInvestigation() {
    syncControlsFromInputs();

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
    syncControlsFromInputs();

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
        const account = node.type === "ACCOUNT" ? DATA.accounts[node.key] : null;
        const linkedCount = account?.linked_customer_count || 0;
        const riskyLinkedCustomers = node.type === "ACCOUNT" ? accountRiskCustomerCount(node.key) : 0;
        const blockedReason = linkedCount <= 1
            ? "CONTEXT_ONLY_SINGLE_CUSTOMER"
            : "BROAD_CONTEXT_CONNECTOR";
        const message = linkedCount <= 1
            ? `${node.label} is shown for context. It does not currently create a useful relationship path because it links to one visible customer.`
            : `${node.label} is shown for context. It is connected to many customers, so the relationship should not be interpreted on its own.`;

        recordEvent("REVIEW_CONTEXT_CONNECTOR", message, node, {
            expansion_allowed_flag: false,
            blocked_reason: blockedReason,
            linked_customer_count: linkedCount,
            fraud_flagged_linked_customer_count: riskyLinkedCustomers
        });

        return {
            status: "warn",
            message
        };
    }

    if (node.policy === "evidence") {
        node.expanded = true;

        const message = `${node.label} is supporting evidence. Review it as context, but do not use it alone to infer a relationship.`;

        recordEvent("REVIEW_EVIDENCE_ONLY_NODE", message, node, {
            expansion_allowed_flag: false,
            blocked_reason: "SUPPORTING_EVIDENCE_ONLY"
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
    if (node.type === "CUSTOMER") {
        const maxSeverity = customerMaxSeverity(node.key);
        const exposureCount = customerRelatedRiskCount(node.key);

        if (maxSeverity === 3) return "highrisk";
        if (maxSeverity === 2 || maxSeverity === 1) return "mediumrisk";
        if (exposureCount > 0) return "exposed";
        return "customer";
    }

    if (node.type === "EID") return "eid";

    if (node.type === "ACCOUNT") {
        if (node.policy === "evidence") return "evidence";
        if (node.policy === "blocked") return "blocked";
        if (accountRiskCustomerCount(node.key) > 0) return "suspicious-account";
        return "account";
    }

    return "customer";
}

function nodeStatus(node) {
    if (node.type === "CUSTOMER") {
        const maxSeverity = customerMaxSeverity(node.key);
        const exposureCount = customerRelatedRiskCount(node.key);

        if (node.riskCount > 0) {
            if (maxSeverity === 3) return {dot: "high", text: `${node.riskCount} indicator(s)`};
            return {dot: "flagged", text: `${node.riskCount} indicator(s)`};
        }

        if (exposureCount > 0) return {dot: "exposed", text: `exposed to ${exposureCount} flagged`};
    }

    if (node.type === "ACCOUNT") {
        const riskyLinkedCustomers = accountRiskCustomerCount(node.key);

        if (node.policy === "allow" && riskyLinkedCustomers > 0) {
            return {dot: "suspicious", text: `${riskyLinkedCustomers} flagged link(s)`};
        }
    }

    if (node.expanded) return {dot: "expanded", text: "expanded"};
    if (node.policy === "blocked") return {dot: "blocked", text: "controlled"};
    if (node.policy === "evidence") return {dot: "evidence", text: "evidence only"};
    return {dot: "allow", text: "click to expand"};
}


function edgeStroke(edge) {
    const sourceNode = state.nodes[edge.source];
    const targetNode = state.nodes[edge.target];
    const accountNode = sourceNode?.type === "ACCOUNT" ? sourceNode : targetNode?.type === "ACCOUNT" ? targetNode : null;

    if (edge.relationshipType.includes("EID")) {
        return "#7c3aed";
    }

    if (accountNode) {
        if (accountNode.policy === "evidence") return "#f59e0b";
        if (accountNode.policy === "blocked") return "#94a3b8";
        if (accountRiskCustomerCount(accountNode.key) > 0) return "#f97316";
        return "#16a34a";
    }

    return "#16a34a";
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

        const stroke = edgeStroke(edge);
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
        const marker = visualMarker(node);

        const div = document.createElement("div");
        div.className = `node ${nodeCss(node)}${node.id === state.selectedNodeId ? " selected" : ""}`;
        div.style.left = `${position.x}px`;
        div.style.top = `${position.y}px`;
        div.title = node.summary;

        div.innerHTML = `
            ${marker.emoji ? `<div class="node-icon" title="${escapeHtml(marker.title)}">${marker.emoji}</div>` : ""}
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

function formatMoney(value) {
    const numeric = Number(value || 0);
    if (!Number.isFinite(numeric)) return "AED 0";

    return `AED ${numeric.toLocaleString(undefined, {
        maximumFractionDigits: 0
    })}`;
}

function formatNumber(value) {
    return Number(value || 0).toLocaleString();
}

function highestSeverityText(customerId) {
    const rank = customerMaxSeverity(customerId);
    if (rank === 3) return "High";
    if (rank === 2) return "Medium";
    if (rank === 1) return "Low";
    return "None";
}

function customerAccountLinks(customerId) {
    return DATA.customer_accounts[customerId] || [];
}

function accountLinks(accountId) {
    const rows = [];

    for (const [customerId, links] of Object.entries(DATA.customer_accounts || {})) {
        for (const link of links || []) {
            if (link.account === accountId) {
                rows.push({
                    customerId,
                    direction: link.direction,
                    transactionCount: Number(link.transaction_count || 0),
                    amount: Number(link.amount || 0)
                });
            }
        }
    }

    return rows;
}

function accountFlowProfile(accountId) {
    const links = accountLinks(accountId);
    let receivesFromCustomersAmount = 0;
    let sendsToCustomersAmount = 0;
    let receivesFromCustomersTxns = 0;
    let sendsToCustomersTxns = 0;
    let totalAmount = 0;
    let totalTransactions = 0;

    for (const link of links) {
        totalAmount += link.amount;
        totalTransactions += link.transactionCount;

        if (link.direction === "Paid to") {
            receivesFromCustomersAmount += link.amount;
            receivesFromCustomersTxns += link.transactionCount;
        } else if (link.direction === "Received from") {
            sendsToCustomersAmount += link.amount;
            sendsToCustomersTxns += link.transactionCount;
        } else {
            receivesFromCustomersAmount += link.amount / 2;
            sendsToCustomersAmount += link.amount / 2;
            receivesFromCustomersTxns += link.transactionCount / 2;
            sendsToCustomersTxns += link.transactionCount / 2;
        }
    }

    let flowDirection = "Mixed activity";
    if (receivesFromCustomersAmount > sendsToCustomersAmount * 1.5 && receivesFromCustomersAmount > 0) {
        flowDirection = "Mostly receives funds";
    } else if (sendsToCustomersAmount > receivesFromCustomersAmount * 1.5 && sendsToCustomersAmount > 0) {
        flowDirection = "Mostly sends funds";
    }

    return {
        links,
        totalAmount,
        totalTransactions,
        receivesFromCustomersAmount,
        sendsToCustomersAmount,
        receivesFromCustomersTxns,
        sendsToCustomersTxns,
        flowDirection
    };
}

function linkedCustomerRiskCounts(customerIds) {
    const uniqueCustomers = [...new Set(customerIds || [])];
    let flagged = 0;
    let high = 0;
    let medium = 0;
    let low = 0;

    for (const customerId of uniqueCustomers) {
        const maxSeverity = customerMaxSeverity(customerId);
        if (maxSeverity > 0) flagged += 1;
        if (maxSeverity === 3) high += 1;
        if (maxSeverity === 2) medium += 1;
        if (maxSeverity === 1) low += 1;
    }

    return {
        total: uniqueCustomers.length,
        flagged,
        high,
        medium,
        low,
        unflagged: uniqueCustomers.length - flagged
    };
}

function customerTransactionProfile(customerId) {
    const links = customerAccountLinks(customerId);
    let paidToAmount = 0;
    let receivedFromAmount = 0;
    let totalAmount = 0;
    let transactionCount = 0;
    let largestLink = null;

    for (const link of links) {
        const amount = Number(link.amount || 0);
        const txns = Number(link.transaction_count || 0);
        totalAmount += amount;
        transactionCount += txns;

        if (link.direction === "Paid to") {
            paidToAmount += amount;
        } else if (link.direction === "Received from") {
            receivedFromAmount += amount;
        }

        if (!largestLink || amount > largestLink.amount) {
            largestLink = {
                account: link.account,
                direction: link.direction,
                amount,
                transactionCount: txns
            };
        }
    }

    let flowDirection = "No visible account activity";
    if (paidToAmount > receivedFromAmount * 1.5 && paidToAmount > 0) {
        flowDirection = "Mostly paid out";
    } else if (receivedFromAmount > paidToAmount * 1.5 && receivedFromAmount > 0) {
        flowDirection = "Mostly received funds";
    } else if (totalAmount > 0) {
        flowDirection = "Mixed in/out activity";
    }

    return {
        links,
        paidToAmount,
        receivedFromAmount,
        totalAmount,
        transactionCount,
        largestLink,
        flowDirection
    };
}

function customerConnectedSummary(customerId) {
    const relatedCustomers = new Set();
    const identityLinks = DATA.customer_eids[customerId] || [];
    const accountLinksForCustomer = customerAccountLinks(customerId);
    let suspiciousAccountCount = 0;

    for (const eidKey of identityLinks) {
        for (const linkedCustomer of DATA.eids[eidKey]?.linked_customers || []) {
            if (linkedCustomer !== customerId) relatedCustomers.add(linkedCustomer);
        }
    }

    for (const accountLink of accountLinksForCustomer) {
        const account = DATA.accounts[accountLink.account];
        if (accountRiskCustomerCount(accountLink.account) > 0) suspiciousAccountCount += 1;

        for (const linkedCustomer of account?.linked_customers || []) {
            if (linkedCustomer !== customerId) relatedCustomers.add(linkedCustomer);
        }
    }

    const riskCounts = linkedCustomerRiskCounts([...relatedCustomers]);

    return {
        relatedCustomers: [...relatedCustomers],
        identityLinkCount: identityLinks.length,
        accountLinkCount: accountLinksForCustomer.length,
        suspiciousAccountCount,
        flaggedRelatedCount: riskCounts.flagged,
        highRiskRelatedCount: riskCounts.high
    };
}

function observationCard(label, value) {
    return `
        <div class="observation-card">
            <div class="observation-label">${escapeHtml(label)}</div>
            <div class="observation-value">${escapeHtml(value)}</div>
        </div>
    `;
}

function observationGrid(items) {
    return `
        <div class="observation-grid">
            ${items.map(item => observationCard(item.label, item.value)).join("")}
        </div>
    `;
}

function nextStepsList(steps) {
    return `
        <ol class="next-steps">
            ${steps.map(step => `<li>${escapeHtml(step)}</li>`).join("")}
        </ol>
    `;
}

function nodeActionVerb(node) {
    if (node.type === "ACCOUNT") {
        if (node.policy === "allow") return "Open linked customers";
        if (node.policy === "evidence") return "Use as supporting evidence";
        return "Keep as context";
    }

    if (node.type === "EID") return "Review linked entities";
    if (node.type === "CUSTOMER") return "Review customer context";
    return "Review node";
}

function panelHeaderSubtitle(node) {
    if (node.type === "CUSTOMER") {
        const riskCount = customerRisk(node.key).length;
        const exposureCount = customerRelatedRiskCount(node.key);

        if (riskCount > 0) return `${riskCount} fraud indicator(s) attached to this customer.`;
        if (exposureCount > 0) return `No direct indicators, but linked to ${exposureCount} fraud-flagged customer(s).`;
        return "No direct indicators visible in this network extract.";
    }

    if (node.type === "ACCOUNT") {
        const account = DATA.accounts[node.key];
        const riskCounts = linkedCustomerRiskCounts(account?.linked_customers || []);
        return `${riskCounts.total} related Wio customer(s); ${riskCounts.flagged} have fraud indicators.`;
    }

    if (node.type === "EID") {
        const eid = DATA.eids[node.key];
        const riskCounts = linkedCustomerRiskCounts(eid?.linked_customers || []);
        return `${eid?.linked_customers?.length || 0} linked customer/entity node(s); ${riskCounts.flagged} have fraud indicators.`;
    }

    return node.summary;
}

function customerGuidance(node) {
    const customerId = node.key;
    const customer = DATA.customers[customerId];
    const risks = customerRisk(customerId);
    const maxSeverity = customerMaxSeverity(customerId);
    const exposureCount = customerRelatedRiskCount(customerId);
    const connectedSummary = customerConnectedSummary(customerId);
    const tx = customerTransactionProfile(customerId);
    const largest = tx.largestLink;

    let recommendation = "Review this customer’s relationship path before deciding whether to expand further.";
    let why = "This customer is part of the visible relationship network through shared accounts, identity links, or both.";

    if (maxSeverity === 3) {
        recommendation = "Prioritise this customer. They have a high-severity fraud indicator and should anchor the next review step.";
        why = "A directly flagged customer connected to other customers or accounts can explain how risk moves through the network.";
    } else if (risks.length > 0) {
        recommendation = "Review this customer’s fraud indicators, then inspect their strongest account connections.";
        why = "This customer has direct indicators, so their shared accounts and identity links may reveal related activity.";
    } else if (exposureCount > 0 && largest && largest.direction === "Paid to") {
        recommendation = "Review as a potentially exposed customer. Check whether the outgoing payment looks like scam or victim behaviour.";
        why = "This customer has no direct fraud indicators, but they paid a counterparty connected to fraud-flagged customers.";
    } else if (exposureCount > 0) {
        recommendation = "Review as network-exposed. Check whether the connection is explainable or suspicious.";
        why = "This customer has no direct indicators but is close to fraud-flagged customers in the relationship graph.";
    }

    const observations = [
        {label: "Customer type", value: customer.segment || "Unknown"},
        {label: "Fraud indicators", value: `${risks.length}`},
        {label: "Highest severity", value: highestSeverityText(customerId)},
        {label: "Connected flagged customers", value: `${connectedSummary.flaggedRelatedCount}`},
        {label: "Visible account links", value: `${connectedSummary.accountLinkCount}`},
        {label: "Identity links", value: `${connectedSummary.identityLinkCount}`},
        {label: "Flow direction", value: tx.flowDirection},
        {label: "Visible value", value: formatMoney(tx.totalAmount)}
    ];

    if (largest) {
        observations.push({
            label: "Largest visible link",
            value: `${largest.direction} ${formatMoney(largest.amount)} via ${largest.account}`
        });
    }

    const steps = risks.length > 0
        ? [
            "Start with the highest-severity fraud indicator and confirm what behaviour triggered it.",
            "Open the shared accounts connected to this customer and compare transaction direction and value.",
            "Review customers reached through the same account or identity connector.",
            "Document whether the customer appears to be driving the network activity or being exposed to it."
        ]
        : [
            "Check whether money moved from this customer to a counterparty connected to flagged customers.",
            "Compare the amount and frequency against normal customer behaviour.",
            "Review linked flagged customers before concluding whether this customer is a victim or participant.",
            "Look for supporting evidence from identity, device, employer, beneficiary, or support case signals."
        ];

    return {recommendation, why, observations, steps};
}

function accountGuidance(node) {
    const account = DATA.accounts[node.key];
    const visibleCustomers = account?.linked_customers || [];
    const riskCounts = linkedCustomerRiskCounts(visibleCustomers);
    const flow = accountFlowProfile(node.key);
    const relatedWioCustomers = account?.linked_customer_count || visibleCustomers.length;

    let recommendation = "Review this account to understand how the linked customers are connected.";
    let why = "A shared account can reveal a relationship between customers, especially when the connected customers have fraud indicators.";

    if (node.policy === "evidence") {
        recommendation = "Use this as supporting evidence only. Do not rely on this account alone to explain the network.";
        why = "This account appears across a wide customer base or is better treated as background context. A link here needs supporting evidence from other signals.";
    } else if (node.policy === "blocked" && visibleCustomers.length <= 1) {
        recommendation = "Keep this as context. It does not currently connect multiple visible customers in this case.";
        why = "The account is visible because it is related to the selected customer, but it does not create a useful relationship path on its own.";
    } else if (node.policy === "blocked") {
        recommendation = "Use carefully. This account is connected to many customers, so the relationship is weaker without supporting evidence.";
        why = "Broad payment points can create misleading network links. Use this only to support other stronger evidence.";
    } else if (riskCounts.flagged >= 2) {
        recommendation = "Open this account first. It connects multiple customers with fraud indicators.";
        why = "The account links a focused set of customers, and several are already risk flagged. This makes it useful for relationship discovery.";
    } else if (riskCounts.flagged === 1) {
        recommendation = "Review this account. It connects at least one flagged customer to others who may be exposed.";
        why = "The account may explain how risk is spreading from a flagged customer to connected customers.";
    }

    let roleInsight = "The account has mixed activity with linked customers.";
    if (flow.flowDirection === "Mostly receives funds") {
        roleInsight = "The account mostly receives funds from linked customers. Review whether it acts as a collection point.";
    } else if (flow.flowDirection === "Mostly sends funds") {
        roleInsight = "The account mostly sends funds to linked customers. Review whether it acts as a distribution point.";
    }

    const observations = [
        {label: "Related Wio customers", value: `${relatedWioCustomers}`},
        {label: "Visible customers", value: `${visibleCustomers.length}`},
        {label: "Flagged customers", value: `${riskCounts.flagged}`},
        {label: "High-risk customers", value: `${riskCounts.high}`},
        {label: "Flow pattern", value: flow.flowDirection},
        {label: "Visible transactions", value: `${formatNumber(flow.totalTransactions)}`},
        {label: "Visible value", value: formatMoney(flow.totalAmount)},
        {label: "Analyst action", value: nodeActionVerb(node)}
    ];

    const steps = node.policy === "allow"
        ? [
            "Open the linked customers and review the fraud-flagged ones first.",
            "Compare who paid into the account and who received funds from it.",
            "Check whether the amounts look like normal business/customer activity or suspicious pass-through activity.",
            "Look for repeated identity, employer, device, beneficiary, or support case signals across linked customers."
        ]
        : [
            "Do not treat this account as a strong relationship by itself.",
            "Use it to support stronger links from shared identity, focused shared accounts, or direct fraud indicators.",
            "Review transaction direction and value only if another signal makes this account relevant.",
            "Avoid expanding broad context unless the analyst has a specific reason."
        ];

    return {recommendation, why: `${why} ${roleInsight}`, observations, steps};
}

function eidGuidance(node) {
    const eid = DATA.eids[node.key];
    const linkedCustomers = eid?.linked_customers || [];
    const riskCounts = linkedCustomerRiskCounts(linkedCustomers);
    let retailCount = 0;
    let smeCount = 0;

    for (const customerId of linkedCustomers) {
        const segment = DATA.customers[customerId]?.segment;
        if (segment === "Retail") retailCount += 1;
        if (segment === "SME") smeCount += 1;
    }

    let recommendation = "Review the customers connected by this identity link.";
    let why = "The same identity links multiple Wio customer/entity records. This can reveal related accounts that should be reviewed together.";

    if (riskCounts.flagged > 0) {
        recommendation = "Review the flagged customers on this identity link first, then compare the linked Retail and SME activity.";
        why = "When one linked customer has fraud indicators, related customers under the same identity may need review even if they are not directly flagged.";
    }

    const observations = [
        {label: "Linked customers", value: `${linkedCustomers.length}`},
        {label: "Retail", value: `${retailCount}`},
        {label: "SME", value: `${smeCount}`},
        {label: "Flagged customers", value: `${riskCounts.flagged}`},
        {label: "High-risk customers", value: `${riskCounts.high}`},
        {label: "Analyst action", value: "Review linked entities"}
    ];

    const steps = [
        "Start with the linked customers that have fraud indicators.",
        "Compare whether Retail and SME accounts share counterparties or transaction patterns.",
        "Check whether funds move between related entities or through the same external accounts.",
        "Document whether the identity link strengthens the case or is only background context."
    ];

    return {recommendation, why, observations, steps};
}

function guidanceForNode(node) {
    if (node.type === "CUSTOMER") return customerGuidance(node);
    if (node.type === "ACCOUNT") return accountGuidance(node);
    if (node.type === "EID") return eidGuidance(node);

    return {
        recommendation: "Review this node in context.",
        why: node.summary,
        observations: [],
        steps: ["Review connected nodes before taking action."]
    };
}

function renderWelcomePanel() {
    document.getElementById("panelKicker").textContent = "Ready";
    document.getElementById("panelTitle").textContent = "Start the investigation";
    document.getElementById("panelSubtitle").textContent = "Click Start to load the selected customer and immediate connections.";

    document.getElementById("panelBody").innerHTML = `
        <div class="guidance-card">
            <div class="guidance-kicker">Analyst guidance</div>
            <div class="guidance-main">Start with the selected customer, then follow the strongest relationship path.</div>
        </div>
        <div class="section">
            <div class="section-title">How to use this view</div>
            <div class="section-text">
                Click a customer, identity connector, or counterparty account to get a plain-English investigation summary and suggested next checks.
            </div>
        </div>
        <div class="section">
            <div class="section-title">Investigation principle</div>
            <div class="section-text">
                Prioritise direct fraud indicators, focused shared accounts, and identity links that connect flagged customers. Treat broad or single-customer context as supporting evidence only.
            </div>
        </div>
    `;
}

function statusCard(result) {
    if (!result) return "";

    return `
        <div class="status-card ${result.status}">
            <strong>Latest action</strong><br>
            ${escapeHtml(result.message)}
        </div>
    `;
}

function renderRiskDetails(node) {
    if (node.type !== "CUSTOMER") return "";

    const risks = customerRisk(node.key);

    if (!risks.length) {
        const exposureCount = customerRelatedRiskCount(node.key);
        const message = exposureCount > 0
            ? `No direct fraud indicators are attached to this customer, but they are connected to ${exposureCount} fraud-flagged customer(s).`
            : "No fraud indicators are attached to this customer in the current risk overlay.";

        return `
            <div class="section">
                <div class="section-title">Fraud indicators</div>
                <div class="section-text">${escapeHtml(message)}</div>
            </div>
        `;
    }

    return `
        <div class="section">
            <div class="section-title">Fraud indicators</div>
            ${risks.map(risk => {
                const severityClass = risk.severity === "High" ? "high" : risk.severity === "Medium" ? "medium" : "low";
                return `
                    <div class="risk-flag ${severityClass}">
                        <strong>${escapeHtml(risk.name)}</strong>
                        <div class="section-text" style="margin-top: 4px;">${escapeHtml(risk.description)}</div>
                    </div>
                `;
            }).join("")}
        </div>
    `;
}

function renderAuditTrail() {
    if (!state.history.length) {
        return "";
    }

    return `
        <details class="section">
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
    const guidance = guidanceForNode(node);

    document.getElementById("panelKicker").textContent = node.type;
    document.getElementById("panelTitle").textContent = node.label;
    document.getElementById("panelSubtitle").textContent = panelHeaderSubtitle(node);

    document.getElementById("panelBody").innerHTML = `
        ${statusCard(result)}

        <div class="guidance-card">
            <div class="guidance-kicker">Analyst guidance</div>
            <div class="guidance-main">${escapeHtml(guidance.recommendation)}</div>
        </div>

        <div class="section">
            <div class="section-title">Why this matters</div>
            <div class="section-text">${escapeHtml(guidance.why)}</div>
        </div>

        <div class="section">
            <div class="section-title">Key observations</div>
            ${observationGrid(guidance.observations)}
        </div>

        ${renderRiskDetails(node)}

        <div class="section">
            <div class="section-title">Suggested next checks</div>
            ${nextStepsList(guidance.steps)}
        </div>

        ${renderAuditTrail()}
    `;
}


initApp();
</script>
</body>
</html>
"""

    return template.replace("__DATA_JSON__", data_json)


def main() -> None:
    st.set_page_config(
        page_title="Wio Network Graphing",
        layout="wide",
    )

    st.markdown(
        """
        <style>
            [data-testid="stAppViewContainer"] {
                background: #f5f7fb;
            }

            [data-testid="stSidebar"] {
                display: none;
            }

            [data-testid="collapsedControl"] {
                display: none;
            }

            .block-container {
                max-width: 100%;
                padding: 0;
            }

            [data-testid="stHeader"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    components.html(
        build_html(),
        height=1000,
        scrolling=False,
    )


if __name__ == "__main__":
    main()