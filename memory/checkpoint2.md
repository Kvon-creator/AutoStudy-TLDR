# Agent Update Instructions: AutoStudy-TLDR Checkpoint 2

Follow these instructions to update the project repository to meet the Checkpoint 2 submission criteria:

### 1. File Structure Updates
Ensure the following files are created or updated in the repository:
- `src/graph_builder.py`: Contains `TopicDependencyDAG` with cycle rejection and `prune_redundancies()`.
- `src/scheduler.py`: Contains `ScheduleAllocator` for capacity-bound week assignments.
- `src/baseline.py`: Contains `LinearChronologicalBaseline`.
- `src/evaluation.py`: Contains `compute_prerequisite_inversions` and `compute_workload_variance`.
- `tests/test_checkpoint2.py`: Verification tests comparing baseline vs. DAG model.
- `generate_checkpoint2_report.py`: Script to generate the benchmark results and print report outputs.
- `reports/checkpoint_2_report.md`: Markdown text of the 6-section report for PDF generation.

### 2. Execution Commands
Run the following commands in the virtual environment to verify the implementation:
1. `pytest tests/test_checkpoint2.py -v`
2. `python generate_checkpoint2_report.py`

### 3. Submission Verification
Confirm that:
1. `tests/test_checkpoint2.py` passes with 0 failures.
2. `generate_checkpoint2_report.py` prints the results table showing 10 test cases, 0.0% PIR for AutoStudy, and baseline comparison.
3. The report adheres strictly to the 6 required sections and does not exceed 5 pages when rendered to PDF.