# Copyright 2026 Google LLC
# Firestore tools for Travel Concierge Agent

from google.cloud import firestore

# HARDCODED PROJECT ID:
# On Agent Platform, GOOGLE_CLOUD_PROJECT and google.auth.default() return the project NUMBER,
# which causes Firestore database lookup to fail. Always use the explicit project ID string.
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-8d917c684652"


def _get_firestore_db():
    return firestore.Client(project=FIRESTORE_PROJECT_ID)


def list_destinations(category: str = "", country: str = "") -> list[dict]:
    """Lists travel destinations from the Firestore database with optional filters.

    Args:
        category: Optional category to filter by (e.g. 'City & Nature', 'Culture & Food', 'Culture & Art', 'Culture & History', 'History & Food').
        country: Optional country to filter by (e.g. 'USA', 'Japan', 'France', 'Italy').

    Returns:
        A list of destination dictionaries matching the query criteria.
    """
    db = _get_firestore_db()
    ref = db.collection("destinations")

    docs = ref.stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        if category and category.lower() not in data.get("category", "").lower():
            continue
        if country and country.lower() not in data.get("country", "").lower():
            continue
        results.append(data)

    return results


def get_destination_details(destination_id: str) -> dict:
    """Retrieves detailed information about a specific destination by its ID.

    Args:
        destination_id: The unique string ID of the destination (e.g., 'san-francisco', 'tokyo', 'paris', 'kyoto', 'rome').

    Returns:
        A dictionary containing destination details or an error message if not found.
    """
    db = _get_firestore_db()
    doc_ref = db.collection("destinations").document(destination_id.lower().strip())
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()
    return {"error": f"Destination with ID '{destination_id}' was not found in Firestore database."}


def add_destination(
    destination_id: str,
    name: str,
    country: str,
    description: str,
    category: str,
    avg_cost_per_day: int,
    popular_activities: list[str],
) -> str:
    """Adds a new destination or updates an existing destination in the Firestore database.

    Args:
        destination_id: Unique string identifier for the destination (e.g., 'barcelona').
        name: Name of the destination city or area (e.g., 'Barcelona').
        country: Country name (e.g., 'Spain').
        description: Brief overview of why travelers visit this destination.
        category: Category (e.g., 'Culture & Beach', 'Food & Architecture').
        avg_cost_per_day: Estimated average daily travel budget in USD.
        popular_activities: List of popular activity strings.

    Returns:
        A confirmation message string.
    """
    db = _get_firestore_db()
    doc_ref = db.collection("destinations").document(destination_id.lower().strip())
    data = {
        "id": destination_id.lower().strip(),
        "name": name,
        "country": country,
        "description": description,
        "category": category,
        "avg_cost_per_day": avg_cost_per_day,
        "popular_activities": popular_activities,
        "rating": 4.5,
    }
    doc_ref.set(data)
    return f"Successfully saved destination '{name}' ({destination_id}) to Firestore."
