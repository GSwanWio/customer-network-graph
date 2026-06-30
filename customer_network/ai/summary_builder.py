from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "ai_test" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "ai_test" / "processed" / "customer_ai_inputs"


def load_raw_data(raw_dir: Path = RAW_DIR) -> dict[str, pd.DataFrame]:
    return {
        "customers": pd.read_csv(raw_dir / "customers.csv"),
        "transactions": pd.read_csv(raw_dir / "transactions.csv"),
        "beneficiaries": pd.read_csv(raw_dir / "beneficiaries.csv"),
        "fraud_indicators": pd.read_csv(raw_dir / "fraud_indicators.csv"),
        "identity_links": pd.read_csv(raw_dir / "identity_links.csv"),
        "counterparty_links": pd.read_csv(raw_dir / "counterparty_links.csv"),
        "peer_benchmarks": pd.read_csv(raw_dir / "peer_benchmarks.csv"),
    }


def as_float(value: Any) -> float:
    if pd.isna(value):
        return 0.0
    return float(value)


def as_int(value: Any) -> int:
    if pd.isna(value):
        return 0
    return int(value)


def safe_divide(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def round_or_none(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def pct_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 2)


def days_ago(as_of_date: datetime, value: Any) -> int | None:
    if pd.isna(value):
        return None
    return (as_of_date - pd.to_datetime(value)).days


def benchmark_for(peer_benchmarks: pd.DataFrame, peer_group: str, metric: str) -> pd.Series | None:
    rows = peer_benchmarks[
        (peer_benchmarks["peer_group"] == peer_group)
        & (peer_benchmarks["metric"] == metric)
    ]

    if rows.empty:
        return None

    return rows.iloc[0]


def percentile_bucket(value: float | int | None, benchmark_row: pd.Series | None) -> dict[str, Any]:
    if value is None or benchmark_row is None:
        return {
            "value": value,
            "approx_percentile_bucket": None,
            "peer_p50": None,
            "peer_p75": None,
            "peer_p90": None,
            "peer_p95": None,
        }

    p50 = as_float(benchmark_row["p50"])
    p75 = as_float(benchmark_row["p75"])
    p90 = as_float(benchmark_row["p90"])
    p95 = as_float(benchmark_row["p95"])

    if value >= p95:
        bucket = ">=p95"
    elif value >= p90:
        bucket = "p90_to_p95"
    elif value >= p75:
        bucket = "p75_to_p90"
    elif value >= p50:
        bucket = "p50_to_p75"
    else:
        bucket = "<p50"

    return {
        "value": value,
        "approx_percentile_bucket": bucket,
        "peer_p50": p50,
        "peer_p75": p75,
        "peer_p90": p90,
        "peer_p95": p95,
    }


def movement_metrics(txns: pd.DataFrame) -> dict[str, Any]:
    sent = txns[txns["direction"] == "sent"]
    received = txns[txns["direction"] == "received"]

    total_sent = as_float(sent["amount_aed"].sum())
    total_received = as_float(received["amount_aed"].sum())
    total_movement = total_sent + total_received
    total_count = len(txns)

    sent_transfer = sent[sent["transaction_type"] == "transfer"]
    received_transfer = received[received["transaction_type"] == "transfer"]

    return {
        "total_sent_aed": round(total_sent, 2),
        "total_received_aed": round(total_received, 2),
        "total_movement_aed": round(total_movement, 2),
        "net_flow_aed": round(total_received - total_sent, 2),
        "sent_transaction_count": len(sent),
        "received_transaction_count": len(received),
        "total_transaction_count": total_count,
        "average_transaction_size_aed": round_or_none(safe_divide(total_movement, total_count), 2),
        "largest_sent_transaction_aed": round(as_float(sent["amount_aed"].max()), 2) if not sent.empty else 0.0,
        "largest_received_transaction_aed": round(as_float(received["amount_aed"].max()), 2) if not received.empty else 0.0,
        "unique_receivers": sent_transfer["counterparty_id"].nunique(),
        "unique_senders": received_transfer["counterparty_id"].nunique(),
    }


def concentration_metrics(current_txns: pd.DataFrame) -> dict[str, Any]:
    sent_transfers = current_txns[
        (current_txns["direction"] == "sent")
        & (current_txns["transaction_type"] == "transfer")
    ]

    total_sent_transfer_value = as_float(sent_transfers["amount_aed"].sum())

    if sent_transfers.empty or total_sent_transfer_value == 0:
        return {
            "largest_counterparty_share_of_sent_value": None,
            "top_3_counterparty_share_of_sent_value": None,
        }

    by_counterparty = (
        sent_transfers
        .groupby("counterparty_id", as_index=False)["amount_aed"]
        .sum()
        .sort_values("amount_aed", ascending=False)
    )

    largest_share = by_counterparty.iloc[0]["amount_aed"] / total_sent_transfer_value
    top_3_share = by_counterparty.head(3)["amount_aed"].sum() / total_sent_transfer_value

    return {
        "largest_counterparty_share_of_sent_value": round(float(largest_share), 4),
        "top_3_counterparty_share_of_sent_value": round(float(top_3_share), 4),
    }


def build_risk_indicators(
    fraud_indicators: pd.DataFrame,
    customer_id: str,
    as_of_date: datetime,
) -> dict[str, Any]:
    rows = fraud_indicators[fraud_indicators["customer_id"] == customer_id].copy()

    if rows.empty:
        return {
            "total_count": 0,
            "high_severity_count": 0,
            "medium_severity_count": 0,
            "low_severity_count": 0,
            "categories": [],
        }

    categories = []

    for _, row in rows.iterrows():
        categories.append({
            "indicator_type": row["indicator_type"],
            "severity": row["severity"],
            "trigger_count": as_int(row["trigger_count"]),
            "first_seen_days_ago": days_ago(as_of_date, row["first_seen_date"]),
            "last_seen_days_ago": days_ago(as_of_date, row["last_seen_date"]),
            "supporting_metric": row["supporting_metric"],
            "supporting_value": row["supporting_value"],
        })

    severity_counts = rows["severity"].value_counts().to_dict()

    return {
        "total_count": len(rows),
        "high_severity_count": as_int(severity_counts.get("high", 0)),
        "medium_severity_count": as_int(severity_counts.get("medium", 0)),
        "low_severity_count": as_int(severity_counts.get("low", 0)),
        "categories": categories,
    }


def build_relationship_exposure(data: dict[str, pd.DataFrame], customer_id: str) -> dict[str, Any]:
    fraud_indicators = data["fraud_indicators"]
    identity_links = data["identity_links"]
    counterparty_links = data["counterparty_links"]

    customers_with_indicators = set(fraud_indicators["customer_id"].unique())
    customers_with_high_indicators = set(
        fraud_indicators[fraud_indicators["severity"] == "high"]["customer_id"].unique()
    )

    customer_counterparties = counterparty_links[
        counterparty_links["customer_id"] == customer_id
    ]["counterparty_id"].unique().tolist()

    counterparty_related = set(
        counterparty_links[
            (counterparty_links["counterparty_id"].isin(customer_counterparties))
            & (counterparty_links["customer_id"] != customer_id)
        ]["customer_id"].unique()
    )

    customer_eids = identity_links[
        identity_links["customer_id"] == customer_id
    ]["eid_id"].unique().tolist()

    identity_related = set(
        identity_links[
            (identity_links["eid_id"].isin(customer_eids))
            & (identity_links["customer_id"] != customer_id)
        ]["customer_id"].unique()
    )

    related_customers = sorted(counterparty_related.union(identity_related))
    flagged_related = sorted([c for c in related_customers if c in customers_with_indicators])
    high_priority_related = sorted([c for c in related_customers if c in customers_with_high_indicators])

    strongest = None

    for counterparty_id in customer_counterparties:
        cp_rows = counterparty_links[counterparty_links["counterparty_id"] == counterparty_id].copy()
        linked_customers = sorted(cp_rows["customer_id"].unique().tolist())
        linked_excluding_customer = [c for c in linked_customers if c != customer_id]
        flagged_linked = [c for c in linked_excluding_customer if c in customers_with_indicators]

        seed_rows = cp_rows[cp_rows["customer_id"] == customer_id]
        seed_value = as_float(seed_rows["linked_value_aed"].sum())
        total_value = as_float(cp_rows["linked_value_aed"].sum())

        candidate = {
            "counterparty_id": counterparty_id,
            "linked_customer_count": len(linked_customers),
            "flagged_linked_customer_count": len(flagged_linked),
            "linked_customers": linked_customers,
            "flagged_linked_customers": sorted(flagged_linked),
            "total_shared_value_aed": round(total_value, 2),
            "seed_customer_value_aed": round(seed_value, 2),
        }

        if strongest is None:
            strongest = candidate
            continue

        current_score = (
            candidate["flagged_linked_customer_count"],
            candidate["total_shared_value_aed"],
        )
        strongest_score = (
            strongest["flagged_linked_customer_count"],
            strongest["total_shared_value_aed"],
        )

        if current_score > strongest_score:
            strongest = candidate

    return {
        "linked_counterparty_count": len(customer_counterparties),
        "linked_identity_count": len(customer_eids),
        "related_customer_count": len(related_customers),
        "flagged_related_customer_count": len(flagged_related),
        "high_priority_related_customer_count": len(high_priority_related),
        "related_customers": related_customers,
        "flagged_related_customers": flagged_related,
        "high_priority_related_customers": high_priority_related,
        "strongest_shared_counterparty": strongest,
    }


def build_customer_ai_input(
    customer_id: str,
    selected_path: list[str] | None = None,
    raw_dir: Path = RAW_DIR,
) -> dict[str, Any]:
    data = load_raw_data(raw_dir)

    customers = data["customers"]
    transactions = data["transactions"]
    beneficiaries = data["beneficiaries"]
    peer_benchmarks = data["peer_benchmarks"]

    customer_rows = customers[customers["customer_id"] == customer_id]

    if customer_rows.empty:
        raise ValueError(f"Unknown customer_id: {customer_id}")

    customer = customer_rows.iloc[0].to_dict()

    transactions["transaction_date"] = pd.to_datetime(transactions["transaction_date"])
    beneficiaries["beneficiary_created_date"] = pd.to_datetime(beneficiaries["beneficiary_created_date"])

    as_of_date = transactions["transaction_date"].max().to_pydatetime()

    current_txns = transactions[
        (transactions["customer_id"] == customer_id)
        & (transactions["period_label"] == "current_90d")
    ].copy()

    previous_txns = transactions[
        (transactions["customer_id"] == customer_id)
        & (transactions["period_label"] == "previous_90d")
    ].copy()

    current_metrics = movement_metrics(current_txns)
    previous_metrics = movement_metrics(previous_txns)

    total_movement = current_metrics["total_movement_aed"]
    total_sent = current_metrics["total_sent_aed"]
    total_received = current_metrics["total_received_aed"]
    average_balance = as_float(customer["average_balance_aed"])
    monthly_income = as_float(customer["monthly_income_aed"])

    movement_to_balance = round_or_none(safe_divide(total_movement, average_balance), 2)
    sent_to_income = round_or_none(safe_divide(total_sent, monthly_income), 2)
    received_to_income = round_or_none(safe_divide(total_received, monthly_income), 2)

    cash_withdrawal = as_float(
        current_txns[current_txns["is_cash_withdrawal"] == True]["amount_aed"].sum()
    )

    international_transfer = as_float(
        current_txns[
            (current_txns["direction"] == "sent")
            & (current_txns["is_international"] == True)
        ]["amount_aed"].sum()
    )

    customer_beneficiaries = beneficiaries[beneficiaries["customer_id"] == customer_id]
    active_beneficiaries = customer_beneficiaries[customer_beneficiaries["active_90d"] == True]

    new_beneficiaries_30d = customer_beneficiaries[
        customer_beneficiaries["beneficiary_created_date"]
        >= (as_of_date - pd.Timedelta(days=30))
    ]

    sent_transfers = current_txns[
        (current_txns["direction"] == "sent")
        & (current_txns["transaction_type"] == "transfer")
    ]

    top_country = None

    if not sent_transfers.empty:
        top_country = (
            sent_transfers
            .groupby("payment_country")["amount_aed"]
            .sum()
            .sort_values(ascending=False)
            .index[0]
        )

    concentration = concentration_metrics(current_txns)
    relationship_exposure = build_relationship_exposure(data, customer_id)

    peer_group = customer["peer_group"]

    peer_comparison = {
        "peer_group": peer_group,
        "movement_to_average_balance_ratio": percentile_bucket(
            movement_to_balance,
            benchmark_for(peer_benchmarks, peer_group, "movement_to_average_balance_ratio"),
        ),
        "sent_to_monthly_income_ratio": percentile_bucket(
            sent_to_income,
            benchmark_for(peer_benchmarks, peer_group, "sent_to_monthly_income_ratio"),
        ),
        "beneficiaries_added": percentile_bucket(
            len(customer_beneficiaries),
            benchmark_for(peer_benchmarks, peer_group, "beneficiaries_added"),
        ),
        "total_transaction_count": percentile_bucket(
            current_metrics["total_transaction_count"],
            benchmark_for(peer_benchmarks, peer_group, "total_transaction_count"),
        ),
        "flagged_related_customer_count": percentile_bucket(
            relationship_exposure["flagged_related_customer_count"],
            benchmark_for(peer_benchmarks, peer_group, "flagged_related_customer_count"),
        ),
    }

    selected_path = selected_path or [customer_id]

    if len(selected_path) == 1 and selected_path[0] == customer_id:
        relationship_to_seed = "seed_customer"
        distance_from_seed = 0
    else:
        relationship_to_seed = "path_member"
        distance_from_seed = max(0, len(selected_path) - 1)

    current_path = {
        "active_path": selected_path,
        "selected_node_id": selected_path[-1],
        "selected_node_type": "customer" if selected_path[-1].startswith("CUST_") else "connector",
        "relationship_to_seed": relationship_to_seed,
        "distance_from_seed": distance_from_seed,
        "path_contains_flagged_customer": any(
            node_id in set(data["fraud_indicators"]["customer_id"].unique())
            for node_id in selected_path
        ),
    }

    return {
        "selected_node": {
            "node_type": "customer",
            "node_id": customer_id,
            "is_seed_customer": relationship_to_seed == "seed_customer",
            "distance_from_seed": distance_from_seed,
            "current_path": selected_path,
        },
        "profile": {
            "customer_id": customer_id,
            "customer_name": customer["customer_name"],
            "segment": customer["segment"],
            "account_status": customer["account_status"],
            "age": as_int(customer["age"]),
            "nationality": customer["nationality"],
            "occupation": customer["occupation"],
            "employer": customer["employer"],
            "customer_since": customer["customer_since"],
            "customer_tenure_months": as_int(customer["customer_tenure_months"]),
            "monthly_income_aed": as_float(customer["monthly_income_aed"]),
            "average_balance_aed": as_float(customer["average_balance_aed"]),
            "peer_group": peer_group,
        },
        "risk_indicators": build_risk_indicators(
            data["fraud_indicators"],
            customer_id,
            as_of_date,
        ),
        "activity": {
            "period_days": 90,
            **current_metrics,
        },
        "normalized_activity": {
            "movement_to_average_balance_ratio": movement_to_balance,
            "sent_to_monthly_income_ratio": sent_to_income,
            "received_to_monthly_income_ratio": received_to_income,
            "cash_withdrawal_to_total_movement_ratio": round_or_none(
                safe_divide(cash_withdrawal, total_movement),
                4,
            ),
            "international_transfer_to_total_movement_ratio": round_or_none(
                safe_divide(international_transfer, total_movement),
                4,
            ),
        },
        "peer_comparison": peer_comparison,
        "own_history_comparison": {
            "current_period_days": 90,
            "previous_period_days": 90,
            "total_movement_change_pct": pct_change(
                current_metrics["total_movement_aed"],
                previous_metrics["total_movement_aed"],
            ),
            "sent_value_change_pct": pct_change(
                current_metrics["total_sent_aed"],
                previous_metrics["total_sent_aed"],
            ),
            "received_value_change_pct": pct_change(
                current_metrics["total_received_aed"],
                previous_metrics["total_received_aed"],
            ),
            "transaction_count_change": (
                current_metrics["total_transaction_count"]
                - previous_metrics["total_transaction_count"]
            ),
            "average_transaction_size_change_pct": pct_change(
                current_metrics["average_transaction_size_aed"] or 0,
                previous_metrics["average_transaction_size_aed"] or 0,
            ),
            "unique_receivers_change": (
                current_metrics["unique_receivers"]
                - previous_metrics["unique_receivers"]
            ),
            "unique_senders_change": (
                current_metrics["unique_senders"]
                - previous_metrics["unique_senders"]
            ),
        },
        "beneficiaries_and_counterparties": {
            "beneficiaries_added": len(customer_beneficiaries),
            "active_beneficiaries_90d": len(active_beneficiaries),
            "new_beneficiaries_30d": len(new_beneficiaries_30d),
            "unique_receivers_90d": current_metrics["unique_receivers"],
            "unique_senders_90d": current_metrics["unique_senders"],
            "top_payment_country": top_country,
            "largest_counterparty_share_of_sent_value": concentration[
                "largest_counterparty_share_of_sent_value"
            ],
            "top_3_counterparty_share_of_sent_value": concentration[
                "top_3_counterparty_share_of_sent_value"
            ],
        },
        "relationship_exposure": relationship_exposure,
        "current_investigation_path": current_path,
        "data_quality": {
            "has_customer_profile": True,
            "has_income_data": monthly_income > 0,
            "has_average_balance": average_balance > 0,
            "has_transaction_history": not current_txns.empty,
            "has_beneficiary_data": not customer_beneficiaries.empty,
            "has_relationship_data": (
                relationship_exposure["linked_counterparty_count"] > 0
                or relationship_exposure["linked_identity_count"] > 0
            ),
            "known_limitations": [
                "payment purpose is not available in the simulated data",
                "source of funds is not available in the simulated data",
                "external counterparty ownership is not verified in the simulated data",
                "peer benchmarks are simulated and should be replaced with production benchmarks later",
            ],
        },
    }


def write_customer_ai_input(customer_id: str, output_dir: Path = PROCESSED_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    ai_input = build_customer_ai_input(customer_id)
    output_path = output_dir / f"{customer_id}.json"

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(ai_input, f, indent=2)

    return output_path
