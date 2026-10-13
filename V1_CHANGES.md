# V1 Changes to DocAgent

This document describes what was added to DocAgent in the V1 enhancement pass.
It is written for a developer or researcher joining the project who is already
familiar with Python but may not know the DocAgent codebase.

---

## What the original DocAgent did

DocAgent automatically generates Python docstrings using a multi-agent pipeline
(Reader → Searcher → Writer → Verifier). Before generating anything, it parses
the target repository with a static AST analyser and builds a **dependency
graph** over all code components (functions, classes, and methods).

Each component was represented by a `CodeComponent` object with these fields:

```
id              – dotted qualified name, e.g. "inventory.manager.Store.put"
component_type  – "function", "class", or "method"
file_path       – absolute path to the file
relative_path   – path relative to the repo root
depends_on      – set of component IDs this component depends on
source_code     – raw source text
start_line      – 1-indexed start line
end_line        – 1-indexed end line
has_docstring   – bool
docstring       – existing docstring text, or ""
node            – live AST node (not serialised)
```

The `depends_on` set was the core of the graph. An edge A → B meant
"A depends on B". The graph was used for **one purpose: documentation
ordering**. Components with no dependencies were documented first, so that
when a complex component was processed its dependencies already had docstrings.
The graph was saved to JSON as a flat dictionary keyed by component ID.

---

## What V1 adds

### 1. Typed relationships

The original `depends_on` edges carry no semantic label — you cannot tell from
them whether A *calls* B, *inherits from* B, or merely *contains* B as a method.
V1 adds a separate `relationships` list on every `CodeComponent`. Each entry is
a `TypedRelationship(source, target, rel_type)` where `rel_type` is one of:

| Type | Meaning |
|---|---|
| `calls` | A (function/method) directly calls B (function/method) |
| `imports` | A's own code body references a symbol B that was imported into A's module via `from X import B` |
| `instantiates` | A (function/method) creates an instance of class B via `B()` |
| `inherits` | A (class) directly inherits from B (class) |
| `contains` | A (class) structurally contains B (method), including `__init__` |

All relationships are derived from **static AST analysis only**. If a
relationship cannot be resolved with certainty (e.g. a call through a local
variable), no edge is emitted. Nothing is guessed.

The `imports` type specifically means: A's own AST body references the imported
name, not merely that A's file contains an import statement. Two components in
the same file can have different `imports` edges depending on what each one
actually uses.

### 2. Additional component metadata

Three new fields are extracted from the AST node during the same parsing pass
that already creates the component — no extra file reads:

- `signature` — full text signature, e.g. `"process(self, data: list) -> bool"`
- `parameters` — ordered list of `{name, annotation, default}` dicts (`self`/`cls` excluded)
- `return_type` — return annotation string, or `None` if not annotated
- `containing_class` — component ID of the enclosing class for methods, `None` otherwise

### 3. RelationshipIndex

A `RelationshipIndex` helper class builds forward and reverse lookup tables
from any component dict:

```python
index = RelationshipIndex.from_components(parser.components)

index.outgoing("mod.A.run")                        # all edges from A.run
index.outgoing("mod.A.run", rel_type="calls")      # only calls edges
index.incoming("mod.B", rel_type="instantiates")   # who instantiates B?
index.incoming("mod.Base", rel_type="inherits")    # who inherits Base?
```

The index stores each `(source, target, type)` triple exactly once.

### 4. Extended JSON output format

`save_dependency_graph` now writes:

```json
{
  "components": {
    "mod.A": { "id": "mod.A", "component_type": "class", "depends_on": [...],
               "signature": null, "parameters": [], "return_type": null,
               "containing_class": null, "relationships": [...], ... }
  },
  "relationships": [
    { "source": "mod.A.run", "target": "mod.A.process", "type": "calls" },
    { "source": "mod.A",     "target": "mod.A.run",     "type": "contains" }
  ]
}
```

`load_dependency_graph` handles both the old flat format and the new format
transparently, so existing saved graphs still load without errors.

---

## Before / after example

Given this code in `mod.py`:

```python
from utils import helper

class A:
    def __init__(self):
        self.value = 0

    def run(self):
        self.process()
        helper()

    def process(self):
        return self.value
```

**Before V1 — original `depends_on` for `mod.A`:**

```json
"depends_on": ["mod.A.run", "mod.A.process"]
```

All you know is that `A` has some relationship to `run` and `process`.
`__init__` is absent (intentionally excluded from `depends_on` for ordering).
No edge to `helper`. No labels.

**After V1 — typed `relationships` for `mod.A` and its methods:**

```json
"relationships": [
  { "source": "mod.A",         "target": "mod.A.__init__", "type": "contains" },
  { "source": "mod.A",         "target": "mod.A.run",      "type": "contains" },
  { "source": "mod.A",         "target": "mod.A.process",  "type": "contains" },
  { "source": "mod.A.run",     "target": "mod.A.process",  "type": "calls"    },
  { "source": "mod.A.run",     "target": "utils.helper",   "type": "calls"    },
  { "source": "mod.A.run",     "target": "utils.helper",   "type": "imports"  }
]
```

`depends_on` is unchanged and still drives documentation ordering exactly as before.

---

## Important design decisions

**`depends_on` was left completely unchanged.**  
It is the backbone of documentation ordering and must not be altered.
Typed relationships are additive — a new field, not a replacement.

**No new LLM calls.**  
All new information is derived from the Python AST. The docstring generation
pipeline (Reader / Searcher / Writer / Verifier) is untouched.

**Unresolved relationships are omitted.**  
If a call or import cannot be traced to a known component in the repository,
no edge is produced. The graph is a conservative lower bound — edges that exist
are reliable; a missing edge does not guarantee the relationship is absent.

**No new infrastructure.**  
No embeddings, vector databases, graph databases, or new parsers were introduced.

---

## Why these changes were made

The original DocAgent output was sufficient for generating docstrings but too
coarse to support the next phase of the research pipeline, which will involve:

- A **Retrieval Agent** that finds relevant components given a query
- A **Mapping Agent** that traces relationships between requirements and code
- A **Verification Agent** that checks whether code and documentation are consistent

All three need to know *how* components relate to each other, not just *that*
they are related. The typed relationships, enriched metadata, and
`RelationshipIndex` provide that structure without redesigning the existing system.

---

## What is intentionally not in V1

The following are known limitations that are deferred to V2:

- **Local variable type inference** — `h = HelperClass(); h.process()` is not
  resolved because tracing the type of `h` requires data-flow analysis.
- **Import aliases** — `from utils import helper as h; h()` is not resolved
  because alias mappings are not yet tracked.
- **`import module; module.func()` aliased imports** — same reason.
- **Transitive inheritance** — if `C(B)` and `B(A)`, only the direct
  `C → B` and `B → A` edges are stored; `C → A` is not inferred.
- **The Retrieval, Mapping, and Verification agents themselves** — V1 only
  prepares the structured output they will consume.
