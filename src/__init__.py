"""
AutoStudy-TLDR: Prerequisite-aware syllabus parser and schedule optimizer.
"""

from src.baseline import LinearChronologicalBaseline
from src.evaluation import compute_prerequisite_inversions, compute_workload_variance
from src.exporters import export_schedule_to_ics, export_schedule_to_pdf
from src.graph_builder import TopicDependencyDAG
from src.scheduler import ScheduleAllocator
from src.syllabus import extract_text_from_pdf, parse_syllabus_pdf, parse_syllabus_text

__all__ = [
    "LinearChronologicalBaseline",
    "compute_prerequisite_inversions",
    "compute_workload_variance",
    "export_schedule_to_ics",
    "export_schedule_to_pdf",
    "ScheduleAllocator",
    "TopicDependencyDAG",
    "extract_text_from_pdf",
    "parse_syllabus_pdf",
    "parse_syllabus_text",
]

