# APPN Phenomate Project Manager

A Python package for managing project templates, metadata, and file organization using flexible YAML schemas. Designed for research and data projects that require consistent file naming, metadata, and directory structures.

## Install

```bash
pip install appm
```

## Features

- Template-driven project structure: Define project layouts, file naming conventions, and metadata in YAML.
- Automatic project initialization: Create new projects with standardized folders and metadata files.
- File placement and matching: Automatically determine where files belong based on their names and template rules.
- Extensible and validated: Uses Pydantic for schema validation and ruamel.yaml for YAML parsing.
Installation
Or for development:

## Usage
1. Define a Template

Create a YAML template describing your project's structure, naming conventions, and file formats. See `examples/template.yaml` for the default template.

2. Initialize a Project

```py
from appm import ProjectManager

pm = ProjectManager.from_template(
    root="projects",
    year=2024,
    summary="Wheat yield trial",
    internal=True,
    researcherName="Jane Doe",
    organisationName="Plant Research Org",
    template="examples/template.yaml"
)
pm.init_project()

```

3. Add Files

Files are automatically placed in the correct directory based on the template.

```py
pm.copy_file("data/20240601-120000_SiteA_SensorX_Trial1_T0-raw.csv")
```

## Project Structure
- appm – Core package (template parsing, project management, utilities)
- examples – Example YAML templates
- schema – JSON schema for template validation
- tests – Unit tests and fixtures

## Development
- Python 3.11+
- Pydantic
- ruamel.yaml
- pytest for testing

## Run tests:

```
pytest
```
