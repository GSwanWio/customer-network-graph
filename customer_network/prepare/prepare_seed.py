import pandas as pd

from customer_network.prepare.utils import clean_string, require_columns


def prepare_seed_customers(seed_customers_raw: pd.DataFrame) -> pd.DataFrame:
	required_columns = [
		"seed_customer_id",
	]

	require_columns(seed_customers_raw, required_columns, "seed_customers")

	seed_customers = seed_customers_raw.copy()

	seed_customers["seed_customer_id"] = seed_customers["seed_customer_id"].apply(clean_string)

	seed_customers = seed_customers[
		seed_customers["seed_customer_id"].notna()
	].copy()

	seed_customers = seed_customers.drop_duplicates(
		subset=["seed_customer_id"]
	).reset_index(drop=True)

	return seed_customers[
		[
			"seed_customer_id",
		]
	]