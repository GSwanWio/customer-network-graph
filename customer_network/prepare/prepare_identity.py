import pandas as pd

from customer_network.prepare.utils import clean_string, clean_upper_string, normalize_identifier, require_columns


def prepare_identity_entities(identity_entities_raw: pd.DataFrame) -> pd.DataFrame:
	required_columns = [
		"entity_type",
		"entity_id",
		"lookup_customer_id",
		"emirates_id_number",
		"entity_created_at",
	]

	require_columns(identity_entities_raw, required_columns, "identity_entities")

	identity_entities = identity_entities_raw.copy()

	identity_entities["entity_type"] = identity_entities["entity_type"].apply(clean_upper_string)
	identity_entities["entity_id"] = identity_entities["entity_id"].apply(clean_string)
	identity_entities["lookup_customer_id"] = identity_entities["lookup_customer_id"].apply(clean_string)
	identity_entities["emirates_id_number"] = identity_entities["emirates_id_number"].apply(normalize_identifier)
	identity_entities["entity_created_at"] = pd.to_datetime(
		identity_entities["entity_created_at"],
		errors="coerce",
	)

	identity_entities = identity_entities[
		identity_entities["entity_type"].notna()
		& identity_entities["entity_id"].notna()
		& identity_entities["lookup_customer_id"].notna()
	].copy()

	identity_entities["entity_key"] = (
		identity_entities["entity_type"]
		+ "|"
		+ identity_entities["entity_id"]
	)

	identity_entities = identity_entities.drop_duplicates(
		subset=["entity_key"]
	).reset_index(drop=True)

	return identity_entities[
		[
			"entity_type",
			"entity_id",
			"entity_key",
			"lookup_customer_id",
			"emirates_id_number",
			"entity_created_at",
		]
	]