import pytest

from src.baseline import LinearChronologicalBaseline, baseline_extract_milestones
from src.evaluation import compute_workload_variance
from src.graph_builder import TopicDependencyDAG
from src.parser import extract_raw_text
from src.scheduler import ScheduleAllocator


def test_cycle_rejection_preserves_graph_and_pruning_preserves_metadata():
    dag = TopicDependencyDAG()
    for name in ("A", "B", "C"):
        dag.add_topic(name, name, 2, 3)
    for edge in (("A", "B"), ("B", "C"), ("A", "C")):
        dag.add_prerequisite(*edge)
    with pytest.raises(ValueError, match="Cycle"):
        dag.add_prerequisite("C", "A")
    dag.prune_redundancies()
    assert set(dag.graph.edges) == {("A", "B"), ("B", "C")}
    sequence = dag.get_study_sequence()
    assert [topic["topic_id"] for topic in sequence] == ["A", "B", "C"]
    assert all(topic["estimated_hours"] == 2 for topic in sequence)


@pytest.mark.parametrize("model", [ScheduleAllocator, LinearChronologicalBaseline])
def test_capacity_overflow_is_rejected(model):
    instance = model(3)
    method = instance.allocate if isinstance(instance, ScheduleAllocator) else instance.schedule
    topics = [{"topic_id": str(i), "title": "Topic", "estimated_hours": 3} for i in range(2)]
    with pytest.raises(ValueError, match="available weeks"):
        method(topics, total_weeks=1)
    topics[0]["estimated_hours"] = 4
    with pytest.raises(ValueError, match="capacity"):
        method(topics, total_weeks=2)


@pytest.mark.parametrize("capacity", [0, -1, float("nan"), float("inf")])
def test_invalid_capacity(capacity):
    with pytest.raises(ValueError):
        ScheduleAllocator(capacity)


def test_deadline_and_capacity():
    topics = [{"topic_id": str(i), "title": "Topic", "estimated_hours": 2,
               "deadline_week": 1} for i in range(2)]
    with pytest.raises(ValueError, match="deadline"):
        ScheduleAllocator(2).allocate(topics, total_weeks=2)
    schedule = ScheduleAllocator(4).allocate(topics, total_weeks=2)
    assert sum(topic["hours"] for topic in schedule[1]) == 4
    assert schedule[2] == []


def test_text_paths_and_milestones(tmp_path):
    path = tmp_path / "SYLLABUS.TXT"
    path.write_text("Week 1: Arrays\nAssignment 1 Due: Sep 18\nMidterm Exam: Oct 15\n", encoding="utf-8")
    milestones = baseline_extract_milestones(extract_raw_text(path))
    assert [(m.title, m.date_str) for m in milestones] == [
        ("Assignment 1 Due", "Sep 18"), ("Midterm Exam", "Oct 15")]


def test_empty_and_known_workload():
    assert compute_workload_variance({}) == 0
    assert compute_workload_variance({1: [{"hours": 4}], 2: []}) == 2
