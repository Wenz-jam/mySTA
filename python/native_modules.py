import importlib
import sys
from pathlib import Path


def import_native_module(name: str):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError:
        repo_root = Path(__file__).resolve().parent.parent
        candidates = [
            repo_root / "build" / "shared" / "src" / "user-interface",
        ]
        for module_dir in candidates:
            if module_dir.exists():
                sys.path.insert(0, str(module_dir))
                try:
                    return importlib.import_module(name)
                except ModuleNotFoundError:
                    pass
        raise
