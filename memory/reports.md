# Error report: live syllabus parser

Date: October 4, 2026

## Cause

The fallback in `run_live_test.py` treated every numbered list item as a course topic. In COMP365, both the learning objectives and academic dishonesty policy begin with `1.`, producing duplicate `TOPIC_01` IDs. `TopicDependencyDAG.add_topic` correctly rejected the second ID. Renaming those policy items alone would produce an incorrect study schedule.

## Fixes

1. Removed the unrestricted numbered-list fallback. Only explicit Week, Module, Unit, and Chapter headings are extracted.
2. Ignore exact repeated headings and give distinct headings with the same number unique IDs.
3. Keep the graph's duplicate-topic validation.
4. Explain when a PDF is skipped because no supported topic headings were found.
5. Added `pypdf` to `requirements.txt`, matching the runner's import.
6. Corrected documentation to describe sequential edges as inferred document-order dependencies.

## Verification

- `.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider`: 15 tests passed.
- `.venv/Scripts/python.exe -B run_live_test.py`: found all three PDFs and completed without a traceback.
- All three PDFs lack headings recognized by this parser and were skipped. No schedule or benchmark result was generated for them. A course outline with supported headings, or a parser adapted to the actual outline format, is needed to generate meaningful schedules.
- `git diff --check`: passed before this report was added.

## Update: generate plans from the three supplied syllabi

The earlier skip-only fix prevented false topics but did not generate the intended output. All three PDFs have now been extracted and reviewed, including visual checks of the relevant outcome and schedule pages.

- Added `src/syllabus.py` for section-aware extraction, removal of print headers/footers, joining wrapped lines, unique IDs, course metadata, dated class tables, and learning-outcome fallback.
- COMP365 and COMP440 each yield five complete learning outcomes. Numbered policy lists remain excluded. These become suggested plans with assumed three-hour study blocks and a 15-week horizon.
- COMP385 yields 27 dated study sessions and ten calendar entries (eight homework entries and two exams). Its dated outline defines a 17-week horizon. The final exam remains on December 10, 2026; homework dates are explicitly described as scheduled dates rather than confirmed due dates.
- The runner now prints complete schedules and comparisons, writes one Markdown report and one JSON result per PDF to `reports/live_syllabi`, and supports custom input/output directories and weekly capacity.
- Deadline and capacity validation remain active. Prerequisite edges are inferred from source order; course prerequisites such as COMP285 and COMP360 are metadata, rather than fabricated scheduled topics.
- Baseline and DAG both produce 0% inversions for these already ordered inputs. Equal results are reported without asserting a performance advantage.
- Verification: 21 tests passed, including integration checks against all three actual PDFs, source dates, policy exclusion, topic completeness, deadlines, weekly capacity, saved reports, and insufficient-capacity rejection. The live runner completed all three files successfully and generated six outputs. `git diff --check` passed.

This update supersedes the earlier limitation that all three PDFs were skipped. Learning-outcome plans are an initial study pass, not a complete instructor calendar: no dates are invented for the two courses without dated outlines. Topics are packed into early weeks; the remaining weeks are unassigned.
