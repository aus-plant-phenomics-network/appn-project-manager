from pathlib import Path
from typing import Any

import pytest

from appm.exceptions import FileFormatMismatch
from appm.manager import ProjectManager
from appm.model import Metadata

FIXTURE_PATH = Path(__file__).parent / "fixtures/valid_templates"


def overwrite(base: dict[str, Any], change: dict[str, Any]) -> dict[str, Any]:
    for k, v in change.items():
        base[k] = v
    return base


@pytest.fixture
def default_components() -> dict[str, str | None]:
    return {
        "date": "20201010",
        "time": "122022",
        "site": "adelaide",
        "sensor": "oak",
        "trial": "trial-alpha",
        "procLevel": "raw",
        "rest": ".bin",
    }


def build_name(components: dict[str, str | None]) -> str:
    if components["procLevel"]:
        return f"{components['date']}-{components['time']}_{components['site']}_{components['sensor']}_{components['trial']}_{components['procLevel']}{components['rest']}"
    return f"{components['date']}-{components['time']}_{components['site']}_{components['sensor']}_{components['trial']}{components['rest']}"


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
    assert model.location == tmp_path / exp_name


@pytest.mark.parametrize(
    "change, overwrite_component, layout",
    (
        ({}, {}, "adelaide/oak/20201010/trial-alpha/T0-raw"),
        (
            {"date": "20250101", "time": "150001", "site": "waite"},
            {},
            "waite/oak/20250101/trial-alpha/T0-raw",
        ),
        ({"procLevel": "T0-raw"}, {}, "adelaide/oak/20201010/trial-alpha/T0-raw"),
        ({"procLevel": "T1-proc"}, {}, "adelaide/oak/20201010/trial-alpha/T1-proc"),
        ({"procLevel": "T2-trait"}, {}, "adelaide/oak/20201010/trial-alpha/T2-trait"),
        ({"procLevel": "raw"}, {}, "adelaide/oak/20201010/trial-alpha/T0-raw"),
        ({"procLevel": "proc"}, {}, "adelaide/oak/20201010/trial-alpha/T1-proc"),
        ({"procLevel": "trait"}, {}, "adelaide/oak/20201010/trial-alpha/T2-trait"),
        (
            {"procLevel": None},
            {"procLevel": "raw"},
            "adelaide/oak/20201010/trial-alpha/T0-raw",
        ),
        (
            {"procLevel": None, "rest": "_camera-2_setup-1"},
            {"procLevel": "raw"},
            "adelaide/oak/20201010/trial-alpha/T0-raw",
        ),
    ),
)
def test_match_file_name_and_layout_default_model(
    change: dict[str, str | None],
    overwrite_component: dict[str, str | None],
    layout: str,
    m_default: ProjectManager,
    default_components: dict[str, str | None],
) -> None:
    components = overwrite(default_components, change)
    name = build_name(components)
    assert overwrite(components, overwrite_component) == m_default.match(name)
    assert layout == m_default.get_file_placement(name)


@pytest.mark.parametrize(
    "name",
    [
        "2024-01-01_10-10-10_adelaide_oak_trial-alpha_raw.bin",
        "adelaide_lidar_2024.bin",
        "20250101_adelaide_lidar_0_raw.bin",
    ],
)
def test_match_file_name_default_model_expects_fails(
    name: str, m_default: ProjectManager
) -> None:
    with pytest.raises(FileFormatMismatch):
        m_default.match(name)


def test_init_project(m_default: ProjectManager) -> None:
    m_default.init_project()
    assert m_default.location.exists()
    assert (m_default.location / m_default.METADATA_NAME).exists()


def test_load_project(m_default: ProjectManager) -> None:
    m_default.init_project()
    m = ProjectManager.load_project(m_default.location)
    assert m_default.location == m.location
    assert m_default.metadata.model_dump() == m.metadata.model_dump()


def test_init_project_from_template_dict(
    m_default: ProjectManager, default_meta: dict[Any, Any], tmp_path: Path
) -> None:
    # From dict
    m = ProjectManager.from_template(
        root=tmp_path, template=m_default.metadata.model_dump(), **default_meta
    )
    assert m_default.location == m.location
    assert m_default.metadata.model_dump() == m.metadata.model_dump()


def test_init_project_from_template_no_template_val(
    m_default: ProjectManager, default_meta: dict[Any, Any], tmp_path: Path
) -> None:
    # From dict
    m = ProjectManager.from_template(root=tmp_path, template=None, **default_meta)
    assert m_default.location == m.location
    assert m_default.metadata.model_dump() == m.metadata.model_dump()
