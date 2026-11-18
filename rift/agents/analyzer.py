"""
RepoAnalyzerAgent - Clones repository, initializes git branch, and discovers source/test files.
"""

import os
import re
import shutil
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List

from rift.state import AgentState
from rift.utils import fork_repo, check_gh_available, check_gh_authenticated

logger = logging.getLogger("rift.agents.analyzer")


def _run_cmd(cmd: List[str], cwd: Path = None, timeout: int = 120) -> subprocess.CompletedProcess:
    """Execute a shell command with git safety flags."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "/usr/bin/true" if os.path.exists("/usr/bin/true") else "/bin/true"
    env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o ConnectTimeout=30"

    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )
    except Exception as e:
        logger.error(f"Command {' '.join(cmd)} failed: {e}")
        return subprocess.CompletedProcess(cmd, -1, "", str(e))


def repo_analyzer_agent(state: AgentState) -> Dict[str, Any]:
    """Agent node that clones the repository and discovers project files."""
    logger.info("--- [RepoAnalyzerAgent] Starting repository analysis ---")

    repo_url = state["repo_url"]
    team_name = re.sub(r'[^A-Z0-9_]', '', re.sub(r'\s+', '_', state["team_name"].strip().upper()))
    leader_name = re.sub(r'[^A-Z0-9_]', '', re.sub(r'\s+', '_', state["leader_name"].strip().upper()))
    branch_name = f"{team_name}_{leader_name}_AI_Fix"
    token = state.get("token") or os.environ.get("GITHUB_TOKEN", "")

    # Allocate clean temporary directory
    clone_dir = Path(state.get("clone_path") or tempfile.mkdtemp(prefix="rift_repo_"))
    if clone_dir.exists():
        shutil.rmtree(clone_dir, ignore_errors=True)
    clone_dir.mkdir(parents=True, exist_ok=True)

    # Determine clone URL (check gh CLI and fork if needed)
    clone_url = repo_url
    forked_url = None

    if not token and "github.com" in repo_url:
        if check_gh_available() and check_gh_authenticated():
            token_res = _run_cmd(["gh", "auth", "token"])
            if token_res.returncode == 0 and token_res.stdout.strip():
                token = token_res.stdout.strip()
                logger.info("Retrieved GitHub token from gh CLI")

    if token and "github.com" in repo_url:
        fork_res = fork_repo(repo_url, token)
        if fork_res:
            clone_url = fork_res
            forked_url = fork_res
            logger.info(f"Using forked repository: {clone_url}")

        # Inject auth token into clone URL
        clone_url = re.sub(r'https://(github\.com)', f'https://{token}@\\1', clone_url)

    safe_log_url = re.sub(r'https://[^@]+@github\.com', 'https://***@github.com', clone_url)
    logger.info(f"Cloning {safe_log_url} into {clone_dir}")

    clone_res = _run_cmd(["git", "clone", "--depth=1", clone_url, str(clone_dir)])
    if clone_res.returncode != 0 or not any(clone_dir.iterdir()):
        safe_err = re.sub(r'https://[^@]+@github\.com', 'https://***@github.com', clone_res.stderr or clone_res.stdout)[:300]
        raise RuntimeError(f"Git clone failed (exit code {clone_res.returncode}): {safe_err}")

    # Checkout target healing branch
    logger.info(f"Checking out branch: {branch_name}")
    _run_cmd(["git", "checkout", "-b", branch_name], cwd=clone_dir)

    # Discover source and test files
    source_files = []
    test_files = []
    for p in clone_dir.rglob("*.py"):
        if any(skip in str(p) for skip in ["__pycache__", ".git", "venv", "env", "node_modules", ".tox"]):
            continue
        rel_str = str(p.relative_to(clone_dir))
        if "test_" in p.name or p.name.startswith("test_") or p.name.endswith("_test.py") or "tests/" in rel_str or "tests\\" in rel_str:
            test_files.append(rel_str)
        else:
            source_files.append(rel_str)

    logger.info(f"Discovered {len(source_files)} source files and {len(test_files)} test files")

    return {
        "team_name": team_name,
        "leader_name": leader_name,
        "branch_name": branch_name,
        "token": token,
        "clone_path": str(clone_dir),
        "forked_repo_url": forked_url,
        "source_files": source_files,
        "test_files": test_files,
        "current_iteration": 0,
        "max_iterations": state.get("max_iterations") or 5,
        "iteration_history": [],
        "detected_errors": [],
        "fixes_applied": [],
        "ci_cd_passed": False
    }
