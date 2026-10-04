"""Allocate an ordered study sequence within weekly capacity."""
import math


class ScheduleAllocator:
    def __init__(self, weekly_study_capacity_hours=6.0):
        if not math.isfinite(weekly_study_capacity_hours) or weekly_study_capacity_hours <= 0:
            raise ValueError("Weekly capacity must be finite and positive")
        self.capacity = weekly_study_capacity_hours

    def allocate(self, ordered_topics, total_weeks=15):
        if not isinstance(total_weeks, int) or total_weeks < 1:
            raise ValueError("Total weeks must be a positive integer")
        schedule = {week: [] for week in range(1, total_weeks + 1)}
        week, used_hours = 1, 0.0
        for topic in ordered_topics:
            hours = topic.get("estimated_hours", 2.0)
            if not math.isfinite(hours) or hours <= 0 or hours > self.capacity:
                raise ValueError("Topic hours must be positive and fit weekly capacity")
            if used_hours + hours > self.capacity:
                week += 1
                used_hours = 0.0
            if week > total_weeks:
                raise ValueError("Study sequence exceeds available weeks")
            if week > topic.get("deadline_week", total_weeks):
                raise ValueError(f"Cannot meet deadline for {topic['topic_id']}")
            schedule[week].append({"topic_id": topic["topic_id"],
                                   "title": topic["title"], "hours": hours})
            used_hours += hours
        return schedule
