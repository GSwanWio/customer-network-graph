#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

python -m pip install -r requirements.txt

python -m streamlit run customer_network/app/streamlit_v2_explorer.py \
  --server.port 8502 \
  --server.address 0.0.0.0
