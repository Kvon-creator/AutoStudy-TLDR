"""Evaluation metrics for weekly study schedules."""
from statistics import pstdev


def compute_prerequisite_inversions(schedule, prerequisites):
    """Fraction of scheduled prerequisite pairs assigned to reversed weeks."""
    topic_to_week = {topic["topic_id"]: week
                     for week, topics in schedule.items() for topic in topics}
    pairs = [(source, target) for source, target in prerequisites
             if source in topic_to_week and target in topic_to_week]
    if not pairs:
        return 0.0
    return sum(topic_to_week[source] > topic_to_week[target]
               for source, target in pairs) / len(pairs)


def compute_workload_variance(schedule):
    """Population standard deviation in hours (legacy function name)."""
    hours = [sum(topic.get("hours", 0.0) for topic in topics)
             for topics in schedule.values()]
    return pstdev(hours) if hours else 0.0
