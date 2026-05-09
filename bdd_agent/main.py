from __future__ import annotations

import argparse
from pathlib import Path

from bdd_agent.graph import run_agent



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate BDD feature files from Excel-based test cases."
    )
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="One or more Excel files containing test cases.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Directory where generated .feature files should be written.",
    )
    parser.add_argument(
        "--model",
        default="gpt-4.1-mini",
        help="OpenAI model to use when OPENAI_API_KEY is configured.",
    )
    return parser



def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_paths = [str(Path(path).expanduser().resolve()) for path in args.input]
    output_dir = str(Path(args.output).expanduser().resolve())

    result = run_agent(input_paths=input_paths, output_dir=output_dir, model=args.model)

    written_files = result.get("written_files", [])
    validation_errors = result.get("validation_errors", [])

    for path in written_files:
        print(f"Generated: {path}")

    if validation_errors:
        print("Validation warnings:")
        for error in validation_errors:
            print(f" - {error}")

    return 0
