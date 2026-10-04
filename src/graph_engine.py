import networkx as nx
from typing import List
from src.parser import TopicNode

def build_prerequisite_dag(topics: List[TopicNode]) -> nx.DiGraph:
    """
    Builds a Directed Acyclic Graph (DAG) using NetworkX.
    Ensures no circular prerequisite loops exist.
    """
    G = nx.DiGraph()

    for topic in topics:
        G.add_node(topic.name, week=topic.week)
        for prereq in topic.prerequisites:
            G.add_node(prereq)
            # Directed edge from prereq -> dependent topic
            G.add_edge(prereq, topic.name)

    if not nx.is_directed_acyclic_graph(G):
        cycles = list(nx.simple_cycles(G))
        raise ValueError(f"Cycle detected in prerequisites: {cycles}")

    return G

def get_topological_study_order(G: nx.DiGraph) -> List[str]:
    """Returns a study order where all prerequisites come before advanced topics."""
    return list(nx.topological_sort(G))