"""
services/geocode.py — Converts a property address into lat/lng
using the Google Maps Geocoding API.
"""

import os
import requests


def geocode_address(address):
    """
    Geocode an address into coordinates.

    Args:
        address (str): Property address, e.g. "1 Raffles Place, Singapore".

    Returns:
        dict: { "formatted_address": str, "latitude": float, "longitude": float }

    Raises:
        ValueError: If the address could not be geocoded.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    url = "https://maps.googleapis.com/maps/api/geocode/json"

    params = {"address": address, "key": api_key}
    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    if data["status"] != "OK":
        raise ValueError(
            f"Geocoding failed for '{address}'. "
            f"API status: {data['status']}. Check your API key and address."
        )

    result = data["results"][0]
    location = result["geometry"]["location"]

    return {
        "formatted_address": result["formatted_address"],
        "latitude": location["lat"],
        "longitude": location["lng"],
    }
