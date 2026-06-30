from __future__ import annotations

import json
import os
from typing import Any

from customer_network.ai.contract import AI_INTERPRETATION_SCHEMA, SYSTEM_PROMPT, build_user_prompt


def litellm_is_configured() -> bool:
    return bool(os.getenv("LITELLM_API_BASE") and os.getenv("LITELLM_API_KEY"))


def fmt_aed(value: Any) -> str:
    if value is None:
        return "AED not available"

    try:
        return f"AED {float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def fmt_ratio(value: Any) -> str:
    if value is None:
        return "not available"

    try:
        return f"{float(value):.2f}x"
    except (TypeError, ValueError):
        return str(value)


def fmt_pct_change(value: Any) -> str:
    if value is None:
        return "not available"

    try:
        number = float(value)
        sign = "+" if number >= 0 else ""
        return f"{sign}{number:.1f}%"
    except (TypeError, ValueError):
        return str(value)


def bite(bite_id: str, text: str, source_fields: list[str]) -> dict[str, Any]:
    return {
        "bite_id": bite_id,
        "text": text,
        "source_fields": source_fields,
    }


def mock_interpretation(ai_input: dict[str, Any]) -> dict[str, Any]:
    profile = ai_input["profile"]
    activity = ai_input["activity"]
    normalized = ai_input["normalized_activity"]
    history = ai_input["own_history_comparison"]
    beneficiaries = ai_input["beneficiaries_and_counterparties"]
    relationships = ai_input["relationship_exposure"]

    strongest_cp = relationships.get("strongest_shared_counterparty") or {}
    strongest_cp_id = strongest_cp.get("counterparty_id") or "not available"

    cards = [
        {
            "card_id": "customer_profile",
            "question": "Does the customer profile explain the observed behaviour?",
            "ai_view": "needs_more_context",
            "bites": [
                bite(
                    "profile_1",
                    f"{profile['account_status']} {profile['segment']}",
                    ["profile.account_status", "profile.segment"],
                ),
                bite(
                    "profile_2",
                    f"{profile['occupation']} @ {profile['employer']}",
                    ["profile.occupation", "profile.employer"],
                ),
                bite(
                    "profile_3",
                    f"Account opened {profile['customer_tenure_months']} months ago",
                    ["profile.customer_tenure_months"],
                ),
                bite(
                    "profile_4",
                    f"{fmt_aed(profile['monthly_income_aed'])} declared income; {fmt_aed(profile['average_balance_aed'])} average balance",
                    ["profile.monthly_income_aed", "profile.average_balance_aed"],
                ),
            ],
            "recommended_check": "Compare customer profile against funding and transaction behaviour.",
        },
        {
            "card_id": "income_and_funding",
            "question": "Does declared income match what actually enters the account?",
            "ai_view": "potential_concern",
            "bites": [
                bite(
                    "income_1",
                    f"{fmt_aed(activity['total_received_aed'])} received in 90 days",
                    ["activity.total_received_aed"],
                ),
                bite(
                    "income_2",
                    f"Received value is {fmt_ratio(normalized['received_to_monthly_income_ratio'])} declared monthly income",
                    ["normalized_activity.received_to_monthly_income_ratio"],
                ),
                bite(
                    "income_3",
                    f"{activity['unique_senders']} unique senders",
                    ["activity.unique_senders"],
                ),
                bite(
                    "income_4",
                    f"Largest received transaction: {fmt_aed(activity['largest_received_transaction_aed'])}",
                    ["activity.largest_received_transaction_aed"],
                ),
            ],
            "recommended_check": "Check source of funds and whether inflows match expected salary or business revenue.",
        },
        {
            "card_id": "transaction_activity",
            "question": "Is the transaction activity normal for this customer?",
            "ai_view": "potential_concern",
            "bites": [
                bite(
                    "activity_1",
                    f"{fmt_aed(activity['total_movement_aed'])} total movement in 90 days",
                    ["activity.total_movement_aed"],
                ),
                bite(
                    "activity_2",
                    f"Movement is {fmt_ratio(normalized['movement_to_average_balance_ratio'])} average balance",
                    ["normalized_activity.movement_to_average_balance_ratio"],
                ),
                bite(
                    "activity_3",
                    f"Outbound value is {fmt_ratio(normalized['sent_to_monthly_income_ratio'])} monthly income",
                    ["normalized_activity.sent_to_monthly_income_ratio"],
                ),
                bite(
                    "activity_4",
                    f"Movement changed {fmt_pct_change(history['total_movement_change_pct'])} vs previous 90 days",
                    ["own_history_comparison.total_movement_change_pct"],
                ),
            ],
            "recommended_check": "Review largest transactions and compare against the previous 90-day period.",
        },
        {
            "card_id": "beneficiaries_and_relationships",
            "question": "Do beneficiaries or relationships create concern?",
            "ai_view": "potential_concern",
            "bites": [
                bite(
                    "relationship_1",
                    f"{beneficiaries['beneficiaries_added']} beneficiaries added; {beneficiaries['active_beneficiaries_90d']} active in 90 days",
                    [
                        "beneficiaries_and_counterparties.beneficiaries_added",
                        "beneficiaries_and_counterparties.active_beneficiaries_90d",
                    ],
                ),
                bite(
                    "relationship_2",
                    f"{beneficiaries['new_beneficiaries_30d']} new beneficiaries in last 30 days",
                    ["beneficiaries_and_counterparties.new_beneficiaries_30d"],
                ),
                bite(
                    "relationship_3",
                    f"{relationships['linked_counterparty_count']} linked counterparties",
                    ["relationship_exposure.linked_counterparty_count"],
                ),
                bite(
                    "relationship_4",
                    f"{relationships['flagged_related_customer_count']} flagged related customers",
                    ["relationship_exposure.flagged_related_customer_count"],
                ),
                bite(
                    "relationship_5",
                    f"Strongest shared path: {strongest_cp_id}",
                    ["relationship_exposure.strongest_shared_counterparty.counterparty_id"],
                ),
            ],
            "recommended_check": f"Open shared counterparty {strongest_cp_id} and compare linked customers.",
        },
    ]

    return {
        "customer_id": profile["customer_id"],
        "cards": cards,
        "overall_confidence": "medium",
    }


def interpret_with_litellm(ai_input: dict[str, Any]) -> dict[str, Any]:
    if not litellm_is_configured():
        raise RuntimeError("LiteLLM is not configured. Set LITELLM_API_BASE and LITELLM_API_KEY.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("The openai package is required for the LiteLLM client.") from exc

    client = OpenAI(
        api_key=os.environ["LITELLM_API_KEY"],
        base_url=os.environ["LITELLM_API_BASE"],
    )

    model = os.getenv("LITELLM_MODEL", "gpt-5.1")

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(ai_input)},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "single_card_investigation_flow",
                "strict": True,
                "schema": AI_INTERPRETATION_SCHEMA,
            },
        },
    )

    content = response.choices[0].message.content
    return json.loads(content)
