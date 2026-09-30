"""Discover sourced repository facts for an implementation plan."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOTNET_RESOURCES = (
    ".agents/resources/developer-commands.md",
    ".agents/resources/dotnet-implementation-reference.md",
    ".agents/rules/dotnet-coding-rules.md",
)


def build_repository_context(
    root: Path, technology: str, scope_paths: list[str] | None = None
) -> dict[str, Any]:
    normalized_paths = sorted(set(scope_paths or []))
    if technology.lower() != "dotnet":
        raise ValueError(f"Unsupported technology: {technology}")

    sdk_path = root / "global.json"
    sdk_version = None
    if sdk_path.is_file():
        sdk_data = json.loads(sdk_path.read_text(encoding="utf-8"))
        sdk_version = sdk_data.get("sdk", {}).get("version")

    projects = [
        project
        for project in (_read_project(root, path) for path in sorted(root.rglob("*.csproj")))
        if _project_matches_scope(project["path"], normalized_paths)
    ]

    resources = [path for path in DOTNET_RESOURCES if (root / path).is_file()]
    return {
        "technology": "dotnet",
        "scopePaths": normalized_paths,
        "facts": [
            {
                "name": "sdkVersion",
                "value": sdk_version,
                "source": "global.json" if sdk_path.is_file() else None,
            },
            {
                "name": "buildAndTestCommands",
                "value": "See the canonical .NET section in developer-commands.md.",
                "source": ".agents/resources/developer-commands.md",
            },
        ],
        "projects": projects,
        "resources": resources,
    }


def _read_project(root: Path, path: Path) -> dict[str, Any]:
    relative_path = path.relative_to(root).as_posix()
    tree = ET.parse(path)
    properties = {
        _local_name(element.tag): (element.text or "").strip()
        for element in tree.iter()
        if _local_name(element.tag)
        in {"TargetFramework", "TargetFrameworks", "IsTestProject"}
    }
    package_references = sorted(
        {
            element.attrib.get("Include", element.attrib.get("Update", ""))
            for element in tree.iter()
            if _local_name(element.tag) == "PackageReference"
        }
        - {""}
    )
    test_frameworks = [
        name
        for name in ("xunit", "NUnit", "MSTest")
        if any(package.lower().startswith(name.lower()) for package in package_references)
    ]
    is_test = (
        properties.get("IsTestProject", "").lower() == "true"
        or "Microsoft.NET.Test.Sdk" in package_references
        or ".tests." in path.name.lower()
    )
    references = sorted(
        (path.parent / element.attrib["Include"]).resolve().relative_to(root).as_posix()
        for element in tree.iter()
        if _local_name(element.tag) == "ProjectReference" and "Include" in element.attrib
    )
    target_frameworks = properties.get("TargetFrameworks") or properties.get("TargetFramework")

    return {
        "path": relative_path,
        "name": path.stem,
        "kind": "test" if is_test else "application",
        "targetFrameworks": target_frameworks.split(";") if target_frameworks else [],
        "testFrameworks": test_frameworks,
        "references": references,
        "source": relative_path,
    }


def _project_matches_scope(project_path: str, scope_paths: list[str]) -> bool:
    if not scope_paths:
        return True
    project_directory = project_path.rsplit("/", maxsplit=1)[0] + "/"
    normalized_project = project_path.lower()
    normalized_directory = project_directory.lower()
    return any(
        path.lower() == normalized_project
        or path.lower().startswith(normalized_directory)
        or normalized_project.startswith(path.lower().rstrip("/") + "/")
        for path in scope_paths
    )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python .agents/run.py repo-context")
    parser.add_argument("technology", choices=["dotnet"])
    parser.add_argument("--paths", nargs="*", default=[])
    parser.add_argument("--root", type=Path, default=REPOSITORY_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        profile = build_repository_context(arguments.root.resolve(), arguments.technology, arguments.paths)
    except (OSError, ET.ParseError, json.JSONDecodeError, ValueError) as error:
        json.dump({"ok": False, "error": {"code": "repository_context_error", "message": str(error)}}, sys.stderr)
        sys.stderr.write("\n")
        return 2

    json.dump({"ok": True, "data": profile}, sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())