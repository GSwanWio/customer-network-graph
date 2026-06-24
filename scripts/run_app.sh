#!/bin/bash
cd /workspaces/customer-network-graph

python -m streamlit run customer_network/app/streamlit_v2_explorer.py \
  --server.port 3000 \
  --server.address 0.0.0.0 \
  --server.headless true
