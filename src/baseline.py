"""
Baseline Model for Checkpoint 2 Comparison.
Implements a naive chronological linear scheduler that assumes topics must simply
be scheduled in the raw order of appearance in the syllabus without topological
dependency resolution or prerequisite capacity balancing.
"""

from typing import List, Dict, Any
import re
from src.parser import CourseMilestone
from src.scheduler import ScheduleAllocator


def baseline_extract_milestones(text: str) -> List[CourseMilestone]:
    """Extract milestone lines containing a month and day."""
    pattern = re.compile(
        r"^\s*(?P<title>[^\n:]+):\s*(?P<date>(?:Jan(?:uary)?|Feb(?:ruary)?|"
        r"Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
        r"Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
        r"\s+\d{1,2}(?:,?\s+\d{4})?)\s*$", re.MULTILINE | re.IGNORECASE)
    return [CourseMilestone(title=match.group("title").strip(),
                            date_str=match.group("date"))
            for match in pattern.finditer(text)]

class LinearChronologicalBaseline:
    def __init__(self, weekly_study_capacity_hours: float = 6.0):
        self.capacity = ScheduleAllocator(weekly_study_capacity_hours).capacity

    def schedule(self, raw_topics: List[Dict[str, Any]], total_weeks: int = 15) -> Dict[int, List[Dict[str, Any]]]:
        """
        Sequentially packs topics into weeks based on order of appearance.
        Does not check prerequisites or transitive relationships.
        """
        # Preserve raw order without resolving prerequisites or deadlines.
        topics = [{key: value for key, value in topic.items() if key != "deadline_week"}
                  for topic in raw_topics]
        return ScheduleAllocator(self.capacity).allocate(topics, total_weeks)
