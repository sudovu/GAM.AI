"""GAM.AI User Interface Package."""
import os
import sys
import importlib.util

_ui_dir = os.path.dirname(__file__)
for _mod_name in ("cli", "web"):
    _mod_file = os.path.join(_ui_dir, f"{_mod_name}.py")
    if os.path.exists(_mod_file):
        _spec = importlib.util.spec_from_file_location(f"gam_ai.ui.{_mod_name}", _mod_file)
        if _spec and _spec.loader:
            _mod = importlib.util.module_from_spec(_spec)
            sys.modules[f"gam_ai.ui.{_mod_name}"] = _mod
            _spec.loader.exec_module(_mod)
