"""Structural test enforcing zero runtime JSON parsing across the application."""
from pathlib import Path
import pytest


def test_no_runtime_json_parsing():
    """
    Assert that neither 'ast.literal_eval' nor 'import ast' appears
    anywhere in pages/ or src/ (excluding src/preprocessing.py).
    """
    root = Path(__file__).resolve().parent.parent
    
    files_to_check = list((root / "pages").glob("*.py"))
    src_files = [f for f in (root / "src").glob("*.py") if f.name != "preprocessing.py"]
    files_to_check.extend(src_files)
    
    violations = []
    for file_path in files_to_check:
        content = file_path.read_text(encoding="utf-8")
        if "ast.literal_eval" in content or "import ast" in content or "from ast import" in content:
            violations.append(str(file_path.relative_to(root)))
            
    assert len(violations) == 0, f"Found runtime JSON parsing in forbidden modules: {violations}"
