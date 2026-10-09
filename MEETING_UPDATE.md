# Progress Update — Meeting Notes

---

## What We Did This Week

We worked on two things: **benchmarking the DocAgent system** across multiple
models, and **extending the code analysis output** to make it more useful for
the next phase of the research.

---

## Part 1 — Benchmarking

### What we benchmarked

DocAgent's pipeline stays the same regardless of which AI model powers it. We
ran the same pipeline with four different locally-runnable models and measured
which one produces the best docstrings.

The four models tested (all run locally via Ollama):

| Model | Size |
|---|---|
| qwen2.5-coder-1.5b | 1.5 billion parameters |
| qwen2.5-coder-3b | 3 billion parameters |
| qwen3-4b | 4 billion parameters (general purpose) |
| qwen2.5-coder-7b | 7 billion parameters |

### How we measured quality

We used three independent methods:

1. **Structural completeness (no AI needed)** — We check whether the generated
   docstring actually covers everything the code requires. For example, if a
   function has parameters, does the docstring document them? If it raises an
   exception, is that mentioned? Score is 0 to 1.

2. **LLM judge scores** — A separate model reads each docstring and scores it
   on six dimensions: summary quality, description, parameter coverage,
   correctness, clarity, and conciseness. Score is 1 to 5.

3. **Head-to-head comparison (primary metric)** — We show two docstrings for
   the same function to a judge and ask which one is more useful. To avoid
   bias, every pair is shown in both orders and a "win" only counts when the
   judge agrees both times. No model judges its own output.

### Results

**qwen2.5-coder-7b came out on top overall.**

| Model | Completeness | LLM Score (avg) | Win Rate |
|---|---|---|---|
| qwen2.5-coder-7b | 0.82 | 3.82 | **17.9%** |
| qwen3-4b | 0.55 | 3.22 | 16.1% |
| qwen2.5-coder-1.5b | 0.75 | **3.99** | 13.7% |
| qwen2.5-coder-3b | 0.81 | 3.73 | 12.5% |

A few interesting takeaways:

- **Specialisation beats size.** The code-focused 3B model beat the
  general-purpose 4B model head-to-head (19 wins vs 5 losses), even though
  it has fewer parameters. For docstring writing, domain-specific training
  matters more than raw size.

- **qwen3-4b has a completeness problem.** Despite a decent LLM score, it only
  scored 0.55 on completeness — it often wrote reasonable prose but skipped
  entire sections (like parameters or return values).

- **The 1.5B model is surprisingly good at LLM scores but loses head-to-head.**
  When judges score docstrings in isolation it looks strong, but when they
  compare it directly to the 7B model's output they prefer the 7B version.
  This suggests the 1.5B model writes longer but less focused docstrings.

- **The 7B and 3B models are nearly indistinguishable in direct comparison.**
  In their head-to-head matchup: 0 wins, 0 losses, 56 ties — judges could not
  reliably tell them apart. This is useful to know for resource-constrained runs.

### What's next for benchmarking

We built the infrastructure to be model-agnostic. The next round will add models
from other families (DeepSeek Coder, CodeLlama, StarCoder, Llama 3.1) to get a
broader picture beyond the Qwen family.

---

## Part 2 — Extending the Code Analysis Output

### The original system

DocAgent already parsed every Python file and built a dependency graph — a map
of which components depend on which others. This was used purely for **ordering**:
document leaf functions first so each component's dependencies are already
documented when you get to it.

The original graph only stored one thing per component: a list of other component
IDs it depends on. No labels, no types, no explanation of *how* they are related.

### What we added

We kept the original dependency graph exactly as it was and added a layer of
**typed, labelled relationships** on top. Each relationship now says not just
*that* A is connected to B, but *how*:

| Relationship | Meaning |
|---|---|
| `calls` | A directly calls B as a function or method |
| `instantiates` | A creates a new instance of class B |
| `imports` | A's own code uses a symbol B that was imported from another module |
| `inherits` | Class A directly inherits from class B |
| `contains` | Class A structurally contains method B (including `__init__`) |

We also added richer per-component information that was already sitting in the
code but never extracted:

- **Signature** — e.g. `process(self, data: list) -> bool`
- **Parameters** — each parameter's name, type annotation, and default value
- **Return type** — the annotated return type if present
- **Containing class** — which class a method belongs to

All of this comes from the same static code analysis that was already running —
no new AI calls, no new parsers, no new infrastructure.

We also added a simple lookup tool (`RelationshipIndex`) so you can ask
questions like "what calls this function?" or "who inherits from this class?"
efficiently.

### Why this matters

The enriched output is the foundation for the next phase of the project: a
**Retrieval → Mapping → Verification pipeline** that will connect code components
to requirements and check consistency. That pipeline needs to know *how* code
components relate to each other, not just that they are related.

### What we deliberately did not do

To keep the changes minimal and safe:

- The existing pipeline behaviour is 100% unchanged
- No AI calls were added
- We did not try to infer relationships that cannot be determined from the source
  code alone (e.g. we do not trace calls through local variables like
  `obj = Foo(); obj.bar()` — that requires type inference which is V2 work)

---

## Summary

| Area | What was done |
|---|---|
| Benchmarking | Compared 4 models; qwen2.5-coder-7b is the best overall; code specialisation beats size |
| Code analysis | Added typed relationships (calls, imports, inherits, instantiates, contains) and richer metadata to the dependency graph output |
| Architecture | No changes to the DocAgent pipeline itself |
