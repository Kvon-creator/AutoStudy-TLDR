"""Parse course sections from Simple Syllabus exports without policy-list leakage."""
import re
from datetime import date
from pathlib import Path

from pypdf import PdfReader


def extract_text_from_pdf(path):
    return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)


def clean_lines(text):
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if not line or line.startswith("https://ncat.instructure.com/"):
            continue
        if re.match(r"^\d+/\d+/\d+.*,?\s+\d+:\d+\s+[AP]M", line):
            continue
        lines.append(line)
    return lines


def section(lines, heading, end_headings):
    for index, line in enumerate(lines):
        if line.lower() == heading.lower():
            result = []
            for following in lines[index + 1:]:
                if following.lower() in {end.lower() for end in end_headings}:
                    break
                result.append(following)
            return result
    return []


def parse_syllabus_text(text, source_name="syllabus.pdf", default_hours=3.0, default_weeks=15):
    lines = clean_lines(text)
    # Restrict all topic extraction to the course-specific portion of the export.
    if "University Policies" in lines:
        lines = lines[:lines.index("University Policies")]
    year_match = re.search(r"(?:Fall|Spring|Summer)\s+(\d{4})", text)
    year = int(year_match.group(1)) if year_match else None
    course_match = re.search(r"\bCOMP\s*(\d{3})", text)
    code = "COMP" + course_match.group(1) if course_match else Path(source_name).stem
    title = code
    for index, line in enumerate(lines):
        if "Course Syllabus" in line and index + 1 < len(lines):
            title = lines[index + 1]
            break
    prereq_lines = section(lines, "Course Prerequisites", ["Course Description"])
    course_prerequisites = sorted(set("COMP" + number for number in
        re.findall(r"COMP\s*(\d{3})", " ".join(prereq_lines))))
    description = " ".join(section(lines, "Course Description", [
        "Student Learning Objectives/Outcomes (SLO)", "Required Textbooks and Materials"]))
    topics, milestones = [], []
    notes = [f"Study effort defaults to {default_hours:g} hours per item unless explicitly stated.",
             "Dependency edges infer source order; the syllabus does not specify topic prerequisites."]

    def add_topic(item_title, origin, source_date=None, hours=None):
        topics.append({"topic_id": f"{code}_T{len(topics) + 1:02d}", "title": item_title,
                       "estimated_hours": default_hours if hours is None else hours,
                       "deadline_week": default_weeks, "raw_order": len(topics) + 1,
                       "source_section": origin, "source_date": source_date})

    schedule_lines = section(lines, "Class Schedule", ["Additional Course Information", "University Policies"])
    rows = []
    for line in schedule_lines:
        match = re.match(r"^(\d{1,2})/(\d{1,2})\s+(.+)$", line)
        if match:
            if year is None:
                raise ValueError("A syllabus year is required to interpret dated schedule entries")
            rows.append([date(year, int(match.group(1)), int(match.group(2))), match.group(3)])
        elif rows and not re.match(r"^(Date Subject|Homework, Exam)", line):
            rows[-1][1] += " " + line
    if rows:
        start = min(row[0] for row in rows)
        end = max(row[0] for row in rows)
        total_weeks = (end - start).days // 7 + 1
        for day, content in rows:
            source_date = day.isoformat()
            if re.search(r"\b(?:Midterm|Final) Exam\b", content, re.I):
                milestones.append({"title": content, "date": source_date, "kind": "exam"})
                continue
            homework = re.findall(r"\bHW\s*\d+\b", content)
            for assignment in homework:
                milestones.append({"title": assignment, "date": source_date,
                                   "kind": "scheduled homework", "note": "Listed on this class date; not confirmed as a due date."})
            content = re.sub(r"\bHW\s*\d+\b", "", content).strip()
            if content:
                add_topic(content, "Class Schedule", source_date)
                topics[-1]["deadline_week"] = (day - start).days // 7 + 1
        origin = "Class Schedule"
        notes.append("Weeks are seven-day periods starting at the first class date. Scheduled class dates act as study deadlines.")
    else:
        total_weeks, start, end = default_weeks, None, None
        pattern = re.compile(r"^(?:Week|Module|Unit|Chapter)\s+\d+[:\-\s]+(.+?)(?:\((\d+(?:\.\d+)?)\s*(?:hrs|hours)\))?$", re.I)
        seen = set()
        for line in lines:
            match = pattern.match(line)
            if match and line not in seen:
                seen.add(line)
                add_topic(match.group(1).strip(), "Module headings",
                          hours=float(match.group(2)) if match.group(2) else None)
        origin = "Module headings"
        if not topics:
            outcomes = section(lines, "Student Learning Objectives/Outcomes (SLO)", [
                "Career Competencies", "Required Textbooks and Materials", "Grading Scale"])
            items = []
            for line in outcomes:
                match = re.match(r"^\d+\.\s+(.+)", line)
                if match:
                    items.append(match.group(1))
                elif items:
                    items[-1] += " " + line
            for item in items:
                add_topic(item.replace("- ", "-"), "Student Learning Objectives/Outcomes (SLO)")
            origin = "Student Learning Objectives/Outcomes (SLO)"
            notes.append(f"No dated course outline was found; this is a suggested outcome-based study plan over an assumed {default_weeks}-week horizon, not the instructor's calendar.")
    edges = [(left["topic_id"], right["topic_id"]) for left, right in zip(topics, topics[1:])]
    return {"source_file": source_name, "course_code": code, "course_title": title,
            "course_description": description, "course_prerequisites": course_prerequisites,
            "topic_source": origin, "topics": topics, "prerequisites": edges,
            "milestones": milestones, "total_weeks": total_weeks,
            "start_date": start.isoformat() if start else None,
            "end_date": end.isoformat() if end else None, "assumptions": notes}


def parse_syllabus_pdf(path):
    return parse_syllabus_text(extract_text_from_pdf(path), Path(path).name)
