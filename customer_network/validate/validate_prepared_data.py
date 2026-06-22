import pandas as pd


def validate_no_nulls(df: pd.DataFrame, columns: list[str], dataset_name: str) -> list[str]:
	errors = []

	for column in columns:
		null_count = df[column].isna().sum()

		if null_count > 0:
			errors.append(f"{dataset_name}.{column} has {null_count} null values")

	return errors


def validate_unique(df: pd.DataFrame, columns: list[str], dataset_name: str) -> list[str]:
	duplicate_count = df.duplicated(subset=columns).sum()

	if duplicate_count > 0:
		return [f"{dataset_name} has {duplicate_count} duplicate rows by {columns}"]

	return []


def validate_seed_customers(seed_customers: pd.DataFrame) -> list[str]:
	errors = []

	required_columns = [
		"seed_customer_id",
	]

	missing_columns = [
		column
		for column in required_columns
		if column not in seed_customers.columns
	]

	if missing_columns:
		errors.append(f"seed_customers missing columns: {missing_columns}")
		return errors

	errors.extend(validate_no_nulls(seed_customers, required_columns, "seed_customers"))
	errors.extend(validate_unique(seed_customers, ["seed_customer_id"], "seed_customers"))

	return errors


def validate_identity_entities(identity_entities: pd.DataFrame) -> list[str]:
	errors = []

	required_columns = [
		"entity_type",
		"entity_id",
		"entity_key",
		"lookup_customer_id",
		"emirates_id_number",
		"entity_created_at",
	]

	missing_columns = [
		column
		for column in required_columns
		if column not in identity_entities.columns
	]

	if missing_columns:
		errors.append(f"identity_entities missing columns: {missing_columns}")
		return errors

	errors.extend(
		validate_no_nulls(
			identity_entities,
			[
				"entity_type",
				"entity_id",
				"entity_key",
				"lookup_customer_id",
			],
			"identity_entities",
		)
	)

	errors.extend(validate_unique(identity_entities, ["entity_key"], "identity_entities"))

	invalid_entity_type_count = (~identity_entities["entity_type"].isin(["SME", "RETAIL"])).sum()

	if invalid_entity_type_count > 0:
		errors.append(f"identity_entities has {invalid_entity_type_count} invalid entity_type values")

	return errors


def validate_local_counterparty_flows(local_counterparty_flows: pd.DataFrame) -> list[str]:
	errors = []

	required_columns = [
		"flow_direction",
		"lookup_customer_id",
		"transaction_id",
		"transaction_timestamp",
		"counterparty_account_number",
		"transaction_amount",
	]

	missing_columns = [
		column
		for column in required_columns
		if column not in local_counterparty_flows.columns
	]

	if missing_columns:
		errors.append(f"local_counterparty_flows missing columns: {missing_columns}")
		return errors

	errors.extend(
		validate_no_nulls(
			local_counterparty_flows,
			[
				"flow_direction",
				"lookup_customer_id",
				"transaction_id",
				"transaction_timestamp",
				"counterparty_account_number",
				"transaction_amount",
			],
			"local_counterparty_flows",
		)
	)

	invalid_direction_count = (~local_counterparty_flows["flow_direction"].isin(["OUTBOUND", "INBOUND"])).sum()

	if invalid_direction_count > 0:
		errors.append(f"local_counterparty_flows has {invalid_direction_count} invalid flow_direction values")

	negative_amount_count = (local_counterparty_flows["transaction_amount"] < 0).sum()

	if negative_amount_count > 0:
		errors.append(f"local_counterparty_flows has {negative_amount_count} negative transaction_amount values")

	errors.extend(
		validate_unique(
			local_counterparty_flows,
			[
				"transaction_id",
				"lookup_customer_id",
				"counterparty_account_number",
				"flow_direction",
			],
			"local_counterparty_flows",
		)
	)

	return errors


def validate_seed_customer_coverage(
	seed_customers: pd.DataFrame,
	identity_entities: pd.DataFrame,
) -> list[str]:
	errors = []

	matched_seed_count = seed_customers["seed_customer_id"].isin(
		identity_entities["lookup_customer_id"]
	).sum()

	unmatched_seed_count = len(seed_customers) - matched_seed_count

	if unmatched_seed_count > 0:
		errors.append(f"{unmatched_seed_count} seed customers do not exist in identity_entities")

	return errors


def validate_counterparty_customer_coverage(
	local_counterparty_flows: pd.DataFrame,
	identity_entities: pd.DataFrame,
) -> list[str]:
	errors = []

	missing_customer_count = (~local_counterparty_flows["lookup_customer_id"].isin(
		identity_entities["lookup_customer_id"]
	)).sum()

	if missing_customer_count > 0:
		errors.append(f"{missing_customer_count} counterparty flow rows have lookup_customer_id not found in identity_entities")

	return errors


def validate_prepared_data(
	seed_customers: pd.DataFrame,
	identity_entities: pd.DataFrame,
	local_counterparty_flows: pd.DataFrame,
) -> list[str]:
	errors = []

	errors.extend(validate_seed_customers(seed_customers))
	errors.extend(validate_identity_entities(identity_entities))
	errors.extend(validate_local_counterparty_flows(local_counterparty_flows))
	errors.extend(validate_seed_customer_coverage(seed_customers, identity_entities))
	errors.extend(validate_counterparty_customer_coverage(local_counterparty_flows, identity_entities))

	return errors