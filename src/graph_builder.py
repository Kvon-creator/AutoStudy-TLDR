"""Validated topic dependency graphs."""
import math
import networkx as nx


class TopicDependencyDAG:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_topic(self, topic_id, title, estimated_hours, deadline_week):
        if topic_id in self.graph:
            raise ValueError(f"Duplicate topic: {topic_id}")
        if not math.isfinite(estimated_hours) or estimated_hours <= 0:
            raise ValueError("Estimated hours must be finite and positive")
        if not isinstance(deadline_week, int) or deadline_week < 1:
            raise ValueError("Deadline week must be a positive integer")
        self.graph.add_node(topic_id, topic_id=topic_id, title=title,
                            estimated_hours=estimated_hours, deadline_week=deadline_week)

    def add_prerequisite(self, prerequisite, target):
        if prerequisite not in self.graph or target not in self.graph:
            raise ValueError("Both prerequisite topics must be added first")
        if self.graph.has_edge(prerequisite, target):
            return
        self.graph.add_edge(prerequisite, target)
        if not nx.is_directed_acyclic_graph(self.graph):
            self.graph.remove_edge(prerequisite, target)
            raise ValueError("Cycle detected in prerequisites")

    def prune_redundancies(self):
        reduced = nx.transitive_reduction(self.graph)
        reduced.add_nodes_from(self.graph.nodes(data=True))
        self.graph = reduced

    def get_study_sequence(self):
        return [dict(self.graph.nodes[node]) for node in nx.topological_sort(self.graph)]
