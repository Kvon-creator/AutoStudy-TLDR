import pytest
from src.graph_builder import TopicDependencyDAG
from src.scheduler import ScheduleAllocator
from src.baseline import LinearChronologicalBaseline
from src.evaluation import compute_prerequisite_inversions, compute_workload_variance

def test_checkpoint2_comparative_benchmark():
    # 1. Setup sample curriculum with a known out-of-order syllabus declaration
    topics = [
        {"topic_id": "T3", "title": "Deep Neural Networks", "estimated_hours": 3.0, "deadline_week": 8},
        {"topic_id": "T1", "title": "Linear Algebra & Matrices", "estimated_hours": 3.0, "deadline_week": 4},
        {"topic_id": "T2", "title": "Gradient Descent Optimization", "estimated_hours": 3.0, "deadline_week": 6},
    ]
    prereqs = [("T1", "T2"), ("T2", "T3")]

    # 2. Run Baseline (preserves naive raw syllabus order T3 -> T1 -> T2)
    baseline_model = LinearChronologicalBaseline(weekly_study_capacity_hours=3.0)
    baseline_sched = baseline_model.schedule(topics, total_weeks=6)
    baseline_pir = compute_prerequisite_inversions(baseline_sched, prereqs)

    # 3. Run AutoStudy DAG Pipeline
    dag = TopicDependencyDAG()
    for t in topics:
        dag.add_topic(t["topic_id"], t["title"], t["estimated_hours"], t["deadline_week"])
    for u, v in prereqs:
        dag.add_prerequisite(u, v)

    dag.prune_redundancies()
    ordered = dag.get_study_sequence()
    allocator = ScheduleAllocator(weekly_study_capacity_hours=3.0)
    dag_sched = allocator.allocate(ordered, total_weeks=6)
    dag_pir = compute_prerequisite_inversions(dag_sched, prereqs)

    # Topological sorting must eliminate prerequisite inversions
    assert dag_pir == 0.0
    assert baseline_pir > 0.0