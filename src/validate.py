"""
validate.py — validate the knowledge graph against SHACL shapes.

Why this matters for enterprise AI: an agent grounded on a knowledge graph is
only as trustworthy as the graph. SHACL lets you assert rules ("every Order has
a Customer", "Invoice amount > 0") and mechanically catch bad data before it
ever reaches the LLM.

Run:  python src/validate.py
"""
from pathlib import Path
from rdflib import Graph
from pyshacl import validate

ROOT = Path(__file__).resolve().parent.parent


def validate_graph(extra_data: Graph = None):
    data = Graph()
    data.parse(ROOT / "ontology" / "o2c.ttl", format="turtle")
    data.parse(ROOT / "ontology" / "data.ttl", format="turtle")
    if extra_data is not None:
        data += extra_data
    shapes = Graph().parse(ROOT / "ontology" / "shapes.ttl", format="turtle")

    conforms, _report_graph, report_text = validate(
        data, shacl_graph=shapes, inference="rdfs", abort_on_first=False,
    )
    print("CONFORMS:", conforms)
    if not conforms:
        print(report_text)
    return conforms


if __name__ == "__main__":
    print("Validating clean graph...")
    validate_graph()

    # Demonstrate a violation: an Order with no Customer and no line item.
    print("\nInjecting a bad Order (no customer, no line item)...")
    from rdflib import Namespace, RDF
    EX = Namespace("http://sujith.dev/o2c#")
    bad = Graph()
    bad.add((EX.ordBAD, RDF.type, EX.Order))
    validate_graph(extra_data=bad)
