import json
from pathlib import Path

from tools.repo_context import build_repository_context


def test_context_reports_sourced_sdk_project_and_test_framework_facts(tmp_path: Path) -> None:
    project_directory = tmp_path / "src" / "Api"
    project_directory.mkdir(parents=True)
    (tmp_path / "global.json").write_text(
        json.dumps({"sdk": {"version": "10.0.100"}}), encoding="utf-8"
    )
    project_path = project_directory / "Api.Tests.csproj"
    project_path.write_text(
        """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><TargetFramework>net10.0</TargetFramework><IsTestProject>true</IsTestProject></PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="18.0.0" />
    <PackageReference Include="xunit.v3" Version="3.0.0" />
  </ItemGroup>
</Project>""",
        encoding="utf-8",
    )

    profile = build_repository_context(tmp_path, "dotnet", ["src/Api"])

    assert profile["facts"][0] == {
        "name": "sdkVersion",
        "value": "10.0.100",
        "source": "global.json",
    }
    assert profile["projects"] == [
        {
            "path": "src/Api/Api.Tests.csproj",
            "name": "Api.Tests",
            "kind": "test",
            "targetFrameworks": ["net10.0"],
            "testFrameworks": ["xunit"],
            "references": [],
            "source": "src/Api/Api.Tests.csproj",
        }
    ]