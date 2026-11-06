"""CLI: python -m agent_v3.cli --task '...' --tool checklist --approve"""

import argparse
import json
from dataclasses import asdict
from .core import execute


def main():
    parser = argparse.ArgumentParser(description="Autonomous Agent v3 controlled MVP")
    parser.add_argument("--task", required=True)
    parser.add_argument(
        "--tool", choices=["summarize", "classify", "checklist"], default="checklist"
    )
    parser.add_argument(
        "--approve", action="store_true", help="Explicitly approve local execution"
    )
    args = parser.parse_args()
    print(
        json.dumps(
            asdict(execute(args.task, args.tool, args.approve)),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
