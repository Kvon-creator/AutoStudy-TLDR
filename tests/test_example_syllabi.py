import json
from pathlib import Path

import pytest

from run_live_test import build_result, run_pipeline_on_pdf
from src.syllabus import parse_syllabus_pdf, parse_syllabus_text


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("code,count,prerequisite", [(365, 5, "COMP285"), (385, 27, "COMP360"), (440, 5, "COMP285")])
def test_actual_example_syllabi(code, count, prerequisite):
    parsed = parse_syllabus_pdf(ROOT / f"data/raw/raw_syllabi/Simple_Syllabus_COMP{code}.pdf")
    assert parsed["course_prerequisites"] == [prerequisite]
    assert len(parsed["topics"]) == count
    assert len({topic["topic_id"] for topic in parsed["topics"]}) == count
    assert not any("cheating" in topic["title"].lower() or "plagiarism" in topic["title"].lower()
                   for topic in parsed["topics"])
    result = build_result(parsed)
    assigned = [(week, topic) for week, topics in result["study_schedule"].items() for topic in topics]
    assert [topic["topic_id"] for _, topic in assigned] == [topic["topic_id"] for topic in parsed["topics"]]
    deadlines = {topic["topic_id"]: topic["deadline_week"] for topic in parsed["topics"]}
    assert all(week <= deadlines[topic["topic_id"]] for week, topic in assigned)
    assert all(sum(topic["hours"] for topic in topics) <= 6 for topics in result["study_schedule"].values())
    if code == 385:
        assert parsed["topic_source"] == "Class Schedule"
        assert parsed["total_weeks"] == 17
        assert parsed["topics"][2]["title"] == "Deterministic finite automata (DFA)"
        exams = [item for item in parsed["milestones"] if item["kind"] == "exam"]
        assert [item["date"] for item in exams] == ["2026-10-06", "2026-12-10"]
        assert len(parsed["milestones"]) == 10
    else:
        assert parsed["topic_source"] == "Student Learning Objectives/Outcomes (SLO)"
        assert all(topic["source_date"] is None for topic in parsed["topics"])


def test_outcomes_continue_across_page_headers_and_stop_before_policies():
    parsed = parse_syllabus_text("""Fall 2026 Course Syllabus
Example Course
Student Learning Objectives/Outcomes (SLO)
Upon the completion of this course:
1. Explain machine
10/4/26, 4:18 PM COMP 365 - Simple Syllabus
https://ncat.instructure.com/courses/123 2/16
learning.
2. Build models.
Required Textbooks and Materials
A book
University Policies
Academic Dishonesty Policy
1. Cheating
""")
    assert [topic["title"] for topic in parsed["topics"]] == ["Explain machine learning.", "Build models."]


def test_saved_reports_are_complete_and_machine_readable(tmp_path):
    source = ROOT / "data/raw/raw_syllabi/Simple_Syllabus_COMP385.pdf"
    result = run_pipeline_on_pdf(source, tmp_path)
    saved = json.loads((tmp_path / f"{source.stem}.json").read_text(encoding="utf-8"))
    assert len(saved["topics"]) == 27
    assert len(saved["milestones"]) == 10
    report = (tmp_path / f"{source.stem}.md").read_text(encoding="utf-8")
    assert all(topic["title"] in report for topic in result["topics"])
    assert "2026-12-10" in report
    assert "not confirmed as a due date" in report
    plain = (tmp_path / f"{source.stem}.txt").read_text(encoding="utf-8")
    assert "STUDY SCHEDULE" in plain
    assert "Week 17" in plain
    assert "2026-12-10" in plain
    assert "not confirmed as a due date" in " ".join(plain.split())
    assert all(topic["title"] in " ".join(plain.split()) for topic in result["topics"])
    assert all(len(line) <= 88 for line in plain.splitlines())


def test_insufficient_capacity_reports_failure():
    parsed = parse_syllabus_pdf(ROOT / "data/raw/raw_syllabi/Simple_Syllabus_COMP385.pdf")
    with pytest.raises(ValueError):
        build_result(parsed, capacity=3)
