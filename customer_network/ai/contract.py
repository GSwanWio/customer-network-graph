from __future__ import annotations

import json
from typing import Any


AI_INTERPRETATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["customer_id", "cards", "overall_confidence"],
    "properties": {
        "customer_id": {"type": "string"},
        "cards": {
            "type": "array",
            "minItems": 4,
            "maxItems": 4,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "card_id",
                    "question",
                    "ai_view",
                    "bites",
                    "recommended_check",
                ],
                "properties": {
                    "card_id": {
                        "type": "string",
                        "enum": [
                            "customer_profile",
                            "income_and_funding",
                            "transaction_activity",
                            "beneficiaries_and_relationships",
                        ],
                    },
                    "question": {"type": "string"},
                    "ai_view": {
                        "type": "string",
                        "enum": [
                            "no_clear_concern",
                            "potential_concern",
                            "needs_more_context",
                        ],
                    },
                    "bites": {
                        "type": "array",
                        "minItems": 3,
                        "maxItems": 5,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["bite_id", "text", "source_fields"],
                            "properties": {
                                "bite_id": {"type": "string"},
                                "text": {"type": "string"},
                                "source_fields": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                        },
                    },
                    "recommended_check": {"type": "string"},
                },
            },
        },
        "overall_confidence": {
            "type": "string",
            "enum": ["low", "medium", "high"],
        },
    },
}


SYSTEM_PROMPT = """
You assist fraud analysts by turning neutral customer facts into a short guided investigation flow.

Rules:
- Do not make the final suspicious/not suspicious decision.
- Do not assume fraud.
- Do not say the customer is fraudulent.
- Use only the provided facts.
- Create exactly four cards.
- Each card should ask one natural analyst question.
- Each card should contain 3 to 5 short factual bites.
- Each bite should be brief enough to fit on a small card.
- Avoid long explanations.
- Avoid generic commentary.
- The analyst will select the bites they agree are relevant.
- Return only JSON matching the required schema.
""".strip()


def build_user_prompt(ai_input: dict[str, Any]) -> str:
    return (
        "Create a concise single-card investigation flow from this neutral customer input. "
        "Use short factual bites only.\n\n"
        f"{json.dumps(ai_input, indent=2, sort_keys=True)}"
    )
