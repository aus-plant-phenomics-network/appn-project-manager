from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from ruamel.yaml import YAML

from appm.model import Extension, Field, Layout, NamingConv, Template

FIXTURE_PATH = Path(__file__).parent / "fixtures"
yaml = YAML()


@pytest.mark.parametrize(
    "data, msg",
    [
        ({"components": []}, "Components cannot be empty"),
        (None, ""),
        (
            {"components": [["date", r"\d{8}"], ["date", r"\d{6}"]]},
            "Non-unique field name",
        ),
        (
            {"components": [["date", r"\d{8}"], Field(name="date", pattern=r"d\{6}")]},
            "Non-unique field name",
        ),
        (
            {
                "components": [
                    {
                        "sep": "-",
                        "components": [["date", r"\d{8}"], ["time", r"\d{6}"]],
                    },
                    Field(name="date", pattern=r"d\{6}"),
                ]
            },
            "Non-unique field name",
        ),
        (
            {
                "components": [
                    {
                        "sep": "-",
                        "components": [["date", r"\d{8}"], ["date", r"\d{6}"]],
                    },
                    {"name": "time", "pattern": r"\d{6}"},
                ]
            },
            "Non-unique field name",
        ),
        (
            {
                "components": [
                    {
                        "sep": "-",
                        "components": [["date", r"\d{8}"], ["time", r"\d{6}"]],
                    },
                    {"name": "rest", "pattern": r"\d{6}"},
                ]
            },
            "Field component must not contain reserved key: rest",
        ),
    ],
    ids=[
        "Empty component list",
        "Invalid component type",
        "Duplicate field name 1",
        "Duplicate field name 2",
        "Duplicate field name 3",
        "Duplicate field name 4",
        "Reserved field name",
    ],
)
def test_validate_extension_expects_fails(data: dict[Any, Any], msg: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Extension.model_validate(data)
    if msg:
        assert msg in str(excinfo.value)


@pytest.mark.parametrize(
    "data, msg",
    [
        (
            {
                "structure": [],
                "mapping": {"site": {"adelaide": "the plant accelerator"}},
            },
            "Mapping keys must be a subset of structure",
        ),
        (
            {
                "structure": ["location", "date", "sensor"],
                "mapping": {"site": {"adelaide": "the plant accelerator"}},
            },
            "Mapping keys must be a subset of structure",
        ),
    ],
    ids=["Mapping key superset 1", "Mapping key superset 2"],
)
def test_validate_layout_expects_fails(data: dict[Any, Any], msg: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Layout.model_validate(data)
    if msg:
        assert msg in str(excinfo.value)


@pytest.mark.parametrize(
    "data, msg",
    [
        ({"structure": []}, "empty structure"),
        ({"structure": ["year", "summary", "year"]}, "repetition"),
        ({"structure": ["year", "month", "day"]}, "permutation"),
        ({"structure": ["site", "sensor"]}, "permutation"),
    ],
    ids=["Empty structure", "Duplicated fields", "Invalid Field 1", "Invalid Field 2"],
)
def test_validate_naming_convention_expects_fails(data: dict[Any, Any], msg: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        NamingConv.model_validate(data)
    if msg:
        assert msg in str(excinfo.value)


@pytest.mark.parametrize(
    "path, msg",
    [
        ("extension_empty.yaml", "Components cannot be empty"),
        ("file_empty.yaml", "Empty extension"),
        (
            "file_extension_name.yaml",
            "Component fields must be a superset of layout fields",
        ),
        (
            "file_extension_no_default_name.yaml",
            "Component fields must be a superset of layout fields",
        ),
        ("file_first_field_optional_group.yaml", "First component must be required"),
        ("file_first_field_optional.yaml", "First component must be required"),
        (
            "file_no_default.yaml",
            "Optional field that is also a layout field must have a default value",
        ),
        ("group_empty.yaml", "Components cannot be empty"),
        ("layout_mapping.yaml", "Mapping keys must be a subset of structure"),
        ("naming_conv_duplicate.yaml", "repetition"),
        ("naming_conv_empty_structure.yaml", "empty structure"),
        ("naming_conv_invalid_field_structure.yaml", "permutation"),
    ],
)
def test_validate_template_expects_fails(path: str, msg: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        file_path = FIXTURE_PATH / f"invalid_templates/{path}"
        with file_path.open("r") as file:
            data = yaml.load(file)
        Template.model_validate(data)
    if msg:
        assert msg in str(excinfo.value)


@pytest.mark.parametrize(
    "path",
    (
        ("default.yaml"),
        ("file_missing_component_but_has_default.yaml"),
        ("file_multi_ext.yaml"),
        ("file_no_default_ext.yaml"),
        ("layout_list.yaml"),
        ("layout_with_mapping.yaml"),
        ("naming_perm_year_researcher_org.yaml"),
        ("naming_perm_year_summary_internal.yaml"),
    ),
)
def test_validate_template(path: str) -> None:
    file_path = FIXTURE_PATH / f"valid_templates/{path}"
    with file_path.open("r") as file:
        data = yaml.load(file)
    Template.model_validate(data)
