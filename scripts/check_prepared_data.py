from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from customer_network.prepare.prepare_counterparty_flows import prepare_local_counterparty_flows
from customer_network.prepare.prepare_identity import prepare_identity_entities
from customer_network.prepare.prepare_seed import prepare_seed_customers
from customer_network.sources.excel_source import ExcelSource
from customer_network.utils.config import load_yaml


def main() -> None:
	demo_config = load_yaml(project_root / "config" / "demo_excel.yml")

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

	prepared_data = {
		"seed_customers": seed_customers,
		"identity_entities": identity_entities,
		"local_counterparty_flows": local_counterparty_flows,
	}

	for name, df in prepared_data.items():
		print("")
		print(f"Prepared dataset: {name}")
		print(f"Rows: {len(df)}")
		print(f"Columns: {list(df.columns)}")
		print(df.head(20).to_string(index=False))


if __name__ == "__main__":
	main()