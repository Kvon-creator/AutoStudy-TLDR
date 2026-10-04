import pytest
from src.parser import TopicNode
from src.graph_engine import build_prerequisite_dag, get_topological_study_order

def test_topological_precedence():
    topics = [
        TopicNode(name="Calculus II", week=2, prerequisites=["Calculus I"]),
        TopicNode(name="Calculus I", week=1, prerequisites=[])
    ]
    dag = build_prerequisite_dag(topics)
    order = get_topological_study_order(dag)
    assert order.index("Calculus I") < order.index("Calculus II")

def test_cycle_detection():
    cyclic_topics = [
        TopicNode(name="Topic A", week=1, prerequisites=["Topic B"]),
        TopicNode(name="Topic B", week=2, prerequisites=["Topic A"])
    ]
    with pytest.raises(ValueError):
        build_prerequisite_dag(cyclic_topics)