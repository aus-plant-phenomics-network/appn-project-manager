DEFAULT_TEMPLATE = {
    "version": "0.0.10",
    "naming_convention": {
        "sep": "\\",
        "structure": [
            "organisationName",
            "project",
            "site",
            "platform"
        ],
    },
    "layout": {
        "structure": ["date", "procLevel", "sensor"],
        "mapping": {"procLevel": {"raw": "T0-raw", "proc": "T1-proc", "trait": "T2-trait"}},
        "date_convert": { "base_timezone": "UTC", 
                          "output_timezone": "Australia/Adelaide", 
                          "input_format": '%Y-%m-%d %H-%M-%S',
                          "output_format": '%Y%m%d%z'
                          },
    },
    "file": {
        "*": {
            "sep": "_",
            "preprocess": {"find": "", "replace": "", "casesensitive": "false" },
            "default": {"procLevel": "raw"},
            "components": [
                {
                    "sep": "-",
                    "components": [["date", r"\d{4}-\d{2}-\d{2}"], ["time", r"\d{2}-\d{2}-\d{2}"]],
                },
                ["ms", r"\d{6}"],
                ["dateshort", r"d{4}"],
                ["run", "[^_.]+"],
                ["sensor", "[^_.]+"],
                {
                    "name": "procLevel",
                    "pattern": "T0-raw|T1-proc|T2-trait|raw|proc|trait",
                    "required": False,
                },
            ],
        }
    },
}
