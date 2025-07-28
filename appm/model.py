from __future__ import annotations

import re
from typing import Any, Self, cast

from pydantic import BaseModel, model_validator

from appm.__version__ import __version__
from appm.exceptions import FileFormatMismatch
from appm.utils import slugify

STRUCTURES = {"year", "summary", "internal", "researcherName", "organisationName"}


def extract_field_decl(
    fields: list[FieldDecl | tuple[str, str]] | None,
) -> list[FieldDecl]:
    if not fields:
        return []
    result = []
    for field in fields:
        if isinstance(field, FieldDecl):
            result.append(field)
        elif isinstance(field, tuple | list):
            result.append(FieldDecl.from_tuple(field))
        elif isinstance(field, dict):
            result.append(FieldDecl.model_validate(field))
    return result


class FieldDecl(BaseModel):
    name: str
    sep: str | None = None
    pattern: str | None = None
    subfields: list[FieldDecl | tuple[str, str]] | None = None
    required: bool = True

    @property
    def matched_fields(self) -> list[str]:
        result = [self.name]
        for field in self.processed_subfields:
            result.extend(
                [f"{self.name}__{field_name}" for field_name in field.matched_fields]
            )
        return result

    @model_validator(mode="after")
    def validate_pattern_subfields(self) -> Self:
        # Error when none of pattern and subfields are provided
        if not self.pattern and not self.subfields:
            raise ValueError("Either one of pattern or subfield must be provided")
        # Error when both of pattern and subfields are provided
        if self.pattern and self.subfields:
            raise ValueError(
                "pattern and subfields must not be provided at the same time"
            )
        # Error when subfields are provided but sep is None
        if self.subfields and not self.sep:
            raise ValueError("If subfields is provided, sep must also be provided")
        self._subfields = extract_field_decl(self.subfields)
        return self

    @classmethod
    def from_tuple(cls, value: tuple[str, str]) -> "FieldDecl":
        return FieldDecl(
            name=value[0],
            pattern=value[1],
        )

    @property
    def processed_subfields(self) -> list["FieldDecl"]:
        return self._subfields

    @property
    def processed_pattern(self) -> str:
        if self.pattern:
            return self.pattern
        patterns = [
            f"({field.processed_pattern})" for field in self.processed_subfields
        ]
        assert self.sep
        return self.sep.join(patterns)


class ExtDecl(BaseModel):
    """Pydantic model for extension file name convention

    This metadata defines how file names are described and organised in the project.

    File names are separator separated fields with a . extensions. For instance, the
    file name `20200101-100000_adelaide_oak_trial-alpha.bin` is made up of the following
    components:
    - `date`: `20200101-100000`
    - `site`: `adelaide`
    - `sensor`: `oak`
    - `trial`: `trial-alph`

    Components are defined using the format parameter which is a list of string pairs, the
    first being the field name and the second being its regex pattern.

    The order at which a field definition (a string pair) appears in the `format` list must
    match how the field value appears in the matching file name. In the previous example, since date is the first
    field in `format`, the file name begins with a date value.

    Note that if `_` is used as the separator, user must ensure that no `_` is used in field
    value. An appropriate replacement is the `-` literal. For instance, `trial-alpha` is prefered
    over `trial_alpha` (the latter will throw an error). The library also provides a utility function
    called `slugify` to handle such cases.
    """

    sep: str = "_"
    """File name separator"""
    format: list[tuple[str, str] | FieldDecl]
    """File name format components - list of fields and their regex pattern. The order 
    of fields in format is used for regex group capture.
    """

    @property
    def processed_format(self) -> list[FieldDecl]:
        return self._format

    @property
    def format_map(self) -> dict[str, FieldDecl]:
        return self._format_map

    @property
    def processed_pattern(self) -> str:
        return self._pattern

    @property
    def fields(self) -> set[str]:
        """Set of fields defined in format"""
        return set(self.matched_fields)

    @model_validator(mode="after")
    def transform_format(self) -> Self:
        self._format = extract_field_decl(self.format)
        self._format_map: dict[str, FieldDecl] = {}
        for field in self._format:
            if field.name in self._format_map:
                raise ValueError(f"Field name must be unique: {field.name}")
            self._format_map[field.name] = field

        self._pattern = (
            r"^"
            + self.sep.join([f"({p.processed_pattern})" for p in self._format])
            + r"(.*)$"
        )
        return self

    @property
    def matched_fields(self) -> list[str]:
        result = []
        for field in self.processed_format:
            result.extend(field.matched_fields)
        result.append("*")
        return result

    def match(self, name: str) -> dict[str, Any]:
        match = re.match(self.processed_pattern, name)
        if not match:
            raise FileFormatMismatch(f"Name: {name}. Pattern: {self.processed_pattern}")
        groups = match.groups()
        assert len(groups) == len(self.matched_fields)
        return dict(zip(self.matched_fields, groups))


class NamingConvDecl(BaseModel):
    """Pydantic model for project naming convention declaration.

    This metadata defines how a project name is constructed from its structural components.

    Note that the structural components must come from the metadata fields - i.e. year, summary etc,
    and hence the parameter `structure` must be a valid permutation of a non empty subset of
    `{"year", "summary", "internal", "researcherName", "organisationName"}`. This means that the parameter
    structure:
    - cannot be empty
    - cannot have repeated component(s)
    - cannot have a field component that is not one of the metadata fields.

    Note that if `_` is used as the separator, user must ensure that no `_` is used in field
    value. An appropriate replacement is the `-` literal. For instance, `trial-alpha` is prefered
    over `trial_alpha` (the latter will throw an error). The library also provides a utility function
    called `slugify` to handle such cases.
    """

    sep: str = "_"
    "Project name separator"
    structure: list[str] = [
        "year",
        "summary",
        "internal",
        "researcherName",
        "organisationName",
    ]
    """Project name format components"""

    @model_validator(mode="after")
    def validate_structure_values(self) -> Self:
        """Validate structure value

        structure:
            - cannot be empty
            - cannot have repeated component(s)
            - cannot have a field component that is not one of the metadata fields.
        """
        counter: dict[str, int] = {}
        if len(self.structure) == 0:
            raise ValueError("Invalid naming structure - empty structure")
        for field in self.structure:
            counter[field] = counter.get(field, 0) + 1
            if counter[field] > 1:
                raise ValueError(f"Invalid naming structure - repetition: {field}")
            if field not in STRUCTURES:
                raise ValueError(
                    f"Invalid naming structure - invalid field: {field}. Structure must be a non empty permutation of {STRUCTURES}"
                )
        return self


class ProjectTemplateDecl(BaseModel):
    """Pydantic model for project yaml template declaration.

    This model validate fields defined in `metadata.yaml`. Note that this class defines a metadata
    template and not the full metadata. The full metadata class is `ProjectMetadata`.

    <h4>Fields:</h4>

    - layout: a list of fields that define the layout organisation of the project. Must be present.
    - file: a mapping between file extensions and their definiton (`ExtDecl`). Must be present.
    - naming_convention: a naming convention declaration object (`NamingConvDecl`). Can be missing.
    - version: the current metadata version. If not provided, will be interpreted using the latest version.

    Project layout defined using the `appm` package is very flexible. For instance, valid layouts can be

    - `[site, sensor, trial]` - i.e. `adelaide/oak/trial-alpha`
    - `[sensor, serial_number, location]` - i.e `oak-d/A00110-INTL/adelaide`
    - `[site, year, month, sensor]` - i.e. `adelaide/2024/01/oak-d`

    However, valid metadata must satisfy the following constraints:

    - Folder organisation must strictly adhere to layout definition - i.e. users can't mix and match 2 layouts in the
    same project.
    - File extension fields must be a proper superset of layout. This allows appm to interprete the appropriate
    location to place the file to using the layout definition.

    Example:

    Given the standard template, the file `20200101-100000_adelaide_oak_trial-alpha.bin` will be placed into
    `{project_name}/adelaide/oak/trial-alpha/20200101-100000_adelaide_oak_trial-alpha.bin`

    """

    layout: list[str]
    """Describes how the folder structure described by the current template is organised. For instance, a valid layout is ['site','sensor','trial'], and a valid path is `adelaide/oak/trial-alpha`"""
    file: dict[str, ExtDecl]
    """File extension and declaration, which is a mapping of extension name to extension declaration. When copying files to the project, appm matches the file extension to extension declaration to determine the location where the file should be placed. Users can use 
    `*` in place of a file extension as a default catch all. This means if a declaration for an extension is found, that declaration will be used for path matching. If the exact extension declaration is not found, but a `*` declaration is define, the declaration for 
    `*` will be used instead."""
    naming_convention: NamingConvDecl = NamingConvDecl()

    version: str | None = __version__
    """APPM template version"""

    @property
    def layout_set(self) -> set[str]:
        return set(self.layout)

    @model_validator(mode="after")
    def validate_format_and_layout(self) -> Self:
        for ext, decl in self.file.items():
            if not self.layout_set.issubset(decl.fields):
                raise ValueError(
                    f"""Format fields must be a superset of layout fields. 
                    Extension: {ext}. Format fields: {decl.fields}. Layout fields: {self.layout_set}"""
                )
        return self


class ProjectMetadataDecl(BaseModel):
    """Pydantic model for general project information"""

    year: int
    summary: str
    internal: bool = True
    researcherName: str | None = None
    organisationName: str | None = None


class ProjectMetadata(ProjectTemplateDecl):
    """Pydantic model for full project metadata"""

    meta: ProjectMetadataDecl

    @property
    def project_name(self) -> str:
        """Project name based on metadata and naming convention definiton"""
        fields = self.naming_convention.structure
        name: list[str] = []
        for field in fields:
            value = getattr(self.meta, field)
            if value is not None:
                if isinstance(value, str):
                    name.append(slugify(value))
                elif field == "year":
                    name.append(str(value))
                elif field == "internal":
                    value = "internal" if value else "external"
                    name.append(value)
        return self.naming_convention.sep.join(name)
