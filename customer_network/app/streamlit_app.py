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


def load_prepared_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
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


def main() -> None:
	st.set_page_config(
		page_title="Customer Network Graph Demo",
		layout="wide",
	)

	st.title("Customer Network Graph Demo")
	st.caption("Demo version using simulated Excel data. Later, this source can be replaced with Databricks.")

	identity_entities, _, _ = load_prepared_data()

	available_customers = (
		identity_entities["lookup_customer_id"]
		.dropna()
		.drop_duplicates()
		.sort_values()
		.tolist()
	)

	default_customer = "CUST_1" if "CUST_1" in available_customers else available_customers[0]

	seed_customer_id = st.selectbox(
		"Select customer ID",
		options=available_customers,
		index=available_customers.index(default_customer),
	)

	run_button = st.button("Build network graph", type="primary")

	if run_button:
		try:
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

			metric_columns[0].metric("Nodes", int(component["graph_node_count"]))
			metric_columns[1].metric("Edges", int(component["graph_edge_count"]))
			metric_columns[2].metric("Entities", int(component["entity_node_count"]))
			metric_columns[3].metric("EID nodes", int(component["eid_node_count"]))
			metric_columns[4].metric("Accounts", int(component["counterparty_account_node_count"]))
			metric_columns[5].metric("Transactions", int(component["total_transaction_count"]))

			html_content = output_path.read_text(encoding="utf-8")

			components.html(
				html_content,
				height=760,
				scrolling=True,
			)

			with st.expander("Combined nodes"):
				st.dataframe(combined_graph["combined_nodes"], use_container_width=True)

			with st.expander("Combined edges"):
				st.dataframe(combined_graph["combined_edges"], use_container_width=True)

			with st.expander("Combined components"):
				st.dataframe(combined_graph["combined_components"], use_container_width=True)

		except Exception as error:
			st.error(str(error))


if __name__ == "__main__":
	main()
