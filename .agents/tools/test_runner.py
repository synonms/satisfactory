"""Run Microsoft Testing Platform projects and normalize xUnit CTRF results."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def parse_ctrf_report(
    report: dict[str, Any],
    exit_code: int,
    command: list[str],
    report_path: Path,
    baseline_test_count: int | None = None,
    test_count_decrease_justification: str | None = None,
) -> dict[str, Any]:
    results = report.get("results", {})
    tests = results.get("tests", [])
    summary = results.get("summary", {})
    failed_tests = sorted(
        (
            {
                "name": str(test.get("name", "unknown test")),
                "message": str(test.get("message", "")),
            }
            for test in tests
            if str(test.get("status", "")).lower()
            in {"failed", "error", "timedout", "cancelled"}
        ),
        key=lambda test: test["name"],
    )
    failed_names = [test["name"] for test in failed_tests]
    signature = (
        hashlib.sha256("\n".join(failed_names).encode("utf-8")).hexdigest()
        if failed_names
        else None
    )
    test_count = int(summary.get("tests", len(tests)))
    count_decreased = baseline_test_count is not None and test_count < baseline_test_count
    integrity_violation = count_decreased and not test_count_decrease_justification
    if integrity_violation and signature is None:
        signature = hashlib.sha256(
            f"test-count-decreased:{baseline_test_count}:{test_count}".encode("utf-8")
        ).hexdigest()
    outcome = (
        "tests-failing"
        if failed_tests or integrity_violation
        else "blocked"
        if test_count == 0 or exit_code
        else "tests-passing"
    )
    return {
        "outcome": outcome,
        "exitCode": exit_code,
        "testCount": test_count,
        "passed": int(summary.get("passed", 0)),
        "failed": int(summary.get("failed", len(failed_tests))),
        "skipped": int(summary.get("skipped", 0)),
        "failedTests": failed_tests,
        "failureSignature": signature,
        "integrityViolation": integrity_violation,
        "testCountDecrease": (
            {
                "baseline": baseline_test_count,
                "current": test_count,
                "justification": test_count_decrease_justification,
            }
            if count_decreased
            else None
        ),
        "command": command,
        "reportPath": str(report_path),
    }


def build_command(
    project: Path,
    configuration: str,
    report_directory: Path,
    *,
    no_build: bool = False,
    filter_methods: list[str] | None = None,
    filter_classes: list[str] | None = None,
    filter_namespaces: list[str] | None = None,
) -> list[str]:
    command = [
        "dotnet",
        "run",
        "--project",
        str(project),
        "--configuration",
        configuration,
        "--no-restore",
    ]
    if no_build:
        command.append("--no-build")

    command.extend(
        [
            "--",
            "--report-xunit-ctrf",
            "--report-xunit-ctrf-filename",
            "results.json",
            "--results-directory",
            str(report_directory),
            "--progress",
            "off",
        ]
    )
    for option, values in (
        ("--filter-method", filter_methods or []),
        ("--filter-class", filter_classes or []),
        ("--filter-namespace", filter_namespaces or []),
    ):
        for value in values:
            command.extend([option, value])
    return command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python .agents/run.py test-runner")
    parser.add_argument("--technology", choices=["dotnet"], default="dotnet")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--configuration", default="Release")
    parser.add_argument("--no-build", action="store_true")
    parser.add_argument("--filter-method", action="append", default=[])
    parser.add_argument("--filter-class", action="append", default=[])
    parser.add_argument("--filter-namespace", action="append", default=[])
    parser.add_argument("--results-directory", type=Path)
    parser.add_argument("--baseline-report", type=Path)
    parser.add_argument("--test-count-decrease-justification")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    project = arguments.project.resolve()
    if not project.is_file():
        return _write_error(f"Test project does not exist: {project}")

    report_directory = arguments.results_directory
    if report_directory is None:
        report_directory = Path(tempfile.mkdtemp(prefix="satisfactory-test-run-"))
    else:
        report_directory = report_directory.resolve()
    report_directory.mkdir(parents=True, exist_ok=True)

    command = build_command(
        project,
        arguments.configuration,
        report_directory,
        no_build=arguments.no_build,
        filter_methods=arguments.filter_method,
        filter_classes=arguments.filter_class,
        filter_namespaces=arguments.filter_namespace,
    )
    process = subprocess.run(command, cwd=REPOSITORY_ROOT, capture_output=True, text=True, check=False)
    report_path = report_directory / "results.json"
    if not report_path.is_file():
        _write_json(
            {
                "outcome": "blocked",
                "exitCode": process.returncode,
                "command": command,
                "stdout": process.stdout[-8000:],
                "stderr": process.stderr[-8000:],
                "reportPath": None,
            }
        )
        return 2

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return _write_error(f"Cannot read CTRF report: {error}")

    baseline_test_count = None
    if arguments.baseline_report:
        try:
            baseline = json.loads(arguments.baseline_report.read_text(encoding="utf-8"))
            baseline_test_count = int(baseline["results"]["summary"]["tests"])
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            return _write_error(f"Cannot read baseline CTRF test count: {error}")

    result = parse_ctrf_report(
        report,
        process.returncode,
        command,
        report_path,
        baseline_test_count,
        arguments.test_count_decrease_justification,
    )
    _write_json(result)
    if result["integrityViolation"] or result["outcome"] == "tests-failing":
        return 1
    return process.returncode


def _write_error(message: str) -> int:
    _write_json({"outcome": "blocked", "error": message})
    return 2


def _write_json(value: object) -> None:
    json.dump(value, sys.stdout, separators=(",", ":"), ensure_ascii=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())