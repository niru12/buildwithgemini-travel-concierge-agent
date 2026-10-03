# Copyright 2026 Google LLC
# Google Maps Platform tools (Geocoding and Places API New) for Travel Concierge Agent

import os
import httpx
from dotenv import load_dotenv

load_dotenv()


def _get_maps_api_key() -> str:
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not key:
        raise ValueError("GOOGLE_MAPS_API_KEY is not set in environment or .env file.")
    return key


def geocode_address(address: str) -> dict:
    """Converts a street address or location name into geographic coordinates (latitude/longitude).

    Args:
        address: The address or place name to geocode (e.g., 'Eiffel Tower, Paris' or '1600 Amphitheatre Pkwy, Mountain View, CA').

    Returns:
        A dictionary containing formatted_address, latitude, longitude, and place_id.
    """
    try:
        api_key = _get_maps_api_key()
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        response = httpx.get(url, params={"address": address, "key": api_key}, timeout=10.0)
        
        if response.status_code != 200:
            return {"error": f"Geocoding request failed with HTTP status {response.status_code}"}
            
        data = response.json()
        if not data.get("results"):
            return {"error": f"No geocoding results found for '{address}'"}
            
        first = data["results"][0]
        location = first["geometry"]["location"]
        
        return {
            "formatted_address": first.get("formatted_address"),
            "latitude": location["lat"],
            "longitude": location["lng"],
            "place_id": first.get("place_id"),
        }
    except Exception as e:
        return {"error": f"Geocoding failed: {e}"}


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "tourist_attraction",
    radius_meters: float = 1000.0,
) -> list[dict]:
    """Finds nearby places of a given type around a latitude/longitude coordinate using Google Places API (New).

    Args:
        latitude: Latitude coordinate of the central location.
        longitude: Longitude coordinate of the central location.
        place_type: Type of places to search for (e.g., 'cafe', 'restaurant', 'tourist_attraction', 'museum', 'lodging', 'park').
        radius_meters: Radius in meters around the central point to search within (default 1000m).

    Returns:
        A list of dictionaries containing name, address, location (latitude/longitude), and types.
    """
    try:
        api_key = _get_maps_api_key()
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.types",
        }
        
        payload = {
            "includedTypes": [place_type.lower().strip()],
            "maxResultCount": 5,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": float(latitude),
                        "longitude": float(longitude),
                    },
                    "radius": float(radius_meters),
                }
            },
        }
        
        response = httpx.post(url, json=payload, headers=headers, timeout=10.0)
        if response.status_code != 200:
            return [{"error": f"Places request failed with status code {response.status_code}: {response.text}"}]
            
        data = response.json()
        places_data = data.get("places", [])
        
        results = []
        for p in places_data:
            display_name = p.get("displayName", {}).get("text", "Unknown Place")
            loc = p.get("location", {})
            results.append({
                "name": display_name,
                "address": p.get("formattedAddress", "N/A"),
                "location": {
                    "latitude": loc.get("latitude"),
                    "longitude": loc.get("longitude"),
                },
                "types": p.get("types", []),
            })
            
        return results
    except Exception as e:
        return [{"error": f"Failed to search nearby places: {e}"}]
