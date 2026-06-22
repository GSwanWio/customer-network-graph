from pathlib import Path
import subprocess
import sys


def run_command(command: list[str]) -> None:
	print("")
	print("=" * 80)
	print(f"Running: {' '.join(command)}")
	print("=" * 80)

	result = subprocess.run(command)

	if result.returncode != 0:
		raise SystemExit(result.returncode)


def main() -> None:
	project_root = Path(__file__).resolve().parents[1]

	checks = [
		["python", "scripts/check_setup.py"],
		["python", "scripts/create_simulated_excel.py"],
		["python", "scripts/check_excel_source.py"],
		["python", "scripts/check_prepared_data.py"],
		["python", "scripts/check_prepared_data_validation.py"],
		["python", "scripts/check_eid_graph.py"],
		["python", "scripts/check_eid_graph_validation.py"],
		["python", "scripts/check_counterparty_graph.py"],
		["python", "scripts/check_counterparty_graph_validation.py"],
		["python", "scripts/check_combined_graph.py"],
		["python", "scripts/check_combined_graph_validation.py"],
		["python", "scripts/run_demo_pipeline.py"],
	]

	for command in checks:
		run_command(command)

	print("")
	print("All checks passed.")
	print(f"Demo HTML output: {project_root / 'outputs' / 'demo_customer_network.html'}")


if __name__ == "__main__":
	main()
