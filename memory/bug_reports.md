# Code Error Report

Date: October 4, 2026

## Findings and fixes

| Error | Effect | Fix |
| --- | --- | --- |
| Missing `src/graph_builder.py` | Pytest stopped during collection with `ModuleNotFoundError`; the benchmark could not start. | Added `TopicDependencyDAG`, including topic metadata, topological ordering, cycle rejection, and transitive edge pruning. A rejected cycle leaves the graph valid. |
| Missing `src/scheduler.py` | Checkpoint 2 scheduling imports failed. | Added `ScheduleAllocator` to pack the ordered topics into weeks, enforce weekly capacity and deadlines, and reject schedules that cannot fit. |
| Evaluation module named `evalutation.py` | Imports of `src.evaluation` failed. | Added the correctly named module; retained the old spelling as compatibility imports. |
| Undeclared NumPy dependency | Evaluation and benchmark depended on a package absent from `requirements.txt`. | Used Python's standard-library `statistics.mean` and `statistics.pstdev`; removed the unused random seed. |
| Missing `baseline_extract_milestones` | `main.py` imported a function that did not exist. | Restored extraction of month/day milestone lines into `CourseMilestone` objects. The sample yields three milestones. |
| Baseline silently exceeded capacity | Oversized topics and a full final week could produce invalid schedules; zero weeks could cause a key error. | Reused validated allocation while preserving raw syllabus order and ignoring deadlines for the baseline comparison. Invalid capacity, oversized topics, and insufficient weeks raise `ValueError`. |
| Empty workload metric | An empty schedule previously produced an undefined NumPy result. | Return `0.0` for an empty schedule; retain population standard deviation for nonempty schedules. |
| Working-directory-dependent demo path | Running the demo from another directory could fail to find the sample syllabus. | Resolve the syllabus relative to `main.py`. |
| Text extraction rejected `Path` objects and uppercase extensions | Valid file paths could raise an attribute error or unsupported-format error. | Normalize paths with `pathlib.Path` and compare extensions without case sensitivity. |

## Verification

Executed with the existing `venv/Scripts/python.exe` environment:

- `python -m pytest -q`: **13 passed**, with one dependency deprecation warning.
- `python main.py`: completed successfully; extracted three milestones and printed five topics in prerequisite order.
- `python generate_checkpoint2_report.py`: completed all ten benchmark cases.
- `git diff --check`: passed before this report was added.

Regression tests cover rejected cycles, metadata preservation after pruning, capacity overflow, invalid capacity, missed deadlines, valid packing, uppercase text paths, milestone extraction, and empty/known workload metrics. The original graph and comparative benchmark tests also pass.

| Benchmark metric | Linear baseline | AutoStudy DAG |
| --- | ---: | ---: |
| Mean prerequisite inversion rate | 42.86% | 0.00% |
| Mean weekly workload standard deviation | 2.45 hours | 2.45 hours |

## Remaining limitations

- The local environment uses Python 3.8.8. The PDF dependency emits a `CryptographyDeprecationWarning`; it does not fail the tests. Updating the Python environment is outside these code changes.
- The benchmark repeats the same reversed eight-topic chain with different IDs ten times. These results verify this synthetic scenario, rather than performance across ten distinct real curricula. Workload balance is identical for both models in this scenario.
- Prerequisite inversion rate compares weeks, so it does not count reversed ordering within the same week. The DAG allocator preserves the supplied topological sequence within each week.
- The allocator packs whole topics in the supplied order. It raises an error for infeasible capacity/deadline assignments and does not split topics or search alternative topological orders.
- `compute_workload_variance` retains its existing public name but computes standard deviation, as expected by the benchmark.
- This task did not create the separate Checkpoint 2 submission report or a PDF. The requested error report is this file.

Changes are local; no commit or GitHub push was performed.
