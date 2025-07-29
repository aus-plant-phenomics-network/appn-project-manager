from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

import pytest

from appm.exceptions import FileFormatMismatch, UnsupportedFileExtension
from appm.manager import ProjectManager
from appm.model import Metadata

FIXTURE_PATH = Path(__file__).parent / "fixtures/valid_templates"
MakeProjectT = Callable[[str | None | Path | dict[str, Any]], ProjectManager]
MakeFileNameT = Callable[[dict[str, Any]], str]
MakeComponentT = Callable[[dict[str, Any]], dict[str, Any]]
MakeLayoutT = MakeFileNameT


@pytest.fixture
def default_components() -> dict[str, str | None]:
    return {
        "date": "20201010",
        "time": "101010",
        "site": "adelaide",
        "sensor": "lidar",
        "trial": "alpha",
        "procLevel": "raw",
        "rest": ".bin",
    }


@pytest.fixture
def make_filename(default_components: dict[str, str | None]):
    def _make_filename(change: dict[str, str | None]) -> str:
        components = overwrite(default_components, change)
        base = f"{components['date']}-{components['time']}_{components['site']}_{components['sensor']}_{components['trial']}"
        if components["procLevel"]:
            base = f"{base}_{components['procLevel']}"
        base = f"{base}{components['rest']}"
        return base

    return _make_filename


@pytest.fixture
def make_components(default_components: dict[str, str | None]):
    def _make_components(change: dict[str, str | None]) -> dict[str, str | None]:
        return overwrite(default_components, change)

    return _make_components


@pytest.fixture
def make_layout(default_components: dict[str, str | None]):
    def _make_layout(change: dict[str, str | None]) -> str:
        components = overwrite(default_components, change)
        return f"{components['site']}/{components['sensor']}/{components['date']}/{components['trial']}/{components['procLevel']}"

    return _make_layout


@pytest.fixture
def make_project(default_meta: dict[str, Any], tmp_path: Path):
    def _make_project(template: str | Path | None | dict[str, Any]) -> ProjectManager:
        return ProjectManager.from_template(
            root=tmp_path, template=template, **default_meta
        )

    return _make_project


def overwrite(base: dict[str, Any], change: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for k, v in change.items():
        result[k] = v
    return result


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
    "change, component_change, layout_change, template",
    (
        # default.yaml
        ({}, {}, {"procLevel": "T0-raw"}, "default.yaml"),
        (
            {"procLevel": None},
            {},
            {"procLevel": "T0-raw"},
            "default.yaml",
        ),
        (
            {"procLevel": "proc"},
            {"procLevel": "proc"},
            {"procLevel": "T1-proc"},
            "default.yaml",
        ),
        (
            {"procLevel": "trait"},
            {"procLevel": "trait"},
            {"procLevel": "T2-trait"},
            "default.yaml",
        ),
        (
            {"procLevel": "T0-raw"},
            {"procLevel": "T0-raw"},
            {"procLevel": "T0-raw"},
            "default.yaml",
        ),
        (
            {"procLevel": "T1-proc"},
            {"procLevel": "T1-proc"},
            {"procLevel": "T1-proc"},
            "default.yaml",
        ),
        (
            {"procLevel": "T2-trait"},
            {"procLevel": "T2-trait"},
            {"procLevel": "T2-trait"},
            "default.yaml",
        ),
        # file_no_default_ext.yaml
        ({}, {}, {"procLevel": "T0-raw"}, "file_no_default_ext.yaml"),
        (
            {"procLevel": None},
            {},
            {"procLevel": "T0-raw"},
            "file_no_default_ext.yaml",
        ),
        (
            {"procLevel": "proc"},
            {"procLevel": "proc"},
            {"procLevel": "T1-proc"},
            "file_no_default_ext.yaml",
        ),
        (
            {"procLevel": "trait"},
            {"procLevel": "trait"},
            {"procLevel": "T2-trait"},
            "file_no_default_ext.yaml",
        ),
        (
            {"procLevel": "T0-raw"},
            {"procLevel": "T0-raw"},
            {"procLevel": "T0-raw"},
            "file_no_default_ext.yaml",
        ),
        (
            {"procLevel": "T1-proc"},
            {"procLevel": "T1-proc"},
            {"procLevel": "T1-proc"},
            "file_no_default_ext.yaml",
        ),
        (
            {"procLevel": "T2-trait"},
            {"procLevel": "T2-trait"},
            {"procLevel": "T2-trait"},
            "file_no_default_ext.yaml",
        ),
        # file_missing_component_but_has_default
        (
            {},
            {"rest": "_raw.bin"},
            {"procLevel": "T0-raw"},
            "file_missing_component_but_has_default.yaml",
        ),
        (
            {"procLevel": None},
            {},
            {"procLevel": "T0-raw"},
            "file_missing_component_but_has_default.yaml",
        ),
        (
            {"procLevel": "proc"},
            {"procLevel": "raw", "rest": "_proc.bin"},
            {"procLevel": "T0-raw"},
            "file_missing_component_but_has_default.yaml",
        ),
        (
            {"procLevel": "trait"},
            {"procLevel": "raw", "rest": "_trait.bin"},
            {"procLevel": "T0-raw"},
            "file_missing_component_but_has_default.yaml",
        ),
        (
            {"procLevel": "T0-raw"},
            {"procLevel": "raw", "rest": "_T0-raw.bin"},
            {"procLevel": "T0-raw"},
            "file_missing_component_but_has_default.yaml",
        ),
        (
            {"procLevel": "T1-proc"},
            {"procLevel": "raw", "rest": "_T1-proc.bin"},
            {"procLevel": "T0-raw"},
            "file_missing_component_but_has_default.yaml",
        ),
        (
            {"procLevel": "T2-trait"},
            {"procLevel": "raw", "rest": "_T2-trait.bin"},
            {"procLevel": "T0-raw"},
            "file_missing_component_but_has_default.yaml",
        ),
    ),
)
def test_match_file_name_and_layout(
    change: dict[str, str | None],
    component_change: dict[str, str | None],
    layout_change: dict[str, str | None],
    template: str,
    make_filename: MakeFileNameT,
    make_components: MakeComponentT,
    make_layout: MakeLayoutT,
    make_project: MakeProjectT,
    tmp_path: Path,
) -> None:
    name = make_filename(change)
    components = make_components(component_change)
    layout = make_layout(layout_change)
    model = make_project(FIXTURE_PATH / template)
    assert components == model.match(name)
    assert layout == model.get_file_placement(name)
    filename = tmp_path / name
    filename.touch(exist_ok=True)
    model.copy_file(filename)
    assert (model.location / layout).exists()


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


def test_match_invalid_file_name_expects_fails(make_project: MakeProjectT) -> None:
    m = make_project(FIXTURE_PATH / "file_no_default_ext.yaml")
    with pytest.raises(UnsupportedFileExtension):
        m.match("2020919-101010_adelaide_lidar_trial-0_proc.jpeg")


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
    m_default: ProjectManager, make_project: MakeProjectT
) -> None:
    # From dict
    m = make_project(m_default.metadata.model_dump())
    assert m_default.location == m.location
    assert m_default.metadata.model_dump() == m.metadata.model_dump()


def test_init_project_from_template_no_template_val(
    m_default: ProjectManager, make_project: MakeProjectT
) -> None:
    # From dict
    m = make_project(None)
    assert m_default.location == m.location
    assert m_default.metadata.model_dump() == m.metadata.model_dump()
