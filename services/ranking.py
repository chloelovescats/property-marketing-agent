"""
services/ranking.py — Filters and ranks amenities.

Rules:
    - Sort by distance ascending
    - Return top 5 per category
"""


def filter_and_rank(amenities):
    """
    Filter, sort, and trim amenities to the top 5 per category.

    Args:
        amenities (dict): Raw amenities from get_nearby_amenities().

    Returns:
        dict: Same structure, filtered and ranked.
    """
    ranked = {}

    for category, places in amenities.items():
        # Closest first
        filtered = sorted(places, key=lambda p: p.get("distance_meters", 99999))

        ranked[category] = filtered[:5]

    return ranked
