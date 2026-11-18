"""
LangGraph Multi-Agent StateGraph Workflow for Autonomous CI/CD Healing.
"""

import logging
from typing import Dict, Any, Literal

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None

from rift.state import AgentState
from rift.agents.analyzer import repo_analyzer_agent
from rift.agents.test_runner import test_runner_agent
from rift.agents.classifier import failure_classifier_agent
from rift.agents.fixer import code_repair_agent
from rift.agents.publisher import git_publish_agent

logger = logging.getLogger("rift.graph")


def evaluate_healing_condition(state: AgentState) -> Literal["heal", "publish"]:
    """Conditional router that determines whether to iterate or finalize."""
    if state.get("ci_cd_passed", False):
        logger.info("All tests passed! Transitioning to git publication.")
        return "publish"

    curr_iter = state.get("current_iteration", 0)
    max_iter = state.get("max_iterations", 5)

    if curr_iter >= max_iter:
        logger.info(f"Reached max iterations limit ({curr_iter}/{max_iter}). Finalizing run.")
        return "publish"

    logger.info(f"Tests failed in iteration {curr_iter}. Triggering failure classifier and code repair loop.")
    return "heal"


def create_healing_graph():
    """Compile and return the LangGraph StateGraph workflow."""
    if not LANGGRAPH_AVAILABLE:
        logger.warning("LangGraph not installed. Falling back to state-machine runner.")
        return FallbackHealingWorkflow()

    graph = StateGraph(AgentState)

    # Register agent nodes
    graph.add_node("analyze_repo", repo_analyzer_agent)
    graph.add_node("discover_and_test", test_runner_agent)
    graph.add_node("classify_errors", failure_classifier_agent)
    graph.add_node("repair_code", code_repair_agent)
    graph.add_node("publish_git", git_publish_agent)

    # Set workflow flow
    graph.set_entry_point("analyze_repo")
    graph.add_edge("analyze_repo", "discover_and_test")

    # Conditional edge: loop back if failed and iterations remain, otherwise publish
    graph.add_conditional_edges(
        "discover_and_test",
        evaluate_healing_condition,
        {
            "heal": "classify_errors",
            "publish": "publish_git"
        }
    )

    graph.add_edge("classify_errors", "repair_code")
    graph.add_edge("repair_code", "discover_and_test")
    graph.add_edge("publish_git", END)

    return graph.compile()


class FallbackHealingWorkflow:
    """State-machine fallback maintaining identical multi-agent semantics if LangGraph is missing."""

    def invoke(self, initial_state: AgentState) -> Dict[str, Any]:
        state = dict(initial_state)

        # 1. Analyze repo
        step1 = repo_analyzer_agent(state)
        state.update(step1)

        # 2. Iterative loop
        while True:
            test_res = test_runner_agent(state)
            state.update(test_res)

            decision = evaluate_healing_condition(state)
            if decision == "publish":
                break

            class_res = failure_classifier_agent(state)
            state.update(class_res)

            fix_res = code_repair_agent(state)
            state.update(fix_res)

        # 3. Publish git & write results.json
        pub_res = git_publish_agent(state)
        state.update(pub_res)

        return state
