"""
agent/graph.py — Builds the LangGraph StateGraph and provides
the main entry point: run_agent(address, buyer_profile_text).

Graph structure:

    START → planner → search → critic → should_loop?
                                            ├── Yes → planner  (loop)
                                            └── No  → END
"""

from langgraph.graph import StateGraph, END

from agent.state import AgentState
from agent.nodes import planner_node, search_node, critic_node


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def _should_loop(state):
    """Conditional edge: continue looping or finish."""
    if state.get("is_satisfied", False):
        return "end"
    return "planner"


def _build_graph():
    """Construct and compile the LangGraph StateGraph."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("search", search_node)
    graph.add_node("critic", critic_node)

    # Define edges
    graph.set_entry_point("planner")
    graph.add_edge("planner", "search")
    graph.add_edge("search", "critic")

    # Conditional edge from critic: loop back or finish
    graph.add_conditional_edges(
        "critic",
        _should_loop,
        {
            "planner": "planner",
            "end": END,
        },
    )

    return graph.compile()


# Compile once at module load
_compiled_graph = _build_graph()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_agent(address, buyer_profile_text, max_iterations=3):
    """
    Run the agentic search loop (blocking).

    Returns:
        dict with keys: coordinates, amenities, buyer_profile,
                        agent_log, api_call_count
    """
    initial_state = _make_initial_state(address, buyer_profile_text, max_iterations)

    # Run the graph — this blocks until the loop finishes
    final_state = _compiled_graph.invoke(initial_state)

    return _extract_result(final_state)


def run_agent_streaming(address, buyer_profile_text, max_iterations=3):
    """
    Run the agentic search loop with streaming.

    Yields dicts with:
        - node: which node just completed (planner / search / critic)
        - log_entry: the latest agent_log entry from that node
        - api_call_count: running total of API calls
        - is_done: True on the final yield

    On the final yield, also includes the full result keys:
        coordinates, amenities, buyer_profile, agent_log
    """
    initial_state = _make_initial_state(address, buyer_profile_text, max_iterations)

    last_state = initial_state
    for event in _compiled_graph.stream(initial_state, stream_mode="updates"):
        # event is a dict like {"planner": {partial_state_updates}}
        for node_name, updates in event.items():
            if node_name == "__end__":
                continue

            # Merge updates into last_state for tracking
            last_state = {**last_state, **updates}

            # Get the latest log entry
            log_entries = updates.get("agent_log", [])
            latest_entry = log_entries[-1] if log_entries else None

            yield {
                "node": node_name,
                "log_entry": latest_entry,
                "api_call_count": last_state.get("api_call_count", 0),
                "is_done": False,
            }

    # Final yield with full results
    yield {
        "node": "done",
        "is_done": True,
        **_extract_result(last_state),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_initial_state(address, buyer_profile_text, max_iterations):
    return {
        "address": address,
        "buyer_profile_text": buyer_profile_text,
        "buyer_profile": None,
        "search_categories": None,
        "coordinates": None,
        "amenities": None,
        "critic_feedback": None,
        "is_satisfied": False,
        "iteration": 0,
        "max_iterations": max_iterations,
        "agent_log": [],
        "api_call_count": 0,
    }


def _extract_result(state):
    return {
        "coordinates": state.get("coordinates"),
        "amenities": state.get("amenities", {}),
        "buyer_profile": state.get("buyer_profile"),
        "agent_log": state.get("agent_log", []),
        "api_call_count": state.get("api_call_count", 0),
    }
