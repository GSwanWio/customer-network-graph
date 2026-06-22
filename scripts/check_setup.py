from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from customer_network.utils.config import load_yaml


def main() -> None:
	graph_rules_path = project_root / "config" / "graph_rules.yml"
	demo_excel_config_path = project_root / "config" / "demo_excel.yml"

	graph_rules = load_yaml(graph_rules_path)
	demo_excel_config = load_yaml(demo_excel_config_path)

	required_dirs = [
		"config",
		"data/simulated",
		"customer_network/sources",
		"customer_network/prepare",
		"customer_network/validate",
		"customer_network/graph",
		"customer_network/export",
		"customer_network/app",
		"customer_network/utils",
		"scripts",
		"tests",
	]

	missing_dirs = [
		directory
		for directory in required_dirs
		if not (project_root / directory).exists()
	]

	if missing_dirs:
		raise RuntimeError(f"Missing directories: {missing_dirs}")

	print("Project setup check passed.")
	print(f"Graph rules loaded: {graph_rules}")
	print(f"Demo Excel config loaded: {demo_excel_config}")


if __name__ == "__main__":
	main()