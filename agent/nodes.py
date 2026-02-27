"""
agent/nodes.py — The three nodes that make up the agentic loop.

    1. planner_node  — LLM decides what amenity categories to search
    2. search_node   — Calls geocode + Google Places tools (deterministic)
    3. critic_node   — LLM reviews results and decides: loop or stop
"""

import os
import json
import google.generativeai as genai

from services.geocode import geocode_address
from services.amenities import get_nearby_amenities
from services.ranking import filter_and_rank


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_model():
    """Return a configured Gemini model instance."""
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    return genai.GenerativeModel("gemini-2.5-flash")


def _log(state, step, message):
    """Append an entry to the agent log."""
    log = list(state.get("agent_log", []))
    log.append({"step": step, "message": message, "iteration": state.get("iteration", 0)})
    return log


# ---------------------------------------------------------------------------
# 1. PLANNER NODE
# ---------------------------------------------------------------------------

PLANNER_PROMPT = """\
You are a real-estate search planner for Singapore properties.

BUYER DESCRIPTION:
"{buyer_profile_text}"

{feedback_section}

YOUR TASK:
1. Extract a structured buyer profile (persona_name, life_stage, priorities,
   commute info, kids info, lifestyle likes).
2. Based on the profile, choose 3-5 Google Places amenity categories that
   would matter MOST to this buyer. Be creative and specific.

RESPOND IN THIS EXACT JSON FORMAT (no markdown, no extra text):
{{
    "buyer_profile": {{
        "persona_name": "...",
        "life_stage": "single|couple|family_young_kids|family_teens|empty_nester|investor",
        "priorities": ["..."],
        "commute": {{"destination_name": "...", "mode": "mrt|bus|car|walk", "max_commute_mins": 30}},
        "kids": {{"has_kids": true, "school_level": "childcare|primary|secondary|jc"}},
        "lifestyle": {{"likes": ["..."]}}
    }},
    "amenity_categories": {{
        "Friendly Name": "google_places_type",
        "Another Name": "another_type"
    }}
}}

Use exactly supported Google Places API types as values:
gym, cafe, restaurant, school, shopping_mall, park, pet_store,
supermarket, subway_station, transit_station, hospital, pharmacy,
primary_school, secondary_school, library, movie_theater, bakery,
beauty_salon, book_store, bowling_alley, church, mosque,
convenience_store, dentist, doctor, laundry, zoo, aquarium,
amusement_park, night_club, spa, stadium, university.
You may combine with pipe: "subway_station|transit_station"
"""


def planner_node(state):
    """
    Use Gemini to analyse the buyer profile and decide which amenity
    categories to search for.  On subsequent iterations, the critic's
    feedback is included so the planner can adjust.
    """
    model = _get_model()

    # Build feedback section for iterations > 0
    feedback_section = ""
    if state.get("critic_feedback"):
        feedback_section = (
            "PREVIOUS SEARCH RESULTS WERE INSUFFICIENT. The critic said:\n"
            f'"{state["critic_feedback"]}"\n\n'
            "Please choose DIFFERENT or ADDITIONAL categories this time.\n"
            "Previously searched categories were:\n"
            f"{json.dumps(state.get('search_categories', {}), indent=2)}\n"
        )

    prompt = PLANNER_PROMPT.format(
        buyer_profile_text=state["buyer_profile_text"],
        feedback_section=feedback_section,
    )

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
        ),
    )

    result = json.loads(response.text)
    api_calls = state.get("api_call_count", 0) + 1  # 1 Gemini call

    plan_summary = ", ".join(result.get("amenity_categories", {}).keys())
    log = _log(state, "planner", f"Searching for: {plan_summary}")

    return {
        "buyer_profile": result.get("buyer_profile"),
        "search_categories": result.get("amenity_categories"),
        "agent_log": log,
        "api_call_count": api_calls,
    }


# ---------------------------------------------------------------------------
# 2. SEARCH NODE (deterministic — no LLM)
# ---------------------------------------------------------------------------

def search_node(state):
    """
    Call geocode + Google Places + ranking.
    This is pure tool execution — no LLM involved.
    """
    api_calls = state.get("api_call_count", 0)

    # Geocode (only on first iteration — coordinates don't change)
    coordinates = state.get("coordinates")
    if not coordinates:
        coordinates = geocode_address(state["address"])
        api_calls += 1  # 1 Google Maps Geocoding call

    lat = coordinates["latitude"]
    lng = coordinates["longitude"]

    # Search amenities with the planner's categories
    categories = state.get("search_categories", {})
    raw_amenities = get_nearby_amenities(lat, lng, custom_categories=categories)
    api_calls += len(categories)  # 1 Google Places call per category

    ranked = filter_and_rank(raw_amenities)

    # Merge with any amenities from previous iterations
    existing = dict(state.get("amenities") or {})
    existing.update(ranked)

    total_found = sum(len(v) for v in existing.values())
    log = _log(state, "search", f"Found {total_found} places across {len(existing)} categories")

    return {
        "coordinates": coordinates,
        "amenities": existing,
        "agent_log": log,
        "api_call_count": api_calls,
    }


# ---------------------------------------------------------------------------
# 3. CRITIC NODE
# ---------------------------------------------------------------------------

CRITIC_PROMPT = """\
You are a quality reviewer for a real-estate amenity search.

BUYER PROFILE:
{buyer_profile}

AMENITIES FOUND SO FAR:
{amenities_summary}

ITERATION: {iteration} of {max_iterations}

Evaluate whether the amenities above are SUFFICIENT for this buyer's needs.
Consider:
- Are the most important categories for this buyer represented?
- Are there enough results (at least 2-3 per important category)?
- Is anything obviously missing that this buyer would care about?

RESPOND IN THIS EXACT JSON FORMAT (no markdown):
{{
    "is_satisfied": true or false,
    "feedback": "If not satisfied, explain what categories are missing or weak. If satisfied, say why the results are good."
}}
"""


def critic_node(state):
    """
    Use Gemini to judge whether the search results are good enough
    for the buyer, or whether the planner should try again.
    """
    model = _get_model()
    iteration = state.get("iteration", 0) + 1

    # Build amenities summary
    amenities = state.get("amenities", {})
    lines = []
    for cat, places in amenities.items():
        lines.append(f"\n{cat}: {len(places)} results")
        for p in places[:3]:  # show top 3 to keep prompt small
            lines.append(f"  - {p['name']} ({p['distance_meters']}m)")
    amenities_summary = "\n".join(lines) if lines else "(no amenities found)"

    prompt = CRITIC_PROMPT.format(
        buyer_profile=json.dumps(state.get("buyer_profile", {}), indent=2),
        amenities_summary=amenities_summary,
        iteration=iteration,
        max_iterations=state.get("max_iterations", 3),
    )

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
        ),
    )

    result = json.loads(response.text)
    api_calls = state.get("api_call_count", 0) + 1  # 1 Gemini call

    is_satisfied = result.get("is_satisfied", True)
    feedback = result.get("feedback", "")

    # Force stop if we hit the iteration cap
    if iteration >= state.get("max_iterations", 3):
        is_satisfied = True
        feedback += " (Max iterations reached — returning best results.)"

    status = "✓ Satisfied" if is_satisfied else "✗ Not satisfied"
    log = _log(state, "critic", f"{status}: {feedback}")

    return {
        "critic_feedback": feedback,
        "is_satisfied": is_satisfied,
        "iteration": iteration,
        "agent_log": log,
        "api_call_count": api_calls,
    }
