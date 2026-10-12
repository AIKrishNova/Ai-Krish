"""Fallback runner for dependency-free tests when pytest is not installed. Not a pytest replacement."""
import importlib, sys, traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
mod = importlib.import_module("tests.test_core_logic")
passed = failed = 0
for name in sorted(n for n in dir(mod) if n.startswith("test_")):
    try:
        getattr(mod, name)(); passed += 1; print(f"PASS {name}")
    except Exception:
        failed += 1; print(f"FAIL {name}"); traceback.print_exc()
print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
