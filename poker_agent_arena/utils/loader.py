"""Dynamic agent loading utilities."""
from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import List, Tuple, Type

from pypokerengine.players import BasePokerPlayer


def load_agent_class(module_path: str, class_name: str) -> Type[BasePokerPlayer]:
    """
    Dynamically import and return an agent class.

    Args:
        module_path: Dotted module path, e.g. ``'agents.baseline.fold_agent'``.
        class_name:  Class name, e.g. ``'FoldAgent'``.

    Returns:
        The uninstantiated agent class.

    Raises:
        ImportError:    If the module cannot be found.
        AttributeError: If the class does not exist inside the module.
    """
    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise ImportError(
            f"Could not import module '{module_path}'. "
            "Ensure you ran `pip install -e .` from the project root "
            f"and that the module path in arena.yaml is correct.\n"
            f"Original error: {exc}"
        ) from exc

    if not hasattr(module, class_name):
        raise AttributeError(
            f"Module '{module_path}' has no attribute '{class_name}'. "
            "Check the 'class' field in arena/config/arena.yaml."
        )

    return getattr(module, class_name)


def instantiate_agent(module_path: str, class_name: str) -> BasePokerPlayer:
    """Load and return a freshly instantiated agent."""
    return load_agent_class(module_path, class_name)()


CUSTOM_AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents" / "custom"


def discover_custom_agents(
    custom_dir: Path = CUSTOM_AGENTS_DIR,
) -> List[Tuple[str, Type[BasePokerPlayer]]]:
    """Auto-discover all BasePokerPlayer subclasses in the custom agents folder.

    Scans every non-underscore ``.py`` file in *custom_dir*, imports the module,
    and collects any class that directly subclasses ``BasePokerPlayer``.

    Returns a list of ``(ClassName, class)`` tuples sorted by class name.
    """
    agents: List[Tuple[str, Type[BasePokerPlayer]]] = []
    for py_file in sorted(custom_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        module_name = f"poker_agent_arena.agents.custom.{py_file.stem}"
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BasePokerPlayer) and obj is not BasePokerPlayer:
                agents.append((name, obj))
    return agents
