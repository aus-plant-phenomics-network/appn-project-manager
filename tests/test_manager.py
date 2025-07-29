from pathlib import Path
from typing import Any

import pytest

from appm.manager import ProjectManager
from appm.model import Metadata

FIXTURE_PATH = Path(__file__).parent / "fixtures/valid_templates"


def overwrite(base: dict[str, Any], change: dict[str, Any]) -> dict[str, Any]:
    for k, v in change.items():
        base[k] = v
    return base


@pytest.fixture
def default_meta() -> dict[Any, Any]:
    return Metadata(
        year=2024,
        summary="test project",
        internal=True,
        researcherName="Hoang Son Le",
        organisationName="APPN",
    ).model_dump()


@pytest.fixture
def m_default(tmp_path: Path, default_meta: dict[Any, Any]) -> ProjectManager:
    return ProjectManager.from_template(
        tmp_path,
        template=FIXTURE_PATH / "default.yaml",
        **default_meta,
    )


@pytest.mark.parametrize(
    "template, meta, exp_name",
    [
        ("default.yaml", {}, "2024_test-project_internal_hoang-son-le_appn"),
        (
            "default.yaml",
            {"year": 2025},
            "2025_test-project_internal_hoang-son-le_appn",
        ),
        (
            "default.yaml",
            {"internal": False},
            "2024_test-project_external_hoang-son-le_appn",
        ),
        (
            "default.yaml",
            {"researcherName": "john doe"},
            "2024_test-project_internal_john-doe_appn",
        ),
        ("default.yaml", {"researcherName": None}, "2024_test-project_internal_appn"),
        (
            "default.yaml",
            {"organisationName": "UOA"},
            "2024_test-project_internal_hoang-son-le_uoa",
        ),
        (
            "default.yaml",
            {"organisationName": None},
            "2024_test-project_internal_hoang-son-le",
        ),
        (
            "default.yaml",
            {
                "year": 2020,
                "summary": "demo project",
                "internal": False,
                "researcherName": None,
                "organisationName": None,
            },
            "2020_demo-project_external",
        ),
        ("naming_perm_year_researcher_org.yaml", {}, "2024_hoang-son-le_appn"),
        (
            "naming_perm_year_researcher_org.yaml",
            {"year": 2025, "researcherName": "john doe", "organisationName": "UOA"},
            "2025_john-doe_uoa",
        ),
        ("naming_perm_year_summary_internal.yaml", {}, "2024_test-project_internal"),
    ],
)
def test_get_project_name(
    template: str,
    meta: dict[str, Any],
    exp_name: str,
    tmp_path: Path,
    default_meta: dict[str, Any],
) -> None:
    metadata = overwrite(default_meta, meta)
    model = ProjectManager.from_template(
        root=tmp_path, template=FIXTURE_PATH / template, **metadata
    )
    assert exp_name == model.metadata.project_name
