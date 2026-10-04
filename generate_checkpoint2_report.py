"""
Checkpoint 2 Technical Artifact & Report Runner
Executes evaluation on 10 course curricula benchmarks and formats the Checkpoint 2 report.
"""

from statistics import mean
from src.graph_builder import TopicDependencyDAG
from src.scheduler import ScheduleAllocator
from src.baseline import LinearChronologicalBaseline
from src.evaluation import compute_prerequisite_inversions, compute_workload_variance

def run_benchmark():
    total_test_cases = 10
    baseline_pirs, dag_pirs = [], []
    baseline_wsds, dag_wsds = [], []

    for case_id in range(total_test_cases):
        num_topics = 8
        raw_topics = [
            {"topic_id": f"C{case_id}_T{i}", "title": f"Module {i}", "estimated_hours": 2.5, "deadline_week": 12}
            for i in range(num_topics)
        ]
        
        # Ground truth DAG chains (e.g., T0 -> T1, T1 -> T2, etc.)
        prereqs = [(f"C{case_id}_T{i}", f"C{case_id}_T{i+1}") for i in range(num_topics - 1)]

        # Simulate scrambled syllabus ordering
        scrambled_topics = list(reversed(raw_topics))

        # Baseline
        baseline = LinearChronologicalBaseline(weekly_study_capacity_hours=5.0)
        b_sched = baseline.schedule(scrambled_topics, total_weeks=10)
        baseline_pirs.append(compute_prerequisite_inversions(b_sched, prereqs))
        baseline_wsds.append(compute_workload_variance(b_sched))

        # AutoStudy DAG
        dag = TopicDependencyDAG()
        for t in scrambled_topics:
            dag.add_topic(t["topic_id"], t["title"], t["estimated_hours"], t["deadline_week"])
        for u, v in prereqs:
            dag.add_prerequisite(u, v)
        dag.prune_redundancies()
        
        allocator = ScheduleAllocator(weekly_study_capacity_hours=5.0)
        d_sched = allocator.allocate(dag.get_study_sequence(), total_weeks=10)
        dag_pirs.append(compute_prerequisite_inversions(d_sched, prereqs))
        dag_wsds.append(compute_workload_variance(d_sched))

    print("================ CHECKPOINT 2 BENCHMARK RESULTS ================")
    print(f"Total Test Cases Evaluated: {total_test_cases}")
    print(f"Baseline Mean Prereq Inversion Rate (PIR): {mean(baseline_pirs)*100:.2f}%")
    print(f"AutoStudy DAG Mean Prereq Inversion Rate:   {mean(dag_pirs)*100:.2f}%")
    print(f"Baseline Workload Std Dev (hrs):           {mean(baseline_wsds):.2f}")
    print(f"AutoStudy Workload Std Dev (hrs):          {mean(dag_wsds):.2f}")
    print("=================================================================")

if __name__ == "__main__":
    run_benchmark()
