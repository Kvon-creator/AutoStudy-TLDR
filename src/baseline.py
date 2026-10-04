import re
from typing import List
from src.parser import CourseMilestone

def baseline_extract_milestones(text: str) -> List[CourseMilestone]:
    """
    Regex Baseline: Scans text for deadline keywords and date formats.
    """
    milestones = []
    lines = text.split("\n")
    
    date_pattern = r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}\b|\b\d{1,2}/\d{1,2}\b)"
    keyword_pattern = r"(exam|midterm|final|quiz|project|assignment|due)"

    for line in lines:
        if re.search(keyword_pattern, line, re.IGNORECASE):
            date_match = re.search(date_pattern, line, re.IGNORECASE)
            if date_match:
                milestones.append(
                    CourseMilestone(
                        title=line.strip()[:40],
                        date_str=date_match.group(1),
                        weight=0.0
                    )
                )
    return milestones