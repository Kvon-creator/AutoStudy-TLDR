"""Generate reproducible study plans from the example syllabus PDFs."""
import argparse
import json
from pathlib import Path
from textwrap import fill

from src.baseline import LinearChronologicalBaseline
from src.evaluation import compute_prerequisite_inversions, compute_workload_variance
from src.graph_builder import TopicDependencyDAG
from src.scheduler import ScheduleAllocator
from src.syllabus import extract_text_from_pdf, parse_syllabus_text


def parse_syllabus_pdf(pdf_path):
    """Compatibility API returning topics and inferred prerequisite edges."""
    result = parse_syllabus_text(extract_text_from_pdf(pdf_path), Path(pdf_path).name)
    return result["topics"], result["prerequisites"]


def build_result(parsed, capacity=6.0):
    topics, edges = parsed["topics"], parsed["prerequisites"]
    if not topics:
        raise ValueError("No course outline or scoped learning outcomes were found")
    weeks = parsed["total_weeks"]
    baseline = LinearChronologicalBaseline(capacity).schedule(topics, weeks)
    dag = TopicDependencyDAG()
    for topic in topics:
        dag.add_topic(topic["topic_id"], topic["title"], topic["estimated_hours"], topic["deadline_week"])
    for source, target in edges:
        dag.add_prerequisite(source, target)
    dag.prune_redundancies()
    sequence = dag.get_study_sequence()
    schedule = ScheduleAllocator(capacity).allocate(sequence, weeks)
    metrics = {}
    for name, assigned in (("baseline", baseline), ("autostudy", schedule)):
        metrics[name] = {"prerequisite_inversion_rate": compute_prerequisite_inversions(assigned, edges),
                         "workload_standard_deviation_hours": compute_workload_variance(assigned)}
    return dict(parsed, weekly_capacity_hours=capacity, baseline_schedule=baseline,
                study_schedule=schedule, metrics=metrics)


def markdown_report(result):
    lines = [f"# {result['course_code']}: {result['course_title']}", "",
             f"Source: `{result['source_file']}`", "",
             f"Course prerequisites: {', '.join(result['course_prerequisites']) or 'Not stated'}", "",
             result['course_description'], "", f"Topic source: {result['topic_source']}", "",
             f"Plan: {result['total_weeks']} weeks; {result['weekly_capacity_hours']:g} hours/week maximum.", ""]
    lines += [f"- {note}" for note in result['assumptions']]
    lines += ["", "## Comparison", "", "| Model | Inversion rate | Workload standard deviation |",
              "| --- | ---: | ---: |"]
    for model, values in result['metrics'].items():
        lines.append(f"| {model} | {values['prerequisite_inversion_rate']:.2%} | {values['workload_standard_deviation_hours']:.2f} hours |")
    lines += ["", "These metrics use inferred source-order edges. Equal results do not establish a model advantage.",
              "", "## Study schedule", "", "| Week | Study item | Hours | Source class date |",
              "| ---: | --- | ---: | --- |"]
    topic_by_id = {topic['topic_id']: topic for topic in result['topics']}
    for week, topics in result['study_schedule'].items():
        for topic in topics:
            source_date = topic_by_id[topic['topic_id']]['source_date'] or 'Not stated'
            lines.append(f"| {week} | {topic['title'].replace('|', '/')} | {topic['hours']:g} | {source_date} |")
    lines += ["", "## Exam and homework calendar", ""]
    if result['milestones']:
        for item in result['milestones']:
            lines.append(f"- {item['date']}: {item['title']} ({item['kind']}). {item.get('note', '')}".strip())
    else:
        lines.append("No dated milestones were found in a class schedule. Check the course LMS for due dates.")
    return '\n'.join(lines) + '\n'


def text_report(result):
    """Render the complete result as wrapped plain text."""
    title = f"{result['course_code']}: {result['course_title']}"
    lines = [title, '=' * len(title), '', f"Source: {result['source_file']}",
             f"Course prerequisites: {', '.join(result['course_prerequisites']) or 'Not stated'}",
             '', 'COURSE DESCRIPTION', fill(result['course_description'], width=88), '',
             f"Topic source: {result['topic_source']}",
             f"Plan: {result['total_weeks']} weeks; maximum {result['weekly_capacity_hours']:g} study hours/week.",
             '', 'ASSUMPTIONS']
    lines += [fill(note, width=88, initial_indent='- ', subsequent_indent='  ')
              for note in result['assumptions']]
    lines += ['', 'MODEL COMPARISON']
    for model, values in result['metrics'].items():
        lines += [f"{model.title()}:",
                  f"  Prerequisite inversion rate: {values['prerequisite_inversion_rate']:.2%}",
                  f"  Weekly workload standard deviation: {values['workload_standard_deviation_hours']:.2f} hours"]
    lines += [fill('These metrics use inferred source-order edges. Equal results do not establish a model advantage.', width=88),
              '', 'STUDY SCHEDULE']
    topic_by_id = {topic['topic_id']: topic for topic in result['topics']}
    for week, topics in result['study_schedule'].items():
        hours = sum(topic['hours'] for topic in topics)
        lines += ['', f"Week {week:02d} ({hours:g} study hours)"]
        if not topics:
            lines.append('  No study items assigned.')
        for topic in topics:
            lines.append(fill(f"{topic['title']} ({topic['hours']:g} hours)", width=88,
                              initial_indent='  - ', subsequent_indent='    '))
            source_date = topic_by_id[topic['topic_id']]['source_date']
            if source_date:
                lines.append(f"    Source class date: {source_date}")
    lines += ['', 'EXAM AND HOMEWORK CALENDAR']
    for item in result['milestones']:
        lines.append(fill(f"{item['date']}: {item['title']} ({item['kind']}). {item.get('note', '')}".strip(),
                          width=88, initial_indent='- ', subsequent_indent='  '))
    if not result['milestones']:
        lines.append('No dated milestones found. Check the course LMS for due dates.')
    return '\n'.join(lines) + '\n'


def run_pipeline_on_pdf(pdf_path, output_dir=None, capacity=6.0):
    parsed = parse_syllabus_text(extract_text_from_pdf(pdf_path), pdf_path.name)
    result = build_result(parsed, capacity)
    print(f"\n[*] {result['course_code']}: {result['course_title']} ({pdf_path.name})")
    print(f"[+] Extracted {len(result['topics'])} study items from {result['topic_source']}; {len(result['milestones'])} dated milestones.")
    print(f"    Course prerequisites: {', '.join(result['course_prerequisites']) or 'Not stated'}")
    for note in result['assumptions']:
        print(f"    Note: {note}")
    for model, values in result['metrics'].items():
        print(f"  {model}: PIR {values['prerequisite_inversion_rate']:.2%}; workload std dev {values['workload_standard_deviation_hours']:.2f} hrs")
    print(f"  Generated Study Schedule ({result['total_weeks']} weeks):")
    for week, topics in result['study_schedule'].items():
        if topics:
            assigned = '; '.join(f"{topic['title']} ({topic['hours']:g}h)" for topic in topics)
            print(f"    Week {week:02d}: {assigned}")
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        stem = pdf_path.stem
        (output_dir / f"{stem}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
        (output_dir / f"{stem}.md").write_text(markdown_report(result), encoding='utf-8')
        (output_dir / f"{stem}.txt").write_text(text_report(result), encoding='utf-8')
        print(f"  Saved TXT, Markdown, and JSON: {output_dir / stem}")
    return result


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, default=root / 'data/raw/raw_syllabi')
    parser.add_argument('--output-dir', type=Path, default=root / 'test_outputs')
    parser.add_argument('--capacity', type=float, default=6.0)
    args = parser.parse_args()
    files = sorted(path for path in args.input_dir.glob('*') if path.is_file() and path.suffix.lower() == '.pdf')
    if not files:
        parser.exit(1, f"No PDF files found in {args.input_dir.resolve()}\n")
    print(f"Found {len(files)} PDF syllabus file(s) for live testing.")
    failures = 0
    for path in files:
        try:
            run_pipeline_on_pdf(path, args.output_dir, args.capacity)
        except (ValueError, OSError) as error:
            failures += 1
            print(f"[!] {path.name}: {error}")
    if failures:
        parser.exit(1, f"{failures} syllabus file(s) could not be scheduled.\n")


if __name__ == '__main__':
    main()
