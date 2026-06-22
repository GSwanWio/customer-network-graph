from pathlib import Path

import pandas as pd


def main() -> None:
	project_root = Path(__file__).resolve().parents[1]
	output_path = project_root / "data" / "simulated" / "simulated_customer_network.xlsx"

	output_path.parent.mkdir(parents=True, exist_ok=True)

	seed_customers = pd.DataFrame([
		{"seed_customer_id": "CUST_1"}
	])

	identity_entities = pd.DataFrame([
		{
			"entity_type": "SME",
			"entity_id": "CUST_1",
			"lookup_customer_id": "CUST_1",
			"emirates_id_number": "EID_1234",
			"entity_created_at": "2025-01-01",
		},
		{
			"entity_type": "RETAIL",
			"entity_id": "CUST_2",
			"lookup_customer_id": "CUST_2",
			"emirates_id_number": "EID_1234",
			"entity_created_at": "2025-01-05",
		},
		{
			"entity_type": "SME",
			"entity_id": "CUST_3",
			"lookup_customer_id": "CUST_3",
			"emirates_id_number": "EID_9999",
			"entity_created_at": "2025-02-01",
		},
		{
			"entity_type": "RETAIL",
			"entity_id": "CUST_4",
			"lookup_customer_id": "CUST_4",
			"emirates_id_number": "EID_8888",
			"entity_created_at": "2025-02-10",
		},
		{
			"entity_type": "SME",
			"entity_id": "CUST_5",
			"lookup_customer_id": "CUST_5",
			"emirates_id_number": "EID_7777",
			"entity_created_at": "2025-03-01",
		},
	])

	local_counterparty_flows = pd.DataFrame([
		{
			"flow_direction": "OUTBOUND",
			"lookup_customer_id": "CUST_2",
			"transaction_id": "TXN_001",
			"transaction_timestamp": "2026-01-01 10:00:00",
			"counterparty_account_number": "ABC_ACCOUNT",
			"transaction_amount": 1000.00,
		},
		{
			"flow_direction": "INBOUND",
			"lookup_customer_id": "CUST_3",
			"transaction_id": "TXN_002",
			"transaction_timestamp": "2026-01-02 11:00:00",
			"counterparty_account_number": "ABC_ACCOUNT",
			"transaction_amount": 2000.00,
		},
		{
			"flow_direction": "OUTBOUND",
			"lookup_customer_id": "CUST_3",
			"transaction_id": "TXN_003",
			"transaction_timestamp": "2026-01-03 12:00:00",
			"counterparty_account_number": "DEF_ACCOUNT",
			"transaction_amount": 500.00,
		},
		{
			"flow_direction": "INBOUND",
			"lookup_customer_id": "CUST_4",
			"transaction_id": "TXN_004",
			"transaction_timestamp": "2026-01-04 13:00:00",
			"counterparty_account_number": "DEF_ACCOUNT",
			"transaction_amount": 700.00,
		},
		{
			"flow_direction": "OUTBOUND",
			"lookup_customer_id": "CUST_4",
			"transaction_id": "TXN_005",
			"transaction_timestamp": "2026-01-05 14:00:00",
			"counterparty_account_number": "GHI_ACCOUNT",
			"transaction_amount": 300.00,
		},
		{
			"flow_direction": "INBOUND",
			"lookup_customer_id": "CUST_5",
			"transaction_id": "TXN_006",
			"transaction_timestamp": "2026-01-06 15:00:00",
			"counterparty_account_number": "GHI_ACCOUNT",
			"transaction_amount": 400.00,
		},
	])

	with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
		seed_customers.to_excel(writer, sheet_name="seed_customers", index=False)
		identity_entities.to_excel(writer, sheet_name="identity_entities", index=False)
		local_counterparty_flows.to_excel(writer, sheet_name="local_counterparty_flows", index=False)

	print(f"Created simulated Excel file: {output_path}")


if __name__ == "__main__":
	main()