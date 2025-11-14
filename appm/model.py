from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Self

from pydantic import BaseModel, model_validator
from ruamel.yaml import YAML

from appm.__version__ import __version__
from appm.exceptions import FileFormatMismatch
from appm.utils import slugify,  get_task_logger

import zoneinfo
from zoneinfo import ZoneInfo

from datetime import datetime

yaml = YAML()

STRUCTURES = {
    "year",
    "summary",
    "project",
    "site",
    "platform",
    "internal",
    "researcherName",
    "organisationName",
}

# shared_logger = get_logger(__name__, factory=celery.utils.log.get_task_logger)
shared_logger = get_task_logger(__name__)

class Field(BaseModel):
    name: str
    pattern: str
    required: bool = True

    @property
    def regex(self) -> str:
        return f"(?P<{self.name}>{self.pattern})"

    @property
    def js_regex(self) -> str:
        return f"(?<{self.name}>{self.pattern})"

    @classmethod
    def from_tuple(cls, value: tuple[str, str] | list[str]) -> Field:
        assert len(value) == 2
        return Field(name=value[0], pattern=value[1])


class Group(BaseModel):
    components: list[tuple[str, str] | Field | Group]
    sep: str = "-"
    

    def validate_components(self) -> Self:
        if not self.components:
            raise ValueError(f"Components cannot be empty: {self.components}")
        self._fields: list[Field | Group] = []
        self._normalised_fields: list[Field] = []
        for field in self.components:
            if isinstance(field, tuple | list):
                f = Field.from_tuple(field)
                self._fields.append(f)
                self._normalised_fields.append(f)
            elif isinstance(field, Field):
                self._fields.append(field)
                self._normalised_fields.append(field)
            else:
                self._fields.append(field)
                self._normalised_fields.extend(field.normalised_fields)
        return self
        
    # def validate_preprocess(self) -> Self:
        # if not self.preprocess:
            # raise ValueError(f"preprocess cannot be empty: {self.preprocess}")
        
        
    def validate_names(self) -> Self:
        self._names: list[str] = []
        self._optional_names: set[str] = set()
        for field in self.fields:
            if isinstance(field, Field):
                self._names.append(field.name)
                if not field.required:
                    self._optional_names.add(field.name)
            else:
                self._names.extend(field.names)
                self._optional_names.update(field.optional_names)
        return self

    def validate_regex(self) -> Self:
        regex_str = []
        js_regex_str = []
        for i, field in enumerate(self.fields):
            is_optional = isinstance(field, Field) and not field.required
            pattern = field.regex
            js_pattern = field.js_regex

            if i == 0:
                if is_optional:
                    # First field, no separator; make only field optional
                    regex_str.append(f"(?:{pattern})?")
                    js_regex_str.append(f"(?:{js_pattern})?")
                else:
                    regex_str.append(pattern)
                    js_regex_str.append(js_pattern)
            else:
                if is_optional:
                    # Wrap separator + field together as optional
                    regex_str.append(f"(?:{self.sep}{pattern})?")
                    js_regex_str.append(f"(?:{self.sep}{js_pattern})?")
                else:
                    regex_str.append(f"{self.sep}{pattern}")
                    js_regex_str.append(f"{self.sep}{js_pattern}")
        self._regex = "".join(regex_str)
        self._js_regex = "".join(js_regex_str)
        return self

    @model_validator(mode="after")
    def validate_group(self) -> Self:
        return self.validate_components().validate_names().validate_regex()

    @property
    def normalised_fields(self) -> list[Field]:
        return self._normalised_fields

    @property
    def fields(self) -> list[Field | Group]:
        return self._fields

    @property
    def names(self) -> list[str]:
        return self._names

    @property
    def optional_names(self) -> set[str]:
        return self._optional_names

    @property
    def regex(self) -> str:
        return self._regex

    @property
    def js_regex(self) -> str:
        return self._js_regex


class Extension(Group):
    default: dict[str, str] | None = None
    preprocess : dict[str, str]

    @property
    def default_names(self) -> set[str]:
        return set() if not self.default else set(self.default.keys())

    @property
    def all_names(self) -> set[str]:
        return set(self.names) | self.default_names

    def validate_regex(self) -> Self:
        super().validate_regex()
        self._regex = f"^{self._regex}(?P<rest>.*)$"
        self._js_regex = f"^{self._js_regex}(?<rest>.*)$"
        return self

    def validate_unique_names(self) -> Self:
        count = Counter(self.names)
        non_uniques = {k: v for k, v in count.items() if v > 1}
        if non_uniques:
            raise ValueError(f"Non-unique field name: {non_uniques}")
        return self

    def validate_reserved_name(self) -> Self:
        if "rest" in self.names:
            raise ValueError("Field component must not contain reserved key: rest")
        return self

    def validate_first_field_must_be_required(self) -> Self:
        if not (field := self.normalised_fields[0]).required:
            raise ValueError(f"First component must be required: {field.name}")
        return self

    @model_validator(mode="after")
    def validate_extension(self) -> Self:
        return (
            self.validate_components()
            .validate_names()
            .validate_regex()
            .validate_unique_names()
            .validate_reserved_name()
            .validate_first_field_must_be_required()
        )
        
    def preprocess_filename(self, name: str) -> str:
        """"
        Uses the template YAML file 'preprocess' section to choose find and replace 
        strings to be used to modify an input filename.
        
        e.g. 2025-10-29_10-54-14_783583_horsham-jai1.bin -> 2025-10-29_10-54-14_783583_horsham_jai1.bin
        template.yaml:
        preprocess:
            find: '-(?=(jai|imu|Lidar|Hyperspec|canbus))'  # finds a '-' providing it is followed by one of the strings
            replace: '_'                                   # repalces with an '_' (if found)
            casesensitive: 'False
        
        """
        find_str = ''
        replace_str = ''
        casesensitive = True
        
        # This is the filename preprocessing regex find and replace (if needed)
        if self.preprocess:
            find_str = self.preprocess['find'].strip()
            replace_str = self.preprocess['replace'].strip() # may be an empty string if we want to delete a string section
            casesensitive = self.preprocess['casesensitive'].lower() in ("true", "1", "yes", "on")
        
        if (len(find_str) > 0):  
            if casesensitive: 
                name_sub = re.sub(find_str, replace_str, name, flags=re.IGNORECASE)
            else:
                name_sub  = re.sub(find_str, replace_str, name)
        else:
            name_sub = name
            
        return name_sub

    def match(self, name: str) -> dict[str, str | None]:
        
        name_sub = self.preprocess_filename(name)
            
        shared_logger.debug(f'APPM:Extension.match(): self.regex: {self.regex}')
        m = re.match(self.regex, name_sub)
        if not m:
            raise FileFormatMismatch(f"Name: {name_sub}. Pattern: {self.regex}")
        result = m.groupdict()
        if self.default:
            for k, v in self.default.items():
                shared_logger.debug(f'APPM:Extension.match() self.default.items(): self: {k}  {v}')
                if result.get(k) is None:
                    result[k] = v
        shared_logger.debug(f'APPM:Extension.match(): result: {result}')
        return result


File = dict[str, Extension]

# Define common aliases
ALIASES = {
    "z": ["Etc/UTC", "UTC"],
    "utc": ["Etc/UTC", "UTC"],
    "gmt": ["Etc/GMT", "GMT"],
    "aest": ["Australia/Sydney", "Australia/Melbourne", "Australia/Brisbane"],
    "aedt": ["Australia/Sydney", "Australia/Melbourne"],
    "acst": ["Australia/Adelaide",  "Australia/Darwin"],
    "acdt": ["Australia/Adelaide"],
    "awst": ["Australia/Perth"], 
    "awdt": ["Australia/Perth"],
    "acwst": ["Australia/Eucla"],
    "lhst": ["Australia/Lord_Howe"],
    "lhdt": ["Australia/Lord_Howe"],
    "nft": ["Pacific/Norfolk"],
    "nfdt": ["Pacific/Norfolk"],
    "cxt": ["Indian/Christmas"],
    "cct": ["Indian/Cocos"]
    # Add more if needed
}

class DateConvert():
    base_timezone: str # e.g. UTC
    output_timezone: str # e.g. "Australia/Adelaide"
    
    def __init__(self, date_convert : dict[str, str]):
        shared_logger.debug(f'APPM: Initialising DateConvert with: {date_convert}')
        self.base_timezone = date_convert['base_timezone']
        self.output_timezone = date_convert['output_timezone']
        if "input_format" in date_convert:
            self.input_format = date_convert['input_format']
        else:
            self.input_format = "%Y-%m-%d %H-%M-%S"
        if "output_format" in date_convert:
            self.output_format = date_convert['output_format']
        else:
            self.output_format = '%Y%m%d%z'

    def search_timezones(self, query: str) -> list[str] :
        """ matches incomplete timezone area strings to return the full timezone code from IANA timezone database"""
        query_lower = query.lower()

        # Check aliases first
        if query_lower in ALIASES:
            return ALIASES[query_lower]

        # Fallback to substring search
        matches = [tz for tz in zoneinfo.available_timezones() if query_lower in tz.lower()]
        return matches

    def convert_date_timezone(self, 
                            date_str: str, 
                            date_format_in: str = "%Y-%m-%d %H-%M-%S", 
                            date_format_out: str = "%Y%m%d%z", 
                            base_tz: str = 'UTC' , 
                            output_tz: str = 'Australia/Adelaide') -> str:
        """
        Convert a date string from base_tz to output_tz using the given format.
        
        Args:
            date_str (str): The date string to convert.
            date_format (str): The format of the input date string (e.g., "%Y-%m-%d %H:%M").
            base_tz (str): The IANA name of the base timezone (e.g., "UTC").
            output_tz (str): The IANA name of the output timezone (e.g., "Australia/Adelaide").
        
        Returns:
            str: The converted date string in the same format.
            
        Example: 
            
            date_str = "2025-10-30 02:30"
            date_format = "%Y-%m-%d %H:%M"
            base_tz = "UTC"
            output_tz = "Australia/Adelaide"

            converted = convert_date_timezone(date_str, date_format, base_tz, output_tz)
            print(converted)  # Output: "2025-10-30 13:00"

        """
        output_tz_found = self.search_timezones(output_tz)
        if len(output_tz_found) == 0:
            raise ValueError(f"Input requested timezone: {output_tz} was not found as valid.")
        
        base_tz_found = self.search_timezones(base_tz)
        if len(base_tz_found) == 0:
            raise ValueError(f"Input base timezone: {base_tz} was not found as valid.")
        
        # Parse the date string with base timezone
        dt = datetime.strptime(date_str, date_format_in).replace(tzinfo=ZoneInfo(base_tz_found[0]))
        
        # Convert to output timezone
        converted_dt = dt.astimezone(ZoneInfo(output_tz_found[0]))
        
        return converted_dt.strftime(date_format_out)
    
    
    def rearrange_date(self, date_str: str, input_order: str = r"(\d{4})-(\d{2})-(\d{2})", format_order: str = "YYYYMMDD") -> str:
        # Match the date pattern
        match = re.match(input_order, date_str)
        if not match:
            raise ValueError("Date string must be in 'YYYY-MM-DD' format")

        year, month, day = match.groups()

        # Build the new format based on the format_order string
        format_map = {
            "YYYY": year,
            "MM": month,
            "DD": day
        }

        # Replace format tokens with actual values
        for token in format_map:
            format_order = format_order.replace(token, format_map[token])

        return format_order


    
class Layout(BaseModel):
    r"""
    This class is populated via the YAML input template file and it controls the structure 
    of the output directory for where to place output data. 
    
    The class is dependant on the 'file:' section of the YAML file as the file section defines 
    the decomposition of the filename:

    Example YAML input for the layout section:
    
    yaml
        layout:
          structure: [ 'date', 'procLevel', 'sensor' ]
          mapping:
            procLevel:
              raw: 'T0-raw'
              proc: 'T1-proc'
              trait: 'T2-trait'
          date_convert:
            base_timezone: 'UTC'
            output_timezone: 'Australia/Adelaide'
            input_format: '%Y-%m-%d %H-%M-%S'  # concatenated file:components:components: 'date' and 'time'
            output_format: '%Y%m%d%z'
        file:
          "bin":
            sep: "_"
            preprocess:
              find: '-'
              replace: '_'
              casesensitve: True
            default:
              procLevel: raw   
            components:
              - sep: "_"
                components:
                  - ['date', '\d{4}-\d{2}-\d{2}']
                  - ['time', '\d{2}-\d{2}-\d{2}']
              - ['ms', '\d{6}']
              - ['site_fn', '[^_.]+']
              - ['sensor', '[^_.]+']
              - name: 'procLevel'
                pattern: 'T0-raw|T1-proc|T2-trait|raw|proc|trait'
                required: false
    
        e.g. Input filename: 2025-08-14_06-30-14_783583_horsham_jai1.bin
    
        Requested variables:
            'date':       2025-08-14
            'procLevel':  T0-raw
            'sensor':     jai
        
        unused variables:
            'time':       06-30-14
            'ms':         783583
            'site_fn':    horsham
        
        Output directory:
            20250814+0930/T0-raw/jai
    
    """
    structure: list[str]
    mapping: dict[str, dict[str, str]] | None = None
    date_convert: dict[str, str] 
    _structure_set: set[str]
    
    @classmethod
    def from_list(cls, value: list[str]) -> Layout:
        return cls(structure=value)

    @property
    def structure_set(self) -> set[str]:
        return self._structure_set

    # @property
    # def date_convert_obj(self) -> DateConvert:
        # return self._date_convert_obj
        
    @model_validator(mode="after")
    def validate_layout(cls, self: Self) -> Self:
        self._structure_set = set(self.structure)
        if self.mapping and not set(self.mapping.keys()).issubset(self._structure_set):
            raise ValueError(
                f"Mapping keys must be a subset of structure. Mapping keys: {set(self.mapping.keys())}, structure: {self.structure}"
            )
        
        dc = DateConvert(self.date_convert) 
        base_tz = dc.base_timezone
        output_tz = dc.output_timezone
        
        output_tz_found = dc.search_timezones(output_tz)
        if len(output_tz_found) == 0:
            raise ValueError(f"validate_layout(): Input requested timezone: {output_tz} was not found as valid.")
        
        base_tz_found = dc.search_timezones(base_tz)
        if len(base_tz_found) == 0:
            raise ValueError(f"validate_layout(): Input base timezone: {base_tz} was not found as valid.")
        
        
        shared_logger.debug(f'APPM: Layout.validate_layout(): self: {self}')
            
        return self
    
    def get_path(self, components: dict[str, str | None]) -> str:
        """ 
        Converts the set of keys from the layout['structure'] dictionary into nested set of Posix directories
      
        The method will convert the date into a local timezone based on the layout['date_convert'] values.
                
        """
        result: list[str] = []
        component_date: str 
        component_time: str | None
        
        # loop through once
        for key in self.structure:
            value = components.get(key)
            shared_logger.debug(f'APPM: Layout.get_path(): {key} : {value}')
            if key == 'date':                
                if value is None:
                    raise ValueError("APPM: Layout.get_path(): components['date'] is required")
                component_date = value
            
        # This ensures the time component is found, even if it is not 
        # specified  in the layout['structure'] list
        timezone_convert = True
        if 'time' in components.keys():
            component_time = components.get('time')
            if component_time is None:
                component_time = '00-00-00'
        else:
            timezone_convert = False
            converted_date = component_date  # default date is the one found in the filename
            shared_logger.debug(f'APPM: Layout.get_path(): No time key in file:components, not converting timezones')
 
        if timezone_convert:
            # '2025-08-14_06-30-03...bin' -> component_date = '2025-08-14'  component_time = '06-30-03' 
            date_str = component_date + " " + component_time
            dc = DateConvert(self.date_convert) 
            base_tz = dc.base_timezone
            output_tz = dc.output_timezone
            # date_format_in = "%Y-%m-%d %H-%M-%S"
            # date_format_out = "%Y%m%d%z"
            date_format_in  = dc.input_format
            date_format_out = dc.output_format
            converted_date  = dc.convert_date_timezone(date_str, date_format_in, date_format_out,  base_tz , output_tz)
            shared_logger.info(f'APPM: Layout.get_path(): Converting timezones {base_tz} to {output_tz}')
        
        for key in self.structure:
            value = components.get(key)
            # swap the date found in the filename with the converted 
            # date from UTC to the selected timezone
            if key == 'date':
                value = converted_date
                
            if self.mapping and key in self.mapping and value in self.mapping[key]:
                value = self.mapping[key][value]
                
            if value is None:
                raise ValueError(
                    f"None value for key: {key}. Either set a default for Extension definition, change Extension pattern to capture key value, or rename file."
                )
            result.append(value)
        return "/".join(result)


class NamingConv(BaseModel):
    sep: str = "_"
    structure: list[str] = [
        "year",
        "summary",
        "project",
        "site",
        "platform",
        "internal",
        "researcherName",
        "organisationName",
    ]
    

    @model_validator(mode="after")
    def validate_naming_convention(self) -> Self:
        """Validate structure value

        structure:
            - cannot be empty
            - cannot have repeated component(s)
            - cannot have a field component that is not one of the metadata fields.
        """
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


class Template(BaseModel):
    layout: Layout | list[str]
    file: File
    naming_convention: NamingConv = NamingConv()
    version: str = __version__

    def validate_layout(self) -> Self:
        if isinstance(self.layout, list):            
            self._layout = Layout.from_list(self.layout)
        else:
            self._layout = self.layout
        return self

    def validate_file_non_empty(self) -> Self:
        if not self.file:
            raise ValueError("Empty extension")
        shared_logger.debug(f'APPM: Template(BaseModel): {self.file}')
        return self

    def validate_file_name_subset_layout(self) -> Self:
        for ext, decl in self.file.items():
            shared_logger.debug(f'APPM: Template():validate_file_name_subset_layout():  {ext}  {decl} ')
            for field in self.parsed_layout.structure_set:
                if field not in decl.all_names:
                    raise ValueError(
                        f"Component fields must be a superset of layout fields: {field}. Ext: {ext}"
                    )
                if field in decl.optional_names and field not in decl.default_names:
                    raise ValueError(
                        f"Optional field that is also a layout field must have a default value: {field}. Ext: {ext}"
                    )
        return self

    @property
    def parsed_layout(self) -> Layout:
        return self._layout

    @model_validator(mode="after")
    def validate_template(self) -> Self:
        return self.validate_layout().validate_file_non_empty().validate_file_name_subset_layout()


class Metadata(BaseModel):
    year: int
    summary: str
    project: str
    site: str
    platform: str
    internal: bool = True
    researcherName: str | None = None
    organisationName: str | None = None


class Project(Template):
    r"""
    Constructs a directory path or single directory, depending on the naming_convention.layout.sep value.

    If sep == '/', then naming_convention.structure[] elements are joined as a multiple element Path
    otherwise, the elements are concatenated with the sep string to form a single directory.

    e.g.
    layout['structure']: ['organisationName', 'project', 'site', 'platform']
    if sep == '/'
      result = <root>/organisationName/project/site/platform

    if sep == '_'
      result = <root>/organisationName_project_site_platform
    """

    meta: Metadata

    @property
    def project_name(self) -> Path:
        """Project name based on metadata and naming convention definition"""
        fields = self.naming_convention.structure
        shared_logger.debug(f'APPM:Project:project_name() called')
        
        name: list[str] = []
        for field in fields:
            value = getattr(self.meta, field)
            if value is not None:
                if isinstance(value, str):
                    name.append(slugify(value))
                elif field == "year":
                    name.append(str(value))
                elif field == "internal":
                    value = "internal" if value else "external"
                    name.append(value)
        if self.naming_convention.sep == "/":
            respath =  Path(*name)
            shared_logger.debug(f'APPM:Project:project_name() respath: {respath}')
            return (respath)
        return Path(self.naming_convention.sep.join(name))
