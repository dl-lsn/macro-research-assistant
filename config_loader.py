import json
from pathlib import Path


CONFIG_FILE = Path("config.json")


def load_config(file_path=CONFIG_FILE):
    """Load the project configuration from JSON."""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        config = json.load(file)

    validate_config(config)

    return config


def validate_config(config):
    """Check that the required configuration sections exist."""
    required_sections = [
        "project",
        "series",
        "files",
        "aggregation",
        "derived_metrics",
    ]

    missing_sections = [
        section
        for section in required_sections
        if section not in config
    ]

    if missing_sections:
        raise ValueError(
            "Missing configuration sections: "
            + ", ".join(missing_sections)
        )

    required_series = [
        "fed_funds",
        "cpi",
        "payrolls",
        "unemployment",
        "treasury_10y",
    ]

    missing_series = [
        series
        for series in required_series
        if series not in config["series"]
    ]

    if missing_series:
        raise ValueError(
            "Missing configured series: "
            + ", ".join(missing_series)
        )

    required_files = [
        "fed_funds_clean",
        "cpi_clean",
        "employment_clean",
        "treasury_clean",
        "frequency_aligned",
        "macro_context",
        "macro_derived",
        "validation_report",
    ]

    missing_files = [
        file_name
        for file_name in required_files
        if file_name not in config["files"]
    ]

    if missing_files:
        raise ValueError(
            "Missing configured files: "
            + ", ".join(missing_files)
        )


def get_series_id(config, series_name):
    """Return a FRED series ID from the configuration."""
    return config["series"][series_name]["id"]


def get_series_label(config, series_name):
    """Return a human-readable series label."""
    return config["series"][series_name]["label"]


def get_file_path(config, file_name):
    """Return a configured file path."""
    return Path(config["files"][file_name])


def get_metric_setting(config, setting_name):
    """Return a derived-metric setting."""
    return config["derived_metrics"][setting_name]


def main():
    config = load_config()

    print("Configuration loaded successfully.")
    print(
        "Project:",
        config["project"]["name"],
    )

    print("\nConfigured series:")

    for series_name, details in config["series"].items():
        print(
            f"- {series_name}: "
            f"{details['id']} — "
            f"{details['label']}"
        )

    print("\nConfigured files:")

    for file_name, file_path in config["files"].items():
        print(f"- {file_name}: {file_path}")

    print("\nDerived-metric settings:")

    for setting_name, value in (
        config["derived_metrics"].items()
    ):
        print(f"- {setting_name}: {value}")


if __name__ == "__main__":
    main()