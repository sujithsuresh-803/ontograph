# OntoGraph — an Order-to-Cash Knowledge Graph with Ontology, SPARQL & GraphRAG

A small but **real** enterprise knowledge graph: an OWL/RDFS **ontology** for the
Order-to-Cash process, populated with data, queried with **SPARQL**, quality-checked
with **SHACL**, and served to an LLM through a **GraphRAG** layer.

Built as the semantic-layer counterpart to my vector-RAG project
[`raggraph`](https://github.com/sujithsuresh-803/raggraph): where RAGgraph retrieves
*text chunks* by embedding similarity, OntoGraph retrieves *facts* by traversing a graph.

```bash
pip install -r requirements.txt
python run_all.py                       # build + query + validate + GraphRAG
python src/queries.py                   # just the SPARQL examples
python src/validate.py                  # SHACL validation (+ a caught violation)
python src/graphrag.py "who still owes us money in APAC?"
```

---

## Teach-me: the five concepts, in plain terms

**1. Knowledge graph = facts as a graph.** Everything is a **triple**:
`subject predicate object`. `ord1 placedBy custAcme`. Nodes are things
(customers, orders), edges are relationships. Unlike rows in a table, you can
walk edges across the whole domain in one query.

**2. Ontology = the schema/vocabulary** (`ontology/o2c.ttl`). It declares the
*types* (`Customer`, `Order`, `Invoice`) and the *allowed relationships*
(`Order placedBy Customer`) using **RDFS/OWL**. This is the "semantic model" the
SAP JD talks about — the shared meaning that lets an AI agent understand data
from SAP, Salesforce, Workday, etc. in the same terms.

**3. SPARQL = SQL for graphs** (`src/queries.py`). You write a *pattern* of
triples with `?variables`; the engine returns every match. Multi-hop joins that
are painful in SQL (Invoice → Order → Customer) are just a chain of triple
patterns. Supports `SUM`, `GROUP BY`, `FILTER`, `ORDER BY`, path traversal.

**4. SHACL = data-quality rules** (`ontology/shapes.ttl`). "Every Order must have
exactly one Customer." "Invoice amount > 0." You *validate* the graph against
these shapes before trusting it — the guardrail that keeps an agent from being
grounded on garbage. `src/validate.py` shows a clean pass **and** a caught
violation.

**5. GraphRAG = ground the LLM on graph facts** (`src/graphrag.py`).
```
question → generate SPARQL → run on the graph → feed the exact facts to the LLM → answer
```
The payoff over vector RAG: **precise, aggregatable, auditable** answers.
"How much do APAC customers still owe?" is a `SUM` over a traversal — vector
similarity can't compute that; a graph query can, and every number is traceable
to a triple.

> **Vocabulary you can now speak:** RDF, triple, T-Box vs A-Box, ontology,
> RDFS/OWL, SPARQL (SELECT / WHERE / GROUP BY / traversal), SHACL shapes &
> validation, triple store vs property graph, GraphRAG / knowledge grounding.

---

## Where next (to go from "built a demo" to "fluent")
- Add **Cypher / a property graph**: load the same data into Neo4j and rewrite two
  queries in Cypher — then you can speak to *both* graph-query dialects.
- Add **SKOS** for a product-category taxonomy, and one **OWL inference** rule
  (e.g. `PremiumCustomer` inferred from revenue) to show reasoning.
- Wire the optional LLM path in `graphrag.py` (set `GEMINI_API_KEY`) so NL→SPARQL
  is model-generated, and add a self-check that re-queries on empty results
  (the same self-correcting loop idea as RAGgraph).

## Maps to the SAP "Data & Applied Science" JD
| JD term | Here |
|---|---|
| enterprise **ontologies / semantic models** | `ontology/o2c.ttl` |
| **knowledge graphs**, structured grounding | the whole graph + GraphRAG |
| **graph query language** (SPARQL) | `src/queries.py` |
| **RDF / OWL / RDFS / SHACL** (W3C stack) | ontology + `shapes.ttl` |
| **Order-to-Cash** business context | the modelled domain |
| grounding agents on **trusted business data** | SHACL validation + GraphRAG |

## Résumé bullet (accurate once you've run & understood it)
> **OntoGraph — Order-to-Cash Knowledge Graph + GraphRAG** (Python · rdflib · SPARQL · SHACL · OWL/RDFS) — Modelled an enterprise ontology for the Order-to-Cash process and built a GraphRAG layer that answers natural-language business questions by generating SPARQL, traversing the knowledge graph, validating it with SHACL, and grounding an LLM on the retrieved facts. *Live code · github.com/sujithsuresh-803/ontograph*
