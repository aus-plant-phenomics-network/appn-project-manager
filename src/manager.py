from __future__ import annotations

import re
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Sequence, overload

from ruamel.yaml import YAML, CommentedMap, CommentedSeq

from src.__version__ import __version__
from src.exceptions import (
    FileFormatMismatch,
    MetadataFileNotFoundErr,
    ProjectNotFoundErr,
    UnsupportedFileExtension,
)
from src.parser import ExtDecl, ProjectMetadata

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.preserve_quotes = True  # optional, if you want to preserve quotes


def to_flow_style(obj: Any) -> Any:
    """Recursively convert dict/list to ruamel structures with ALL lists using flow-style."""
    if isinstance(obj, Mapping):
        cm = CommentedMap()
        for k, v in obj.items():
            cm[k] = to_flow_style(v)
        return cm
    if isinstance(obj, Sequence) and not isinstance(obj, str):
        cs = CommentedSeq()
        for item in obj:
            cs.append(to_flow_style(item))
        cs.fa.set_flow_style()
        return cs
    return obj


class ExtManager:
    def __init__(self, ext: str, decl: ExtDecl) -> None:
        self.ext = ext
        self.decl = decl

    @property
    def pattern(self) -> str:
        return (
            r"^"
            + self.decl.sep.join([f"({p})" for _, p in self.decl.format])
            + r"(.*)$"
        )

    def match(self, name: str) -> dict[str, str]:
        match = re.match(self.pattern, name)
        if not match:
            raise FileFormatMismatch(f"Name: {name}. Pattern: {self.pattern}")
        groups = match.groups()
        result = {}
        for i, (field, _) in enumerate(self.decl.format):
            result[field] = groups[i]
        result["*"] = groups[-1]
        return result


class ProjectManager:
    METADATA_NAME: str = "metadata.yaml"

    def __init__(
        self,
        metadata: dict[str, Any],
        root: str | Path,
    ) -> None:
        self.root = Path(root)
        self.metadata = ProjectMetadata.model_validate(metadata)
        self.handlers = {
            ext: ExtManager(ext, ext_decl)
            for ext, ext_decl in self.metadata.file.items()
        }

    def match(self, name: str) -> dict[str, str]:
        ext = name.split(".")[-1]
        if ext not in self.handlers:
            raise UnsupportedFileExtension(ext)
        return self.handlers[ext].match(name)

    def get_file_placement(self, name: str) -> str:
        layout = self.metadata.layout
        groups = self.match(name)
        values = [groups[component] for component in layout]
        return "/".join(values)

    def init_project(self) -> None:
        self.root.mkdir(exist_ok=True, parents=True)
        self.save_metadata()

    def save_metadata(self) -> None:
        metadata_path = self.root / self.METADATA_NAME
        with metadata_path.open("w") as file:
            data = self.metadata.model_dump(mode="json")
            data["version"] = __version__
            yaml.dump(
                to_flow_style(data),
                file,
            )

    def copy_file(self, src_path: Path) -> None:
        if src_path.exists():
            raise FileNotFoundError(str(src_path))
        location = self.get_file_placement(src_path.name)
        dst_path = self.root / location
        dst_path.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)

    @overload
    @classmethod
    def from_metadata(
        cls,
        root: str | Path,
        metadata: str | Path,
        year: int,
        summary: str,
        internal: bool = True,
        researcher: str | None = None,
        organisation: str | None = None,
    ) -> ProjectManager: ...

    @overload
    @classmethod
    def from_metadata(
        cls,
        root: str | Path,
        metadata: dict[str, Any],
        year: int,
        summary: str,
        internal: bool = True,
        researcher: str | None = None,
        organisation: str | None = None,
    ) -> ProjectManager: ...

    @classmethod
    def from_metadata(
        cls,
        root: str | Path,
        metadata: str | Path | dict[str, Any],
        year: int,
        summary: str,
        internal: bool = True,
        researcher: str | None = None,
        organisation: str | None = None,
    ) -> ProjectManager:
        if isinstance(metadata, str | Path):
            metadata = Path(metadata)
            if not metadata.exists():
                raise MetadataFileNotFoundErr(str(metadata))
            with metadata.open("r") as file:
                _metadata = yaml.load(file)
        else:
            _metadata = metadata
        _metadata.update(
            {
                "year": year,
                "summary": summary,
                "internal": internal,
                "researcher": researcher,
                "organisation": organisation,
            }
        )
        return cls(root=root, metadata=_metadata)

    @classmethod
    def load_project(
        cls, project_path: Path | str, metadata_name: str | None = None
    ) -> ProjectManager:
        project_path = Path(project_path)
        if not project_path.exists():
            raise ProjectNotFoundErr(str(project_path))
        metadata_path = (
            project_path / cls.METADATA_NAME
            if not metadata_name
            else project_path / metadata_name
        )
        if not metadata_path.exists():
            raise MetadataFileNotFoundErr(str(metadata_path))
        with metadata_path.open("r") as file:
            metadata = yaml.load(file)
        return cls(metadata=metadata, root=project_path)
