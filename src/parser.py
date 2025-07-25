from typing import Self

from pydantic import BaseModel, model_validator

from src.__version__ import __version__
from src.utils import slugify

STRUCTURES = {"year", "summary", "internal", "researcher", "organisation"}


class ExtDecl(BaseModel):
    sep: str = "_"
    format: list[tuple[str, str]]

    @property
    def fields(self) -> set[str]:
        return {item[0] for item in self.format}


class NamingConventionDecl(BaseModel):
    sep: str = "_"
    structure: list[str] = ["year", "summary", "internal", "researcher", "organisation"]

    @model_validator(mode="after")
    def validate_structure_values(self) -> Self:
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


class ProjectDecl(BaseModel):
    layout: list[str]
    file: dict[str, ExtDecl]
    naming_convention: NamingConventionDecl = NamingConventionDecl()

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


class ProjectMetadata(ProjectDecl):
    year: int
    summary: str
    internal: bool
    researcher: str | None = None
    organisation: str | None = None
    version: str | None = __version__

    @property
    def name(self) -> str:
        fields = self.naming_convention.structure
        name: list[str] = []
        for field in fields:
            value = getattr(self, field)
            if value is not None:
                if isinstance(value, str):
                    name.append(slugify(value))
                elif field == "year":
                    name.append(str(value))
                elif field == "internal":
                    value = "internal" if value else "external"
                    name.append(value)
        return self.naming_convention.sep.join(name)
