"""Statistics and leaderboard utilities for arena results."""
from __future__ import annotations

from typing import Dict, List


def compute_matchup_result(
    name1: str, stack1: int, name2: str, stack2: int
) -> Dict:
    """
    Summarise a multi-game matchup between two agents.

    Args:
        name1, name2:   Agent display names.
        stack1, stack2: Total chips accumulated across *all* games played.

    Returns:
        Dict containing stacks, win_rates, and the winner's name (or ``'tie'``).
    """
    total = stack1 + stack2
    return {
        "player1": name1,
        "player2": name2,
        "stack1": stack1,
        "stack2": stack2,
        "win_rate1": round(stack1 / total, 4) if total > 0 else 0.5,
        "win_rate2": round(stack2 / total, 4) if total > 0 else 0.5,
        "winner": (
            name1 if stack1 > stack2 else (name2 if stack2 > stack1 else "tie")
        ),
    }


def build_leaderboard(results: List[Dict]) -> List[Dict]:
    """
    Build a ranked leaderboard from a list of matchup result dicts.

    Each result is expected to have keys:
    ``player1``, ``player2``, ``stack1``, ``stack2``, ``winner``.

    Returns:
        List of per-agent dicts sorted by ``avg_stack`` descending.
    """
    scores: Dict[str, Dict] = {}

    for r in results:
        for name, stack, other_stack in [
            (r["player1"], r["stack1"], r["stack2"]),
            (r["player2"], r["stack2"], r["stack1"]),
        ]:
            if name not in scores:
                scores[name] = {
                    "wins": 0,
                    "losses": 0,
                    "ties": 0,
                    "total_stack": 0,
                    "matchups": 0,
                }
            scores[name]["total_stack"] += stack
            scores[name]["matchups"] += 1
            if stack > other_stack:
                scores[name]["wins"] += 1
            elif stack < other_stack:
                scores[name]["losses"] += 1
            else:
                scores[name]["ties"] += 1

    leaderboard = [
        {
            "name": name,
            "wins": data["wins"],
            "losses": data["losses"],
            "ties": data["ties"],
            "avg_stack": data["total_stack"] / max(data["matchups"], 1),
        }
        for name, data in scores.items()
    ]
    return sorted(leaderboard, key=lambda x: x["avg_stack"], reverse=True)
