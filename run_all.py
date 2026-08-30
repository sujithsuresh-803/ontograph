"""
run_all.py — end-to-end demo: build graph, query it, validate it, GraphRAG it.
Run:  python run_all.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import queries
import validate
import graphrag


def main():
    print("#" * 60)
    print("1) LOAD KNOWLEDGE GRAPH + RUN SPARQL")
    print("#" * 60)
    g = queries.load_graph()
    print(f"Graph loaded: {len(g)} triples.")
    queries.run_all(g)

    print("\n" + "#" * 60)
    print("2) VALIDATE WITH SHACL")
    print("#" * 60)
    validate.validate_graph()

    print("\n" + "#" * 60)
    print("3) GRAPHRAG: natural language -> SPARQL -> grounded answer")
    print("#" * 60)
    for q in ["Which APAC customers still owe money?",
              "Who are our biggest customers by revenue?"]:
        print("\n" + "-" * 50)
        graphrag.answer(q)


if __name__ == "__main__":
    main()
