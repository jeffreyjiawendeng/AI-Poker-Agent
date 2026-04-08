# Getting Started

## 1. Create a Python environment

```bash
conda create -n CompSci683 python=3.11
conda activate CompSci683
```

Or use `pyenv`/`venv` -- any Python >= 3.8 works.

## 2. Install the project

```bash
make install
```

This runs `pip install -e ".[dev]"`, installing the project in editable mode along with PyPokerEngine, PyYAML, flake8, and black.

## 3. Verify the install

```bash
python -c "import pypokerengine; print('OK')"
```

## 4. Run a test

```bash
make arena
```

Runs 50 games x 100 rounds to confirm everything works. It pits the baseline agents (Fold, Call, Raise, Random, RuleBased) against the custom agent(s).

## 5. Build your own agent

Edit `poker_agent_arena/agents/custom/custom_agent.py`. The key method is `declare_action`:

```python
def declare_action(self, valid_actions, hole_card, round_state):
    # valid_actions: [{"action": "fold"}, {"action": "call"}, {"action": "raise"}]
    # hole_card: your two cards (e.g. ["SA", "HK"])
    # round_state: full game state dict
    return "call"  # return "fold", "call", or "raise"
```

You can rename the class (e.g. `MCTSAgent`) or add more `.py` files to the
`custom/` folder -- all `BasePokerPlayer` subclasses are auto-discovered.
No YAML editing is needed unless you want to override a name.

## 6. Run the arena

| Command            | What it does                                                     |
| ------------------ | ---------------------------------------------------------------- |
| `make arena`       | Baselines + round-robin (50 games x 100 rounds, stack 1000, SB 10) |
| `make baselines`   | Test your agent against all baseline agents only                 |
| `make round-robin` | Round-robin among custom agents only                             |
| `make ci`          | CI check -- fails if your agent loses to FoldAgent               |

All commands use the same settings from `arena/config/arena.yaml`. Edit that file to change game parameters.

## 7. Test two specific agents head-to-head

Use short aliases -- no need to type full module paths:

```bash
make testperf A1=random A2=custom
make testperf A1=fold A2=call
make testperf A1=rule A2=custom
```

Built-in aliases: `fold`, `call`, `raise`, `random`, `rule`, `custom`

For custom agents you add to the `custom/` folder, use `filename:ClassName`:

```bash
make testperf A1=my_agent:MyAgent A2=random
```

Full `module.path:ClassName` specs still work if needed.

## 8. Code quality

```bash
make lint      # flake8 linter
make format    # auto-format with black
```

## 9. Build a submission

```bash
make submission
```

Creates `submission.zip` containing your `custom_agent.py` renamed to `custom_player.py`.

## 10. Clean up

```bash
make clean     # removes build artifacts, caches, results
```

---

**TL;DR workflow**: `make install` > edit `custom_agent.py` > `make arena` to test > `make submission` to package.
