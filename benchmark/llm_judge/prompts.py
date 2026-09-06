"""
prompts.py
----------
All judge prompts in one place.

Point-wise prompts return a score in <score>N</score> tags (1-5).
Pairwise prompt returns a winner in <winner>A</winner>, <winner>B</winner>,
or <winner>TIE</winner> tags.
"""

SYSTEM_PROMPT = (
    "You are an expert technical writer evaluating Python docstring quality. "
    "Follow instructions exactly. Always end with the required XML tag."
)

# ── Point-wise rubrics ────────────────────────────────────────────────────────

POINTWISE_RUBRICS = {
    "summary": {
        "label": "Summary Quality",
        "instruction": (
            "Evaluate the one-line summary of the docstring.\n"
            "Score 1 — Merely restates the function signature; no added value.\n"
            "Score 2 — Adds one minor detail but still vague.\n"
            "Score 3 — Provides useful context but could be more specific.\n"
            "Score 4 — Clearly explains purpose and when/why to use it.\n"
            "Score 5 — Perfectly concise and informative; captures both what and why."
        ),
    },
    "description": {
        "label": "Description Quality",
        "instruction": (
            "Evaluate the extended description of the docstring.\n"
            "Score 1 — No description, or just repeats the summary.\n"
            "Score 2 — Vague; little added context.\n"
            "Score 3 — Explains motivation or usage but misses integration context.\n"
            "Score 4 — Covers motivation, usage scenarios, and key interactions.\n"
            "Score 5 — Comprehensive; explains why the code exists, when to use it, "
            "and how it fits into the larger system."
        ),
    },
    "parameters": {
        "label": "Parameter Description Quality",
        "instruction": (
            "Evaluate the Args / Parameters section of the docstring.\n"
            "Score 1 — Just repeats type hints in natural language.\n"
            "Score 2 — Basic purpose stated, no constraints or valid values.\n"
            "Score 3 — Explains purpose plus some constraints; misses edge cases.\n"
            "Score 4 — Clear purpose, constraints, and common usage patterns.\n"
            "Score 5 — Full guidance: purpose, constraints, examples, edge cases, "
            "and impact on behaviour."
        ),
    },
    "correctness": {
        "label": "Correctness / Faithfulness",
        "instruction": (
            "Evaluate whether the docstring accurately describes what the code does.\n"
            "Score 1 — Contains statements that directly contradict the implementation.\n"
            "Score 2 — Mostly inaccurate or misleading about key behaviour.\n"
            "Score 3 — Broadly correct but misses or misrepresents some details.\n"
            "Score 4 — Accurate for all major aspects; minor omissions only.\n"
            "Score 5 — Fully faithful; every claim matches the implementation."
        ),
    },
    "clarity": {
        "label": "Clarity",
        "instruction": (
            "Evaluate how easy the docstring is to understand.\n"
            "Score 1 — Confusing, jargon-heavy, or grammatically broken.\n"
            "Score 2 — Readable but requires extra effort to interpret.\n"
            "Score 3 — Generally clear; a few awkward phrases.\n"
            "Score 4 — Clear and well-structured throughout.\n"
            "Score 5 — Immediately understandable to a developer unfamiliar with "
            "this codebase."
        ),
    },
    "conciseness": {
        "label": "Conciseness",
        "instruction": (
            "Evaluate whether the docstring avoids unnecessary verbosity.\n"
            "Score 1 — Extremely verbose; full of filler and repetition.\n"
            "Score 2 — Noticeably padded; key info buried in noise.\n"
            "Score 3 — Some redundancy but mostly on-point.\n"
            "Score 4 — Tight and focused; trivial redundancy at most.\n"
            "Score 5 — Every sentence adds value; nothing wasted."
        ),
    },
}


def pointwise_prompt(
    aspect: str,
    source_code: str,
    docstring: str,
    comp_type: str,
) -> str:
    rubric = POINTWISE_RUBRICS[aspect]
    return (
        f"You are evaluating the **{rubric['label']}** of a Python {comp_type} docstring.\n\n"
        f"### Rubric\n{rubric['instruction']}\n\n"
        f"### Source Code\n```python\n{source_code}\n```\n\n"
        f"### Docstring\n```\n{docstring}\n```\n\n"
        "Reason briefly, then output your score (1–5) in this exact format:\n"
        "<score>N</score>"
    )


# ── Pairwise prompt ───────────────────────────────────────────────────────────

def pairwise_prompt(
    source_code: str,
    docstring_a: str,
    docstring_b: str,
    comp_type: str,
) -> str:
    return (
        f"You are comparing two docstrings for the same Python {comp_type}.\n\n"
        "Judge which docstring is more useful to a developer who is reading the "
        "code for the first time. Consider accuracy, clarity, completeness, and "
        "conciseness together.\n\n"
        f"### Source Code\n```python\n{source_code}\n```\n\n"
        f"### Docstring A\n```\n{docstring_a}\n```\n\n"
        f"### Docstring B\n```\n{docstring_b}\n```\n\n"
        "Give a brief explanation (2–3 sentences), then output exactly one of:\n"
        "<winner>A</winner>  or  <winner>B</winner>  or  <winner>TIE</winner>"
    )
