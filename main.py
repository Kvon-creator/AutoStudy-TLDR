"""
AutoStudy + TLDR: Main Execution Entrypoint.

Standard entrypoint that parses course syllabi, builds prerequisite DAGs,
computes workload-balanced weekly schedules, and automatically exports:
  1. Printable PDF study schedules (.pdf)
  2. Google Calendar importable iCalendar schedules (.ics)
  3. Structured curriculum metadata (.json)
  4. Markdown summaries (.md)
  5. Formatted plain text (.txt)
"""

import argparse
from pathlib import Path
from typing import List

from run_live_test import schedule_syllabus


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    default_input = root_dir / "data" / "raw" / "raw_syllabi"
    default_output = root_dir / "test_outputs"

    parser = argparse.ArgumentParser(
        description="AutoStudy-TLDR: Automatically parse syllabi and generate study schedules (.pdf, .ics)."
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        default=default_input,
        help="Path to a syllabus PDF file or a directory containing syllabus PDFs (default: data/raw/raw_syllabi)."
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=default_output,
        help="Destination directory for generated schedules and calendar files (default: test_outputs)."
    )
    parser.add_argument(
        "-c", "--capacity",
        type=float,
        default=6.0,
        help="Weekly study budget in hours (default: 6.0 hrs/week)."
    )
    args = parser.parse_args()

    print("==========================================================")
    print("  AutoStudy + TLDR: Topological Syllabus Study Scheduler  ")
    print("==========================================================")

    # Resolve PDF files from file or folder input
    input_path = args.input.resolve()
    pdf_files: List[Path] = []
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        pdf_files = [input_path]
    elif input_path.is_dir():
        pdf_files = sorted(input_path.glob("*.pdf"))

    if not pdf_files:
        print(f"[!] No PDF syllabus files found at: {input_path}")
        return

    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Discovered {len(pdf_files)} syllabus file(s) to process.")
    print(f"Output Directory: {output_dir}")
    print(f"Study Capacity:   {args.capacity:g} hours/week\n")

    for pdf_path in pdf_files:
        schedule_syllabus(pdf_path, output_dir=output_dir, capacity=args.capacity, export_files=True)

    print("\n==========================================================")
    print("  Schedule Generation Complete (All Formats Ready)        ")
    print("==========================================================")
    print(f"Destination folder: {output_dir}\n")
    print("Generated artifacts per course:")
    print("  • Printable Study Schedule: <course>.pdf")
    print("  • Google Calendar Schedule: <course>.ics")
    print("  • Markdown & Text Reports:  <course>.md, <course>.txt")
    print("  • Machine-Readable Data:    <course>.json\n")
    print("Google Calendar Import Instructions:")
    print("  1. Open Google Calendar (https://calendar.google.com)")
    print("  2. Click the gear icon (Settings) -> Settings")
    print("  3. In the left sidebar, click 'Import & export'")
    print("  4. Upload your generated .ics file from test_outputs/")
    print("==========================================================")


if __name__ == "__main__":
    main()
