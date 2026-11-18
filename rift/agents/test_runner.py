"""
TestDiscoveryAgent - Automatically discovers and runs test suites (pytest/unittest) and monitors pass/fail.
"""

import sys
import json
import ast
import logging
import datetime
import subprocess
from pathlib import Path
from typing import Dict, Any, List

from rift.state import AgentState

logger = logging.getLogger("rift.agents.test_runner")


def _run_cmd(cmd: List[str], cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess:
    """Run command with timeout and captured output."""
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        logger.warning(f"Command {' '.join(cmd)} timed out after {timeout}s")
        return subprocess.CompletedProcess(cmd, -1, "", "Command timed out")
    except Exception as e:
        logger.error(f"Failed to execute {' '.join(cmd)}: {e}")
        return subprocess.CompletedProcess(cmd, -1, "", str(e))


def test_runner_agent(state: AgentState) -> Dict[str, Any]:
    """Agent node that executes the test suite for the current iteration."""
    iteration = state.get("current_iteration", 0) + 1
    max_iterations = state.get("max_iterations", 5)
    clone_path = Path(state["clone_path"])
    test_files = state.get("test_files", [])

    logger.info(f"--- [TestDiscoveryAgent] Running Iteration {iteration}/{max_iterations} ---")
    now_ts = datetime.datetime.now().strftime("%H:%M:%S")

    test_output = ""
    passed = False

    # Check if we have dedicated test files
    if test_files:
        logger.info(f"Executing pytest on {len(test_files)} test files...")
        res = _run_cmd(["pytest", "--tb=short", "-v"], cwd=clone_path, timeout=90)
        test_output = (res.stdout or "") + "\n" + (res.stderr or "")

        # If pytest command was not found or failed execution, fallback to python -m unittest
        if res.returncode != 0 and "pytest: command not found" in test_output.lower():
            logger.info("Falling back to python -m unittest...")
            res = _run_cmd([sys.executable, "-m", "unittest", "discover", "-s", "."], cwd=clone_path, timeout=90)
            test_output = (res.stdout or "") + "\n" + (res.stderr or "")

        passed = (res.returncode == 0) and ("FAILED" not in test_output) and ("ERROR:" not in test_output)
    else:
        # If no dedicated test files, run py_compile and static AST validation across all source files
        logger.info("No test files detected; verifying syntax and static compliance across source files...")
        syntax_errors = []
        for src_file in state.get("source_files", []):
            full_path = clone_path / src_file
            res = _run_cmd([sys.executable, "-m", "py_compile", str(full_path)], cwd=clone_path, timeout=15)
            if res.returncode != 0:
                syntax_errors.append(f"{src_file}: {res.stderr or res.stdout}")

        if not syntax_errors:
            # Also verify if any static linting or zero-division errors remain
            ast_issues = []
            for src_file in state.get("source_files", []):
                full_path = clone_path / src_file
                if not full_path.exists():
                    continue
                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        code = f.read()
                    tree = ast.parse(code, filename=str(full_path))
                    # Check unused imports
                    imports = {}
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports[alias.asname or alias.name.split('.')[0]] = node.lineno
                        elif isinstance(node, ast.ImportFrom):
                            for alias in node.names:
                                if alias.name != '*':
                                    imports[alias.asname or alias.name] = node.lineno
                    used = set()
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            continue
                        if isinstance(node, ast.Name):
                            used.add(node.id)
                        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                            used.add(node.value.id)
                    for imp_name, lno in imports.items():
                        if imp_name not in used:
                            ast_issues.append(f"{src_file}:{lno} Unused import '{imp_name}' (LINTING)")

                    # Check literal zero division
                    for node in ast.walk(tree):
                        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                            if isinstance(node.right, ast.Constant) and node.right.value == 0:
                                ast_issues.append(f"{src_file}:{node.lineno} Zero division (LOGIC)")
                except Exception:
                    pass

            if not ast_issues:
                passed = True
                test_output = "All Python files compiled successfully without syntax, linting, or logic errors."
            else:
                passed = False
                test_output = "Static verification detected remaining issues:\n" + "\n".join(ast_issues)
        else:
            passed = False
            test_output = "\n".join(syntax_errors)

    status_str = "passed" if passed else "failed"
    iteration_entry = {
        "iteration": iteration,
        "max_iterations": max_iterations,
        "status": status_str,
        "timestamp": now_ts,
        "output_preview": test_output[:400]
    }

    # Emit real-time event for UI streaming
    event_payload = {
        "type": "ITERATION_UPDATE",
        "iteration": iteration,
        "max_iterations": max_iterations,
        "status": status_str,
        "timestamp": now_ts
    }
    print(f"EVENT:{json.dumps(event_payload)}", flush=True)

    new_history = list(state.get("iteration_history", []))
    new_history.append(iteration_entry)

    logger.info(f"Iteration {iteration}/{max_iterations} result: {status_str.upper()}")

    return {
        "current_iteration": iteration,
        "ci_cd_passed": passed,
        "iteration_history": new_history,
        "raw_test_output": test_output
    }
