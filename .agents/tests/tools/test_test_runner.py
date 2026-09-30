from pathlib import Path

from tools.test_runner import build_command, parse_ctrf_report


def test_ctrf_report_normalizes_failures_and_stable_signature(tmp_path: Path) -> None:
    report = {
        "results": {
            "tests": [
                {"name": "Z.Tests.Fails", "status": "failed", "message": "z failure"},
                {"name": "A.Tests.Fails", "status": "failed", "message": "a failure"},
                {"name": "A.Tests.Passes", "status": "passed"},
            ],
            "summary": {"tests": 3, "passed": 1, "failed": 2, "skipped": 0},
        }
    }

    result = parse_ctrf_report(report, 1, ["dotnet", "test"], tmp_path / "results.json")
    reordered = parse_ctrf_report(
        {"results": {"tests": list(reversed(report["results"]["tests"])), "summary": report["results"]["summary"]}},
        1,
        ["dotnet", "test"],
        tmp_path / "results.json",
    )

    assert result["outcome"] == "tests-failing"
    assert [test["name"] for test in result["failedTests"]] == [
        "A.Tests.Fails",
        "Z.Tests.Fails",
    ]
    assert result["failureSignature"] == reordered["failureSignature"]


def test_build_command_uses_mtp_and_requested_filters(tmp_path: Path) -> None:
    command = build_command(
        Path("tests/Example.Tests.csproj"),
        "Release",
        tmp_path,
        no_build=True,
        filter_methods=["Example.Tests.Sample.Passes"],
    )

    assert command[:3] == ["dotnet", "run", "--project"]
    assert Path(command[3]) == Path("tests/Example.Tests.csproj")
    assert command[4:6] == [
        "--configuration",
        "Release",
    ]
    assert "--no-restore" in command
    assert "--no-build" in command
    assert "--report-xunit-ctrf" in command
    assert command[-2:] == ["--filter-method", "Example.Tests.Sample.Passes"]


def test_ctrf_report_with_zero_selected_tests_is_blocked(tmp_path: Path) -> None:
    result = parse_ctrf_report(
        {"results": {"tests": [], "summary": {"tests": 0, "passed": 0, "failed": 0}}},
        8,
        ["dotnet", "run"],
        tmp_path / "results.json",
    )

    assert result["outcome"] == "blocked"
    assert result["failureSignature"] is None


def test_ctrf_failed_test_is_failing_even_when_process_exit_code_is_zero(tmp_path: Path) -> None:
    result = parse_ctrf_report(
        {
            "results": {
                "tests": [{"name": "Example.Tests.Fails", "status": "failed", "message": "failure"}],
                "summary": {"tests": 1, "passed": 0, "failed": 1},
            }
        },
        0,
        ["dotnet", "run"],
        tmp_path / "results.json",
    )

    assert result["outcome"] == "tests-failing"
    assert result["failureSignature"]


def test_ctrf_test_count_decrease_requires_justification(tmp_path: Path) -> None:
    current = {"results": {"tests": [], "summary": {"tests": 1, "passed": 1, "failed": 0}}}

    rejected = parse_ctrf_report(current, 0, ["dotnet", "run"], tmp_path / "current.json", 2)
    justified = parse_ctrf_report(
        current,
        0,
        ["dotnet", "run"],
        tmp_path / "current.json",
        2,
        "Removed a duplicate obsolete test as approved in the plan.",
    )

    assert rejected["outcome"] == "tests-failing"
    assert rejected["integrityViolation"] is True
    assert rejected["failureSignature"]
    assert justified["outcome"] == "tests-passing"
    assert justified["integrityViolation"] is False