from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, overload

from ruamel.yaml import YAML

from appm.__version__ import __version__
from appm.exceptions import (
    UnsupportedFileExtension,
)
from appm.model import ProjectMetadata
from appm.utils import to_flow_style, validate_path

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.preserve_quotes = True  # optional, if you want to preserve quotes


class ProjectManager:
    METADATA_NAME: str = "metadata.yaml"

    def __init__(
        self,
        metadata: dict[str, Any],
        root: str | Path,
    ) -> None:
        self.root = Path(root)
        self.metadata = ProjectMetadata.model_validate(metadata)
        self.handlers = {ext: handler for ext, handler in self.metadata.file.items()}

    @property
    def location(self) -> Path:
        return self.root / self.metadata.project_name

    def build_path(self, layout_kwargs: dict[str, str]) -> None:
        layout = [(key, layout_kwargs.get(key, None)) for key in self.metadata.layout]
        layout_path = []
        for key, value in layout[::-1]:
            if value:
                layout_path.append(value)
            else:
                if not layout_path:
                    continue
                raise ValueError(f"Missing value for layout component: {key}")
        if layout_path:
            path = self.location / "/".join(layout_path[::-1])
            path.mkdir(parents=True, exist_ok=True)

    def match(self, name: str) -> dict[str, str]:
        """Match a file name and separate into format defined field components

        The result contains a * which captures all non-captured values.

        Args:
            name (str): file name

        Raises:
            UnsupportedFileExtension: the metadata does not define an
            extension declaration for the file's extension.

        Returns:
            dict[str, str]: key value dictionary of the field component
            defined using the format field.
        """
        ext = name.split(".")[-1]
        if ext in self.handlers:
            return self.handlers[ext].match(name)
        if "*" in self.handlers:
            return self.handlers["*"].match(name)
        raise UnsupportedFileExtension(str(ext))

    def get_file_placement(self, name: str) -> str:
        """Find location where a file should be placed.

        Determination is based on the metadata's layout field,
        the file extension format definition, and the file name.
        More concretely, field component - values are matched using the
        RegEx defined in format. Fields that match layout values will be
        extracted and path-appended in the order they appear in layout.

        Args:
            name (str): file name

        Returns:
            str: file placement directory
        """
        layout = self.metadata.layout
        groups = self.match(name)
        values = [groups[component] for component in layout]
        return "/".join(values)

    def init_project(self) -> None:
        """Create a project:

        - Determine the project's name from nameing_convention and metadata
        - Create a folder based on project's root and project name
        - Create a metadata file in the project's location
        """
        self.location.mkdir(exist_ok=True, parents=True)
        self.save_metadata()

    def save_metadata(self) -> None:
        """Save the current metadata to the project location"""
        metadata_path = self.location / self.METADATA_NAME
        with metadata_path.open("w") as file:
            data = self.metadata.model_dump(mode="json")
            data["version"] = __version__
            yaml.dump(
                to_flow_style(data),
                file,
            )

    def copy_file(self, src_path: str | Path) -> None:
        """Copy a file located at `src_path` to an appropriate
        location in the project.

        Args:
            src_path (str | Path): path to where src data is found
        """
        src_path = validate_path(src_path)
        dst_path = self.location / self.get_file_placement(src_path.name)
        dst_path.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)

    @overload
    @classmethod
    def from_template(
        cls,
        root: str | Path,
        template: str | Path,
        year: int,
        summary: str,
        internal: bool = True,
        researcherName: str | None = None,
        organisationName: str | None = None,
    ) -> ProjectManager: ...

    @overload
    @classmethod
    def from_template(
        cls,
        root: str | Path,
        template: dict[str, Any],
        year: int,
        summary: str,
        internal: bool = True,
        researcherName: str | None = None,
        organisationName: str | None = None,
    ) -> ProjectManager: ...

    @classmethod
    def from_template(
        cls,
        root: str | Path,
        template: str | Path | dict[str, Any],
        year: int,
        summary: str,
        internal: bool = True,
        researcherName: str | None = None,
        organisationName: str | None = None,
    ) -> ProjectManager:
        """Create a ProjectManager based on template and meta information

        Args:
            root (str | Path): parent directory - where project is stored
            template (str | Path | dict[str, Any]): path to template file or the template content.
            year (int): meta information - year
            summary (str): meta information - summary
            internal (bool, optional): meta information - internal. Defaults to True.
            researcher (str | None, optional): meta information - researcherName. Defaults to None.
            organisation (str | None, optional): meta information - organisationName. Defaults to None.

        Returns:
            ProjectManager: ProjectManager object
        """
        if isinstance(template, str | Path):
            metadata_path = Path(template)
            metadata_path = validate_path(template)
            with metadata_path.open("r") as file:
                metadata = yaml.load(file)
        else:
            metadata = template
        metadata["meta"] = {
            "year": year,
            "summary": summary,
            "internal": internal,
            "researcherName": researcherName,
            "organisationName": organisationName,
        }
        return cls(root=root, metadata=metadata)

    @classmethod
    def load_project(
        cls, project_path: Path | str, metadata_name: str | None = None
    ) -> ProjectManager:
        """Load a project from project's path

        Args:
            project_path (Path | str): path to project to open
            metadata_name (str | None, optional): name for metadata file. If not provided, use "metadata.yaml". Defaults to None.

        Returns:
            ProjectManager: ProjectManager object
        """
        project_path = validate_path(project_path)
        metadata_path = (
            project_path / cls.METADATA_NAME
            if not metadata_name
            else project_path / metadata_name
        )
        metadata_path = validate_path(metadata_path)

        with metadata_path.open("r") as file:
            metadata = yaml.load(file)
        return cls(metadata=metadata, root=project_path.parent)
