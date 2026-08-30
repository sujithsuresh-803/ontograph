"""
graphrag.py — GraphRAG over the Order-to-Cash knowledge graph.

Vector RAG (your RAGgraph) retrieves *text chunks* by embedding similarity.
GraphRAG instead retrieves *facts* by querying a knowledge graph, then grounds
the LLM answer on those facts. The win: precise, auditable, aggregatable
answers ("total unpaid across APAC") that vector search cannot compute.

Pipeline:
    question --> [nl_to_sparql] --> SPARQL --> run on KG --> rows
             --> [ground] --> natural-language answer + the exact facts used

The LLM steps are OPTIONAL. With no API key this runs fully offline using a
small intent router + deterministic templating, so the mechanism is always
demonstrable. Set GEMINI_API_KEY (or OPENAI_API_KEY) to enable real NL->SPARQL.

Run:  python src/graphrag.py "how much do APAC customers still owe?"
"""
import os
import sys
from pathlib import Path
from rdflib import Graph

ROOT = Path(__file__).resolve().parent.parent
PREFIX = "PREFIX ex: <http://sujith.dev/o2c#>"


def load_graph() -> Graph:
    g = Graph()
    g.parse(ROOT / "ontology" / "o2c.ttl", format="turtle")
    g.parse(ROOT / "ontology" / "data.ttl", format="turtle")
    return g


def schema_text() -> str:
    """The ontology, as compact text — this is what we hand the LLM as grounding
    so it writes SPARQL against the REAL schema instead of hallucinating terms."""
    return (
        "Classes: Customer, Order, LineItem, Product, Invoice, Payment.\n"
        "Edges: Order ex:placedBy Customer; Order ex:hasLineItem LineItem; "
        "LineItem ex:refersTo Product; Invoice ex:forOrder Order; Payment ex:paysInvoice Invoice.\n"
        "Literals: customerName, region, orderDate, quantity, unitPrice, productName, "
        "category, amount, invoiceStatus('paid'|'unpaid'), paymentAmount."
    )


# --- Deterministic intent router (offline fallback) ---------------------------
INTENTS = {
    "unpaid": f"""{PREFIX}
        SELECT ?name (SUM(?amount) AS ?owed) WHERE {{
            ?inv ex:invoiceStatus "unpaid" ; ex:amount ?amount ; ex:forOrder ?o .
            ?o ex:placedBy ?c . ?c ex:customerName ?name .
        }} GROUP BY ?name ORDER BY DESC(?owed)""",
    "revenue": f"""{PREFIX}
        SELECT ?name (SUM(?q * ?p) AS ?revenue) WHERE {{
            ?o ex:placedBy ?c ; ex:hasLineItem ?li .
            ?c ex:customerName ?name . ?li ex:quantity ?q ; ex:unitPrice ?p .
        }} GROUP BY ?name ORDER BY DESC(?revenue)""",
    "product": f"""{PREFIX}
        SELECT DISTINCT ?name ?product WHERE {{
            ?o ex:placedBy ?c ; ex:hasLineItem ?li . ?c ex:customerName ?name .
            ?li ex:refersTo ?prod . ?prod ex:productName ?product .
        }} ORDER BY ?name""",
}


def _route(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ("unpaid", "owe", "outstanding", "due")):
        return INTENTS["unpaid"]
    if any(w in q for w in ("revenue", "sales", "spend", "biggest", "top")):
        return INTENTS["revenue"]
    if any(w in q for w in ("product", "buy", "bought", "order")):
        return INTENTS["product"]
    return INTENTS["revenue"]


def nl_to_sparql(question: str) -> str:
    """Turn a natural-language question into SPARQL.
    Uses an LLM when a key is present; otherwise the deterministic router."""
    key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if key:
        try:
            return _llm_to_sparql(question, key)   # real NL->SPARQL
        except Exception as e:                     # never crash the demo
            print(f"[llm unavailable: {e}; using offline router]")
    return _route(question)


def _llm_to_sparql(question: str, key: str) -> str:
    """Prompt an LLM to WRITE SPARQL grounded on the schema. Kept minimal;
    swap in your Gemini/OpenAI client of choice."""
    prompt = (
        "You write SPARQL for an RDF graph. Use only these terms.\n"
        f"{schema_text()}\n"
        f"Prefix is: {PREFIX}\n"
        f"Question: {question}\n"
        "Return ONLY a SPARQL query."
    )
    import google.generativeai as genai  # optional dependency
    genai.configure(api_key=key)
    text = genai.GenerativeModel("gemini-2.5-flash").generate_content(prompt).text
    return text.replace("```sparql", "").replace("```", "").strip()


def answer(question: str):
    g = load_graph()
    sparql = nl_to_sparql(question)
    rows = [tuple(str(x) for x in r) for r in g.query(sparql)]

    print(f"Q: {question}")
    print(f"\nSPARQL used:\n{sparql.strip()}")
    print("\nFacts retrieved from the knowledge graph (the 'grounding'):")
    for r in rows:
        print("   ", " | ".join(r))

    # Ground the answer. (With an LLM you'd pass `rows` as context; offline we
    # template a faithful answer directly from the retrieved facts.)
    print("\nGrounded answer:")
    if not rows:
        print("    No matching facts in the graph.")
    else:
        print("    " + "; ".join(f"{r[0]} = {r[1]}" for r in rows if len(r) >= 2))
    return rows


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "which APAC customers still owe money?"
    answer(q)
