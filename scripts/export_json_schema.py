import json
from pathlib import Path

from appm.model import Template

with Path("schema/yaml_template_schema.json").open("w") as file:
    json.dump(Template.model_json_schema(), file, indent=2)
