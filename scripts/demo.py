import json

from appm.model import Template

with open("../schema/yaml_template_schema.json", "w") as file:
    json.dump(Template.model_json_schema(), file, indent=2)
