from typing import Self

from pydantic import BaseModel, model_validator

from appm.__version__ import __version__
from appm.utils import slugify

STRUCTURES = {"year", "summary", "internal", "researcher", "organisation"}


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
    first being the field name and the second being its regex pattern. For instance,
    the `date` component in the previous example can be defined as `['date', "\d{8}-\d{6}"]`.

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
    format: list[tuple[str, str]]
    """File name format components - list of fields and their regex pattern. The order 
    of fields in format is used for regex group capture.
    """

    @property
    def fields(self) -> set[str]:
        """Set of fields defined in format"""
        return {item[0] for item in self.format}


class NamingConvDecl(BaseModel):
    """Pydantic model for project naming convention declaration.

    This metadata defines how a project name is constructed from its structural components.

    Note that the structural components must come from the metadata fields - i.e. year, summary etc,
    and hence the parameter `structure` must be a valid permutation of a non empty subset of
    `{"year", "summary", "internal", "researcher", "organisation"}`. This means that the parameter
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
    structure: list[str] = ["year", "summary", "internal", "researcher", "organisation"]
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

    Given
    `layout: ['site', 'sensor', 'trial']`

    ```
    file:
        bin:
            sep: "_"
                format:
                - ['date', '\d{8}-\d{6}']
                - ['site', '[^_.]+']
                - ['sensor', '[^_.]+']
                - ['trial', '[^_.]+']
    ```
    The file `20200101-100000_adelaide_oak_trial-alpha.bin` will be placed into
    `{project_name}/adelaide/oak/trial-alpha/20200101-100000_adelaide_oak_trial-alpha.bin`

    """

    layout: list[str]
    file: dict[str, ExtDecl]
    naming_convention: NamingConvDecl = NamingConvDecl()
    version: str | None = __version__

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
    def name(self) -> str:
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
