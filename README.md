# Customer Network Graph Demo

This project demonstrates a modular customer relationship graph using simulated Excel data.

The current demo builds a combined network from two relationship layers:

1. Identity layer
   - Entity to Emirates ID relationships.
   - Example: CUST_1 -- EID1234 -- CUST_2

2. Local counterparty layer
   - Entity to local counterparty account relationships.
   - Example: CUST_2 -- ABCACCOUNT -- CUST_3

The combined graph shows how a searched customer can expand through identity links and then through shared local counterparty accounts.

## Current demo output

For the simulated seed customer CUST_1, the demo produces:

    CUST_1
      |
    EID1234
      |
    CUST_2
      |
    ABCACCOUNT
      |
    CUST_3
      |
    DEFACCOUNT
      |
    CUST_4
      |
    GHIACCOUNT
      |
    CUST_5

## Project structure

    config/
      demo_excel.yml
      graph_rules.yml

    data/
      simulated/
        simulated_customer_network.xlsx

    customer_network/
      sources/
      prepare/
      validate/
      graph/
      export/
      app/
      utils/

    scripts/
      create_simulated_excel.py
      run_demo_pipeline.py
      run_all_checks.py

## How to run the full smoke test

    python scripts/run_all_checks.py

Expected ending:

    All checks passed.
    Demo HTML output: /workspaces/customer-network-graph/outputs/demo_customer_network.html

## How to generate the HTML graph

    python scripts/run_demo_pipeline.py

This creates:

    outputs/demo_customer_network.html

To view it in Codespaces:

    python -m http.server 8000

Then open port 8000 from the Codespaces PORTS tab and navigate to:

    /outputs/demo_customer_network.html

## How to run the Streamlit app

    streamlit run customer_network/app/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

Then open port 8501 from the Codespaces PORTS tab.

## Current graph rules

    counterparty:
      group_forming_min_linked_entities: 2
      group_forming_max_linked_entities: 9
      stopped_min_linked_entities: 10
      seed_bridge_max_group_forming_counterparties: 20
      non_seed_bridge_max_group_forming_counterparties: 3

    eid:
      enable_identity_expansion: true

## Future Databricks integration

The project is designed so that the source layer can be swapped later.

Current source:

    ExcelSource

Future source:

    DatabricksSource

As long as the source produces the same prepared data contracts, the downstream preparation, validation, graph-building, and export layers should continue to work.
