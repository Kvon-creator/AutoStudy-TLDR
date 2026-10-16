"""
AutoStudy + TLDR: Main Execution Entrypoint.
Processes raw syllabi from data/raw/raw_syllabi, constructs prerequisite DAGs,
and generates capacity-allocated weekly study schedules.
"""
from pathlib import Path
from run_live_test import run_pipeline_on_pdf


def main() -> None:
    print("==============================================")
    print(" AutoStudy + TLDR: Syllabus Study Scheduler   ")
    print("==============================================")

    root_dir = Path(__file__).resolve().parent
    raw_dir = root_dir / "data" / "raw" / "raw_syllabi"
    output_dir = root_dir / "test_outputs"

    pdf_files = sorted(raw_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"[!] No PDF syllabus files found in: {raw_dir}")
        return

    print(f"Discovered {len(pdf_files)} syllabus file(s) in {raw_dir.relative_to(root_dir)}:\n")
    for pdf_path in pdf_files:
        run_pipeline_on_pdf(pdf_path, output_dir=output_dir, capacity=6.0)

    print(f"\n[+] Processing complete. Reports and schedules saved to: {output_dir.relative_to(root_dir)}")


if __name__ == "__main__":
    main()
