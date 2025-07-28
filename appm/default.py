DEFAULT_TEMPLATE = {
    "naming_convention": {
        "sep": "_",
        "structure": [
            "year",
            "summary",
            "internal",
            "researcherName",
            "organisationName",
        ],
    },
    "layout": ["site", "sensor", "datetime__date", "trial", "procLevel"],
    "file": {
        "*": {
            "sep": "_",
            "format": [
                {
                    "name": "datetime",
                    "sep": "-",
                    "subfields": [["date", r"\d{8}"], ["time", r"\d{6}"]],
                },
                ["site", r"[^_.]+"],
                ["sensor", r"[^_.]+"],
                ["trial", r"[^_.]+"],
                ["procLevel", r"(T0-raw|T1-proc|T2-trait)?"],
            ],
        }
    },
}
