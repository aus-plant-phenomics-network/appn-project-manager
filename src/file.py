from typing import Any, TypedDict 
from pydantic import BaseModel, RootModel
import re 

class FieldDeclaration(TypedDict): 
    date: str 
    site: str 
    sensor: str 
    trial: str 
    rest: str

class ExtensionDeclaration(BaseModel): 
    sep: str 
    order: list[str]
    fields: dict[str, str]

FileDeclaration = RootModel[dict[str, ExtensionDeclaration]]

class FileParser: 
    def __init__(self, data: Any)->None: 
        self.data = FileDeclaration.model_validate(data)
        self.patterns = {ext: self.build_pattern(decl) for ext, decl in self.data.root.items()}

    @staticmethod 
    def build_pattern(decl: ExtensionDeclaration)->str: 
        return r"^" + decl.sep.join([f"({decl.fields[item]})" for item in decl.order]) + r"(.*)$"
        
    def extract_filename(self, name: str)->FieldDeclaration: 
        ext = name.split(".")[-1]
        if ext not in self.patterns: 
            raise ValueError(f"No mattching pattern for extension: {ext}")
        pattern = self.patterns[ext] 
        match = re.match(pattern, name)
        if match:
            data = dict(zip(self.data.root[ext].order, match.groups()))
            data['rest'] = match.groups()[-1].lstrip(self.data.root[ext].sep)
            return data 
        raise ValueError(f"file: {name} does not match pattern: {pattern}")
        
