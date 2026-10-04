from pathlib import Path

import run_live_test


def parse_text(monkeypatch, text):
    monkeypatch.setattr(run_live_test, "extract_text_from_pdf", lambda path: text)
    return run_live_test.parse_syllabus_pdf(Path("sample.pdf"))


def test_numbered_objectives_and_policies_are_not_topics(monkeypatch):
    topics, edges = parse_text(monkeypatch,
        "Learning Objectives\n1. Explain AI concepts\n2. Build models\n"
        "Academic Dishonesty\n1. Cheating\n2. Plagiarism\n")
    assert topics == []
    assert edges == []


def test_repeated_numbers_have_unique_ids_and_repeated_headings_are_ignored(monkeypatch):
    topics, edges = parse_text(monkeypatch,
        "Week 1: Arrays\nWeek 1: Arrays\nModule 1: Pointers\nWeek 2: Lists (2 hours)\n")
    ids = [topic["topic_id"] for topic in topics]
    assert len(topics) == len(set(ids)) == 3
    assert topics[-1]["estimated_hours"] == 2
    assert edges == list(zip(ids, ids[1:]))
    dag = run_live_test.TopicDependencyDAG()
    for topic in topics:
        dag.add_topic(topic["topic_id"], topic["title"], topic["estimated_hours"], topic["deadline_week"])
    for source, target in edges:
        dag.add_prerequisite(source, target)
    assert len(dag.get_study_sequence()) == 3
