"""
Arena runner — evaluates poker agents via simulation.

Modes (configurable via arena/config/arena.yaml):
  --baselines       Each custom agent plays every baseline agent.
  --round-robin     All custom agents play each other (round-robin).
  Default: both modes run in sequence.

CI mode (--ci):
  Exits with code 1 if any custom agent loses to a 'trivial' baseline
  (configured under ``arena.ci_trivial_baselines`` in arena.yaml).

Usage:
    python -m poker_agent_arena.arena.arena
    python -m poker_agent_arena.arena.arena --baselines
    python -m poker_agent_arena.arena.arena --round-robin
    python -m poker_agent_arena.arena.arena --baselines --ci
    python -m poker_agent_arena.arena.arena --agents MyAgent,CFRAgent
    python -m poker_agent_arena.arena.arena --config path/to/arena.yaml
"""
from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path
from typing import List, Tuple, Type

import yaml

from pypokerengine.api.game import setup_config, start_poker
from pypokerengine.players import BasePokerPlayer

# Ensure the project root is on sys.path so imports work without `pip install -e .`
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from poker_agent_arena.utils.loader import discover_custom_agents, load_agent_class  # noqa: E402
from poker_agent_arena.utils.stats import build_leaderboard, compute_matchup_result  # noqa: E402

DEFAULT_CONFIG = Path(__file__).parent / "config" / "arena.yaml"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"

AgentSpec = Tuple[str, Type[BasePokerPlayer]]


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def load_config(path: Path) -> dict:
    with open(path) as fh:
        return yaml.safe_load(fh)


def agents_from_config(entries: list) -> List[AgentSpec]:
    return [
        (entry["name"], load_agent_class(entry["module"], entry["class"]))
        for entry in (entries or [])
    ]


# ---------------------------------------------------------------------------
# Core matchup runner
# ---------------------------------------------------------------------------

def run_matchup(
    name1: str,
    cls1: Type[BasePokerPlayer],
    name2: str,
    cls2: Type[BasePokerPlayer],
    game_cfg: dict,
) -> dict:
    """Run ``num_games`` games between two agent *classes*; return aggregated result."""
    num_games = game_cfg["num_games"]
    stack1_total = stack2_total = 0

    for _ in range(num_games):
        cfg = setup_config(
            max_round=game_cfg["max_round"],
            initial_stack=game_cfg["initial_stack"],
            small_blind_amount=game_cfg["small_blind_amount"],
        )
        # Fresh instances each game so stateful agents reset properly
        cfg.register_player(name=name1, algorithm=cls1())
        cfg.register_player(name=name2, algorithm=cls2())
        result = start_poker(cfg, verbose=0)
        stack1_total += result["players"][0]["stack"]
        stack2_total += result["players"][1]["stack"]

    return compute_matchup_result(name1, stack1_total, name2, stack2_total)


# ---------------------------------------------------------------------------
# Test modes
# ---------------------------------------------------------------------------

def run_vs_baselines(
    custom_agents: List[AgentSpec],
    baseline_agents: List[AgentSpec],
    game_cfg: dict,
) -> List[dict]:
    print("\n=== Agents vs Baselines ===\n")
    results = []
    for ca_name, ca_cls in custom_agents:
        for ba_name, ba_cls in baseline_agents:
            result = run_matchup(ca_name, ca_cls, ba_name, ba_cls, game_cfg)
            results.append(result)
            label = _outcome_label(result, ca_name)
            print(
                f"  {ca_name:28s} vs {ba_name:28s}"
                f"  [{label}]"
                f"  ({result['stack1']:>9,} vs {result['stack2']:>9,})"
            )
    return results


def run_round_robin(
    custom_agents: List[AgentSpec],
    game_cfg: dict,
) -> List[dict]:
    if len(custom_agents) < 2:
        print("\n[round-robin] Need at least 2 custom agents — skipping.\n")
        return []

    print("\n=== Round-Robin Tournament ===\n")
    results = []
    for (n1, c1), (n2, c2) in combinations(custom_agents, 2):
        result = run_matchup(n1, c1, n2, c2, game_cfg)
        results.append(result)
        label = _outcome_label(result, n1)
        print(
            f"  {n1:28s} vs {n2:28s}"
            f"  [{label}]"
            f"  ({result['stack1']:>9,} vs {result['stack2']:>9,})"
        )
    return results


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _outcome_label(result: dict, pov_name: str) -> str:
    if result["winner"] == pov_name:
        return "WIN "
    if result["winner"] == "tie":
        return "TIE "
    return "LOSS"


def print_leaderboard(results: List[dict]) -> None:
    if not results:
        return
    board = build_leaderboard(results)
    header = f"  {'#':<4} {'Name':<30} {'W':>4} {'L':>4} {'T':>4} {'Avg Stack':>12}"
    print("\n=== Leaderboard ===\n")
    print(header)
    print("  " + "-" * (len(header) - 2))
    for rank, entry in enumerate(board, 1):
        print(
            f"  {rank:<4} {entry['name']:<30}"
            f" {entry['wins']:>4} {entry['losses']:>4} {entry['ties']:>4}"
            f" {entry['avg_stack']:>12,.0f}"
        )
    print()


# ---------------------------------------------------------------------------
# CI check
# ---------------------------------------------------------------------------

def ci_check(
    results: List[dict],
    custom_names: List[str],
    trivial_baselines: List[str],
) -> bool:
    """Return True (pass) if no custom agent lost to a trivial baseline."""
    failures = [
        r for r in results
        if r["player1"] in custom_names
        and r["player2"] in trivial_baselines
        and r["winner"] == r["player2"]
    ]
    if failures:
        print("\n[CI FAIL] Custom agent(s) lost to trivial baseline(s):")
        for f in failures:
            print(
                f"  {f['player1']} lost to {f['player2']}"
                f" ({f['stack1']:,} vs {f['stack2']:,})"
            )
        return False
    print("\n[CI PASS] All custom agents passed trivial-baseline checks.")
    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Poker Agent Arena — compare agents via simulation."
    )
    parser.add_argument(
        "--config", type=Path, default=DEFAULT_CONFIG,
        help="Path to arena.yaml (default: arena/config/arena.yaml)"
    )
    parser.add_argument(
        "--baselines", action="store_true",
        help="Test every custom agent against all baselines"
    )
    parser.add_argument(
        "--round-robin", action="store_true",
        help="Run a round-robin tournament among custom agents"
    )
    parser.add_argument(
        "--ci", action="store_true",
        help="Exit 1 if any custom agent loses to a trivial baseline"
    )
    parser.add_argument(
        "--agents", type=str, default=None,
        help="Comma-separated list of custom agent names to include (default: all discovered)"
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    game_cfg = cfg["game"]
    arena_cfg = cfg.get("arena", {})

    results_file = RESULTS_DIR / "arena_results.json"

    run_baselines = args.baselines or (
        not args.round_robin and arena_cfg.get("test_vs_baselines", True)
    )
    run_rr = args.round_robin or (
        not args.baselines and arena_cfg.get("round_robin", True)
    )

    baseline_agents = agents_from_config(cfg.get("baselines", []))

    # Custom agents: merge YAML entries + auto-discovered from custom/ folder.
    # YAML entries take priority; auto-discovered agents fill in the rest.
    yaml_custom = agents_from_config(cfg.get("custom_agents", []))
    seen = {name for name, _ in yaml_custom}
    discovered = discover_custom_agents()
    custom_agents = list(yaml_custom)
    for name, cls in discovered:
        if name not in seen:
            custom_agents.append((name, cls))
            seen.add(name)

    # Filter to specific agents if --agents was supplied.
    if args.agents:
        requested = [a.strip() for a in args.agents.split(",")]
        available = {name: cls for name, cls in custom_agents}
        missing = [a for a in requested if a not in available]
        if missing:
            print(f"[arena] Unknown agent(s): {', '.join(missing)}")
            print(f"        Available: {', '.join(available)}")
            sys.exit(1)
        custom_agents = [(name, available[name]) for name in requested]

    if not custom_agents:
        print("[arena] No custom agents found in config or custom/ folder.")
        sys.exit(1)

    print(f"Custom agents: {', '.join(n for n, _ in custom_agents)}")
    print(f"Baseline agents: {', '.join(n for n, _ in baseline_agents)}")

    all_results: List[dict] = []

    if run_baselines:
        all_results.extend(run_vs_baselines(custom_agents, baseline_agents, game_cfg))

    if run_rr:
        all_results.extend(run_round_robin(custom_agents, game_cfg))

    print_leaderboard(all_results)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_file.write_text(json.dumps(all_results, indent=2))
    print(f"Results saved to {results_file}")

    if args.ci:
        trivial = arena_cfg.get("ci_trivial_baselines", ["FoldAgent"])
        custom_names = [a[0] for a in custom_agents]
        if not ci_check(all_results, custom_names, trivial):
            sys.exit(1)


if __name__ == "__main__":
    main()
