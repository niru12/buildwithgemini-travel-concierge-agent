import os
from google.cloud import firestore

# Hardcoded project ID as required to avoid project number issues on Agent Platform
PROJECT_ID = "qwiklabs-gcp-01-8d917c684652"

DESTINATIONS = [
    {
        "id": "san-francisco",
        "name": "San Francisco",
        "country": "USA",
        "description": "Iconic coastal city known for foggy weather, Golden Gate Bridge, cable cars, and tech innovation.",
        "category": "City & Nature",
        "avg_cost_per_day": 250,
        "popular_activities": ["Walk the Golden Gate Bridge", "Visit Alcatraz Island", "Ride historic Cable Cars", "Explore Fisherman's Wharf"],
        "rating": 4.8,
    },
    {
        "id": "tokyo",
        "name": "Tokyo",
        "country": "Japan",
        "description": "Bustling metropolis blending ultramodern skyscrapers with historic temples, world-class cuisine, and vibrant culture.",
        "category": "Culture & Food",
        "avg_cost_per_day": 200,
        "popular_activities": ["Visit Senso-ji Temple", "Explore Shibuya Crossing", "Dine in Omoide Yokocho", "Visit Tokyo Skytree"],
        "rating": 4.9,
    },
    {
        "id": "paris",
        "name": "Paris",
        "country": "France",
        "description": "The City of Light, world-famous for art, fashion, gastronomy, historical monuments, and romantic charm.",
        "category": "Culture & Art",
        "avg_cost_per_day": 230,
        "popular_activities": ["Ascend the Eiffel Tower", "Tour the Louvre Museum", "Stroll along the Seine", "Visit Notre-Dame Cathedral"],
        "rating": 4.7,
    },
    {
        "id": "kyoto",
        "name": "Kyoto",
        "country": "Japan",
        "description": "Japan's cultural capital known for classical Buddhist temples, gardens, imperial palaces, Shinto shrines, and traditional wooden houses.",
        "category": "Culture & History",
        "avg_cost_per_day": 180,
        "popular_activities": ["Walk through Fushimi Inari Shrine", "Visit Kinkaku-ji (Golden Pavilion)", "Explore Arashiyama Bamboo Grove"],
        "rating": 4.9,
    },
    {
        "id": "rome",
        "name": "Rome",
        "country": "Italy",
        "description": "Historic capital rich in ancient ruins, stunning Renaissance architecture, lively plazas, and world-renowned Italian food.",
        "category": "History & Food",
        "avg_cost_per_day": 210,
        "popular_activities": ["Tour the Colosseum", "Visit the Vatican Museums & Sistine Chapel", "Toss a coin in Trevi Fountain"],
        "rating": 4.8,
    },
]

def seed_database():
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("destinations")
    
    print(f"Seeding 'destinations' collection in Firestore project '{PROJECT_ID}'...")
    for item in DESTINATIONS:
        doc_id = item["id"]
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(item)
        print(f"  - Added destination: {item['name']} ({doc_id})")
    
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
