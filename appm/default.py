DEFAULT_TEMPLATE = {
    "version": "0.1.1",
    "naming_convention": {
        "sep": "/",
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
                          "input_format": "%Y-%m-%d %H-%M-%S",
                          "output_format": "%Y%m%d%z"
                        },
    },
    "file": {
        "bin": {
            "sep": "_",
            "preprocess": {"find": "-(?=(jai|imu|Lidar|Hyperspec))", "replace": "_", "casesensitive": "false" },
            "default": {"procLevel": "raw"},
            "components": [
                {
                    "sep": "_",
                    "components": [["date", r"\d{4}-\d{2}-\d{2}"], ["time", r"\d{2}-\d{2}-\d{2}"]],
                },
                ["ms", r"\d{6}"],
                ["site_fn", "[^_.]+"],
                ["sensor", "[^_.]+"],
                {
                    "name": "procLevel",
                    "pattern": "T0-raw|T1-proc|T2-trait|raw|proc|trait",
                    "required": False,
                },
            ],
        },
        "csv": {
            "sep": "_",
            "preprocess": {"find": "-(?=(canbus))", "replace": "_", "casesensitive": "false" },
            "default": {"procLevel": "raw"},
            "components": [
                {
                    "sep": "_",
                    "components": [["date", r"\d{4}-\d{2}-\d{2}"], ["time", r"\d{2}-\d{2}-\d{2}"]],
                },
                ["ms", r"\d{6}"],
                ["site_fn", "[^_.]+"],
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
