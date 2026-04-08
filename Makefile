PYTHON     := python
ARENA_CFG  := poker_agent_arena/arena/config/arena.yaml
RESULTS_DIR := poker_agent_arena/results

.DEFAULT_GOAL := help

# ── Help ─────────────────────────────────────────────────────────────────────
help: ## Show this help message
	@grep -E '^[a-zA-Z_%/-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ── Setup ────────────────────────────────────────────────────────────────────
install: ## Install project in editable mode with dev extras (run once)
	pip install -e ".[dev]"

# Optional: pass AGENTS=Agent1,Agent2 to any arena command to restrict which
# custom agents participate.  Default (empty) means all discovered agents.
AGENTS ?=
_AGENTS_FLAG := $(if $(AGENTS),--agents $(AGENTS),)

# -- Running & testing -----
arena: ## Run full arena (all agents by default, or AGENTS=A,B)
	$(PYTHON) -m poker_agent_arena.arena.arena $(_AGENTS_FLAG) --config $(ARENA_CFG)

baselines: ## Custom agents vs all baselines (all agents by default, or AGENTS=A,B)
	$(PYTHON) -m poker_agent_arena.arena.arena --baselines $(_AGENTS_FLAG) --config $(ARENA_CFG)

round-robin: ## Round-robin among custom agents (all by default, or AGENTS=A,B)
	$(PYTHON) -m poker_agent_arena.arena.arena --round-robin $(_AGENTS_FLAG) --config $(ARENA_CFG)

ci: ## CI-mode baseline check (exits 1 on trivial-baseline loss)
	$(PYTHON) -m poker_agent_arena.arena.arena --baselines --ci --config $(ARENA_CFG)

testperf: ## Quick 2-player test:  make testperf A1=random A2=custom
	$(PYTHON) -m poker_agent_arena.arena.testperf -a1 $(A1) -a2 $(A2)

# ── Code quality ─────────────────────────────────────────────────────────────
lint: ## Run flake8 linter on poker_agent_arena/
	$(PYTHON) -m flake8 poker_agent_arena/ --max-line-length=100 --count

format: ## Auto-format poker_agent_arena/ with black
	$(PYTHON) -m black poker_agent_arena/

# ── Environment management ───────────────────────────────────────────────────
env-%: ## Create an isolated venv for an agent  (e.g. make env-custom_agent)
	$(PYTHON) -m venv poker_agent_arena/envs/$*/venv
	poker_agent_arena/envs/$*/venv/bin/pip install -e poker_agent_arena/envs/$*/ -e .

# ── Artifacts ────────────────────────────────────────────────────────────────
submission: ## Build submission.zip → submission/custom_player.py (original format)
	rm -f submission.zip
	rm -rf submission
	mkdir -p submission
	cp poker_agent_arena/agents/custom/custom_agent.py submission/custom_player.py
	zip -r submission.zip submission
	rm -rf submission

clean: ## Remove build artifacts, caches, and submission files
	rm -rf dist/ build/ submission/ submission.zip
	rm -f $(RESULTS_DIR)/*.json
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.egg-info" -exec rm -rf {} +
	find . -name "*.pyc" -delete

.PHONY: help install arena baselines round-robin ci testperf lint format submission clean
