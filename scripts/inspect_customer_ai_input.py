from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from customer_network.ai.summary_builder import build_customer_ai_input, write_customer_ai_input


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("customer_id", nargs="?", default="CUST_1")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    ai_input = build_customer_ai_input(args.customer_id)

    print(json.dumps(ai_input, indent=2))

    if args.write:
        output_path = write_customer_ai_input(args.customer_id)
        print(f"\nWrote {output_path}")


if __name__ == "__main__":
    main()
