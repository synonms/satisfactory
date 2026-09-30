"""Run the bundled ADLC tools from the repository root."""

import runpy
import sys
from pathlib import Path


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in {
        "work_items",
        "adlc",
        "repo-context",
        "test-runner",
    }:
        print(
            "Usage: python .agents/run.py {work_items|adlc|repo-context|test-runner} [arguments...]",
            file=sys.stderr,
        )
        raise SystemExit(2)

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    command = sys.argv.pop(1)
    module = {
        "repo-context": "tools.repo_context",
        "test-runner": "tools.test_runner",
    }.get(command, f"tools.{command}.__main__")
    runpy.run_module(module, run_name="__main__", alter_sys=True)