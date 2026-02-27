"""
services/amenities.py — Retrieves nearby amenities using the
Google Places Nearby Search API and calculates distance with Haversine.
"""

import os
import math
import requests

# Categories to search and their Google Places type strings
AMENITY_CATEGORIES = {
    "mrt_stations": "subway_station|transit_station",
    "shopping_malls": "shopping_mall",
    "schools": "school|primary_school|secondary_school",
    "restaurants": "restaurant",
    "parks": "park",
}

SEARCH_RADIUS_METERS = 1500  # 1.5 km


def _haversine(lat1, lng1, lat2, lng2):
    """Return straight-line distance in meters between two lat/lng points."""
    R = 6_371_000  # Earth radius in metres
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def _google_maps_link(place_name, lat, lng):
    """Build a clickable Google Maps URL for a place."""
    return (
        f"https://www.google.com/maps/search/?api=1"
        f"&query={place_name.replace(' ', '+')}"
        f"&center={lat},{lng}"
    )


def get_nearby_amenities(lat, lng, custom_categories=None):
    """
    Search for nearby amenities around the given coordinates.

    Queries Google Places for each category within 1.5 km and
    enriches each result with distance and a Google Maps link.

    Args:
        lat (float): Latitude of the property.
        lng (float): Longitude of the property.
        custom_categories (dict, optional): A map of friendly names to Google Places API types.

    Returns:
        dict: Keyed by category, each value is a list of amenity dicts.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    all_amenities = {}

    categories_to_search = custom_categories if custom_categories else AMENITY_CATEGORIES

    for category, place_type in categories_to_search.items():
        params = {
            "location": f"{lat},{lng}",
            "radius": SEARCH_RADIUS_METERS,
            "type": place_type,
            "key": api_key,
        }

        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()

        results = []
        for place in data.get("results", []):
            p_lat = place["geometry"]["location"]["lat"]
            p_lng = place["geometry"]["location"]["lng"]

            results.append({
                "name": place.get("name", "Unknown"),
                "rating": place.get("rating", 0.0),
                "user_ratings_total": place.get("user_ratings_total", 0),
                "distance_meters": _haversine(lat, lng, p_lat, p_lng),
                "google_maps_link": _google_maps_link(place.get("name", ""), p_lat, p_lng),
            })

        all_amenities[category] = results

    return all_amenities
