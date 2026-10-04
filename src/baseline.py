"""
Baseline Model for Checkpoint 2 Comparison.
Implements a naive chronological linear scheduler that assumes topics must simply
be scheduled in the raw order of appearance in the syllabus without topological
dependency resolution or prerequisite capacity balancing.
"""

from typing import List, Dict, Any

class LinearChronologicalBaseline:
    def __init__(self, weekly_study_capacity_hours: float = 6.0):
        self.capacity = weekly_study_capacity_hours

    def schedule(self, raw_topics: List[Dict[str, Any]], total_weeks: int = 15) -> Dict[int, List[Dict[str, Any]]]:
        """
        Sequentially packs topics into weeks based on order of appearance.
        Does not check prerequisites or transitive relationships.
        """
        schedule = {week: [] for week in range(1, total_weeks + 1)}
        current_week = 1
        current_week_hours = 0.0

        for topic in raw_topics:
            hours = topic.get("estimated_hours", 2.0)
            if current_week_hours + hours > self.capacity and current_week < total_weeks:
                current_week += 1
                current_week_hours = 0.0

            schedule[current_week].append({
                "topic_id": topic["topic_id"],
                "title": topic["title"],
                "hours": hours
            })
            current_week_hours += hours

        return schedule