from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[2]
doc = Document()
section = doc.sections[0]
section.top_margin = section.bottom_margin = Inches(0.7)
section.left_margin = section.right_margin = Inches(0.75)
section.page_width, section.page_height = Inches(8.5), Inches(11)
normal = doc.styles['Normal']
normal.font.name, normal.font.size = 'Calibri', Pt(11)
normal.paragraph_format.space_after = Pt(7)
normal.paragraph_format.line_spacing = 1.06
for name, size in [('Title', 22), ('Heading 1', 14), ('Heading 2', 11)]:
    style = doc.styles[name]
    style.font.name, style.font.size = 'Calibri', Pt(size)
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.space_before = Pt(10)
    style.paragraph_format.space_after = Pt(5)
    style.paragraph_format.keep_with_next = True

def p(text):
    return doc.add_paragraph(text)

def h(text):
    doc.add_heading(text, level=1)

def labeled(label, text):
    para = doc.add_paragraph()
    para.add_run(label + ' ').bold = True
    para.add_run(text)
    return para

doc.add_paragraph('AutoStudy TLDR Checkpoint 2 Report', style='Title')
p('COMP365 AI and Machine Learning | October 4, 2026')
p('AutoStudy TLDR now converts three example syllabi into readable study plans. Controlled tests show that dependency ordering removes prerequisite inversions, but the real syllabus comparisons do not yet demonstrate an advantage over a simple chronological baseline.')

h('1 Question and approach')
p('Project question: Can syllabus extraction and a prerequisite graph generate a valid weekly study plan that respects dependencies and study capacity better than a scheduler that follows the syllabus order?')
p('The project is a local Python pipeline that reads syllabus PDFs, extracts course information and study items, builds a directed acyclic graph, removes redundant edges, and assigns items to weeks. It produces a full schedule, baseline comparisons, and an exam and homework calendar when dates are available. The live runner writes TXT, Markdown, and JSON files to test_outputs.')
p('Checkpoint 1 provided basic TXT/PDF extraction, milestone extraction, and topological ordering for a manually entered topic graph. The major change is an end-to-end Checkpoint 2 pipeline with weekly capacity and deadline checks, a chronological baseline, evaluation metrics, automated tests, and support for the supplied Simple Syllabus formats.')

h('2 Data and methods')
p('The real data consists of three Fall 2026 Simple Syllabus PDFs in data/raw/raw_syllabi: COMP365 AI and Machine Learning, COMP385 Theory of Computing, and COMP440 Game Design. COMP385 provides a dated class table; the other two provide learning outcomes without a dated outline.')
p('Cleaning removes print timestamps, page headers, and Canvas footer URLs; normalizes whitespace; and joins wrapped lines. Extraction stays within course sections and excludes university policy lists. It prefers dated Class Schedule entries, then explicit week/module headings, then numbered learning outcomes within the named outcomes section. IDs are unique. Exams and homework are separated from study topics.')
p('Working methods include PDF extraction with pypdf, section-aware parsing, cycle rejection, transitive edge reduction, topological ordering, and whole-item weekly allocation. Study effort defaults to three hours per item and capacity to six hours per week. COMP385 class dates become study deadlines over a 17-week horizon; the other plans assume 15 weeks. Sequential topic edges are inferred from source order, not verified conceptual prerequisites.')
p('Credits: OpenAI Codex assisted with code fixes, tests, parser development, and report preparation. No other assistance was used. Outside libraries are pypdf and pdfplumber for PDF reading, NetworkX for graph algorithms, Pydantic for data models, and pytest for testing; statistics from the Python standard library computes means and standard deviations. No trained model or language-model inference runs in the study-planning pipeline.')

h('3 Baseline and tests')
p('The LinearChronologicalBaseline packs topics in raw input order using the same weekly capacity. AutoStudy orders the dependency graph first and validates deadlines. Both are tested on the same inputs. Success means each extracted item is scheduled once, weekly capacity is respected, and prerequisites are not assigned to later weeks than their dependents; AutoStudy also checks deadline feasibility.')
p('Completed evaluation covers three distinct real PDFs, ten synthetic runs, and 21 passing automated tests. Each synthetic run repeats the same reversed eight-topic chain with different IDs, 2.5 hours per topic, five-hour weekly capacity, and ten weeks. Prerequisite inversion rate (PIR) is the fraction of scheduled edges whose prerequisite occurs in a later week. Workload standard deviation (WSD) measures weekly-hour spread, including empty weeks. Lower is better for both. PIR does not detect reversed order within one week.')

doc.add_page_break()
h('4 Results')
p('The following results come from the completed synthetic benchmark and saved live-run outputs. PIR is expressed as a percentage; WSD is in hours. Each real-data row covers one PDF. The synthetic row is a mean across ten runs of one repeated structure.')
table = doc.add_table(rows=1, cols=6)
table.style = 'Light Shading Accent 1'
headers = ['Cases', 'Count', 'Baseline PIR', 'DAG PIR', 'Baseline WSD', 'DAG WSD']
for cell, text in zip(table.rows[0].cells, headers):
    cell.text = text
    for run in cell.paragraphs[0].runs:
        run.bold = True
rows = [
    ['Reversed synthetic chain', '10', '42.86%', '0.00%', '2.45', '2.45'],
    ['COMP365 syllabus', '1', '0.00%', '0.00%', '2.10', '2.10'],
    ['COMP385 syllabus', '1', '0.00%', '0.00%', '2.31', '2.31'],
    ['COMP440 syllabus', '1', '0.00%', '0.00%', '2.10', '2.10'],
]
for row in rows:
    for cell, text in zip(table.add_row().cells, row):
        cell.text = text
for row in table.rows:
    trpr = row._tr.get_or_add_trPr()
    trpr.append(OxmlElement('w:cantSplit'))
    for cell in row.cells:
        for para in cell.paragraphs:
            para.paragraph_format.space_after = Pt(5)
            for run in para.runs:
                run.font.size = Pt(10)
repeat = OxmlElement('w:tblHeader')
table.rows[0]._tr.get_or_add_trPr().append(repeat)
p('The synthetic comparison eliminates measured inversions without improving workload spread. Both models agree on all three real syllabi because the dependency edges follow their existing source order. This is a pipeline check rather than evidence of better student learning or independently validated prerequisites.')
p('Extraction produced five outcome-based study items for COMP365, 27 dated class study items and ten calendar entries for COMP385, and five outcome-based items for COMP440. All three live runs completed. The 21 tests check original graph behavior, cycle rejection, unique IDs, metadata preservation, capacity/deadline rejection, scoped extraction, source dates, complete schedules, and saved reports.')
labeled('Example output from one case', 'COMP385 Theory of Computing, from test_outputs/Simple_Syllabus_COMP385.txt:')
example = doc.add_table(rows=0, cols=2)
example.style = 'Light Shading Accent 1'
for left, right in [
    ('Week 1', 'Course Overview, Basics Concepts - 3 hours; Mathematical Preliminaries and Notation, Basic Concepts - 3 hours'),
    ('Week 2', 'Deterministic finite automata (DFA) - 3 hours; Regular Languages - 3 hours'),
    ('Exam calendar', 'Midterm: October 6, 2026; Final: December 10, 2026'),
]:
    cells = example.add_row().cells
    cells[0].text, cells[1].text = left, right
    cells[0].width, cells[1].width = Inches(1.1), Inches(5.8)
    cells[0].paragraphs[0].runs[0].bold = True
p('COMP385 homework entries retain their listed class dates; those dates are not confirmed due dates. Outcome-based plans have no invented instructor dates. Plans pack an initial study pass into early weeks and leave remaining weeks unassigned.')
para = doc.add_paragraph()
para.add_run('Planned tests - not yet completed: ').italic = True
para.add_run('manual extraction scoring against an annotated reference, diverse dependency graphs, scan-only PDF evaluation, and a student usability or learning-outcome study.')
labeled('Reproduction', 'Run python generate_checkpoint2_report.py, python run_live_test.py, and python -m pytest -q. Evidence is saved in test_outputs/*.json and *.txt and the test suite.')

doc.add_page_break()
h('5 Weak case and limitation')
p('A concrete parser failure occurred on COMP365: the original fallback treated all numbered list entries as topics. Learning objectives and academic dishonesty rules both started with item 1, creating duplicate TOPIC_01 IDs. The live run extracted 12 incorrect items and stopped when the graph rejected the duplicate. Removing the fallback prevented the crash but initially caused all three syllabi to be skipped.')
p('The current parser fixes this by reading learning outcomes only inside their named section and by recognizing COMP385 dated schedule rows. It reconstructs wrapped text across page breaks and retains unique topic IDs. University policy items no longer enter the generated schedules.')
p('A remaining weak result is the real-data comparison: all three PDFs produce identical baseline and DAG metrics. The inferred source-order chain makes the input already satisfy its own dependency graph, so this comparison cannot establish whether AutoStudy handles real conceptual prerequisites better. WSD also remains unchanged in the reversed synthetic chain because both methods pack the same number of equal-hour items into each week.')
p('One data limit is that the three real examples come from a single department and share one syllabus export format. Two lack dated outlines, and none supplies an explicit topic-level prerequisite graph. The sample is too small and too uniform to establish general performance. In addition, three hours per item is an assumption rather than measured learning effort; equal blocks can understate the work required by difficult topics. Scan-only PDFs are not supported by an OCR stage.')

h('6 Next steps and paper outline')
labeled('Task 1', 'Build a manually annotated evaluation set with more syllabus formats and independently specified prerequisite edges. Score extraction precision and recall, complete topic coverage, deadline feasibility, and prerequisite violations using a metric that includes within-week order. This evaluation is not yet completed.')
labeled('Task 2', 'Improve the allocator using more realistic effort estimates, feasible prerequisite/deadline ordering, and study blocks spread across available weeks. Compare the improved method with the same baseline on the annotated cases and record infeasible schedules explicitly. These improvements and their evaluation are not yet completed.')
for label, sentence in [
    ('Introduction', 'Present the problem of converting inconsistent syllabus documents into useful study plans and ask whether dependency-aware scheduling improves plan validity over chronological packing.'),
    ('Methods', 'Describe the data, section-aware PDF extraction, graph validation and reduction, weekly allocator, assumptions, chronological baseline, and evaluation metrics.'),
    ('Results', 'Report the completed synthetic and real-syllabus comparisons, extraction counts, regression tests, and one generated study schedule with its case count.'),
    ('Limitations', 'Discuss the small shared-format dataset, inferred prerequisites, assumed effort, equal real-data metrics, and the absence of student learning or usability validation.'),
]:
    doc.add_heading(label, level=2)
    p(sentence)

doc.core_properties.title = 'AutoStudy TLDR Checkpoint 2 Report'
doc.core_properties.subject = 'Project question methods baseline tests results limitations and next steps'
doc.core_properties.author = ''
doc.save(ROOT / 'reports/AutoStudy_TLDR_Checkpoint_2.docx')
print(ROOT / 'reports/AutoStudy_TLDR_Checkpoint_2.docx')
