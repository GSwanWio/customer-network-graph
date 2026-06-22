from pathlib import Path

import pandas as pd


def main() -> None:
	project_root = Path(__file__).resolve().parents[1]
	output_path = project_root / "data" / "simulated" / "simulated_customer_network.xlsx"

	output_path.parent.mkdir(parents=True, exist_ok=True)

	# Demo seeds:
	# CUST_1  = expands through EID and then through a local counterparty chain
	# CUST_6  = expands through EID only, then stops
	# CUST_8  = isolated seed, no EID and no counterparty chain
	# CUST_10 = expands into a larger branched network
	seed_customers = pd.DataFrame([
		{"seed_customer_id": "CUST_1"},
		{"seed_customer_id": "CUST_6"},
		{"seed_customer_id": "CUST_8"},
		{"seed_customer_id": "CUST_10"},
	])

	identity_entities = pd.DataFrame([
		# Original chain seed
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

		# EID-only seed: expands to CUST_7 but has no counterparty continuation
		{
			"entity_type": "SME",
			"entity_id": "CUST_6",
			"lookup_customer_id": "CUST_6",
			"emirates_id_number": "EID_2222",
			"entity_created_at": "2025-03-10",
		},
		{
			"entity_type": "RETAIL",
			"entity_id": "CUST_7",
			"lookup_customer_id": "CUST_7",
			"emirates_id_number": "EID_2222",
			"entity_created_at": "2025-03-15",
		},

		# Isolated seed: should still appear in the display
		{
			"entity_type": "SME",
			"entity_id": "CUST_8",
			"lookup_customer_id": "CUST_8",
			"emirates_id_number": None,
			"entity_created_at": "2025-03-20",
		},

		# Larger branched network seed
		{
			"entity_type": "SME",
			"entity_id": "CUST_10",
			"lookup_customer_id": "CUST_10",
			"emirates_id_number": "EID_5555",
			"entity_created_at": "2025-04-01",
		},
		{
			"entity_type": "RETAIL",
			"entity_id": "CUST_11",
			"lookup_customer_id": "CUST_11",
			"emirates_id_number": "EID_5555",
			"entity_created_at": "2025-04-03",
		},
		{
			"entity_type": "SME",
			"entity_id": "CUST_12",
			"lookup_customer_id": "CUST_12",
			"emirates_id_number": "EID_5555",
			"entity_created_at": "2025-04-05",
		},
		{
			"entity_type": "RETAIL",
			"entity_id": "CUST_13",
			"lookup_customer_id": "CUST_13",
			"emirates_id_number": "EID_1313",
			"entity_created_at": "2025-04-10",
		},
		{
			"entity_type": "SME",
			"entity_id": "CUST_14",
			"lookup_customer_id": "CUST_14",
			"emirates_id_number": "EID_1414",
			"entity_created_at": "2025-04-12",
		},
		{
			"entity_type": "RETAIL",
			"entity_id": "CUST_15",
			"lookup_customer_id": "CUST_15",
			"emirates_id_number": "EID_1515",
			"entity_created_at": "2025-04-14",
		},
		{
			"entity_type": "SME",
			"entity_id": "CUST_16",
			"lookup_customer_id": "CUST_16",
			"emirates_id_number": "EID_1616",
			"entity_created_at": "2025-04-16",
		},
		{
			"entity_type": "RETAIL",
			"entity_id": "CUST_17",
			"lookup_customer_id": "CUST_17",
			"emirates_id_number": "EID_1717",
			"entity_created_at": "2025-04-18",
		},
	])

	local_counterparty_flows = pd.DataFrame([
		# Original chain: CUST_2 -> CUST_3 -> CUST_4 -> CUST_5
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

		# Larger branched network from CUST_10 via EID to CUST_11 and CUST_12
		{
			"flow_direction": "OUTBOUND",
			"lookup_customer_id": "CUST_11",
			"transaction_id": "TXN_101",
			"transaction_timestamp": "2026-02-01 10:00:00",
			"counterparty_account_number": "HUB_ACCOUNT",
			"transaction_amount": 1500.00,
		},
		{
			"flow_direction": "INBOUND",
			"lookup_customer_id": "CUST_13",
			"transaction_id": "TXN_102",
			"transaction_timestamp": "2026-02-02 11:00:00",
			"counterparty_account_number": "HUB_ACCOUNT",
			"transaction_amount": 1800.00,
		},
		{
			"flow_direction": "OUTBOUND",
			"lookup_customer_id": "CUST_14",
			"transaction_id": "TXN_103",
			"transaction_timestamp": "2026-02-03 12:00:00",
			"counterparty_account_number": "HUB_ACCOUNT",
			"transaction_amount": 900.00,
		},
		{
			"flow_direction": "OUTBOUND",
			"lookup_customer_id": "CUST_13",
			"transaction_id": "TXN_104",
			"transaction_timestamp": "2026-02-04 13:00:00",
			"counterparty_account_number": "JKL_ACCOUNT",
			"transaction_amount": 600.00,
		},
		{
			"flow_direction": "INBOUND",
			"lookup_customer_id": "CUST_15",
			"transaction_id": "TXN_105",
			"transaction_timestamp": "2026-02-05 14:00:00",
			"counterparty_account_number": "JKL_ACCOUNT",
			"transaction_amount": 650.00,
		},
		{
			"flow_direction": "OUTBOUND",
			"lookup_customer_id": "CUST_14",
			"transaction_id": "TXN_106",
			"transaction_timestamp": "2026-02-06 15:00:00",
			"counterparty_account_number": "MNO_ACCOUNT",
			"transaction_amount": 750.00,
		},
		{
			"flow_direction": "INBOUND",
			"lookup_customer_id": "CUST_16",
			"transaction_id": "TXN_107",
			"transaction_timestamp": "2026-02-07 16:00:00",
			"counterparty_account_number": "MNO_ACCOUNT",
			"transaction_amount": 800.00,
		},
		{
			"flow_direction": "OUTBOUND",
			"lookup_customer_id": "CUST_12",
			"transaction_id": "TXN_108",
			"transaction_timestamp": "2026-02-08 17:00:00",
			"counterparty_account_number": "PQR_ACCOUNT",
			"transaction_amount": 1200.00,
		},
		{
			"flow_direction": "INBOUND",
			"lookup_customer_id": "CUST_17",
			"transaction_id": "TXN_109",
			"transaction_timestamp": "2026-02-09 18:00:00",
			"counterparty_account_number": "PQR_ACCOUNT",
			"transaction_amount": 1300.00,
		},

		# Single-customer account activity for CUST_6.
		# This should not create a chain because the account is not shared.
		{
			"flow_direction": "OUTBOUND",
			"lookup_customer_id": "CUST_6",
			"transaction_id": "TXN_201",
			"transaction_timestamp": "2026-03-01 10:00:00",
			"counterparty_account_number": "SOLO_ACCOUNT",
			"transaction_amount": 250.00,
		},
	])

	with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
		seed_customers.to_excel(writer, sheet_name="seed_customers", index=False)
		identity_entities.to_excel(writer, sheet_name="identity_entities", index=False)
		local_counterparty_flows.to_excel(writer, sheet_name="local_counterparty_flows", index=False)

	print(f"Created simulated Excel file: {output_path}")


if __name__ == "__main__":
	main()
