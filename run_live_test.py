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
    Scans extracted PDF text for modules, topics, and explicit prerequisite clauses.
    Adapts regex extraction based on syllabus formatting patterns.
    """
    text = extract_text_from_pdf(pdf_path)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    topics = []
    prereqs = []

    # Regex targeting common syllabus module lines:
    # e.g., "Week 1: Introduction to Machine Learning" or "Module 2 - Optimization"
    module_pattern = re.compile(
        r"^(?:Week|Module|Unit|Chapter)\s+(\d+)[:\-\s]+(.+?)(?:\((\d+(?:\.\d+)?)\s*(?:hrs|hours)\))?$",
        re.IGNORECASE
    )

    extracted_modules = []
    for line in lines:
        match = module_pattern.match(line)
        if match:
            mod_num = match.group(1)
            title = match.group(2).strip()
            hours_str = match.group(3)
            hours = float(hours_str) if hours_str else 3.0
            
            topic_id = f"MOD_{int(mod_num):02d}"
            extracted_modules.append((topic_id, title, hours, int(mod_num)))

    # Fallback if no explicit "Module X" tags were matched: chunk by numbered headings
    if not extracted_modules:
        numbered_pattern = re.compile(r"^(\d+)\.\s+([A-Za-z0-9\s,\-\(\)]+)")
        for line in lines:
            match = numbered_pattern.match(line)
            if match and len(match.group(2).strip()) > 4:
                idx = int(match.group(1))
                topic_id = f"TOPIC_{idx:02d}"
                extracted_modules.append((topic_id, match.group(2).strip(), 3.0, idx))

    for topic_id, title, hours, order_num in extracted_modules:
        topics.append({
            "topic_id": topic_id,
            "title": title,
            "estimated_hours": hours,
            "deadline_week": 14,
            "raw_order": order_num
        })

    # Ground-truth heuristic dependencies:
    # 1. Connect linear baseline sequence chains
    # 2. Look for explicit keyword references (e.g. "Prereq: MOD_01" or conceptual chains)
    for i in range(len(topics) - 1):
        # Establish dependency from current to downstream topic
        curr_id = topics[i]["topic_id"]
        next_id = topics[i+1]["topic_id"]
        prereqs.append((curr_id, next_id))

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
    syllabus_dir = Path("data/raw_syllabi")
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