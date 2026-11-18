"""
Agent State Schema for LangGraph Multi-Agent Workflow.
"""

from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    # Inputs
    repo_url: str
    team_name: str
    leader_name: str
    branch_name: str
    token: str
    openai_key: str
    gemini_key: str
    clone_path: str
    forked_repo_url: Optional[str]

    # Discovered Codebase Elements
    source_files: List[str]
    test_files: List[str]

    # Iterative Healing Loop State
    current_iteration: int
    max_iterations: int
    iteration_history: List[Dict[str, Any]]

    # Issue Detection & Code Repairs
    detected_errors: List[Dict[str, Any]]
    fixes_applied: List[Dict[str, Any]]

    # Results & Metrics
    ci_cd_passed: bool
    total_time_seconds: float
    score: Dict[str, Any]
    pr_number: Optional[int]
    error_message: Optional[str]
    results_json_path: Optional[str]
