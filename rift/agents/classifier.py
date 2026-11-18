"""
FailureClassifierAgent - Identifies, classifies, and formats errors into the 6 canonical types.
Generates exact test-case match outputs required by judges.
"""

import re
import ast
import json
import logging
import tokenize
import io
import subprocess
from pathlib import Path
from typing import Dict, Any, List

from rift.state import AgentState

logger = logging.getLogger("rift.agents.classifier")

# Exactly the 6 canonical bug types required by RIFT 2026:
# LINTING, SYNTAX, LOGIC, TYPE_ERROR, IMPORT, INDENTATION
BUG_TYPES = ["LINTING", "SYNTAX", "LOGIC", "TYPE_ERROR", "IMPORT", "INDENTATION"]


def format_expected_dashboard_output(bug_type: str, file_path: str, line_no: int, fix_action: str) -> str:
    """Format string to match Hackathon exact evaluation test cases.
    Example: LINTING error in src/utils.py line 15 → Fix: remove the import statement
    """
    clean_file = file_path.replace("\\", "/")
    return f"{bug_type} error in {clean_file} line {line_no} → Fix: {fix_action}"


def _get_heuristic_fix_action(msg: str, bug_type: str) -> str:
    """Generate exact action phrase matching test-case specifications."""
    m = msg.lower()
    if "imported but unused" in m or "unused import" in m or "f401" in m:
        return "remove the import statement"
    if "missing colon" in m or ("syntaxerror" in m and "colon" in m):
        return "add the colon at the correct position"
    if "cannot assign" in m or "assignment" in m or "==" in m:
        return "replace assignment = with comparison =="
    if "indentationerror" in m or "unexpected indent" in m:
        return "fix indentation to use consistent 4 spaces"
    if "typeerror" in m or "cannot concatenate" in m or "unsupported operand" in m:
        return "convert operand types using str() or int()"
    if "zerodivisionerror" in m or "division by zero" in m:
        return "add check for zero divisor"
    if "import" in bug_type:
        return "install missing module or fix import path"
    if "syntax" in bug_type.lower():
        return "correct the syntax error"
    return "review and fix the logic bug"


def failure_classifier_agent(state: AgentState) -> Dict[str, Any]:
    """Agent node that inspects test outputs and repository files to classify errors."""
    logger.info("--- [FailureClassifierAgent] Classifying detected failures ---")

    clone_path = Path(state["clone_path"])
    raw_output = state.get("raw_test_output", "")
    source_files = state.get("source_files", []) + state.get("test_files", [])

    detected: List[Dict[str, Any]] = []

    def add_issue(rel_file: str, line: int, msg: str, btype: str, fix_action: str = None):
        rel_clean = rel_file.replace("\\", "/")
        # Avoid duplicate (file, line, btype)
        if any(d["file"] == rel_clean and d["line"] == line and d["bug_type"] == btype for d in detected):
            return
        if not fix_action:
            fix_action = _get_heuristic_fix_action(msg, btype)
        expected_str = format_expected_dashboard_output(btype, rel_clean, line, fix_action)
        detected.append({
            "file": rel_clean,
            "line": line,
            "message": msg[:200],
            "bug_type": btype,
            "fix_action": fix_action,
            "expected_dashboard_output": expected_str
        })
        logger.info(f"Classified: {expected_str}")

    # 1. Parse errors from Pytest / Test output
    if raw_output:
        # Pattern: File "path/file.py", line 123, in ... \n Error: message
        for m in re.finditer(r'File\s+"([^"]+)",\s*line\s+(\d+)(?:,\s*in\s+\w+)?\n\s*(?:[^\n]+\n)?\s*([A-Za-z]+Error:[^\n]+)', raw_output):
            fpath, lno, err = m.group(1), int(m.group(2)), m.group(3)
            if str(clone_path) in fpath:
                fpath = fpath.replace(str(clone_path) + "/", "").replace(str(clone_path) + "\\", "")

            btype = "LOGIC"
            if "IndentationError" in err or "TabError" in err:
                btype = "INDENTATION"
            elif "SyntaxError" in err:
                btype = "SYNTAX"
            elif "ImportError" in err or "ModuleNotFoundError" in err:
                btype = "IMPORT"
            elif "TypeError" in err:
                btype = "TYPE_ERROR"
            elif "ZeroDivisionError" in err:
                btype = "LOGIC"

            add_issue(fpath, lno, err, btype)

    # 2. Tokenize & Compile Scan across Python files (Catches INDENTATION & SYNTAX)
    for rel_f in source_files:
        full_p = clone_path / rel_f
        if not full_p.exists():
            continue
        try:
            with open(full_p, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError:
            continue

        file_lines = content.splitlines()

        # Pass A: Tokenize for INDENTATION
        try:
            list(tokenize.generate_tokens(io.StringIO(content).readline))
        except IndentationError as ie:
            add_issue(rel_f, ie.lineno or 1, f"IndentationError: {ie.msg}", "INDENTATION", "fix indentation to use consistent 4 spaces")
        except tokenize.TokenError:
            pass

        # Pass B: Compile for SYNTAX / missing colons / assignment in condition
        try:
            compile(content, str(full_p), "exec")
        except IndentationError as ie:
            add_issue(rel_f, ie.lineno or 1, f"IndentationError: {ie.msg}", "INDENTATION", "fix indentation to use consistent 4 spaces")
        except SyntaxError as se:
            msg = se.msg or "invalid syntax"
            lno = se.lineno or 1
            target_line = se.text or ""
            if not target_line and 1 <= lno <= len(file_lines):
                target_line = file_lines[lno - 1]

            if re.search(r'^\s*(?:if|elif|while)\b', target_line) and re.search(r'(?<![=!<>])=(?![=>])', target_line):
                action = "replace assignment = with comparison =="
            elif "colon" in msg.lower() or (target_line and not target_line.strip().endswith(":") and re.search(r'^\s*(?:def|class|if|elif|else|for|while|try|except|finally|with)\b', target_line)):
                action = "add the colon at the correct position"
            else:
                action = "correct the syntax error"
            add_issue(rel_f, lno, f"SyntaxError: {msg}", "SYNTAX", action)

        # Pass C: AST-level Unused Import Detection (Strictly LINTING as required by test cases)
        try:
            tree = ast.parse(content, filename=str(full_p))
            imported_names: Dict[str, int] = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        used_name = alias.asname or alias.name.split('.')[0]
                        imported_names[used_name] = node.lineno
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name != '*':
                            used_name = alias.asname or alias.name
                            imported_names[used_name] = node.lineno

            used_identifiers = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                if isinstance(node, ast.Name):
                    used_identifiers.add(node.id)
                elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                    used_identifiers.add(node.value.id)

            for name, lno in imported_names.items():
                if name not in used_identifiers:
                    # Note: RIFT test cases evaluate unused imports as LINTING
                    add_issue(
                        rel_f,
                        lno,
                        f"Unused import '{name}'",
                        "LINTING",
                        "remove the import statement"
                    )

            # Pass D: AST Type Errors (e.g. str + int)
            for node in ast.walk(tree):
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                    left_str = isinstance(node.left, ast.Constant) and isinstance(node.left.value, str)
                    right_num = isinstance(node.right, ast.Constant) and isinstance(node.right.value, (int, float))
                    left_num = isinstance(node.left, ast.Constant) and isinstance(node.left.value, (int, float))
                    right_str = isinstance(node.right, ast.Constant) and isinstance(node.right.value, str)
                    if (left_str and right_num) or (left_num and right_str):
                        add_issue(rel_f, node.lineno, "TypeError: cannot concatenate str and int", "TYPE_ERROR", "convert to string using str()")

                # Pass E: AST ZeroDivision (x / 0)
                if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                    if isinstance(node.right, ast.Constant) and node.right.value == 0:
                        add_issue(rel_f, node.lineno, "ZeroDivisionError: division by literal zero", "LOGIC", "add check for zero divisor")

        except Exception:
            pass

    logger.info(f"Total classified issues for this iteration: {len(detected)}")

    return {
        "detected_errors": detected
    }
