"""
iCalendar (.ics) Exporter for AutoStudy-TLDR.
Produces RFC 5545-compliant calendar files compatible with Google Calendar,
Apple Calendar, and Microsoft Outlook.
"""

from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast
import uuid

from icalendar import Calendar, Event


def export_schedule_to_ics(
    result: Dict[str, Any],
    output_path: Union[str, Path],
    semester_start_date: Optional[date] = None,
    study_start_hour: int = 18,
) -> Path:
    """
    Exports the generated study schedule and milestones to an RFC 5545 .ics file.

    Parameters:
        result: The dictionary returned by build_result().
        output_path: Path where the .ics file should be written.
        semester_start_date: Optional base date for courses without explicit dates.
        study_start_hour: Hour of the day (24h) to schedule study sessions (default: 18:00 / 6 PM).

    Returns:
        Path to the saved .ics file.
    """
    cal = Calendar()
    cal.add("prodid", "-//AutoStudy-TLDR//Study Schedule Generator//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", f"{result['course_code']} Study Schedule")
    cal.add("x-wr-timezone", "UTC")

    now_utc = datetime.now(timezone.utc)
    course_code = result.get("course_code", "COURSE")
    course_title = result.get("course_title", "")

    # 1. Determine base semester start date
    if semester_start_date is not None:
        base_date = semester_start_date
    elif result.get("start_date"):
        base_date = date.fromisoformat(result["start_date"])
    else:
        base_date = date.today()

    # 2. Add Milestones (Exams and Homework)
    milestones = cast(List[Dict[str, Any]], result.get("milestones", []))
    for m in milestones:
        m_date_str = m.get("date")
        if not m_date_str:
            continue

        m_date = date.fromisoformat(m_date_str)
        kind = m.get("kind", "Milestone").capitalize()
        title = m.get("title", "Milestone")
        note = m.get("note", "")

        event = Event()
        event.add("summary", f"[{course_code}] {title}")
        desc_lines = [
            f"Course: {course_code} - {course_title}",
            f"Type: {kind}",
        ]
        if note:
            desc_lines.append(f"Note: {note}")
        event.add("description", "\n".join(desc_lines))

        # All-day event for milestones
        event.add("dtstart", m_date)
        event.add("dtend", m_date + timedelta(days=1))

        # Deterministic UUID for idempotency
        uid_seed = f"{course_code}_milestone_{title}_{m_date_str}"
        event.add("uid", str(uuid.uuid5(uuid.NAMESPACE_DNS, uid_seed)))
        event.add("dtstamp", now_utc)

        if "exam" in kind.lower():
            event.add("categories", ["EXAM", "ACADEMIC"])
            event.add("priority", 1)
        else:
            event.add("categories", ["ASSIGNMENT", "HOMEWORK"])
            event.add("priority", 2)

        cal.add_component(event)

    # 3. Add Weekly Study Schedule Allocations
    study_schedule = cast(Dict[int, List[Dict[str, Any]]], result.get("study_schedule", {}))
    topics_list = cast(List[Dict[str, Any]], result.get("topics", []))
    topic_by_id = {t["topic_id"]: t for t in topics_list}

    # Stagger offsets across days of the week: Tuesday, Thursday, Saturday, Monday, Wednesday, Friday
    day_offsets = [1, 3, 5, 0, 2, 4]

    for week_num, assigned_topics in study_schedule.items():
        if not assigned_topics:
            continue

        week_start = base_date + timedelta(weeks=week_num - 1)

        for idx, topic in enumerate(assigned_topics):
            topic_id = topic["topic_id"]
            topic_meta = topic_by_id.get(topic_id, {})
            source_date_str = topic_meta.get("source_date")

            # If the topic has an explicit class schedule date, align study session to that date
            if source_date_str:
                study_date = date.fromisoformat(source_date_str)
            else:
                offset = day_offsets[idx % len(day_offsets)]
                study_date = week_start + timedelta(days=offset)

            hours = float(topic.get("hours", 3.0))
            start_dt = datetime.combine(study_date, time(hour=study_start_hour, minute=0))
            end_dt = start_dt + timedelta(hours=hours)

            event = Event()
            event.add("summary", f"[Study] {course_code}: {topic['title']}")
            desc_lines = [
                f"Course: {course_code} - {course_title}",
                f"Topic: {topic['title']}",
                f"Topic ID: {topic_id}",
                f"Allocated Study Time: {hours:g} hours",
                f"Curriculum Week: {week_num}",
            ]
            if source_date_str:
                desc_lines.append(f"Target Class Date: {source_date_str}")
            event.add("description", "\n".join(desc_lines))

            event.add("dtstart", start_dt)
            event.add("dtend", end_dt)

            uid_seed = f"{course_code}_w{week_num}_{topic_id}_{idx}"
            event.add("uid", str(uuid.uuid5(uuid.NAMESPACE_DNS, uid_seed)))
            event.add("dtstamp", now_utc)
            event.add("categories", ["STUDY", "EDUCATION"])

            cal.add_component(event)

    # 4. Save to disk
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_bytes(cal.to_ical())
    return out_file

