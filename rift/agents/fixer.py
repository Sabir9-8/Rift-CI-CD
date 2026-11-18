"""
CodeRepairAgent - Executes targeted, concrete code modifications on disk.
Applies deterministic AST/regex repairs and LLM-assisted patches (OpenAI / Gemini).
"""

import os
import re
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from rift.state import AgentState

logger = logging.getLogger("rift.agents.fixer")


def _run_cmd(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def repair_unused_import(file_path: Path, line_no: int, error_msg: str) -> bool:
    """Deterministically remove unused import line or name from file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if 1 <= line_no <= len(lines):
            target_line = lines[line_no - 1]
            m = re.search(r"'(?P<name>\w+)'", error_msg)
            ident = m.group("name") if m else None

            # If simple single import e.g. 'import os', remove the line
            if re.match(r'^\s*import\s+\w+\s*$', target_line) or not ident:
                del lines[line_no - 1]
            else:
                # If from x import a, b where only b is unused
                cleaned = re.sub(rf'\b{ident}\b\s*,?\s*', '', target_line)
                cleaned = re.sub(r',\s*$', '', cleaned.strip()) + '\n'
                if cleaned.strip().endswith('import') or cleaned.strip() == '':
                    del lines[line_no - 1]
                else:
                    lines[line_no - 1] = cleaned

            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True
    except Exception as e:
        logger.error(f"Failed to repair unused import in {file_path}:{line_no}: {e}")
    return False


def repair_missing_colon(file_path: Path, line_no: int) -> bool:
    """Deterministically add missing colon to header statement (def, class, if, for, while, etc.)."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if 1 <= line_no <= len(lines):
            line = lines[line_no - 1].rstrip("\r\n")
            if not line.strip().endswith(":"):
                if "#" in line:
                    code_part, comment_part = line.split("#", 1)
                    lines[line_no - 1] = f"{code_part.rstrip()}:  #{comment_part}\n"
                else:
                    lines[line_no - 1] = f"{line.rstrip()}:\n"

                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                return True
    except Exception as e:
        logger.error(f"Failed to repair missing colon in {file_path}:{line_no}: {e}")
    return False


def repair_assignment_in_condition(file_path: Path, line_no: int) -> bool:
    """Deterministically replace assignment '=' with equality '==' in conditional statements."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if 1 <= line_no <= len(lines):
            line = lines[line_no - 1]
            # Match condition headers e.g. if item["stock"] = 0: or while x = 1:
            if re.search(r'^\s*(?:if|elif|while)\b', line):
                # Replace single '=' not preceded or followed by =, !, <, >
                repaired = re.sub(r'(?<![=!<>])=(?![=>])', '==', line)
                if repaired != line:
                    lines[line_no - 1] = repaired
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.writelines(lines)
                    logger.info(f"Repaired assignment in condition {file_path}:{line_no}: {repaired.strip()}")
                    return True
    except Exception as e:
        logger.error(f"Failed to repair assignment in condition {file_path}:{line_no}: {e}")
    return False


def repair_zero_division(file_path: Path, line_no: int) -> bool:
    """Deterministically replace division by literal zero with safe division."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if 1 <= line_no <= len(lines):
            line = lines[line_no - 1]
            repaired = re.sub(r'(?<=[/%])\s*0(?![0-9.])', ' 1', line)
            if repaired != line:
                lines[line_no - 1] = repaired
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                logger.info(f"Repaired zero division in {file_path}:{line_no}: {repaired.strip()}")
                return True
    except Exception as e:
        logger.error(f"Failed to repair zero division in {file_path}:{line_no}: {e}")
    return False


def repair_indentation(file_path: Path, line_no: int) -> bool:
    """Deterministically fix indentation to standard 4-space indent."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if 1 <= line_no <= len(lines):
            target = lines[line_no - 1]
            stripped = target.lstrip()
            lines[line_no - 1] = f"    {stripped}"
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True
    except Exception as e:
        logger.error(f"Failed to repair indentation in {file_path}:{line_no}: {e}")
    return False


def call_llm_fixer(
    file_path: Path,
    line_no: int,
    bug_type: str,
    error_msg: str,
    openai_key: str = "",
    gemini_key: str = ""
) -> bool:
    """Apply LLM patch using modern Google Gemini or OpenAI v1.0+."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        start = max(0, line_no - 6)
        end = min(len(lines), line_no + 5)
        context_lines = "".join(lines[start:end])

        prompt = (
            f"Fix this Python {bug_type} bug at line {line_no}.\n"
            f"Error message: {error_msg}\n"
            f"Context around line {line_no}:\n```python\n{context_lines}\n```\n"
            f"Return ONLY the single replacement line for line {line_no}, no markdown formatting or commentary."
        )

        replacement = None

        # 1. Try Google Gemini if key available
        active_gemini = gemini_key or os.environ.get("GEMINI_API_KEY", "").strip()
        if active_gemini:
            for model_name in ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=active_gemini)
                    model = genai.GenerativeModel(model_name)
                    resp = model.generate_content(prompt)
                    if resp and resp.text:
                        candidate = resp.text.strip().replace("```python", "").replace("```", "").strip()
                        if candidate:
                            replacement = candidate
                            break
                except Exception as e:
                    logger.warning(f"Gemini model {model_name} fix attempt failed: {e}")

        # 2. Try OpenAI v1.0+ if key available
        active_openai = openai_key or os.environ.get("OPENAI_API_KEY", "").strip()
        if not replacement and active_openai:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=active_openai)
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100,
                    temperature=0.1
                )
                candidate = resp.choices[0].message.content.strip().replace("```python", "").replace("```", "").strip()
                if candidate:
                    replacement = candidate
            except Exception as e:
                logger.warning(f"OpenAI fix attempt failed: {e}")

        if replacement and 1 <= line_no <= len(lines):
            lines[line_no - 1] = replacement if replacement.endswith("\n") else replacement + "\n"
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True

    except Exception as e:
        logger.error(f"LLM fix failed: {e}")

    return False


def code_repair_agent(state: AgentState) -> Dict[str, Any]:
    """Agent node that applies actual code modifications to files and commits with [AI-AGENT]."""
    logger.info("--- [CodeRepairAgent] Executing code repairs ---")

    clone_path = Path(state["clone_path"])
    raw_errors = state.get("detected_errors", [])
    # Sort errors descending by line number so edits do not offset earlier lines in same file
    errors = sorted(raw_errors, key=lambda e: (e.get('file', ''), -e.get('line', 0)))

    # Use map keyed by (file, line_number, bug_type) to prevent duplicate rows across iterations
    fixes_map: Dict[str, Dict[str, Any]] = {}
    for existing in state.get("fixes_applied", []):
        key = f"{existing.get('file')}:{existing.get('line_number')}:{existing.get('bug_type')}"
        fixes_map[key] = existing

    openai_key = state.get("openai_key") or os.environ.get("OPENAI_API_KEY", "")
    gemini_key = state.get("gemini_key") or os.environ.get("GEMINI_API_KEY", "")
    iteration = state.get("current_iteration", 1)

    new_fixes_count = 0

    for err in errors:
        rel_file = err["file"]
        full_path = clone_path / rel_file
        if not full_path.exists():
            continue

        line_no = err["line"]
        btype = err["bug_type"]
        msg = err["message"]
        fix_action = err["fix_action"]
        expected_str = err["expected_dashboard_output"]
        key = f"{rel_file}:{line_no}:{btype}"

        # If already successfully fixed in a previous iteration, skip
        if key in fixes_map and fixes_map[key].get("status") == "Fixed":
            continue

        success = False

        # Attempt deterministic repair based on bug type and action
        if btype == "LINTING" and "import" in fix_action.lower():
            success = repair_unused_import(full_path, line_no, msg)
        elif btype == "SYNTAX":
            if "assignment" in fix_action.lower() or "cannot assign" in msg.lower() or "==" in fix_action:
                success = repair_assignment_in_condition(full_path, line_no)
            if not success and ("colon" in fix_action.lower() or "colon" in msg.lower()):
                success = repair_missing_colon(full_path, line_no)
            if not success:
                # Try assignment in condition first for general syntax errors
                success = repair_assignment_in_condition(full_path, line_no)
            if not success:
                success = repair_missing_colon(full_path, line_no)
        elif btype == "INDENTATION":
            success = repair_indentation(full_path, line_no)
        elif btype == "LOGIC" and ("zero" in fix_action.lower() or "zerodivision" in msg.lower()):
            success = repair_zero_division(full_path, line_no)

        # Fallback to LLM if deterministic fix not applicable or failed
        if not success and (openai_key or gemini_key):
            success = call_llm_fixer(full_path, line_no, btype, msg, openai_key, gemini_key)

        status_flag = "Fixed" if success else "Failed"
        commit_msg = f"[AI-AGENT] Fix {btype} error in {rel_file} line {line_no}"

        fixes_map[key] = {
            "file": rel_file,
            "bug_type": btype,
            "line_number": line_no,
            "commit_message": commit_msg,
            "status": status_flag,
            "fix": fix_action,
            "expected_dashboard_output": expected_str
        }
        if success:
            new_fixes_count += 1

    # Stage and commit changes with the mandatory [AI-AGENT] prefix
    _run_cmd(["git", "add", "."], cwd=clone_path)
    diff_check = _run_cmd(["git", "diff", "--staged", "--name-only"], cwd=clone_path)

    if diff_check.stdout.strip():
        commit_title = f"[AI-AGENT] Applied {new_fixes_count} fixes in iteration {iteration}"
        _run_cmd(["git", "commit", "-m", commit_title], cwd=clone_path)
        logger.info(f"Committed changes: {commit_title}")
    else:
        logger.info("No modifications detected to commit in this iteration.")

    return {
        "fixes_applied": list(fixes_map.values())
    }
