"""
Rift CLI - Secure execution entrypoint for RiftAgent.
Accepts JSON configuration payload via STDIN or file argument.
"""

import sys
import os
import json
import logging
import traceback
import argparse
from pathlib import Path
from typing import Dict, Any

# Ensure rift package is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rift.graph import create_healing_graph
from rift.state import AgentState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("rift.cli")


def sanitize_sensitive_data(text: str, token: str = "") -> str:
    """Scrub tokens and secrets from strings."""
    if not text:
        return ""
    sanitized = text
    if token:
        sanitized = sanitized.replace(token, "***")
    import re
    sanitized = re.sub(r'https://[^@]+@github\.com', 'https://***@github.com', sanitized)
    sanitized = re.sub(r'ghp_[a-zA-Z0-9]{36}', 'ghp_***', sanitized)
    sanitized = re.sub(r'github_pat_[a-zA-Z0-9_]{82}', 'github_pat_***', sanitized)
    return sanitized


def save_results_json(data: Dict[str, Any], output_path: Path = None) -> Path:
    """Save results.json to the repository root."""
    if output_path is None:
        output_path = ROOT_DIR / "results.json"
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Generated results.json at {output_path}")
    except Exception as e:
        logger.error(f"Failed to write results.json: {e}")
    return output_path


def parse_payload() -> Dict[str, Any]:
    """Parse JSON payload from command line arguments or stdin."""
    parser = argparse.ArgumentParser(description="Run Rift CI/CD Agent securely")
    parser.add_argument("--config", "-c", type=str, help="Path to input JSON config file")
    args = parser.parse_args()

    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Read from stdin
    stdin_content = sys.stdin.read().strip()
    if not stdin_content:
        raise ValueError("No input JSON configuration received via STDIN or --config")
    
    return json.loads(stdin_content)


def main():
    try:
        payload = parse_payload()
    except Exception as e:
        error_msg = f"Failed to parse input configuration: {e}"
        logger.error(error_msg)
        print(f"ERROR:{error_msg}", flush=True)
        sys.exit(1)

    repo_url = payload.get("repoUrl") or payload.get("repo_url")
    team_name = payload.get("teamName") or payload.get("team_name")
    leader_name = payload.get("leaderName") or payload.get("leader_name")
    token = payload.get("token") or os.environ.get("GITHUB_TOKEN", "")
    openai_key = payload.get("openaiKey") or payload.get("openai_api_key") or os.environ.get("OPENAI_API_KEY", "")
    gemini_key = payload.get("geminiKey") or payload.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
    retry_limit = int(payload.get("retryLimit") or payload.get("retry_limit") or 5)

    if not repo_url or not team_name or not leader_name:
        error_msg = "Missing required fields: repo_url, team_name, leader_name"
        logger.error(error_msg)
        print(f"ERROR:{error_msg}", flush=True)
        sys.exit(1)

    if token:
        os.environ["GITHUB_TOKEN"] = token
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key

    logger.info(f"Starting Multi-Agent Healing Graph for repository: {repo_url}")
    logger.info(f"Team: {team_name}, Leader: {leader_name}, Retry Limit: {retry_limit}")

    import time
    start_time = time.time()

    workflow = create_healing_graph()
    initial_state = {
        "repo_url": repo_url,
        "team_name": team_name,
        "leader_name": leader_name,
        "token": token,
        "openai_key": openai_key,
        "gemini_key": gemini_key,
        "clone_path": "",
        "max_iterations": retry_limit,
        "current_iteration": 0,
        "source_files": [],
        "test_files": [],
        "iteration_history": [],
        "detected_errors": [],
        "fixes_applied": [],
        "ci_cd_passed": False,
        "total_time_seconds": 0.0,
        "score": {},
        "pr_number": None,
        "forked_repo_url": None,
        "error_message": None,
        "results_json_path": None
    }

    try:
        final_state = workflow.invoke(initial_state)
        total_elapsed = time.time() - start_time
        final_state["total_time_seconds"] = total_elapsed

        result = final_state.get("final_results") or {
            "success": final_state.get("ci_cd_passed", False),
            "repository_url": repo_url,
            "team_name": team_name,
            "leader_name": leader_name,
            "branch_name": final_state.get("branch_name", ""),
            "final_status": "PASSED" if final_state.get("ci_cd_passed") else "FAILED",
            "total_time_seconds": round(total_elapsed, 2),
            "errors_detected": len(final_state.get("detected_errors", [])),
            "fixes_applied": len([f for f in final_state.get("fixes_applied", []) if f.get("status") == "Fixed"]),
            "pr_created": final_state.get("pr_number"),
            "score": final_state.get("score"),
            "fixes": final_state.get("fixes_applied", []),
            "ci_cd_timeline": final_state.get("iteration_history", [])
        }

        # Ensure results.json is persisted
        save_results_json(result)

        # Output RESULT line for parent process
        sanitized_json = sanitize_sensitive_data(json.dumps(result), token=token)
        print(f"RESULT:{sanitized_json}", flush=True)

    except Exception as e:
        tb = traceback.format_exc()
        sanitized_error = sanitize_sensitive_data(str(e), token=token)
        logger.error(f"Agent execution failed: {sanitized_error}\n{sanitize_sensitive_data(tb, token=token)}")
        print(f"ERROR:{sanitized_error}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
