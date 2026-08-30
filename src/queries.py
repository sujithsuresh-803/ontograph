"""
queries.py — SPARQL over the Order-to-Cash knowledge graph.

SPARQL is the query language for RDF graphs (the graph-DB equivalent of SQL).
The core idea: you describe a PATTERN of triples with ?variables, and the
engine finds every subgraph that matches.

Run:  python src/queries.py
"""
from pathlib import Path
from rdflib import Graph

ROOT = Path(__file__).resolve().parent.parent
EX = "http://sujith.dev/o2c#"


def load_graph() -> Graph:
    g = Graph()
    g.parse(ROOT / "ontology" / "o2c.ttl", format="turtle")   # schema (T-Box)
    g.parse(ROOT / "ontology" / "data.ttl", format="turtle")   # facts  (A-Box)
    return g


# Each query is (title, teaching-note, SPARQL).
QUERIES = [
    ("Customers and their regions",
     "Simplest pattern: match every ?c that is a Customer and read two attributes.",
     """
     PREFIX ex: <http://sujith.dev/o2c#>
     SELECT ?name ?region WHERE {
         ?c a ex:Customer ;
            ex:customerName ?name ;
            ex:region ?region .
     } ORDER BY ?name
     """),

    ("Total revenue by customer",
     "Traverse Order->Customer and Order->LineItem, compute qty*price, SUM per customer.",
     """
     PREFIX ex: <http://sujith.dev/o2c#>
     SELECT ?name (SUM(?qty * ?price) AS ?revenue) WHERE {
         ?order   ex:placedBy   ?cust ;
                  ex:hasLineItem ?li .
         ?cust    ex:customerName ?name .
         ?li      ex:quantity ?qty ;
                  ex:unitPrice ?price .
     } GROUP BY ?name ORDER BY DESC(?revenue)
     """),

    ("Unpaid invoices with customer and amount",
     "Join Invoice->Order->Customer and FILTER to status 'unpaid' — a multi-hop traversal.",
     """
     PREFIX ex: <http://sujith.dev/o2c#>
     SELECT ?name ?amount WHERE {
         ?inv  a ex:Invoice ;
               ex:invoiceStatus "unpaid" ;
               ex:amount ?amount ;
               ex:forOrder ?order .
         ?order ex:placedBy ?cust .
         ?cust  ex:customerName ?name .
     } ORDER BY DESC(?amount)
     """),

    ("Which products has each APAC customer ordered?",
     "Path traversal Customer<-Order->LineItem->Product, filtered to region APAC.",
     """
     PREFIX ex: <http://sujith.dev/o2c#>
     SELECT DISTINCT ?name ?product WHERE {
         ?cust  ex:region "APAC" ; ex:customerName ?name .
         ?order ex:placedBy ?cust ; ex:hasLineItem ?li .
         ?li    ex:refersTo ?p .
         ?p     ex:productName ?product .
     } ORDER BY ?name ?product
     """),
]


def run_all(g: Graph = None):
    g = g or load_graph()
    for title, note, q in QUERIES:
        print(f"\n=== {title} ===")
        print(f"    ({note})")
        for row in g.query(q):
            print("   ", " | ".join(str(x) for x in row))


if __name__ == "__main__":
    run_all()
