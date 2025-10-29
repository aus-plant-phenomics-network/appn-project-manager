from __future__ import annotations

import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from appm.__version__ import __version__
from appm.default import DEFAULT_TEMPLATE
from appm.exceptions import (
    UnsupportedFileExtension,
)
from appm.model import Project
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
        self.metadata = Project.model_validate(metadata)
        self.handlers = dict(self.metadata.file.items())

    @property
    def location(self) -> Path:
        return self.root / self.metadata.project_name

    def match(self, name: str) -> dict[str, str | None]:
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
        layout = self.metadata.parsed_layout
        groups = self.match(name)
        return layout.get_path(groups)

    def init_project(self) -> None:
        """Create a project:

        - Determine the project's name from naming_convention and metadata
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

    def copy_file(self, src_path: str | Path) -> Path:
        """Copy a file located at `src_path` to an appropriate
        location in the project.

        Args:
            src_path (str | Path): path to where src data is found
        """
        src_path = validate_path(src_path)
        dst_path = self.location / self.get_file_placement(src_path.name)
        dst_path.mkdir(parents=True, exist_ok=True)

        # Write the source path and filename to a file in the destination directory
        # This is needed so as to copy other non '.bin' files associated with the file,
        # particularly for IMU processing which currently (13/10/2025) requires the
        # csv files stored along with the bin data that contain the Amiga system timestamp.
        file_path = dst_path / (src_path.name + ".origin")
        # Create a file in the destination directory with the same name as the source file,
        # and append a '.origin' file extension. Then write the full source path and
        # filename to the file
        with file_path.open("w", encoding="utf-8") as f:
            f.write(str(src_path))

        shutil.copy2(src_path, dst_path)
        return dst_path

    @classmethod
    def from_template(
        cls,
        root: str | Path,
        year: int,
        summary: str,
        project: str,
        site: str,
        platform: str,
        internal: bool = True,
        template: str | Path | dict[str, Any] | None = None,
        researcherName: str | None = None,
        organisationName: str | None = None,
    ) -> ProjectManager:
        """Create a ProjectManager based on template and meta information

        Args:
            root (str | Path): parent directory - where project is stored
            template (str | Path | dict[str, Any]): path to template file or the template content.
            year (int): meta information - year
            summary (str): meta information - summary
            project (str): meta information - e.g. 2025_OzBarley,... To be sourced from currated project data (Excel)
            site (str): meta information - e.g. Roseworthy, Gatton,... To be sourced from currated project data (Excel)
            platform  (str): meta information - e.g. Amiga, Gobi,... To be sourced from currated project data (Excel)
            internal (bool, optional): meta information - internal. Defaults to True.
            researcherName (str | None, optional): meta information - researcher name. Defaults to None. - To be sourced from currated project data (Excel)
            organisationName (str | None, optional): meta information - organisation name. Defaults to None. - To be sourced from currated project data (Excel)

        Returns:
            ProjectManager: ProjectManager object
        """
        if isinstance(template, str | Path):
            metadata_path = Path(template)
            metadata_path = validate_path(template)
            with metadata_path.open("r") as file:
                metadata = yaml.load(file)
        elif isinstance(template, dict):
            metadata = template
        elif not template:
            metadata = deepcopy(DEFAULT_TEMPLATE)
        else:
            raise TypeError(
                f"Unexpected type for template: {type(template)}. Accepts str, dict or None"
            )
        metadata["meta"] = {
            "year": year,
            "summary": summary,
            "project": project,
            "site": site,
            "platform": platform,
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
            project_path / cls.METADATA_NAME if not metadata_name else project_path / metadata_name
        )
        metadata_path = validate_path(metadata_path)

        with metadata_path.open("r") as file:
            metadata = yaml.load(file)
        return cls(metadata=metadata, root=project_path.parent)
