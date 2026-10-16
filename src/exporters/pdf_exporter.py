"""
PDF Exporter for AutoStudy-TLDR.
Generates clean, professional, publication-quality printable study schedules
using ReportLab.
"""

from pathlib import Path
from typing import Any, Dict, List, Union, cast

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _add_page_decorations(canvas, doc):
    """Draws running header and footer with page numbers."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#718096"))
    # Footer
    canvas.drawString(36, 20, "AutoStudy-TLDR — Topological Study Plan")
    canvas.drawRightString(doc.pagesize[0] - 36, 20, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def export_schedule_to_pdf(
    result: Dict[str, Any],
    output_path: Union[str, Path],
) -> Path:
    """
    Renders the study schedule, milestones, and pacing audit into a styled PDF.

    Parameters:
        result: The dictionary returned by build_result().
        output_path: Destination path for the generated PDF.

    Returns:
        Path to the saved PDF file.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Margins: 36 pt (0.5 inch). Printable width: 612 - 72 = 540 pt.
    doc = SimpleDocTemplate(
        str(out_file),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4A5568"),
    )

    section_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=12,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#2D3748"),
    )

    meta_label_style = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#4A5568"),
    )

    meta_value_style = ParagraphStyle(
        "MetaValue",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#1A202C"),
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    story = []

    # 1. Header Banner
    course_code = result.get("course_code", "COURSE")
    course_title = result.get("course_title", "")
    story.append(Paragraph(f"{course_code}: {course_title}", title_style))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            f"Source Document: <b>{result.get('source_file', 'Syllabus')}</b> &nbsp;|&nbsp; "
            f"Topic Source: <b>{result.get('topic_source', 'Extracted')}</b>",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=10))

    # 2. Metadata / Parameters Grid
    metrics = result.get("metrics", {}).get("autostudy", {})
    pir_val = metrics.get("prerequisite_inversion_rate", 0.0)
    wsd_val = metrics.get("workload_standard_deviation_hours", 0.0)
    prereqs_str = ", ".join(result.get("course_prerequisites", [])) or "None stated"

    meta_data = [
        [
            Paragraph("Course Prerequisites:", meta_label_style),
            Paragraph(prereqs_str, meta_value_style),
            Paragraph("Curriculum Horizon:", meta_label_style),
            Paragraph(f"{result.get('total_weeks', 15)} Weeks", meta_value_style),
        ],
        [
            Paragraph("Weekly Study Budget:", meta_label_style),
            Paragraph(f"{result.get('weekly_capacity_hours', 6.0):g} hours/week", meta_value_style),
            Paragraph("Prereq Inversion Rate (PIR):", meta_label_style),
            Paragraph(f"<b>{pir_val:.2%}</b> (0 inversions)", meta_value_style),
        ],
        [
            Paragraph("Workload Std Dev:", meta_label_style),
            Paragraph(f"{wsd_val:.2f} hours", meta_value_style),
            Paragraph("Date Range:", meta_label_style),
            Paragraph(f"{result.get('start_date') or 'N/A'} to {result.get('end_date') or 'N/A'}", meta_value_style),
        ],
    ]

    meta_table = Table(meta_data, colWidths=[110, 160, 130, 140])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 3. Weekly Study Schedule Table
    story.append(Paragraph("Weekly Topological Study Schedule", section_heading_style))

    sched_headers = [
        Paragraph("Week", table_header_style),
        Paragraph("Allocated Topic / Study Concept", table_header_style),
        Paragraph("Hours", table_header_style),
        Paragraph("Source Class Date", table_header_style),
    ]
    sched_rows = [sched_headers]

    study_schedule = cast(Dict[int, List[Dict[str, Any]]], result.get("study_schedule", {}))
    topics_list = cast(List[Dict[str, Any]], result.get("topics", []))
    topic_by_id = {t["topic_id"]: t for t in topics_list}

    row_count = 0
    for week_num, assigned_topics in study_schedule.items():
        if not assigned_topics:
            continue
        for topic in assigned_topics:
            row_count += 1
            topic_meta = topic_by_id.get(topic["topic_id"], {})
            src_date = topic_meta.get("source_date") or "N/A"
            sched_rows.append(
                [
                    Paragraph(f"<b>W{week_num:02d}</b>", body_style),
                    Paragraph(f"<b>{topic['topic_id']}</b>: {topic['title']}", body_style),
                    Paragraph(f"{topic['hours']:g}h", body_style),
                    Paragraph(src_date, body_style),
                ]
            )

    sched_table = Table(sched_rows, colWidths=[40, 340, 50, 110], repeatRows=1)
    sched_table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("ALIGN", (3, 0), (3, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ]

    # Alternating row background colors
    for r in range(1, len(sched_rows)):
        bg = colors.HexColor("#FFFFFF") if r % 2 == 1 else colors.HexColor("#F7FAFC")
        sched_table_style.append(("BACKGROUND", (0, r), (-1, r), bg))

    sched_table.setStyle(TableStyle(sched_table_style))
    story.append(sched_table)
    story.append(Spacer(1, 12))

    # 4. Exam and Milestone Calendar (if any)
    milestones = cast(List[Dict[str, Any]], result.get("milestones", []))
    if milestones:
        milestone_flowables = [
            Paragraph("Exam & Milestone Calendar", section_heading_style),
        ]
        m_headers = [
            Paragraph("Date", table_header_style),
            Paragraph("Event / Milestone Description", table_header_style),
            Paragraph("Category", table_header_style),
        ]
        m_rows = [m_headers]
        for m in milestones:
            kind_str = m.get("kind", "").capitalize()
            note_str = f" &nbsp;<i>({m['note']})</i>" if m.get("note") else ""
            desc = f"<b>{m.get('title', '')}</b>{note_str}"
            m_rows.append(
                [
                    Paragraph(f"<b>{m.get('date', 'N/A')}</b>", body_style),
                    Paragraph(desc, body_style),
                    Paragraph(kind_str, body_style),
                ]
            )

        m_table = Table(m_rows, colWidths=[90, 330, 120], repeatRows=1)
        m_table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C5282")),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]
        for r in range(1, len(m_rows)):
            bg = colors.HexColor("#FFFAF0") if "exam" in m_rows[r][2].text.lower() else (
                colors.HexColor("#FFFFFF") if r % 2 == 1 else colors.HexColor("#F7FAFC")
            )
            m_table_style.append(("BACKGROUND", (0, r), (-1, r), bg))

        m_table.setStyle(TableStyle(m_table_style))
        milestone_flowables.append(m_table)
        milestone_flowables.append(Spacer(1, 10))
        story.append(KeepTogether(milestone_flowables))

    # 5. Model Notes & Assumptions
    assumptions = result.get("assumptions", [])
    if assumptions:
        notes_flowables = [
            Paragraph("Planning Notes & Assumptions", section_heading_style),
        ]
        for note in assumptions:
            notes_flowables.append(
                Paragraph(f"• {note}", ParagraphStyle("NoteItem", parent=body_style, leftIndent=12, spaceAfter=2))
            )
        story.append(KeepTogether(notes_flowables))

    # Build PDF with page numbering
    doc.build(story, onFirstPage=_add_page_decorations, onLaterPages=_add_page_decorations)
    return out_file

