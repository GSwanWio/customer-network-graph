from pathlib import Path
import sys

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from customer_network.export.export_graph_html import export_graph_html
from customer_network.graph.build_combined_graph import build_combined_graph
from customer_network.graph.build_counterparty_graph import build_counterparty_graph
from customer_network.graph.build_eid_graph import build_eid_graph
from customer_network.prepare.prepare_counterparty_flows import prepare_local_counterparty_flows
from customer_network.prepare.prepare_identity import prepare_identity_entities
from customer_network.prepare.prepare_seed import prepare_seed_customers
from customer_network.sources.excel_source import ExcelSource
from customer_network.utils.config import load_yaml
from customer_network.validate.validate_combined_graph import validate_combined_graph
from customer_network.validate.validate_counterparty_graph import validate_counterparty_graph
from customer_network.validate.validate_eid_graph import validate_eid_graph
from customer_network.validate.validate_prepared_data import validate_prepared_data


def apply_page_style() -> None:
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

			[data-testid="stHeader"] {
				background: rgba(245, 247, 251, 0.85);
			}

			.block-container {
				padding-top: 2rem;
				padding-bottom: 3rem;
				max-width: 1500px;
			}

			.hero-card {
				background: linear-gradient(135deg, #111827 0%, #243b63 55%, #355c7d 100%);
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
				max-width: 900px;
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

			.metric-card {
				background: white;
				border: 1px solid #e5e7eb;
				border-radius: 18px;
				padding: 18px 20px;
				box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
				min-height: 110px;
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
				font-size: 34px;
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

			.panel {
				background: white;
				border: 1px solid #e5e7eb;
				border-radius: 20px;
				padding: 20px;
				box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
				margin-top: 16px;
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
				margin-bottom: 14px;
			}

			.insight-box {
				background: #f8fafc;
				border: 1px solid #e2e8f0;
				border-radius: 16px;
				padding: 16px 18px;
				margin-bottom: 12px;
			}

			.insight-title {
				font-weight: 800;
				color: #0f172a;
				margin-bottom: 4px;
			}

			.insight-text {
				color: #475569;
				font-size: 13px;
				line-height: 1.45;
			}

			.stButton > button {
				width: 100%;
				border-radius: 14px;
				background: #ef4444;
				border: 0;
				color: white;
				font-weight: 800;
				padding: 0.75rem 1rem;
			}

			.stButton > button:hover {
				background: #dc2626;
				border: 0;
				color: white;
			}

			div[data-testid="stDataFrame"] {
				border-radius: 14px;
				overflow: hidden;
			}
		</style>
		""",
		unsafe_allow_html=True,
	)


@st.cache_data(show_spinner=False)
def load_prepared_data() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
	demo_config = load_yaml(project_root / "config" / "demo_excel.yml")
	graph_rules = load_yaml(project_root / "config" / "graph_rules.yml")

	excel_path = project_root / demo_config["excel_path"]
	sheets = demo_config["sheets"]

	source = ExcelSource(
		excel_path=excel_path,
		sheets=sheets,
	)

	raw_data = source.load_all()

	identity_entities = prepare_identity_entities(raw_data["identity_entities"])
	local_counterparty_flows = prepare_local_counterparty_flows(raw_data["local_counterparty_flows"])

	return identity_entities, local_counterparty_flows, graph_rules


def build_demo_graph(seed_customer_id: str) -> dict[str, pd.DataFrame]:
	identity_entities, local_counterparty_flows, graph_rules = load_prepared_data()

	seed_customers_raw = pd.DataFrame([
		{"seed_customer_id": seed_customer_id}
	])

	seed_customers = prepare_seed_customers(seed_customers_raw)

	prepared_errors = validate_prepared_data(
		seed_customers=seed_customers,
		identity_entities=identity_entities,
		local_counterparty_flows=local_counterparty_flows,
	)

	if prepared_errors:
		raise ValueError("\n".join(prepared_errors))

	eid_graph = build_eid_graph(
		seed_customers=seed_customers,
		identity_entities=identity_entities,
	)

	eid_errors = validate_eid_graph(eid_graph)

	if eid_errors:
		raise ValueError("\n".join(eid_errors))

	if len(eid_graph["eid_nodes"]) == 0:
		raise ValueError(f"No EID graph found for seed customer: {seed_customer_id}")

	eid_entity_customers = (
		eid_graph["eid_nodes"]
		.loc[
			eid_graph["eid_nodes"]["node_type"] == "ENTITY",
			"lookup_customer_id",
		]
		.dropna()
		.drop_duplicates()
		.sort_values()
		.tolist()
	)

	counterparty_seed_customers = pd.DataFrame({
		"seed_customer_id": eid_entity_customers
	})

	counterparty_graph = build_counterparty_graph(
		seed_customers=counterparty_seed_customers,
		identity_entities=identity_entities,
		local_counterparty_flows=local_counterparty_flows,
		graph_rules=graph_rules,
	)

	counterparty_errors = validate_counterparty_graph(
		counterparty_graph=counterparty_graph,
		graph_rules=graph_rules,
	)

	if counterparty_errors:
		raise ValueError("\n".join(counterparty_errors))

	combined_graph = build_combined_graph(
		eid_graph=eid_graph,
		counterparty_graph=counterparty_graph,
	)

	combined_errors = validate_combined_graph(combined_graph)

	if combined_errors:
		raise ValueError("\n".join(combined_errors))

	return combined_graph


def metric_card(label: str, value: int | float | str, helper: str) -> None:
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


def render_component_summary(component: pd.Series) -> None:
	profile = component["component_profile"]

	if profile == "IDENTITY_AND_COUNTERPARTY_NETWORK":
		profile_text = "The seed expands through both identity and local counterparty relationships."
	elif profile == "IDENTITY_ONLY_NETWORK":
		profile_text = "The seed expands through identity relationships only."
	elif profile == "COUNTERPARTY_ONLY_NETWORK":
		profile_text = "The seed expands through local counterparty relationships only."
	else:
		profile_text = "The seed does not expand into a material network."

	st.markdown(
		f"""
		<div class="insight-box">
			<div class="insight-title">Network profile</div>
			<div class="insight-text">{profile_text}</div>
		</div>
		""",
		unsafe_allow_html=True,
	)

	st.markdown(
		f"""
		<div class="insight-box">
			<div class="insight-title">How to read this view</div>
			<div class="insight-text">
				Red is the original triggered customer. Purple diamonds are Emirates ID connectors.
				Green squares are shared local counterparty accounts. Blue nodes are linked entities.
				Orange nodes are customers reached through identity and then used to start the counterparty expansion.
			</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


def main() -> None:
	st.set_page_config(
		page_title="Customer Network Graph Demo",
		page_icon="🕸️",
		layout="wide",
	)

	apply_page_style()

	identity_entities, _, _ = load_prepared_data()

	available_customers = (
		identity_entities["lookup_customer_id"]
		.dropna()
		.drop_duplicates()
		.sort_values()
		.tolist()
	)

	default_customer = "CUST_1" if "CUST_1" in available_customers else available_customers[0]

	with st.sidebar:
		st.markdown("## Network Demo")
		st.caption("Simulated Excel source")

		seed_customer_id = st.selectbox(
			"Triggered customer ID",
			options=available_customers,
			index=available_customers.index(default_customer),
		)

		st.markdown("---")
		st.markdown("### Relationship layers")
		st.checkbox("Identity / Emirates ID", value=True, disabled=True)
		st.checkbox("Local counterparty accounts", value=True, disabled=True)

		st.markdown("---")
		run_button = st.button("Build network graph", type="primary")

		st.caption("Later this same flow can receive customer IDs from risk indicator thresholds.")

	st.markdown(
		"""
		<div class="hero-card">
			<div class="status-pill">Demo mode · Simulated Excel data</div>
			<div class="hero-title">Customer Relationship Network</div>
			<p class="hero-subtitle">
				Explore how a triggered customer expands through deterministic identity links and shared local counterparty accounts.
				The graph logic is modular, so the Excel source can later be replaced with Databricks queries.
			</p>
		</div>
		""",
		unsafe_allow_html=True,
	)

	if not run_button:
		st.markdown(
			"""
			<div class="panel">
				<div class="panel-title">Ready to build a network</div>
				<div class="panel-caption">
					Choose a triggered customer ID in the sidebar and click Build network graph.
					Try CUST_1 for a compact chain, CUST_6 for an identity-only stop, CUST_8 for an isolated seed, or CUST_10 for a larger branched network.
				</div>
			</div>
			""",
			unsafe_allow_html=True,
		)
		return

	try:
		with st.spinner("Building and validating customer network..."):
			combined_graph = build_demo_graph(seed_customer_id)

			output_path = project_root / "outputs" / "streamlit_customer_network.html"

			export_graph_html(
				combined_nodes=combined_graph["combined_nodes"],
				combined_edges=combined_graph["combined_edges"],
				output_path=output_path,
				title=f"Customer Network Graph: {seed_customer_id}",
			)

			component = combined_graph["combined_components"].iloc[0]

		metric_columns = st.columns(6)

		with metric_columns[0]:
			metric_card("Nodes", int(component["graph_node_count"]), "Total graph nodes")

		with metric_columns[1]:
			metric_card("Edges", int(component["graph_edge_count"]), "Relationship evidence")

		with metric_columns[2]:
			metric_card("Entities", int(component["entity_node_count"]), "Customer/entity nodes")

		with metric_columns[3]:
			metric_card("EID nodes", int(component["eid_node_count"]), "Identity connectors")

		with metric_columns[4]:
			metric_card("Accounts", int(component["counterparty_account_node_count"]), "Counterparty connectors")

		with metric_columns[5]:
			metric_card("Transactions", int(component["total_transaction_count"]), "Counterparty txns")

		tab_graph, tab_summary, tab_nodes, tab_edges, tab_components = st.tabs(
			[
				"Network graph",
				"Summary",
				"Nodes",
				"Edges",
				"Components",
			]
		)

		with tab_graph:
			st.markdown(
				"""
				<div class="panel">
					<div class="panel-title">Combined relationship graph</div>
					<div class="panel-caption">Hover over nodes and edges to see relationship details.</div>
				</div>
				""",
				unsafe_allow_html=True,
			)

			html_content = output_path.read_text(encoding="utf-8")

			components.html(
				html_content,
				height=780,
				scrolling=True,
			)

			st.download_button(
				label="Download HTML graph",
				data=html_content,
				file_name=f"customer_network_{seed_customer_id}.html",
				mime="text/html",
			)

		with tab_summary:
			st.markdown(
				"""
				<div class="panel">
					<div class="panel-title">Network interpretation</div>
					<div class="panel-caption">High-level explanation of the generated component.</div>
				</div>
				""",
				unsafe_allow_html=True,
			)
			render_component_summary(component)

		with tab_nodes:
			st.dataframe(
				combined_graph["combined_nodes"],
				use_container_width=True,
				hide_index=True,
			)

		with tab_edges:
			st.dataframe(
				combined_graph["combined_edges"],
				use_container_width=True,
				hide_index=True,
			)

		with tab_components:
			st.dataframe(
				combined_graph["combined_components"],
				use_container_width=True,
				hide_index=True,
			)

	except Exception as error:
		st.error(str(error))


if __name__ == "__main__":
	main()
