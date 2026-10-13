"""
aggregate.py
------------
Combines objective completeness + pointwise scores + pairwise win rates
into a single summary dict used by the report generator.

Exposed as a function so run_benchmark.py can call it directly without
re-reading files.
"""

from typing import Any, Dict, List, Optional


def build_summary(
    model_names: List[str],
    completeness_summary: Dict[str, Any],
    pointwise_summary: Dict[str, Any],
    win_rate_ranking: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Returns a list of dicts, one per model, sorted by win_rate descending.

    Each dict:
    {
      "model": str,
      "completeness": float,
      "summary_score": float | None,
      "description_score": float | None,
      "parameters_score": float | None,
      "correctness_score": float | None,
      "clarity_score": float | None,
      "conciseness_score": float | None,
      "llm_overall": float | None,   # mean of the 6 pointwise dimensions
      "wins": int,
      "losses": int,
      "ties": int,
      "total_decisions": int,
      "win_rate": float,
    }
    """
    win_map = {entry["model"]: entry for entry in win_rate_ranking}

    rows = []
    for model in model_names:
        comp = completeness_summary.get(model, {})
        pw = pointwise_summary.get(model, {})
        wr = win_map.get(model, {})

        aspect_scores = []
        row: Dict[str, Any] = {"model": model}

        row["completeness"] = round(comp.get("average_score", 0.0), 3)

        for aspect in ["summary", "description", "parameters", "correctness", "clarity", "conciseness"]:
            val = pw.get(aspect, {}).get("average")
            row[f"{aspect}_score"] = val
            if val is not None:
                aspect_scores.append(val)

        row["llm_overall"] = (
            round(sum(aspect_scores) / len(aspect_scores), 3) if aspect_scores else None
        )
        row["wins"] = wr.get("wins", 0)
        row["losses"] = wr.get("losses", 0)
        row["ties"] = wr.get("ties", 0)
        row["total_decisions"] = wr.get("total", 0)
        row["win_rate"] = wr.get("win_rate", 0.0)
        rows.append(row)

    rows.sort(key=lambda r: r["win_rate"], reverse=True)
    return rows
