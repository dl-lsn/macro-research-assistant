import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


STAGES = {
    "fred": [
        "fred_data.py",
    ],
    "cpi": [
        "cpi_data.py",
    ],
    "treasury": [
        "treasury_data.py",
    ],
    "metrics": [
        "derived_metrics.py",
    ],
    "validate": [
        "validate_data.py",
    ],
    "context": [
        "fed_context.py",
    ],
    "analysis": [
        "structured_analysis.py",
    ],
    "report": [
        "generate_report.py",
    ],
}


FULL_PIPELINE = [
    "fred",
    "cpi",
    "treasury",
    "metrics",
    "validate",
    "context",
    "analysis",
    "report",
]


def run_script(script_name):
    """Run one project script and stop if it fails."""
    script_path = PROJECT_ROOT / script_name

    if not script_path.exists():
        raise FileNotFoundError(
            f"Required script not found: {script_name}"
        )

    print(f"\n--- Running {script_name} ---", flush=True)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{script_name} failed with exit code "
            f"{result.returncode}"
        )


def run_stage(stage_name):
    """Run one named stage."""
    for script_name in STAGES[stage_name]:
        run_script(script_name)


def run_full_pipeline():
    """Run every stage in sequence."""
    for stage_name in FULL_PIPELINE:
        run_stage(stage_name)


def build_parser():
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(
        description=(
            "Run the macroeconomic research project "
            "in full or by individual stage."
        )
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "all",
        help="Run the complete project.",
    )

    for stage_name in STAGES:
        subparsers.add_parser(
            stage_name,
            help=f"Run the {stage_name} stage.",
        )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "all":
            run_full_pipeline()
        else:
            run_stage(args.command)

        print("\nProject run completed successfully.")

    except KeyboardInterrupt:
        print("\nProject run cancelled.")
        sys.exit(130)

    except Exception as error:
        print(f"\nProject run failed: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()