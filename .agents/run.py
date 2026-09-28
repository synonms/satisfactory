"""Run the bundled ADLC tools from the repository root."""

import runpy
import sys
from pathlib import Path


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in {"work_items", "adlc"}:
        print("Usage: python .agents/run.py {work_items|adlc} [arguments...]", file=sys.stderr)
        raise SystemExit(2)

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    runpy.run_module(f"tools.{sys.argv.pop(1)}.__main__", run_name="__main__", alter_sys=True)