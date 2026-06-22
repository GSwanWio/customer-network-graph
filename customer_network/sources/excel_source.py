from pathlib import Path

import pandas as pd


class ExcelSource:
	def __init__(self, excel_path: str | Path, sheets: dict[str, str]) -> None:
		self.excel_path = Path(excel_path)
		self.sheets = sheets

		if not self.excel_path.exists():
			raise FileNotFoundError(f"Excel file not found: {self.excel_path}")

	def load_seed_customers(self) -> pd.DataFrame:
		return self._read_sheet("seed_customers")

	def load_identity_entities(self) -> pd.DataFrame:
		return self._read_sheet("identity_entities")

	def load_local_counterparty_flows(self) -> pd.DataFrame:
		return self._read_sheet("local_counterparty_flows")

	def load_all(self) -> dict[str, pd.DataFrame]:
		return {
			"seed_customers": self.load_seed_customers(),
			"identity_entities": self.load_identity_entities(),
			"local_counterparty_flows": self.load_local_counterparty_flows(),
		}

	def _read_sheet(self, sheet_key: str) -> pd.DataFrame:
		if sheet_key not in self.sheets:
			raise KeyError(f"Missing sheet mapping in config for: {sheet_key}")

		sheet_name = self.sheets[sheet_key]

		return pd.read_excel(
			self.excel_path,
			sheet_name=sheet_name,
			engine="openpyxl",
			dtype=str,
		)