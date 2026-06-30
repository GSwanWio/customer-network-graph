from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from customer_network.ai.litellm_client import (
    interpret_with_litellm,
    litellm_is_configured,
    mock_interpretation,
)
from customer_network.ai.summary_builder import build_customer_ai_input, load_raw_data


DECISION_LABELS = {
    "suspicious": "Suspicious",
    "not_suspicious": "Not suspicious",
    "exposed_vulnerable": "Exposed / vulnerable",
    "needs_context": "Needs context",
}


def init_state() -> None:
    defaults = {
        "seed_customer_id": "CUST_1",
        "selected_counterparty_id": None,
        "review_queue": [],
        "active_customer_index": 0,
        "active_card_index": 0,
        "customer_ai_outputs": {},
        "selected_bites": {},
        "customer_decisions": {},
        "evidence_bucket": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def available_customers() -> list[str]:
    data = load_raw_data()
    return sorted(data["customers"]["customer_id"].unique().tolist())


def customer_name_map() -> dict[str, str]:
    data = load_raw_data()
    customers = data["customers"]
    return dict(zip(customers["customer_id"], customers["customer_name"]))


def counterparty_options_for_seed(seed_customer_id: str) -> list[str]:
    data = load_raw_data()
    links = data["counterparty_links"]

    return sorted(
        links.loc[
            links["customer_id"] == seed_customer_id,
            "counterparty_id",
        ].unique().tolist()
    )


def linked_customers_for_counterparty(seed_customer_id: str, counterparty_id: str) -> list[str]:
    data = load_raw_data()
    links = data["counterparty_links"]

    customers = sorted(
        links.loc[
            links["counterparty_id"] == counterparty_id,
            "customer_id",
        ].unique().tolist()
    )

    return [customer_id for customer_id in customers if customer_id != seed_customer_id]


def state_key(customer_id: str, card_id: str) -> str:
    return f"{customer_id}:{card_id}"


def get_selected_bites(customer_id: str, card_id: str) -> set[str]:
    key = state_key(customer_id, card_id)

    if key not in st.session_state.selected_bites:
        st.session_state.selected_bites[key] = set()

    return st.session_state.selected_bites[key]


def toggle_bite(customer_id: str, card_id: str, bite_id: str) -> None:
    selected = get_selected_bites(customer_id, card_id)

    if bite_id in selected:
        selected.remove(bite_id)
    else:
        selected.add(bite_id)


def ai_view_label(value: str) -> str:
    return {
        "no_clear_concern": "No clear concern",
        "potential_concern": "Potential concern",
        "needs_more_context": "Needs more context",
    }.get(value, value)


def get_path_for_customer(customer_id: str) -> list[str]:
    seed = st.session_state.seed_customer_id
    counterparty = st.session_state.selected_counterparty_id

    if counterparty and customer_id != seed:
        return [seed, counterparty, customer_id]

    return [customer_id]


def start_queue(seed_customer_id: str, counterparty_id: str) -> None:
    queue = linked_customers_for_counterparty(seed_customer_id, counterparty_id)

    st.session_state.seed_customer_id = seed_customer_id
    st.session_state.selected_counterparty_id = counterparty_id
    st.session_state.review_queue = queue
    st.session_state.active_customer_index = 0
    st.session_state.active_card_index = 0
    st.session_state.customer_ai_outputs = {}
    st.session_state.selected_bites = {}
    st.session_state.customer_decisions = {}
    st.session_state.evidence_bucket = []


def active_customer_id() -> str | None:
    queue = st.session_state.review_queue

    if not queue:
        return None

    index = min(st.session_state.active_customer_index, len(queue) - 1)
    return queue[index]


def build_or_get_ai_output(customer_id: str, mode: str) -> dict:
    if customer_id in st.session_state.customer_ai_outputs:
        return st.session_state.customer_ai_outputs[customer_id]

    ai_input = build_customer_ai_input(
        customer_id,
        selected_path=get_path_for_customer(customer_id),
    )

    if mode == "LiteLLM interpretation":
        output = interpret_with_litellm(ai_input)
    else:
        output = mock_interpretation(ai_input)

    st.session_state.customer_ai_outputs[customer_id] = output
    return output


def active_card(output: dict) -> dict:
    cards = output["cards"]
    index = min(st.session_state.active_card_index, len(cards) - 1)
    return cards[index]


def move_next_card_or_customer(output: dict) -> None:
    cards = output["cards"]

    if st.session_state.active_card_index < len(cards) - 1:
        st.session_state.active_card_index += 1
        return

    if st.session_state.active_customer_index < len(st.session_state.review_queue) - 1:
        st.session_state.active_customer_index += 1
        st.session_state.active_card_index = 0


def move_back() -> None:
    if st.session_state.active_card_index > 0:
        st.session_state.active_card_index -= 1
        return

    if st.session_state.active_customer_index > 0:
        st.session_state.active_customer_index -= 1
        previous_customer_id = active_customer_id()

        if previous_customer_id in st.session_state.customer_ai_outputs:
            previous_output = st.session_state.customer_ai_outputs[previous_customer_id]
            st.session_state.active_card_index = len(previous_output["cards"]) - 1
        else:
            st.session_state.active_card_index = 0


def add_evidence(customer_id: str, card: dict, decision: str, selected_bite_ids: set[str]) -> None:
    selected_bites = [
        bite
        for bite in card["bites"]
        if bite["bite_id"] in selected_bite_ids
    ]

    evidence_id = state_key(customer_id, card["card_id"])

    st.session_state.evidence_bucket = [
        item
        for item in st.session_state.evidence_bucket
        if item["evidence_id"] != evidence_id
    ]

    st.session_state.evidence_bucket.append({
        "evidence_id": evidence_id,
        "customer_id": customer_id,
        "path": get_path_for_customer(customer_id),
        "decision": decision,
        "card_id": card["card_id"],
        "question": card["question"],
        "bites": selected_bites,
        "recommended_check": card["recommended_check"],
    })


def record_decision(customer_id: str, card: dict, decision: str, selected_bite_ids: set[str]) -> bool:
    st.session_state.customer_decisions[state_key(customer_id, card["card_id"])] = decision

    if decision in {"suspicious", "exposed_vulnerable", "needs_context"}:
        if not selected_bite_ids:
            return False

        add_evidence(customer_id, card, decision, selected_bite_ids)

    return True


def reviewed_customer_status(customer_id: str) -> str:
    decisions = {
        key: value
        for key, value in st.session_state.customer_decisions.items()
        if key.startswith(f"{customer_id}:")
    }

    if not decisions:
        return "Unreviewed"

    values = set(decisions.values())

    if "suspicious" in values:
        return "Suspicious"

    if "exposed_vulnerable" in values:
        return "Exposed / vulnerable"

    if "needs_context" in values:
        return "Needs context"

    return "Not suspicious"


def render_bite(customer_id: str, card: dict, bite: dict) -> None:
    selected = get_selected_bites(customer_id, card["card_id"])
    is_selected = bite["bite_id"] in selected

    label = f"✓ {bite['text']}" if is_selected else bite["text"]

    if st.button(
        label,
        key=f"bite_{customer_id}_{card['card_id']}_{bite['bite_id']}",
        use_container_width=True,
    ):
        toggle_bite(customer_id, card["card_id"], bite["bite_id"])
        st.rerun()


def render_review_queue(name_lookup: dict[str, str]) -> None:
    st.subheader("Review queue")

    if not st.session_state.review_queue:
        st.info("No queue started yet.")
        return

    for idx, customer_id in enumerate(st.session_state.review_queue):
        active_marker = "▶ " if idx == st.session_state.active_customer_index else ""
        status = reviewed_customer_status(customer_id)
        label = f"{active_marker}{customer_id} · {name_lookup.get(customer_id, '')} · {status}"

        if st.button(label, key=f"queue_{customer_id}", use_container_width=True):
            st.session_state.active_customer_index = idx
            st.session_state.active_card_index = 0
            st.rerun()


def render_evidence_bucket(name_lookup: dict[str, str]) -> None:
    st.subheader("Evidence bucket")

    if not st.session_state.evidence_bucket:
        st.info("No evidence added yet.")
        return

    for idx, item in enumerate(st.session_state.evidence_bucket, start=1):
        with st.container(border=True):
            st.caption(
                f"Evidence {idx} · {item['customer_id']} · "
                f"{name_lookup.get(item['customer_id'], '')}"
            )
            st.write(f"**Decision:** {DECISION_LABELS[item['decision']]}")
            st.write(f"**Question:** {item['question']}")
            st.caption("Path: " + " → ".join(item["path"]))

            for bite_item in item["bites"]:
                st.write(f"- {bite_item['text']}")

            st.caption(f"Next check: {item['recommended_check']}")

    if st.button("Clear evidence", use_container_width=True):
        st.session_state.evidence_bucket = []
        st.rerun()


def render_current_card(output: dict, name_lookup: dict[str, str]) -> None:
    customer_id = output["customer_id"]
    cards = output["cards"]
    card = active_card(output)

    customer_position = st.session_state.active_customer_index + 1
    customer_total = len(st.session_state.review_queue)
    card_position = st.session_state.active_card_index + 1
    card_total = len(cards)

    st.caption(
        f"Customer {customer_position} of {customer_total} · "
        f"Card {card_position} of {card_total}"
    )

    st.progress(
        ((st.session_state.active_customer_index * card_total) + card_position)
        / max(1, customer_total * card_total)
    )

    with st.container(border=True):
        st.caption(f"{customer_id} · {name_lookup.get(customer_id, '')} · {ai_view_label(card['ai_view'])}")
        st.header(card["question"])

        st.write("")

        for bite_item in card["bites"]:
            render_bite(customer_id, card, bite_item)

        st.write("")

        selected_bites = get_selected_bites(customer_id, card["card_id"])
        button_cols = st.columns(4)

        decisions = [
            ("suspicious", "Suspicious"),
            ("not_suspicious", "Not suspicious"),
            ("exposed_vulnerable", "Exposed / vulnerable"),
            ("needs_context", "Needs context"),
        ]

        for col, (decision_key, label) in zip(button_cols, decisions):
            with col:
                clicked = st.button(
                    label,
                    key=f"decision_{customer_id}_{card['card_id']}_{decision_key}",
                    type="primary" if decision_key == "suspicious" else "secondary",
                    use_container_width=True,
                )

                if clicked:
                    saved = record_decision(
                        customer_id,
                        card,
                        decision_key,
                        selected_bites,
                    )

                    if not saved:
                        st.warning("Select at least one point first.")
                    else:
                        move_next_card_or_customer(output)
                        st.rerun()

        nav_left, nav_right = st.columns(2)

        with nav_left:
            if st.button("Back", use_container_width=True):
                move_back()
                st.rerun()

        with nav_right:
            if st.button("Skip", use_container_width=True):
                move_next_card_or_customer(output)
                st.rerun()

    with st.expander("Recommended check"):
        st.write(card["recommended_check"])


def render_completion() -> None:
    if not st.session_state.review_queue:
        return

    reviewed = [
        customer_id
        for customer_id in st.session_state.review_queue
        if reviewed_customer_status(customer_id) != "Unreviewed"
    ]

    if len(reviewed) == len(st.session_state.review_queue):
        st.success("Queue review complete. Next step will be AI prioritisation across reviewed customers.")


def main() -> None:
    st.set_page_config(page_title="AI Investigation Queue", layout="wide")
    init_state()

    st.title("AI Investigation Queue")
    st.caption("Review linked customers one at a time. Select evidence bites. Classify each customer.")

    name_lookup = customer_name_map()

    setup_col, status_col = st.columns([0.62, 0.38])

    with setup_col:
        customer_options = available_customers()

        seed_customer_id = st.selectbox(
            "Seed customer",
            customer_options,
            index=customer_options.index(st.session_state.seed_customer_id)
            if st.session_state.seed_customer_id in customer_options
            else 0,
        )

        counterparty_options = counterparty_options_for_seed(seed_customer_id)

        if not counterparty_options:
            st.warning("No linked counterparties available for this seed.")
            return

        selected_counterparty_id = st.selectbox(
            "Counterparty path",
            counterparty_options,
        )

        mode = st.radio(
            "Mode",
            ["Mock interpretation", "LiteLLM interpretation"],
            horizontal=True,
        )

        start_clicked = st.button("Start linked-customer review", type="primary")

        if start_clicked:
            if mode == "LiteLLM interpretation" and not litellm_is_configured():
                st.error("LiteLLM is not configured yet. Set LITELLM_API_BASE and LITELLM_API_KEY.")
                return

            start_queue(seed_customer_id, selected_counterparty_id)
            st.rerun()

    with status_col:
        st.info(
            "Mini workflow before graph integration: "
            "seed → counterparty → linked customers → card review → evidence."
        )

    if not st.session_state.review_queue:
        st.info("Start a linked-customer review to create the queue.")
        return

    left, middle, right = st.columns([0.25, 0.47, 0.28])

    with left:
        render_review_queue(name_lookup)

    customer_id = active_customer_id()

    if not customer_id:
        return

    with middle:
        output = build_or_get_ai_output(customer_id, mode)
        render_current_card(output, name_lookup)
        render_completion()

    with right:
        render_evidence_bucket(name_lookup)

    with st.expander("View active customer AI input"):
        st.json(
            build_customer_ai_input(
                customer_id,
                selected_path=get_path_for_customer(customer_id),
            )
        )

    with st.expander("View active customer AI card output"):
        st.json(st.session_state.customer_ai_outputs.get(customer_id, {}))


if __name__ == "__main__":
    main()
