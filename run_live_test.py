"""
Live Integration Test Runner for AutoStudy-TLDR (Checkpoint 2).

Ingests real or representative syllabus data, constructs the dependency DAG,
resolves topological ordering, allocates weekly pacing, and compares the
results directly against the linear chronological baseline.
"""

from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple

from src.baseline import LinearChronologicalBaseline
from src.evaluation import compute_prerequisite_inversions, compute_workload_variance
from src.graph_builder import TopicDependencyDAG
from src.scheduler import ScheduleAllocator


def parse_sample_raw_syllabus(filepath: str) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str]]]:
    """
    Parses a syllabus text file containing line-delimited topic specifications.
    
    Expected format per line:
      <Topic_ID> | <Title> | Hours: <Hours> | Prereq: <Prereq_ID_or_None>
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Cannot find syllabus file at: {filepath}")

    text = path.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    topics = []
    prereqs = []

    for line in lines:
        if line.startswith("#") or not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3:
            t_id = parts[0]
            title = parts[1]
            hours_str = parts[2].replace("Hours:", "").strip()
            hours = float(hours_str)
            topics.append({
                "topic_id": t_id,
                "title": title,
                "estimated_hours": hours,
                "deadline_week": 12
            })

            if len(parts) >= 4 and "Prereq:" in parts[3]:
                p_id = parts[3].replace("Prereq:", "").strip()
                if p_id and p_id.lower() != "none":
                    prereqs.append((p_id, t_id))

    return topics, prereqs


def create_mock_syllabus(filepath: str) -> None:
    """Creates a sample machine learning curriculum file if one does not exist."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_content = (
        "# AutoStudy Live Test Benchmark Syllabus\n"
        "# Out-of-order syllabus entries to verify DAG topological sorting\n"
        "CS_ML_04 | Deep Feedforward Networks | Hours: 4.0 | Prereq: CS_ML_03\n"
        "CS_ML_01 | Linear Algebra & Vector Spaces | Hours: 3.0 | Prereq: None\n"
        "CS_ML_03 | Gradient Descent & Backpropagation | Hours: 3.5 | Prereq: CS_ML_01\n"
        "CS_ML_02 | Probability & Continuous Distributions | Hours: 3.0 | Prereq: None\n"
        "CS_ML_06 | Transformers & Self-Attention | Hours: 4.5 | Prereq: CS_ML_05\n"
        "CS_ML_05 | Sequence Models & Recurrent Nets | Hours: 3.5 | Prereq: CS_ML_04\n"
    )
    path.write_text(sample_content, encoding="utf-8")


def main() -> None:
    syllabus_file = "data/raw_syllabi/sample_real_syllabus.txt"
    print(f"[*] Ingesting syllabus from: {syllabus_file}")

    try:
        topics, prereqs = parse_sample_raw_syllabus(syllabus_file)
    except FileNotFoundError:
        print("[!] File not found. Creating sample real-world curriculum file...")
        create_mock_syllabus(syllabus_file)
        topics, prereqs = parse_sample_raw_syllabus(syllabus_file)

    print(f"[+] Loaded {len(topics)} topics and {len(prereqs)} explicit prerequisite dependencies.\n")

    # 1. Baseline Evaluation
    print("================== 1. CHRONOLOGICAL BASELINE ==================")
    baseline = LinearChronologicalBaseline(weekly_study_capacity_hours=6.0)
    baseline_schedule = baseline.schedule(topics, total_weeks=6)
    base_pir = compute_prerequisite_inversions(baseline_schedule, prereqs)
    base_wsd = compute_workload_variance(baseline_schedule)

    for week, scheduled_topics in baseline_schedule.items():
        if scheduled_topics:
            week_str = ", ".join([f"{t['topic_id']} ({t['hours']}h)" for t in scheduled_topics])
            print(f"  Week {week:02d}: {week_str}")

    print(f"-> Baseline Prerequisite Inversion Rate (PIR): {base_pir * 100:.2f}%")
    print(f"-> Baseline Workload Variance (Std Dev):       {base_wsd:.2f} hrs\n")

    # 2. AutoStudy DAG Pipeline
    print("================== 2. AUTOSTUDY DAG PIPELINE ==================")
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
    dag_schedule = allocator.allocate(ordered_topics, total_weeks=6)
    dag_pir = compute_prerequisite_inversions(dag_schedule, prereqs)
    dag_wsd = compute_workload_variance(dag_schedule)

    for week, scheduled_topics in dag_schedule.items():
        if scheduled_topics:
            week_str = ", ".join([f"{t['topic_id']} ({t['hours']}h)" for t in scheduled_topics])
            print(f"  Week {week:02d}: {week_str}")

    print(f"-> AutoStudy Prerequisite Inversion Rate (PIR): {dag_pir * 100:.2f}%")
    print(f"-> AutoStudy Workload Variance (Std Dev):       {dag_wsd:.2f} hrs\n")

    # 3. Comparative Summary
    print("=================== 3. COMPARATIVE AUDIT ===================")
    print(f"PIR Reduction:       {(base_pir - dag_pir) * 100:.2f}% improvement")
    print(f"Workload Smoothing:  {(base_wsd - dag_wsd):.2f} hrs std dev difference")
    assert dag_pir == 0.0, "Validation failure: AutoStudy DAG contains prerequisite inversions!"
    print("[SUCCESS] AutoStudy DAG resolved all dependencies with 0 violations.")


if __name__ == "__main__":
    main()