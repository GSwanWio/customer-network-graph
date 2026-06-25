# Customer Network Investigation Graph

An analyst-facing network investigation tool for exploring how customers are connected through identity and counterparty relationships.

The application is designed to help an investigator move through a relationship chain, understand why each link matters, and decide which part of the network should be reviewed next. It is not a fraud prediction model and it does not make final case decisions. It surfaces relationship evidence and investigation guidance for analyst review.

## What the tool does

The graph starts from a selected customer and expands through deterministic relationship layers:

1. **Customer nodes** represent Wio customers in the investigation network.
2. **Identity connectors** represent anonymised Emirates ID links between customers.
3. **Counterparty account connectors** represent external or internal accounts that multiple Wio customers interacted with.
4. **Risk indicators** are shown as visual cues and analyst guidance, so the investigator can prioritise review without relying on raw technical fields.

The right-hand panel explains the selected node in plain language and provides suggested next checks.

## Investigator workflow

1. Select an analyst ID and seed customer.
2. Start the investigation.
3. Click a customer, identity connector, or counterparty connector.
4. Read the analyst guidance panel.
5. Expand the relationship chain where the guidance suggests it is useful.
6. Export the case activity JSON when the review is complete.

## What each click does

### Clicking a customer

A customer click focuses the investigation on that customer. The guidance panel shows:

- fraud indicators linked to the customer;
- whether the customer is directly flagged or only exposed through the network;
- the relationship path that brought the customer into view;
- transaction context behind the visible relationship, such as direction, volume, and value;
- suggested next checks for the analyst.

The backend logic uses the selected customer to identify direct identity and counterparty relationships. If the customer has no direct fraud indicators but is connected to flagged customers, the panel explains that the customer may be exposed and should be reviewed carefully. If the customer appears to have sent a large amount to a risky counterparty, the panel can frame this as a possible victim-style pattern rather than assuming participation.

### Clicking an identity connector

An identity connector click reviews the customers linked by the same anonymised Emirates ID. The guidance panel shows:

- total linked customers;
- Retail customer count;
- SME customer count;
- how many linked customers have fraud indicators;
- how many linked customers have high-severity indicators;
- suggested checks across the linked identities.

The backend logic expands the identity relationship and brings the linked customers into the graph. This helps the investigator assess whether a Retail and SME relationship, or multiple SME relationships, should be reviewed together.

### Clicking a counterparty account connector

A counterparty click reviews the account that links multiple Wio customers. The guidance panel shows:

- how many Wio customers are related through the account;
- how many related customers have fraud indicators;
- whether funds mostly move to the account, from the account, or both;
- transaction count and value where available;
- whether the account looks like a useful investigation path or supporting context only;
- suggested next checks.

The backend logic expands the counterparty relationship and adds related customers where the connection is useful for the investigation. The panel avoids technical terms and explains the account in analyst language, such as possible fund receiver, possible fund sender, shared counterparty, or context-only account.

## Visual language

The graph uses consistent colours and emojis across nodes, connectors, and the legend:

| Visual cue | Meaning |
| --- | --- |
| ☠️ Red | High-risk customer |
| ⚠️ Orange | Flagged customer |
| 😟 Amber | Network-exposed customer |
| 🚩 Orange | Suspicious account or link |
| ✅ Green | Standard expandable account or link |
| 🔗 Purple | Identity connector or link |
| 🛡️ Grey | Controlled context connector or link |
| 🧾 Amber | Evidence-only connector or link |

The visual cues are prioritisation aids. They do not replace analyst judgement.

## Case activity

The application records investigation activity locally in the browser while the session is active. The analyst can export the case activity as JSON. The export is intended to support case review and handover.

The activity log captures actions such as:

- investigation start;
- node clicks;
- relationship expansions;
- already-expanded nodes;
- reset actions.

## Data safety

This repository should only contain anonymised investigation data. Public files must not include raw customer IDs, Emirates ID numbers, account numbers, IBANs, names, phone numbers, email addresses, device IDs, or other personally identifiable information.

Use aliases such as:

- `CUSTOMER_001`
- `EID_001`
- `ACCOUNT_001`

## Project structure

```text
customer_network/
  app/
    streamlit_v2_explorer.py

data/
  investigation/
    customer_network_data.json

scripts/
  run_app.sh
```

## Run the application

From the repository root:

```bash
./scripts/run_app.sh
```

If the script is not executable yet:

```bash
chmod +x scripts/run_app.sh
./scripts/run_app.sh
```

The application runs on port `3000` in Codespaces.

## Validation checks before committing

Run these checks before pushing changes:

```bash
python -m py_compile customer_network/app/streamlit_v2_explorer.py
python -m json.tool data/investigation/customer_network_data.json > /tmp/customer_network_data_check.json
```

Check for raw identifiers before committing public data:

```bash
grep -R -E "[0-9]{8,}|AE[0-9]{2}[A-Z0-9]{11,30}|IBAN|ACCOUNT_NUMBER|CUSTOMER_ID|EIDA" \
  data/investigation/customer_network_data.json \
  customer_network/app/streamlit_v2_explorer.py \
  README.md
```

Aliases such as `CUSTOMER_001`, `ACCOUNT_001`, and `EID_001` are acceptable. Raw identifiers are not.

## Current scope

The current version is focused on relationship investigation and analyst guidance. Logic refinements should be tested with fraud operations stakeholders before being treated as operational decisioning.

Planned refinement areas include:

- clearer classification of fund receiver versus fund sender patterns;
- better transaction value and velocity summaries;
- improved victim-versus-participant guidance;
- fraud-manager review of investigation recommendations;
- additional relationship layers such as device, contact, employer, and address signals where approved.