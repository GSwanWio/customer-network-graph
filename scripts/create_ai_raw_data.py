from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import random

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "ai_test" / "raw"

AS_OF_DATE = date(2026, 6, 30)
CURRENT_START = AS_OF_DATE - timedelta(days=89)
PREVIOUS_START = CURRENT_START - timedelta(days=90)
PREVIOUS_END = CURRENT_START - timedelta(days=1)


CUSTOMERS = [
    {
        "customer_id": "CUST_1",
        "customer_name": "Omar Haddad",
        "segment": "SME",
        "account_status": "Active",
        "age": 42,
        "nationality": "Jordanian",
        "employer": "Blue Palm Trading FZE",
        "occupation": "Managing Partner",
        "customer_since": "2023-04-17",
        "customer_tenure_months": 38,
        "monthly_income_aed": 48500,
        "average_balance_aed": 126400,
        "peer_group": "SME_active_24_to_48m",
    },
    {
        "customer_id": "CUST_2",
        "customer_name": "Maya Nair",
        "segment": "Retail",
        "account_status": "Active",
        "age": 34,
        "nationality": "Indian",
        "employer": "Al Noor Facilities Management LLC",
        "occupation": "Operations Manager",
        "customer_since": "2023-11-02",
        "customer_tenure_months": 31,
        "monthly_income_aed": 19200,
        "average_balance_aed": 38600,
        "peer_group": "Retail_active_24_to_48m",
    },
    {
        "customer_id": "CUST_3",
        "customer_name": "Bilal Qureshi",
        "segment": "SME",
        "account_status": "Active",
        "age": 39,
        "nationality": "Pakistani",
        "employer": "Crescent Digital Services LLC",
        "occupation": "Owner",
        "customer_since": "2024-01-19",
        "customer_tenure_months": 29,
        "monthly_income_aed": 37200,
        "average_balance_aed": 68400,
        "peer_group": "SME_active_24_to_48m",
    },
    {
        "customer_id": "CUST_4",
        "customer_name": "Nadia Petrova",
        "segment": "Retail",
        "account_status": "Active",
        "age": 31,
        "nationality": "Bulgarian",
        "employer": "Gulf Horizon Events LLC",
        "occupation": "Event Coordinator",
        "customer_since": "2024-02-12",
        "customer_tenure_months": 28,
        "monthly_income_aed": 15800,
        "average_balance_aed": 21900,
        "peer_group": "Retail_active_24_to_48m",
    },
    {
        "customer_id": "CUST_5",
        "customer_name": "Samuel Okafor",
        "segment": "SME",
        "account_status": "Under Review",
        "age": 45,
        "nationality": "Nigerian",
        "employer": "Red Falcon General Trading LLC",
        "occupation": "Director",
        "customer_since": "2022-09-05",
        "customer_tenure_months": 45,
        "monthly_income_aed": 62400,
        "average_balance_aed": 94000,
        "peer_group": "SME_active_24_to_48m",
    },
    {
        "customer_id": "CUST_6",
        "customer_name": "Leila Mansour",
        "segment": "Retail",
        "account_status": "Active",
        "age": 29,
        "nationality": "Lebanese",
        "employer": "Aster Media Production LLC",
        "occupation": "Account Executive",
        "customer_since": "2023-07-21",
        "customer_tenure_months": 35,
        "monthly_income_aed": 14750,
        "average_balance_aed": 18400,
        "peer_group": "Retail_active_24_to_48m",
    },
    {
        "customer_id": "CUST_7",
        "customer_name": "Hassan Farouk",
        "segment": "Retail",
        "account_status": "Active",
        "age": 37,
        "nationality": "Egyptian",
        "employer": "Brightline Cargo Services LLC",
        "occupation": "Logistics Supervisor",
        "customer_since": "2024-03-08",
        "customer_tenure_months": 27,
        "monthly_income_aed": 13600,
        "average_balance_aed": 9200,
        "peer_group": "Retail_active_24_to_48m",
    },
    {
        "customer_id": "CUST_8",
        "customer_name": "Anika Sharma",
        "segment": "Retail",
        "account_status": "Active",
        "age": 26,
        "nationality": "Indian",
        "employer": "Pearl Avenue Medical Centre",
        "occupation": "Nurse",
        "customer_since": "2024-05-16",
        "customer_tenure_months": 25,
        "monthly_income_aed": 11200,
        "average_balance_aed": 14100,
        "peer_group": "Retail_active_24_to_48m",
    },
    {
        "customer_id": "CUST_9",
        "customer_name": "Rami Khoury",
        "segment": "SME",
        "account_status": "Active",
        "age": 48,
        "nationality": "Syrian",
        "employer": "Golden Route Auto Parts LLC",
        "occupation": "General Manager",
        "customer_since": "2022-12-11",
        "customer_tenure_months": 42,
        "monthly_income_aed": 53800,
        "average_balance_aed": 153200,
        "peer_group": "SME_active_24_to_48m",
    },
    {
        "customer_id": "CUST_10",
        "customer_name": "Amina Yusuf",
        "segment": "SME",
        "account_status": "Under Review",
        "age": 33,
        "nationality": "Kenyan",
        "employer": "Urban Nest Cleaning Services LLC",
        "occupation": "Business Owner",
        "customer_since": "2023-02-27",
        "customer_tenure_months": 40,
        "monthly_income_aed": 41700,
        "average_balance_aed": 76800,
        "peer_group": "SME_active_24_to_48m",
    },
]


ACTIVITY = {
    "CUST_1":  {"sent": 482000,  "received": 515000,  "sent_txns": 38, "recv_txns": 22, "beneficiaries": 14, "active_beneficiaries": 9,  "cash": 76000,  "intl": 218000, "country": "United Arab Emirates"},
    "CUST_2":  {"sent": 126000,  "received": 214000,  "sent_txns": 18, "recv_txns": 31, "beneficiaries": 6,  "active_beneficiaries": 4,  "cash": 18000,  "intl": 42000,  "country": "India"},
    "CUST_3":  {"sent": 734000,  "received": 689000,  "sent_txns": 61, "recv_txns": 48, "beneficiaries": 21, "active_beneficiaries": 16, "cash": 133000, "intl": 386000, "country": "Pakistan"},
    "CUST_4":  {"sent": 89000,   "received": 173000,  "sent_txns": 15, "recv_txns": 26, "beneficiaries": 5,  "active_beneficiaries": 3,  "cash": 22000,  "intl": 17000,  "country": "United Arab Emirates"},
    "CUST_5":  {"sent": 1189000, "received": 1217000, "sent_txns": 92, "recv_txns": 74, "beneficiaries": 34, "active_beneficiaries": 24, "cash": 244000, "intl": 601000, "country": "Nigeria"},
    "CUST_6":  {"sent": 57000,   "received": 142000,  "sent_txns": 9,  "recv_txns": 19, "beneficiaries": 3,  "active_beneficiaries": 2,  "cash": 11000,  "intl": 9000,   "country": "United Arab Emirates"},
    "CUST_7":  {"sent": 238000,  "received": 251000,  "sent_txns": 34, "recv_txns": 29, "beneficiaries": 11, "active_beneficiaries": 8,  "cash": 58000,  "intl": 73000,  "country": "Egypt"},
    "CUST_8":  {"sent": 44000,   "received": 116000,  "sent_txns": 8,  "recv_txns": 16, "beneficiaries": 2,  "active_beneficiaries": 1,  "cash": 9000,   "intl": 6000,   "country": "India"},
    "CUST_9":  {"sent": 604000,  "received": 752000,  "sent_txns": 43, "recv_txns": 39, "beneficiaries": 17, "active_beneficiaries": 12, "cash": 91000,  "intl": 212000, "country": "United Arab Emirates"},
    "CUST_10": {"sent": 963000,  "received": 901000,  "sent_txns": 86, "recv_txns": 63, "beneficiaries": 29, "active_beneficiaries": 21, "cash": 207000, "intl": 488000, "country": "Kenya"},
}


FRAUD_INDICATORS = [
    ("CUST_1", "rapid_fund_movement", "high", 4, 12, 2, "movement_to_average_balance_ratio", 7.89),
    ("CUST_1", "shared_counterparty_with_flagged_customers", "high", 2, 18, 1, "flagged_related_customer_count", 4),
    ("CUST_1", "high_beneficiary_velocity", "medium", 3, 24, 6, "beneficiaries_added", 14),

    ("CUST_3", "high_beneficiary_velocity", "high", 5, 28, 4, "beneficiaries_added", 21),
    ("CUST_3", "large_international_outflow", "medium", 3, 16, 3, "international_transfer_aed_90d", 386000),

    ("CUST_5", "rapid_fund_movement", "high", 6, 20, 2, "movement_to_average_balance_ratio", 25.60),
    ("CUST_5", "high_beneficiary_velocity", "high", 7, 32, 1, "beneficiaries_added", 34),
    ("CUST_5", "cash_intensive_activity", "medium", 4, 21, 5, "cash_withdrawal_aed_90d", 244000),
    ("CUST_5", "shared_counterparty_with_flagged_customers", "high", 3, 18, 2, "flagged_related_customer_count", 6),

    ("CUST_7", "unusual_outbound_activity", "medium", 2, 14, 2, "sent_to_monthly_income_ratio", 17.50),

    ("CUST_9", "supplier_payment_concentration", "medium", 2, 25, 8, "top_3_counterparty_share_of_sent_value", 0.69),

    ("CUST_10", "rapid_fund_movement", "high", 5, 11, 1, "movement_to_average_balance_ratio", 24.30),
    ("CUST_10", "shared_counterparty_with_flagged_customers", "high", 4, 19, 2, "flagged_related_customer_count", 7),
    ("CUST_10", "high_beneficiary_velocity", "medium", 5, 30, 3, "beneficiaries_added", 29),
]


SHARED_COUNTERPARTIES = {
    "CP_SHARED_001": ["CUST_1", "CUST_3", "CUST_5", "CUST_7", "CUST_10"],
    "CP_SHARED_002": ["CUST_1", "CUST_2", "CUST_4"],
    "CP_SHARED_003": ["CUST_1", "CUST_9"],
    "CP_SHARED_004": ["CUST_1", "CUST_5", "CUST_10"],
    "CP_SHARED_005": ["CUST_3", "CUST_9"],
    "CP_SHARED_006": ["CUST_5", "CUST_10"],
}


IDENTITY_LINKS = {
    "EID_001": ["CUST_1", "CUST_2", "CUST_6"],
    "EID_002": ["CUST_5", "CUST_10"],
    "EID_003": ["CUST_3", "CUST_9"],
    "EID_004": ["CUST_4", "CUST_8"],
}


def split_total(total: float, count: int, seed: int) -> list[float]:
    if count <= 0:
        return []

    rng = random.Random(seed)
    weights = [rng.uniform(0.45, 1.65) for _ in range(count)]
    total_weight = sum(weights)
    amounts = [round(total * weight / total_weight, 2) for weight in weights]
    amounts[-1] = round(amounts[-1] + total - sum(amounts), 2)
    return amounts


def date_for_index(start: date, end: date, index: int, total: int) -> str:
    if total <= 1:
        return end.isoformat()

    span = (end - start).days
    offset = int((index / max(1, total - 1)) * span)
    return (start + timedelta(days=offset)).isoformat()


def build_customers() -> pd.DataFrame:
    return pd.DataFrame(CUSTOMERS)


def build_fraud_indicators() -> pd.DataFrame:
    rows = []

    for idx, item in enumerate(FRAUD_INDICATORS, start=1):
        (
            customer_id,
            indicator_type,
            severity,
            trigger_count,
            first_seen_days_ago,
            last_seen_days_ago,
            supporting_metric,
            supporting_value,
        ) = item

        rows.append({
            "indicator_id": f"FI_{idx:04d}",
            "customer_id": customer_id,
            "indicator_type": indicator_type,
            "severity": severity,
            "trigger_count": trigger_count,
            "first_seen_date": (AS_OF_DATE - timedelta(days=first_seen_days_ago)).isoformat(),
            "last_seen_date": (AS_OF_DATE - timedelta(days=last_seen_days_ago)).isoformat(),
            "supporting_metric": supporting_metric,
            "supporting_value": supporting_value,
        })

    return pd.DataFrame(rows)


def build_counterparty_links() -> pd.DataFrame:
    rows = []

    for cp_index, (counterparty_id, customers) in enumerate(SHARED_COUNTERPARTIES.items(), start=1):
        for customer_position, customer_id in enumerate(customers, start=1):
            rng = random.Random(cp_index * 100 + customer_position)
            activity = ACTIVITY[customer_id]
            linked_value = round(activity["sent"] * rng.uniform(0.10, 0.32), 2)

            rows.append({
                "counterparty_id": counterparty_id,
                "customer_id": customer_id,
                "counterparty_type": "shared_account",
                "linked_value_aed": linked_value,
                "transaction_count": rng.randint(3, 18),
                "first_seen_date": (CURRENT_START + timedelta(days=rng.randint(0, 25))).isoformat(),
                "last_seen_date": (AS_OF_DATE - timedelta(days=rng.randint(0, 10))).isoformat(),
            })

    return pd.DataFrame(rows)


def build_identity_links() -> pd.DataFrame:
    rows = []

    for eid_id, customers in IDENTITY_LINKS.items():
        for customer_id in customers:
            rows.append({
                "eid_id": eid_id,
                "customer_id": customer_id,
                "link_type": "emirates_id",
                "created_date": "2024-01-01",
            })

    return pd.DataFrame(rows)


def build_beneficiaries() -> pd.DataFrame:
    rows = []

    for customer_id, activity in ACTIVITY.items():
        shared = [
            cp
            for cp, customers in SHARED_COUNTERPARTIES.items()
            if customer_id in customers
        ]

        private_count = max(0, activity["beneficiaries"] - len(shared))
        private = [f"CP_{customer_id}_{idx:03d}" for idx in range(1, private_count + 1)]
        counterparties = (shared + private)[:activity["beneficiaries"]]

        for idx, counterparty_id in enumerate(counterparties, start=1):
            if idx <= 3:
                created_date = (AS_OF_DATE - timedelta(days=idx * 6)).isoformat()
            else:
                created_date = date_for_index(CURRENT_START, AS_OF_DATE, idx, len(counterparties))

            rows.append({
                "beneficiary_id": f"BEN_{customer_id}_{idx:03d}",
                "customer_id": customer_id,
                "counterparty_id": counterparty_id,
                "beneficiary_created_date": created_date,
                "beneficiary_country": activity["country"],
                "beneficiary_type": "business" if customer_id in {"CUST_1", "CUST_3", "CUST_5", "CUST_9", "CUST_10"} else "personal",
                "active_90d": idx <= activity["active_beneficiaries"],
            })

    return pd.DataFrame(rows)


def period_scale(customer_index: int) -> float:
    return 0.48 + ((customer_index % 5) * 0.08)


def build_transactions(beneficiaries: pd.DataFrame) -> pd.DataFrame:
    rows = []

    def add_period(
        *,
        customer_id: str,
        customer_index: int,
        period_label: str,
        start: date,
        end: date,
        sent_total: float,
        received_total: float,
        sent_count: int,
        received_count: int,
        cash_total: float,
        international_total: float,
    ) -> None:
        customer_bens = beneficiaries[beneficiaries["customer_id"] == customer_id]
        counterparties = customer_bens["counterparty_id"].tolist() or [f"CP_{customer_id}_001"]

        cash_count = min(max(1, sent_count // 8), sent_count) if cash_total > 0 else 0
        transfer_count = max(0, sent_count - cash_count)

        cash_amounts = split_total(cash_total, cash_count, customer_index * 101)
        transfer_amounts = split_total(max(0, sent_total - cash_total), transfer_count, customer_index * 103)
        received_amounts = split_total(received_total, received_count, customer_index * 107)

        for idx, amount in enumerate(cash_amounts, start=1):
            rows.append({
                "transaction_id": f"TXN_{len(rows) + 1:06d}",
                "customer_id": customer_id,
                "period_label": period_label,
                "transaction_date": date_for_index(start, end, idx, max(1, sent_count)),
                "direction": "sent",
                "transaction_type": "cash_withdrawal",
                "counterparty_id": "CASH_WITHDRAWAL",
                "amount_aed": amount,
                "payment_country": "United Arab Emirates",
                "is_international": False,
                "is_cash_withdrawal": True,
            })

        running_international = 0.0

        for idx, amount in enumerate(transfer_amounts, start=1):
            counterparty_id = counterparties[(idx - 1) % len(counterparties)]
            is_international = running_international < international_total

            if is_international:
                running_international += amount

            rows.append({
                "transaction_id": f"TXN_{len(rows) + 1:06d}",
                "customer_id": customer_id,
                "period_label": period_label,
                "transaction_date": date_for_index(start, end, idx + cash_count, max(1, sent_count)),
                "direction": "sent",
                "transaction_type": "transfer",
                "counterparty_id": counterparty_id,
                "amount_aed": amount,
                "payment_country": ACTIVITY[customer_id]["country"] if is_international else "United Arab Emirates",
                "is_international": is_international,
                "is_cash_withdrawal": False,
            })

        for idx, amount in enumerate(received_amounts, start=1):
            rows.append({
                "transaction_id": f"TXN_{len(rows) + 1:06d}",
                "customer_id": customer_id,
                "period_label": period_label,
                "transaction_date": date_for_index(start, end, idx, max(1, received_count)),
                "direction": "received",
                "transaction_type": "transfer",
                "counterparty_id": f"SRC_{customer_id}_{(idx % 7) + 1:03d}",
                "amount_aed": amount,
                "payment_country": "United Arab Emirates",
                "is_international": False,
                "is_cash_withdrawal": False,
            })

    for customer_index, (customer_id, activity) in enumerate(ACTIVITY.items(), start=1):
        add_period(
            customer_id=customer_id,
            customer_index=customer_index,
            period_label="current_90d",
            start=CURRENT_START,
            end=AS_OF_DATE,
            sent_total=activity["sent"],
            received_total=activity["received"],
            sent_count=activity["sent_txns"],
            received_count=activity["recv_txns"],
            cash_total=activity["cash"],
            international_total=activity["intl"],
        )

        scale = period_scale(customer_index)

        add_period(
            customer_id=customer_id,
            customer_index=customer_index + 100,
            period_label="previous_90d",
            start=PREVIOUS_START,
            end=PREVIOUS_END,
            sent_total=round(activity["sent"] * scale, 2),
            received_total=round(activity["received"] * scale, 2),
            sent_count=max(1, int(activity["sent_txns"] * 0.60)),
            received_count=max(1, int(activity["recv_txns"] * 0.60)),
            cash_total=round(activity["cash"] * scale, 2),
            international_total=round(activity["intl"] * scale, 2),
        )

    return pd.DataFrame(rows)


def build_peer_benchmarks() -> pd.DataFrame:
    rows = []

    values = {
        "SME_active_24_to_48m": {
            "movement_to_average_balance_ratio": (2.8, 4.6, 7.2, 10.5),
            "sent_to_monthly_income_ratio": (3.1, 5.4, 8.5, 12.0),
            "beneficiaries_added": (5, 9, 15, 22),
            "total_transaction_count": (28, 44, 70, 95),
            "flagged_related_customer_count": (0, 1, 2, 4),
        },
        "Retail_active_24_to_48m": {
            "movement_to_average_balance_ratio": (1.7, 3.0, 5.8, 8.2),
            "sent_to_monthly_income_ratio": (1.6, 3.2, 6.0, 9.0),
            "beneficiaries_added": (2, 4, 8, 12),
            "total_transaction_count": (16, 28, 48, 70),
            "flagged_related_customer_count": (0, 0, 1, 2),
        },
    }

    for peer_group, metrics in values.items():
        for metric, benchmark in metrics.items():
            p50, p75, p90, p95 = benchmark
            rows.append({
                "peer_group": peer_group,
                "metric": metric,
                "p50": p50,
                "p75": p75,
                "p90": p90,
                "p95": p95,
            })

    return pd.DataFrame(rows)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    customers = build_customers()
    fraud_indicators = build_fraud_indicators()
    identity_links = build_identity_links()
    counterparty_links = build_counterparty_links()
    beneficiaries = build_beneficiaries()
    transactions = build_transactions(beneficiaries)
    peer_benchmarks = build_peer_benchmarks()

    outputs = {
        "customers.csv": customers,
        "transactions.csv": transactions,
        "beneficiaries.csv": beneficiaries,
        "fraud_indicators.csv": fraud_indicators,
        "identity_links.csv": identity_links,
        "counterparty_links.csv": counterparty_links,
        "peer_benchmarks.csv": peer_benchmarks,
    }

    for filename, df in outputs.items():
        output_path = RAW_DIR / filename
        df.to_csv(output_path, index=False)
        print(f"Wrote {output_path.relative_to(PROJECT_ROOT)} ({len(df):,} rows)")


if __name__ == "__main__":
    main()
