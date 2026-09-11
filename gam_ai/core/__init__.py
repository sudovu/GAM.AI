"""GAM.AI Core Architecture Package."""

import os
import sys
import importlib.util

# Ensure dynamically discovered subpackages are registered reliably
_core_dir = os.path.dirname(__file__)
_network_dir = os.path.join(_core_dir, "network")

if os.path.exists(_network_dir):
    _spec = importlib.util.spec_from_file_location(
        "gam_ai.core.network",
        os.path.join(_network_dir, "__init__.py"),
        submodule_search_locations=[_network_dir]
    )
    if _spec and _spec.loader:
        _mod = importlib.util.module_from_spec(_spec)
        sys.modules["gam_ai.core.network"] = _mod
        _spec.loader.exec_module(_mod)
