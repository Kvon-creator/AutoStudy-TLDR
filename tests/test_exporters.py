"""
Tests for PDF and iCalendar (.ics) exporters.
"""

from pathlib import Path
from icalendar import Calendar
from pypdf import PdfReader

from run_live_test import build_result
from src.exporters import export_schedule_to_ics, export_schedule_to_pdf
from src.syllabus import parse_syllabus_pdf

ROOT = Path(__file__).resolve().parents[1]


def test_ics_export_produces_valid_calendar(tmp_path):
    parsed = parse_syllabus_pdf(ROOT / "data/raw/raw_syllabi/Simple_Syllabus_COMP385.pdf")
    result = build_result(parsed, capacity=6.0)

    ics_path = tmp_path / "schedule.ics"
    export_schedule_to_ics(result, ics_path)

    assert ics_path.exists()
    content = ics_path.read_bytes()
    assert len(content) > 0

    # Parse back with icalendar parser to strictly verify RFC 5545 compliance
    cal = Calendar.from_ical(content)
    events = [comp for comp in cal.walk() if comp.name == "VEVENT"]
    assert len(events) > 0

    summaries = [str(e.get("summary")) for e in events]
    # Check that both milestones and study items exist
    assert any("[COMP385] Midterm Exam" in s for s in summaries)
    assert any("[COMP385] Final Exam" in s for s in summaries)
    assert any("[Study] COMP385:" in s for s in summaries)

    # Every event must have UID, DTSTART, and DTSTAMP for Google Calendar compliance
    for e in events:
        assert e.get("uid") is not None
        assert e.get("dtstart") is not None
        assert e.get("dtstamp") is not None


def test_pdf_export_produces_valid_pdf(tmp_path):
    parsed = parse_syllabus_pdf(ROOT / "data/raw/raw_syllabi/Simple_Syllabus_COMP385.pdf")
    result = build_result(parsed, capacity=6.0)

    pdf_path = tmp_path / "schedule.pdf"
    export_schedule_to_pdf(result, pdf_path)

    assert pdf_path.exists()
    raw_bytes = pdf_path.read_bytes()
    assert raw_bytes.startswith(b"%PDF-")

    # Verify PDF is readable and extractable using pypdf
    reader = PdfReader(str(pdf_path))
    assert len(reader.pages) >= 1
    extracted_text = "\n".join(page.extract_text() for page in reader.pages)
    assert "COMP385: Theory of Computing" in extracted_text
    assert "Weekly Topological Study Schedule" in extracted_text
    assert "Deterministic finite automata" in extracted_text
    assert "Exam & Milestone Calendar" in extracted_text


def test_slo_course_exports_cleanly(tmp_path):
    parsed = parse_syllabus_pdf(ROOT / "data/raw/raw_syllabi/Simple_Syllabus_COMP365.pdf")
    result = build_result(parsed, capacity=6.0)

    ics_path = tmp_path / "comp365.ics"
    pdf_path = tmp_path / "comp365.pdf"

    export_schedule_to_ics(result, ics_path)
    export_schedule_to_pdf(result, pdf_path)

    assert ics_path.exists()
    assert pdf_path.exists()

    cal = Calendar.from_ical(ics_path.read_bytes())
    events = [comp for comp in cal.walk() if comp.name == "VEVENT"]
    assert len(events) == 5

    reader = PdfReader(str(pdf_path))
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert "COMP365: AI and Machine Learning" in text

