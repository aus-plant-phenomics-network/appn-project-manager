import json

from appm import ProjectManager
from appm.model import ProjectTemplateDecl

model = ProjectManager.from_template(root=".", year=2024, summary="test project")

filename = "20200101-101010_adelaide_oak_trial-alpha_T0-raw.bin"

matches = model.match(filename)


# with open("schema/yaml_template_schema.json", "w") as file:
#     json.dump(ProjectTemplateDecl.model_json_schema(), file, indent=2)
