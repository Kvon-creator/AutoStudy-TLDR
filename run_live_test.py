"""
Live Integration Test Runner for AutoStudy-TLDR using real syllabus PDFs.
"""

from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Tuple
from pypdf import PdfReader

from src.baseline import LinearChronologicalBaseline
from src.evaluation import compute_prerequisite_inversions, compute_workload_variance
from src.graph_builder import TopicDependencyDAG
from src.scheduler import ScheduleAllocator


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extracts raw text content across all pages in a syllabus PDF."""
    reader = PdfReader(str(pdf_path))
    full_text = []
    for idx, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            full_text.append(page_text)
    return "\n".join(full_text)


def parse_syllabus_pdf(pdf_path: Path) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str]]]:
    """
    Extracts structured topics from course syllabus PDFs:
    1. Standard Module/Week patterns.
    2. Date-based 'Class Schedule' tables (e.g., Simple Syllabus COMP385).
    3. Targeted 'Course Description' concept lists (for COMP365, COMP440).
    """
    text = extract_text_from_pdf(pdf_path)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    extracted_modules = []
    seen_titles = set()

    # Pattern 1: Week / Module / Chapter headings
    module_pattern = re.compile(
        r"^(?:Week|Module|Unit|Chapter)\s+(\d+)[:\-\s]+(.+?)(?:\((\d+(?:\.\d+)?)\s*(?:hrs|hours)\))?$",
        re.IGNORECASE
    )

    # Pattern 2: Date-based schedule rows (e.g., '8/27', '$8/27$', '10/22 | Time Complexity')
    date_schedule_pattern = re.compile(
        r"^\$?(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\$?\s*(?:\|\s*)?([A-Za-z].*)$"
    )

    in_schedule_section = False
    schedule_counter = 1

    for line in lines:
        # Toggle schedule section context
        if re.search(r"class\s+schedule|course\s+schedule", line, re.IGNORECASE):
            in_schedule_section = True
            continue
        if in_schedule_section and re.search(r"university\s+policies|additional\s+course\s+information", line, re.IGNORECASE):
            in_schedule_section = False

        # Try Week/Module pattern
        m_match = module_pattern.match(line)
        if m_match:
            mod_num = int(m_match.group(1))
            title = m_match.group(2).strip()
            if title.lower() not in seen_titles:
                seen_titles.add(title.lower())
                extracted_modules.append((f"MOD_{mod_num:02d}", title, 3.0, mod_num))
            continue

        # Try Schedule table pattern if in schedule section or matches date format
        if in_schedule_section:
            d_match = date_schedule_pattern.match(line)
            if d_match:
                raw_title = d_match.group(2).split("|")[0].strip()
                # Exclude administrative and non-topic rows
                if raw_title.lower() not in seen_titles and not any(
                    k in raw_title.lower() for k in ["exam", "recess", "break", "holiday", "subject", "reading"]
                ) and len(raw_title) > 3:
                    seen_titles.add(raw_title.lower())
                    extracted_modules.append((f"SCHED_{schedule_counter:02d}", raw_title, 2.5, schedule_counter))
                    schedule_counter += 1

    # Pattern 3: Fallback for syllabi without schedule tables (COMP365, COMP440)
    # Extracts conceptual units from the Course Description block
    if not extracted_modules:
        desc_match = re.search(
            r"Course Description\s+(.*?)(?:Student Learning Objectives|Career Competencies|Required Textbooks)",
            text,
            re.DOTALL | re.IGNORECASE
        )
        if desc_match:
            desc_text = desc_match.group(1).replace("\n", " ")
            # Match clauses like "covers the concepts related to X, Y, and Z" or "Topics will include A, B, C"
            topics_clause = re.search(
                r"(?:covers the concepts related to|Topics will include)\s+([^.]+)",
                desc_text,
                re.IGNORECASE
            )
            if topics_clause:
                raw_items = re.split(r",\s*(?:and\s+)?|\s+and\s+", topics_clause.group(1))
                clause_counter = 1
                for item in raw_items:
                    cleaned_item = item.strip()
                    if len(cleaned_item) > 3 and cleaned_item.lower() not in seen_titles:
                        seen_titles.add(cleaned_item.lower())
                        extracted_modules.append((f"TOPIC_{clause_counter:02d}", cleaned_item.title(), 3.0, clause_counter))
                        clause_counter += 1

    topics = [
        {
            "topic_id": t_id,
            "title": title,
            "estimated_hours": hours,
            "deadline_week": 14,
            "raw_order": order_num
        }
        for t_id, title, hours, order_num in extracted_modules
    ]

    prereqs = [
        (topics[i]["topic_id"], topics[i + 1]["topic_id"])
        for i in range(len(topics) - 1)
    ]

    return topics, prereqs


def run_pipeline_on_pdf(pdf_path: Path):
    print(f"\n=======================================================")
    print(f"[*] Processing Real Syllabus: {pdf_path.name}")
    print(f"=======================================================")

    topics, prereqs = parse_syllabus_pdf(pdf_path)

    if not topics:
        print(f"[!] Warning: No structured modules detected in {pdf_path.name}.")
        print("    Ensure your syllabus text contains recognizable 'Week X:', 'Module X:', or numbered headings.")
        return

    print(f"[+] Extracted {len(topics)} topics/modules and {len(prereqs)} sequential dependencies.")

    # 1. Baseline Evaluation (Simulates out-of-order student study attempt or raw document order)
    print("\n--- 1. Linear Chronological Baseline ---")
    baseline = LinearChronologicalBaseline(weekly_study_capacity_hours=6.0)
    baseline_schedule = baseline.schedule(topics, total_weeks=10)
    base_pir = compute_prerequisite_inversions(baseline_schedule, prereqs)
    base_wsd = compute_workload_variance(baseline_schedule)
    print(f"  Baseline Prerequisite Inversion Rate (PIR): {base_pir * 100:.2f}%")
    print(f"  Baseline Workload Variance (Std Dev):       {base_wsd:.2f} hrs")

    # 2. AutoStudy DAG Pipeline
    print("\n--- 2. AutoStudy DAG Topological Pacing ---")
    dag = TopicDependencyDAG()
    for t in topics:
        dag.add_topic(
            t["topic_id"],
            title=t["title"],
            estimated_hours=t["estimated_hours"],
            deadline_week=t["deadline_week"]
        )

    for u, v in prereqs:
        dag.add_prerequisite(u, v)

    dag.prune_redundancies()
    ordered_topics = dag.get_study_sequence()

    allocator = ScheduleAllocator(weekly_study_capacity_hours=6.0)
    dag_schedule = allocator.allocate(ordered_topics, total_weeks=10)
    dag_pir = compute_prerequisite_inversions(dag_schedule, prereqs)
    dag_wsd = compute_workload_variance(dag_schedule)

    print(f"  AutoStudy Prerequisite Inversion Rate (PIR): {dag_pir * 100:.2f}%")
    print(f"  AutoStudy Workload Variance (Std Dev):       {dag_wsd:.2f} hrs")

    # Display Allocated Study Blocks
    print("\n  Generated Study Schedule (First 4 Weeks):")
    for week in range(1, 5):
        if week in dag_schedule and dag_schedule[week]:
            assigned = ", ".join([f"{t['topic_id']}: {t['title']} ({t['hours']}h)" for t in dag_schedule[week]])
            print(f"    Week {week:02d}: {assigned}")


def main():
    syllabus_dir = Path("data/raw/raw_syllabi")
    pdf_files = list(syllabus_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"[!] No PDF files found in {syllabus_dir.resolve()}.")
        print("    Drop your course PDF files into 'data/raw_syllabi/' and rerun.")
        sys.exit(1)

    print(f"Found {len(pdf_files)} PDF syllabus file(s) for live testing.")
    for pdf_path in pdf_files:
        run_pipeline_on_pdf(pdf_path)


if __name__ == "__main__":
    main()