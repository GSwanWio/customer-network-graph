from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

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

	data = source.load_all()

	for name, df in data.items():
		print("")
		print(f"Dataset: {name}")
		print(f"Rows: {len(df)}")
		print(f"Columns: {list(df.columns)}")
		print(df.head(10).to_string(index=False))


if __name__ == "__main__":
	main()