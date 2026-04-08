# Reference

## Table of Contents

1. [Adding an Agent](#adding-an-agent)
2. [Evaluation Commands](#evaluation-commands)
3. [Configuration](#configuration)
4. [Contributing](#contributing)
5. [Project Layout](#project-layout)


---


## Adding an Agent

### Create the agent file

Place your agent under `agents/custom/`. Name the file after your agent:

```
agents/custom/my_agent.py
```

Subclass `BasePokerPlayer` and implement `declare_action`:

```python
from pypokerengine.players import BasePokerPlayer

class MyAgent(BasePokerPlayer):

    def declare_action(self, valid_actions, hole_card, round_state):
        # valid_actions always has at least [fold, call].
        # raise is at index 2 when available.
        # Return the action string: "fold", "call", or "raise".
        return valid_actions[1]["action"]  # example: always call

    def receive_game_start_message(self, game_info): pass
    def receive_round_start_message(self, round_count, hole_card, seats): pass
    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state): pass
    def receive_round_result_message(self, winners, hand_info, round_state): pass

def setup_ai():
    return MyAgent()
```

### valid_actions format

```python
[
    {"action": "fold"},
    {"action": "call"},           # amount already paid by engine
    {"action": "raise"}           # only present when raise limit not reached
]
```

### hole_card format

```python
["C2", "HA"]   # suit+rank strings: C=Club D=Diamond H=Heart S=Spade
```

### round_state keys

`street`, `pot`, `community_card`, `seats`, `action_histories`, `dealer_btn`, etc.

### Register the agent

Agents in the `custom/` folder are **auto-discovered** -- no YAML editing
required. Any `.py` file in `agents/custom/` that defines a `BasePokerPlayer`
subclass is automatically picked up by `make arena`, `make baselines`,
`make round-robin`, and `make quick`.

Optionally, you can still list agents explicitly in `arena/config/arena.yaml`
under `custom_agents` (explicit entries take priority over auto-discovery).

### Declare dependencies

If your agent needs extra libraries (e.g. PyTorch, NumPy), add them to
`envs/custom_agent/pyproject.toml`:

```toml
dependencies = [
    "PyPokerEngine",
    "pyyaml>=6.0",
    "numpy>=1.24",
    "torch>=2.0",
]
```

Create an isolated virtualenv for your agent:

```bash
python -m venv envs/custom_agent/venv
source envs/custom_agent/venv/bin/activate
pip install -e envs/custom_agent/ -e .
```

### Test your agent locally

```bash
make testperf A1=my_agent:MyAgent A2=random
make arena
```


---


## Evaluation Commands

All evaluation commands run real poker simulations -- no mocked or synthetic data. Agents play full games with shuffled decks, blinds, and hand evaluation via PyPokerEngine.

Custom agents are auto-discovered from the `agents/custom/` folder. Every
`BasePokerPlayer` subclass found there participates automatically.

Baselines are never tested against each other. The two test modes are:

- **baselines** -- each custom agent vs each baseline, one-on-one.
- **round-robin** -- each custom agent vs every other custom agent.

### Make commands

| Command | Purpose | Results file |
| ------- | ------- | ------------ |
| `make arena` | Baselines + round-robin | `arena_results.json` |
| `make baselines` | Custom agents vs all baselines only | `arena_results.json` |
| `make round-robin` | Round-robin among custom agents only | `arena_results.json` |
| `make ci` | Baselines; exit 1 on loss to FoldAgent | `arena_results.json` |
| `make testperf A1=<agent> A2=<agent>` | Head-to-head between two agents | (printed only) |

All commands use the same game settings from `arena/config/arena.yaml`.
Pass `AGENTS=A,B` to restrict which custom agents participate.

Results are saved to `poker_agent_arena/results/arena_results.json`.

### Agent aliases for testperf

| Alias    | Agent          |
| -------- | -------------- |
| `fold`   | FoldAgent      |
| `call`   | CallAgent      |
| `raise`  | RaiseAgent     |
| `random` | RandomAgent    |
| `rule`   | RuleBasedAgent |
| `custom` | CustomAgent    |

For custom agents in the `custom/` folder, use `filename:ClassName`:

```bash
make testperf A1=my_agent:MyAgent A2=random
```

Full `module.path:ClassName` specs still work.

### Python CLI: arena runner

```bash
python -m poker_agent_arena.arena.arena [FLAGS]
```

| Flag             | Description                                             |
| ---------------- | ------------------------------------------------------- |
| (no flags)       | Runs both baselines and round-robin                     |
| `--baselines`    | Only test custom agents vs all baselines                |
| `--round-robin`  | Only run round-robin among custom agents                |
| `--ci`           | Exit code 1 if a custom agent loses to FoldAgent        |
| `--agents A,B`   | Only include the listed custom agents                   |
| `--config <path>`| Use a custom arena.yaml config file                     |

Flags can be combined:

```bash
python -m poker_agent_arena.arena.arena --baselines
python -m poker_agent_arena.arena.arena --baselines --ci
python -m poker_agent_arena.arena.arena --round-robin
```

### Python CLI: two-agent performance test

```bash
python -m poker_agent_arena.arena.testperf -a1 <agent> -a2 <agent> [OPTIONS]
```

| Flag                  | Default      | Description                            |
| --------------------- | ------------ | -------------------------------------- |
| `-a1`, `--agent1`     | (required)   | Agent 1 (alias, file:Class, or full)   |
| `-a2`, `--agent2`     | (required)   | Agent 2 (alias, file:Class, or full)   |
| `-n1`, `--name1`      | class name   | Display name for agent 1               |
| `-n2`, `--name2`      | class name   | Display name for agent 2               |
| `--num-games <N>`     | 50           | Number of games to play                |
| `--max-round <N>`     | 100          | Max rounds per game                    |
| `--initial-stack <N>` | 1000         | Starting chip stack per player         |
| `--small-blind <N>`   | 10           | Small blind amount (big blind is 2x)   |

```bash
python -m poker_agent_arena.arena.testperf -a1 random -a2 custom
python -m poker_agent_arena.arena.testperf -a1 custom -a2 call --num-games 100 --max-round 500
python -m poker_agent_arena.arena.testperf -a1 my_agent:MyAgent -a2 rule
```

### Reading results

All commands write to `poker_agent_arena/results/arena_results.json`.

Each entry is a matchup:

```json
{
  "player1": "CustomAgent",
  "player2": "RandomAgent",
  "stack1": 98432,
  "stack2": 101568,
  "win_rate1": 0.4921,
  "win_rate2": 0.5079,
  "winner": "RandomAgent"
}
```


---


## Configuration

All arena defaults are in `poker_agent_arena/arena/config/arena.yaml`. Edit this file to change game settings for the entire project. The `--config` flag lets you point to an alternate config file.

| Setting                       | Default       | Description                              |
| ----------------------------- | ------------- | ---------------------------------------- |
| `game.num_games`              | 50            | Games per matchup                        |
| `game.max_round`              | 100           | Max rounds per game                      |
| `game.initial_stack`          | 1000          | Starting chips                           |
| `game.small_blind_amount`     | 10            | Small blind (big blind is 2x = 20)       |
| `arena.test_vs_baselines`     | true          | Run baseline tests before round-robin    |
| `arena.round_robin`           | true          | Run round-robin among custom agents      |
| `arena.ci_trivial_baselines`  | [FoldAgent]   | CI fails if custom agent loses to these  |


---


## Contributing

### Prerequisites

- Python >= 3.8
- `make` (via Git Bash, WSL, or MSYS2 on Windows)

### First-time setup

```bash
git clone <repo>
cd AI-Poker-Agent
pip install -e ".[dev]"
```

### Workflow

1. Branch from `main`:
   ```bash
   git checkout -b feature/my-agent
   ```
2. Add or modify your agent under `agents/custom/`.
3. Register it in `arena/config/arena.yaml`.
4. Run local checks before pushing:
   ```bash
   make lint
   make format
   make ci
   ```
5. Open a PR. GitHub Actions runs lint, then baseline tests, then round-robin on merge.

### CI / CD overview

| Job                    | Trigger              | What it checks                                      |
| ---------------------- | -------------------- | --------------------------------------------------- |
| Lint                   | PR + push to main    | flake8 on agents/, arena/, utils/                   |
| Agents vs Baselines    | PR + push to main    | Custom agents must beat FoldAgent (configurable)    |
| Round-Robin            | Push to main only    | Full tournament; results uploaded as artifact        |

Results JSON is uploaded as a GitHub Actions artifact after every run.

### Code style

- Formatter: `black` -- run `make format` to auto-fix.
- Linter: `flake8`, max line length 100.
- Agent files must expose a `setup_ai()` function for compatibility.

### Pre-commit hook (optional)

```bash
echo '#!/bin/sh
make lint
make format
git add -u
' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Make utility commands

| Command           | Description                                      |
| ----------------- | ------------------------------------------------ |
| `make install`    | Install project in editable mode with dev extras |
| `make lint`       | Run flake8 linter                                |
| `make format`     | Auto-format with black                           |
| `make submission` | Build submission.zip                             |
| `make clean`      | Remove build artifacts, caches, results          |


---


## Project Layout

```
agents/
  baseline/     Five fixed baseline agents (do not rename/remove)
  custom/       Your agent(s) go here
arena/
  arena.py      Main arena runner (--baselines, --round-robin, --ci)
  testperf.py   Quick 2-player head-to-head test
  config/
    arena.yaml  Game settings + agent registry
utils/
  loader.py     Dynamic agent loading
  stats.py      Win-rate + leaderboard helpers
envs/
  <agent>/
    pyproject.toml  Per-agent isolated dependency declaration
docs/           Documentation (you are here)
pypokerengine/  Poker simulation engine (do not modify)
```
