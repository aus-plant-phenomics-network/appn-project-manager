DEFAULT_TEMPLATE = {
    "version": "0.0.9",
    "naming_convention": {
        "sep": "_",
        "structure": [
            "year",
            "summary",
            "project",
            "site",
            "platform",
            "internal",
            "researcherName",
            "organisationName",
        ],
    },
    "layout": {
        "structure": ["project", "site", "date", "run", "procLevel", "sensor" ],
        "mapping": {"procLevel": {"raw": "T0-raw", "proc": "T1-proc", "trait": "T2-trait"}},
    },
    "file": {
        "*": {
            "sep": "_",
            "default": {"procLevel": "raw"},
            "components": [
                {"sep": "-", "components": [["date", r"\d{4}-\d{2}-\d{2}"], ["time", r"\d{2}-\d{2}-\d{2}"]]},
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
