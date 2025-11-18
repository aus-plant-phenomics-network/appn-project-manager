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

Files are automatically placed in the correct directory based on the template used.

An example template file:
```json
version: 0.0.8
naming_convention:
  sep: "_"
  structure: ['year', 'summary', 'internal', 'researcherName', 'organisationName']
layout:
  structure: ['sensor', 'date', 'trial', 'procLevel']
  mapping:
    procLevel:
      raw: 'T0-raw'
      proc: 'T1-proc'
      trait: 'T2-trait'
file:
  "*":
    sep: "_"
    default:
      procLevel: raw
    components:
      - sep: "_"
        components:
          - ['date', '\d{4}-\d{2}-\d{2}']
          - ['time', '\d{2}-\d{2}-\d{2}']
      - ['ms', '\d{6}']
      - ['dateshort', '\d{4}']
      - ['trial', '[^_.]+']
      - ['sensor', '[^_.]+']
      - name: 'procLevel'
        pattern: 'T0-raw|T1-proc|T2-trait|raw|proc|trait'
        required: false

```

Using an input file named: ```2025-08-14_06-30-03_393242_0814_test2_jai1_0.bin``` the above
template will output files to the following directory:
```
jai1/2025-08-14/test2/T0-raw

```
as per the ```layout```  format specified in the file: 
```
structure: ['sensor', 'date', 'trial', 'procLevel']
```
and the file(s) will have the name:
```
2025-08-14_06-30-03_393242_0814_test2_jai1_0_preproc-0.jpeg
```

Programmatically this is done using the following method:

```py
pm.copy_file("data/20240601-120000_SiteA_SensorX_Trial1_T0-raw.csv")
```

## Project Updating version numbers
Version numbers follow the standard pattern of: MAJOR.MINOR.PATCH and the project
has been configured to use the Python libray ```bump-my-version``` to help automate the
change of version numbers that are used in the files within the project.
  
The following proceedures outline its use:
  
Make sure mump-my-version is installed
```
uv pip install  bump-my-version
# add to pyproject.toml 
uv add --dev bump-my-version
```
This tool uses the file ```.bumpmyversion.toml``` for configuring what files get modified.  

N.B. If files are added to the project that use an explicit version number, then add the files 
to ```.bumpmyversion.toml``` along with the rules.

Use the tool as follows:
1. set the current version in ```.bumpmyversion.toml```
e.g.
```
current_version = "0.1.1"
```
Set the bumpwhat value and run the ```bump-my-version``` command:
```
# uv run bump-my-version -h

export bumpwhat=major | minor | patch
uv run bump-my-version bump $bumpwhat
```

N.B. For YAML files used in testing, it is easier to modify them using sed
```
# Check the current version:
find ./tests/fixtures -type f \( -name "*.yaml" -o -name "*.yml" \) -exec grep "version" {} +

# set FINDVERSION to be the version number found in files above:
export FINDVERSION=0.0.10
#  set the replacement string:
export REPVERSION=0.1.0
find ./tests/fixtures -type f \( -name "*.yaml" -o -name "*.yml" \) -exec sed -i -e "s/$FINDVERSION/$REPVERSION/g" {} +

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
