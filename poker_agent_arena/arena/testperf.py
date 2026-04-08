"""
Two-agent side-by-side performance test.

Usage:
    # Short aliases -- just use the agent nickname:
    python -m poker_agent_arena.arena.testperf -a1 random -a2 custom

    # Full spec still works:
    python -m poker_agent_arena.arena.testperf \\
        -a1 poker_agent_arena.agents.baseline.random_agent:RandomAgent \\
        -a2 poker_agent_arena.agents.custom.custom_agent:CustomAgent

    # Custom agents in the custom/ folder by filename:classname:
    python -m poker_agent_arena.arena.testperf -a1 my_agent:MyAgent -a2 random

Built-in aliases: fold, call, raise, random, rule, custom
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
import time
from pathlib import Path
from typing import Type

from pypokerengine.api.game import setup_config, start_poker
from pypokerengine.players import BasePokerPlayer

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from poker_agent_arena.utils.loader import load_agent_class  # noqa: E402
from poker_agent_arena.utils.stats import compute_matchup_result  # noqa: E402

# ── Agent aliases ────────────────────────────────────────────────────────────
# Maps short names to "module:ClassName" specs.
AGENT_ALIASES = {
    "fold":   "poker_agent_arena.agents.baseline.fold_agent:FoldAgent",
    "call":   "poker_agent_arena.agents.baseline.call_agent:CallAgent",
    "raise":  "poker_agent_arena.agents.baseline.raise_agent:RaiseAgent",
    "random": "poker_agent_arena.agents.baseline.random_agent:RandomAgent",
    "rule":   "poker_agent_arena.agents.baseline.rule_based_agent:RuleBasedAgent",
    "custom": "poker_agent_arena.agents.custom.custom_agent:CustomAgent",
}


def run_testperf(
    name1: str,
    cls1: Type[BasePokerPlayer],
    name2: str,
    cls2: Type[BasePokerPlayer],
    num_games: int = 10,
    max_round: int = 20,
    initial_stack: int = 1000,
    small_blind: int = 10,
) -> dict:
    """Run ``num_games`` head-to-head games and return a matchup result dict."""
    stack1_total = stack2_total = 0

    for game in range(1, num_games + 1):
        print(f"  Game {game}/{num_games}", end="\r", flush=True)
        cfg = setup_config(
            max_round=max_round,
            initial_stack=initial_stack,
            small_blind_amount=small_blind,
        )
        cfg.register_player(name=name1, algorithm=cls1())
        cfg.register_player(name=name2, algorithm=cls2())
        result = start_poker(cfg, verbose=0)
        stack1_total += result["players"][0]["stack"]
        stack2_total += result["players"][1]["stack"]

    print()  # clear the \r line
    return compute_matchup_result(name1, stack1_total, name2, stack2_total)


def _resolve_alias(spec: str) -> str:
    """
    Resolve a short alias or custom-folder shorthand to a full spec.

    Accepted formats (in priority order):
      1. Built-in alias:       ``random``, ``call``, ``fold``, etc.
      2. Custom folder short:  ``my_agent:MyAgent``  (looks in agents/custom/)
      3. Full spec:            ``poker_agent_arena.agents.baseline.random_agent:RandomAgent``
    """
    lower = spec.lower().strip()
    if lower in AGENT_ALIASES:
        return AGENT_ALIASES[lower]

    # If it has a colon but no dots before the colon, treat as custom folder shorthand
    if ":" in spec:
        module_part, _ = spec.rsplit(":", 1)
        if "." not in module_part:
            return f"poker_agent_arena.agents.custom.{module_part}:{spec.rsplit(':', 1)[1]}"

    return spec


def _parse_agent_spec(spec: str):
    """Parse an alias, shorthand, or full ``'module.path:ClassName'`` into ``(module, classname)``."""
    resolved = _resolve_alias(spec)
    if ":" not in resolved:
        raise ValueError(
            f"Invalid agent spec '{spec}'. "
            "Use a built-in alias (fold, call, raise, random, rule, custom), "
            "'filename:ClassName' for custom agents, or the full "
            "'module.dotted.path:ClassName' format."
        )
    module, cls = resolved.rsplit(":", 1)
    return module, cls


def main() -> None:
    parser = argparse.ArgumentParser(description="Two-agent performance test")
    parser.add_argument(
        "-a1", "--agent1", required=True,
        help="Agent 1: alias (fold/call/raise/random/rule/custom), "
             "'file:Class' for custom/, or full 'module.path:Class'"
    )
    parser.add_argument("-n1", "--name1", default=None, help="Display name for agent 1")
    parser.add_argument(
        "-a2", "--agent2", required=True,
        help="Agent 2: alias (fold/call/raise/random/rule/custom), "
             "'file:Class' for custom/, or full 'module.path:Class'"
    )
    parser.add_argument("-n2", "--name2", default=None, help="Display name for agent 2")
    parser.add_argument("--num-games", type=int, default=50)
    parser.add_argument("--max-round", type=int, default=100)
    parser.add_argument("--initial-stack", type=int, default=1000)
    parser.add_argument("--small-blind", type=int, default=10)
    args = parser.parse_args()

    mod1, cls1_name = _parse_agent_spec(args.agent1)
    mod2, cls2_name = _parse_agent_spec(args.agent2)

    cls1 = load_agent_class(mod1, cls1_name)
    cls2 = load_agent_class(mod2, cls2_name)

    name1 = args.name1 or cls1_name
    name2 = args.name2 or cls2_name

    num_games = args.num_games
    max_round = args.max_round
    initial_stack = args.initial_stack
    small_blind = args.small_blind

    print(f"\n{name1} vs {name2}")
    print(
        f"  {num_games} games x {max_round} rounds"
        f" | stack {initial_stack:,} | SB {small_blind}\n"
    )

    t0 = time.time()
    result = run_testperf(
        name1, cls1, name2, cls2,
        num_games, max_round, initial_stack, small_blind,
    )

    print(f"\nResults after {num_games} games:")
    print(
        f"  {name1:32s}: {result['stack1']:>12,}"
        f"  (win rate {result['win_rate1']:.1%})"
    )
    print(
        f"  {name2:32s}: {result['stack2']:>12,}"
        f"  (win rate {result['win_rate2']:.1%})"
    )
    if result["winner"] == "tie":
        print("\n  Result: TIE")
    else:
        print(f"\n  Winner: {result['winner']}")
    print(f"  Time:   {time.time() - t0:.2f}s\n")


if __name__ == "__main__":
    main()
