"""
Evaluation metrics for comparing DAG Topological Pacing vs Linear Baseline.
Metrics:
1. Prerequisite Inversion Rate (PIR): Percentage of prerequisite pairs scheduled out of order.
2. Workload Standard Deviation (WSD): Variance of assigned study hours across weeks.
"""

import numpy as np
from typing import List, Dict, Tuple, Any

def compute_prerequisite_inversions(
    schedule: Dict[int, List[Dict[str, Any]]], 
    prerequisites: List[Tuple[str, str]]
) -> float:
    """
    Computes fraction of edges (u -> v) where week(u) > week(v).
    """
    if not prerequisites:
        return 0.0

    topic_to_week = {}
    for week, topics in schedule.items():
        for t in topics:
            topic_to_week[t["topic_id"]] = week

    inversions = 0
    valid_pairs = 0

    for prereq, target in prerequisites:
        if prereq in topic_to_week and target in topic_to_week:
            valid_pairs += 1
            if topic_to_week[prereq] > topic_to_week[target]:
                inversions += 1

    return (inversions / valid_pairs) if valid_pairs > 0 else 0.0

def compute_workload_variance(schedule: Dict[int, List[Dict[str, Any]]]) -> float:
    """Computes standard deviation of weekly allocated hours."""
    weekly_hours = [
        sum(t.get("hours", 0.0) for t in topics)
        for topics in schedule.values()
    ]
    return float(np.std(weekly_hours))