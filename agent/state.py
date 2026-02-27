"""
agent/state.py — Defines the shared state that flows through the LangGraph.

AgentState is a TypedDict that every node reads from and writes to.
"""

from typing import TypedDict, Optional


class AgentState(TypedDict):
    """Shared state for the agent graph."""

    # --- Inputs (set once at the start) ---
    address: str                         # Raw property address from the user
    buyer_profile_text: str              # Free-text buyer description

    # --- Set by planner ---
    buyer_profile: Optional[dict]        # Structured profile extracted by Gemini
    search_categories: Optional[dict]    # {friendly_name: google_places_type}

    # --- Set by search node ---
    coordinates: Optional[dict]          # {formatted_address, latitude, longitude}
    amenities: Optional[dict]            # Ranked amenities per category

    # --- Set by critic ---
    critic_feedback: Optional[str]       # What the critic said (if looping)
    is_satisfied: bool                   # True = stop looping

    # --- Loop bookkeeping ---
    iteration: int                       # Current iteration (starts at 0)
    max_iterations: int                  # Hard cap (default 3)

    # --- Logging ---
    agent_log: list                      # List of {step, message} dicts for the UI
    api_call_count: int                  # Total API calls made (Maps + Gemini)
