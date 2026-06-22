from pathlib import Path
import sys

import pandas as pd

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from customer_network.graph.build_counterparty_graph import build_counterparty_graph
from customer_network.graph.build_eid_graph import build_eid_graph
from customer_network.prepare.prepare_counterparty_flows import prepare_local_counterparty_flows
from customer_network.prepare.prepare_identity import prepare_identity_entities
from customer_network.prepare.prepare_seed import prepare_seed_customers
from customer_network.sources.excel_source import ExcelSource
from customer_network.utils.config import load_yaml
from customer_network.validate.validate_eid_graph import validate_eid_graph
from customer_network.validate.validate_prepared_data import validate_prepared_data


def main() -> None:
	demo_config = load_yaml(project_root / "config" / "demo_excel.yml")
	graph_rules = load_yaml(project_root / "config" / "graph_rules.yml")

	excel_path = project_root / demo_config["excel_path"]
	sheets = demo_config["sheets"]

	source = ExcelSource(
		excel_path=excel_path,
		sheets=sheets,
	)

	raw_data = source.load_all()

	seed_customers = prepare_seed_customers(raw_data["seed_customers"])
	identity_entities = prepare_identity_entities(raw_data["identity_entities"])
	local_counterparty_flows = prepare_local_counterparty_flows(raw_data["local_counterparty_flows"])

	prepared_errors = validate_prepared_data(
		seed_customers=seed_customers,
		identity_entities=identity_entities,
		local_counterparty_flows=local_counterparty_flows,
	)

	if prepared_errors:
		print("Prepared data validation failed.")
		for error in prepared_errors:
			print(f"- {error}")
		raise SystemExit(1)

	eid_graph = build_eid_graph(
		seed_customers=seed_customers,
		identity_entities=identity_entities,
	)

	eid_errors = validate_eid_graph(eid_graph)

	if eid_errors:
		print("EID graph validation failed.")
		for error in eid_errors:
			print(f"- {error}")
		raise SystemExit(1)

	# Important:
	# CUST_1 has no direct counterparty transaction in the demo.
	# It reaches CUST_2 through EID first, then CUST_2 starts the counterparty expansion.
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

	for name, df in counterparty_graph.items():
		print("")
		print(f"Counterparty graph dataset: {name}")
		print(f"Rows: {len(df)}")
		print(f"Columns: {list(df.columns)}")

		if len(df) > 0:
			print(df.head(20).to_string(index=False))


if __name__ == "__main__":
	main()
