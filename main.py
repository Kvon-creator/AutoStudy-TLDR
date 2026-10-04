from src.parser import extract_raw_text, TopicNode
from src.baseline import baseline_extract_milestones
from src.graph_engine import build_prerequisite_dag, get_topological_study_order
from pathlib import Path

def main():
    print("==============================================")
    print(" AutoStudy + TLDR: Checkpoint 1 Demo (Local)  ")
    print("==============================================")

    # 1. Read syllabus text and test baseline
    syllabus_text = extract_raw_text(Path(__file__).parent / "data/raw/sample_syllabus.txt")
    milestones = baseline_extract_milestones(syllabus_text)
    
    print(f"\n[1] Extracted Milestones (Baseline): {len(milestones)} found")
    for m in milestones:
        print(f"  • {m.title} -> {m.date_str}")

    # 2. Build and sort the Topic Graph
    topics = [
        TopicNode(name="Arrays & Pointers", week=1, prerequisites=[]),
        TopicNode(name="Linked Lists", week=2, prerequisites=["Arrays & Pointers"]),
        TopicNode(name="Stacks & Queues", week=3, prerequisites=["Linked Lists"]),
        TopicNode(name="Binary Search Trees", week=4, prerequisites=["Linked Lists"]),
        TopicNode(name="Graph Traversal (BFS/DFS)", week=5, prerequisites=["Binary Search Trees", "Stacks & Queues"])
    ]

    print("\n[2] Building Prerequisite DAG (TLDR)...")
    dag = build_prerequisite_dag(topics)
    print(f"  • Total Concept Nodes: {dag.number_of_nodes()}")
    print(f"  • Dependency Edges:    {dag.number_of_edges()}")

    # 3. Output topologically sorted study sequence
    study_order = get_topological_study_order(dag)
    print("\n[3] Topologically Sorted Study Order:")
    for idx, topic in enumerate(study_order, 1):
        print(f"  {idx}. {topic}")

if __name__ == "__main__":
    main()
