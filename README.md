# AutoStudy-TLDR

Generate study schedules from the example Simple Syllabus PDFs:

```powershell
python -m pip install -r requirements.txt
python run_live_test.py
python -m pytest -q
```

The runner finds PDFs in `data/raw/raw_syllabi` relative to the project, prints
the full study schedule and baseline/DAG metrics, and saves readable TXT reports
alongside Markdown and JSON to `test_outputs`. Text reports include wrapped
descriptions, model comparisons, every study week, and the milestone calendar.
Optional arguments: `--input-dir`, `--output-dir`,
and `--capacity` (maximum weekly hours, default 6).

Extraction prefers dated Class Schedule tables, then explicit week/module
headings, then numbered items strictly inside the Student Learning
Objectives/Outcomes section. PDF page headers and footers are removed before
wrapped text is joined. University policy lists are excluded.

COMP385 supplies a dated outline: class dates become study deadlines, and
homework/exam entries form a separate calendar. Homework is listed on its
source class date; this is not necessarily its due date. COMP365 and COMP440
supply learning outcomes: the runner produces suggested study plans using
an assumed 15-week horizon. It does not invent instructor due dates.

Each item defaults to 3 study hours. The allocator packs items in source
order up to weekly capacity, so unused weeks remain empty. Sequential
dependency edges are inferred from that order, rather than verified
conceptual prerequisites. The two models may therefore have identical
metrics. Reports include these assumptions and retain extraction provenance.
