import re

import pandas as pd


def clean_string(value: object) -> str | None:
	if pd.isna(value):
		return None

	cleaned_value = str(value).strip()

	if cleaned_value == "":
		return None

	return cleaned_value


def clean_upper_string(value: object) -> str | None:
	cleaned_value = clean_string(value)

	if cleaned_value is None:
		return None

	return cleaned_value.upper()


def normalize_identifier(value: object) -> str | None:
	cleaned_value = clean_upper_string(value)

	if cleaned_value is None:
		return None

	normalized_value = re.sub(r"[^0-9A-Z]", "", cleaned_value)

	if normalized_value == "":
		return None

	return normalized_value


def require_columns(df: pd.DataFrame, required_columns: list[str], dataset_name: str) -> None:
	missing_columns = [
		column
		for column in required_columns
		if column not in df.columns
	]

	if missing_columns:
		raise ValueError(f"{dataset_name} is missing required columns: {missing_columns}")