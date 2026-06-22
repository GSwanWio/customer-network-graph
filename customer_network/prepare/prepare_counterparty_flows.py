import pandas as pd

from customer_network.prepare.utils import clean_string, clean_upper_string, normalize_identifier, require_columns


def prepare_local_counterparty_flows(local_counterparty_flows_raw: pd.DataFrame) -> pd.DataFrame:
	required_columns = [
		"flow_direction",
		"lookup_customer_id",
		"transaction_id",
		"transaction_timestamp",
		"counterparty_account_number",
		"transaction_amount",
	]

	require_columns(local_counterparty_flows_raw, required_columns, "local_counterparty_flows")

	local_counterparty_flows = local_counterparty_flows_raw.copy()

	local_counterparty_flows["flow_direction"] = local_counterparty_flows["flow_direction"].apply(clean_upper_string)
	local_counterparty_flows["lookup_customer_id"] = local_counterparty_flows["lookup_customer_id"].apply(clean_string)
	local_counterparty_flows["transaction_id"] = local_counterparty_flows["transaction_id"].apply(clean_string)
	local_counterparty_flows["counterparty_account_number"] = local_counterparty_flows["counterparty_account_number"].apply(normalize_identifier)
	local_counterparty_flows["transaction_timestamp"] = pd.to_datetime(
		local_counterparty_flows["transaction_timestamp"],
		errors="coerce",
	)
	local_counterparty_flows["transaction_amount"] = pd.to_numeric(
		local_counterparty_flows["transaction_amount"],
		errors="coerce",
	)

	local_counterparty_flows = local_counterparty_flows[
		local_counterparty_flows["flow_direction"].isin(["OUTBOUND", "INBOUND"])
		& local_counterparty_flows["lookup_customer_id"].notna()
		& local_counterparty_flows["transaction_id"].notna()
		& local_counterparty_flows["counterparty_account_number"].notna()
		& local_counterparty_flows["transaction_timestamp"].notna()
	].copy()

	local_counterparty_flows["transaction_amount"] = local_counterparty_flows["transaction_amount"].fillna(0)

	local_counterparty_flows = local_counterparty_flows.drop_duplicates(
		subset=["transaction_id", "lookup_customer_id", "counterparty_account_number", "flow_direction"]
	).reset_index(drop=True)

	return local_counterparty_flows[
		[
			"flow_direction",
			"lookup_customer_id",
			"transaction_id",
			"transaction_timestamp",
			"counterparty_account_number",
			"transaction_amount",
		]
	]