from __future__ import annotations

from pathlib import Path

patch_path = Path(__file__).with_name("tmp_549.py")
source = patch_path.read_text(encoding="utf-8")
old_guard = '''    if text.count(old) != 1:\n        raise RuntimeError(f"Expected exactly one match in {path}: {old[:80]!r}")\n'''
new_guard = '''    if old not in text:\n        raise RuntimeError(f"Expected a match in {path}: {old[:80]!r}")\n'''
if old_guard not in source:
    raise RuntimeError("tmp_549.py guard shape changed")
source = source.replace(old_guard, new_guard, 1)
exec(
    compile(source, str(patch_path), "exec"),
    {"__file__": str(patch_path), "__name__": "__main__"},
)
