import json
from pathlib import Path


REGISTRY_FILE = Path("source_registry.json")
REPORT_FILE = Path(
    "source_discipline_report.txt"
)


REQUIRED_DATA_FIELDS = [
    "name",
    "series_id",
    "provider",
    "database",
    "source_institution",
    "frequency",
    "units",
    "role",
]


def load_registry():
    """Load the source registry."""
    if not REGISTRY_FILE.exists():
        raise FileNotFoundError(
            f"Missing source registry: {REGISTRY_FILE}"
        )

    with REGISTRY_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def validate_data_sources(registry):
    """Validate required metadata for FRED series."""
    errors = []

    data_sources = registry.get(
        "data_sources",
        {},
    )

    if not data_sources:
        errors.append(
            "No data sources are registered."
        )

    for source_name, source in data_sources.items():
        for field in REQUIRED_DATA_FIELDS:
            if not source.get(field):
                errors.append(
                    f"{source_name}: missing field "
                    f"'{field}'"
                )

    return errors


def validate_official_documents(registry):
    """Validate official-document metadata."""
    errors = []

    documents = registry.get(
        "official_documents",
        {},
    )

    if not documents:
        errors.append(
            "No official documents are registered."
        )

    for document_name, document in documents.items():
        required_fields = [
            "name",
            "provider",
            "document_type",
            "role",
        ]

        for field in required_fields:
            if not document.get(field):
                errors.append(
                    f"{document_name}: missing field "
                    f"'{field}'"
                )

    return errors


def validate_derived_data(registry):
    """Validate derived-data metadata."""
    errors = []

    derived_data = registry.get(
        "derived_data",
        {},
    )

    for data_name, data in derived_data.items():
        if not data.get("file"):
            errors.append(
                f"{data_name}: missing file"
            )

        if not data.get("methods"):
            errors.append(
                f"{data_name}: missing methods"
            )

        if not data.get("role"):
            errors.append(
                f"{data_name}: missing role"
            )

    return errors


def validate_interpretation(registry):
    """Validate interpretation metadata."""
    errors = []

    interpretation = registry.get(
        "interpretation",
        {},
    )

    for output_name, output in interpretation.items():
        if not output.get("file"):
            errors.append(
                f"{output_name}: missing file"
            )

        if output.get("model_output") is not True:
            errors.append(
                f"{output_name}: model_output must be true"
            )

        if not output.get("warning"):
            errors.append(
                f"{output_name}: missing warning"
            )

    return errors


def build_report(
    registry,
    errors,
):
    """Build the source-discipline report."""
    data_sources = registry.get(
        "data_sources",
        {},
    )

    documents = registry.get(
        "official_documents",
        {},
    )

    derived_data = registry.get(
        "derived_data",
        {},
    )

    interpretation = registry.get(
        "interpretation",
        {},
    )

    lines = [
        "Source Discipline Report",
        "=======================",
        "",
        "Evidence categories:",
        "- FRED numerical observations",
        "- Official Federal Reserve documents",
        "- Project-derived calculations",
        "- Gemini interpretation",
        "",
        "Registered FRED data sources:",
    ]

    for source_name, source in data_sources.items():
        lines.append(
            f"- {source_name}: "
            f"{source['series_id']} | "
            f"{source['frequency']} | "
            f"{source['units']} | "
            f"{source['source_institution']}"
        )

    lines.extend(
        [
            "",
            "Registered official documents:",
        ]
    )

    for document_name, document in documents.items():
        lines.append(
            f"- {document_name}: "
            f"{document['provider']} | "
            f"{document['document_type']}"
        )

    lines.extend(
        [
            "",
            "Registered derived datasets:",
        ]
    )

    for data_name, data in derived_data.items():
        lines.append(
            f"- {data_name}: "
            f"{data['file']} | "
            f"{data['role']}"
        )

    lines.extend(
        [
            "",
            "Registered interpretation outputs:",
        ]
    )

    for output_name, output in interpretation.items():
        lines.append(
            f"- {output_name}: "
            f"{output['file']} | "
            f"{output['role']}"
        )

    lines.extend(
        [
            "",
            "Validation result:",
        ]
    )

    if errors:
        lines.append("FAILED")

        for error in errors:
            lines.append(f"- {error}")
    else:
        lines.append(
            "PASSED: all required source metadata exists."
        )

    REPORT_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main():
    registry = load_registry()

    errors = []
    errors.extend(
        validate_data_sources(registry)
    )
    errors.extend(
        validate_official_documents(registry)
    )
    errors.extend(
        validate_derived_data(registry)
    )
    errors.extend(
        validate_interpretation(registry)
    )

    build_report(
        registry,
        errors,
    )

    print(f"Saved: {REPORT_FILE}")

    if errors:
        print("Source validation failed.")

        for error in errors:
            print(f"- {error}")

        raise ValueError(
            "Source registry contains errors."
        )

    print(
        "Source validation passed: "
        "all metadata is present."
    )


if __name__ == "__main__":
    main()