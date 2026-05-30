import os


MODEL = "claude-haiku-4-5-20251001"

MOCK_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "mock_data")

DEFAULTS = {
    "from_city": "Алматы",
    "nights": 2,
    "trip_type": "family_weekend",
    "needs": ["flight", "hotel", "insurance", "restaurant", "activity", "transfer"],
}

VALID_NEEDS = {"flight", "hotel", "insurance", "pharmacy", "restaurant", "activity", "transfer"}

NEED_TO_OPTIONS_KEY = {
    "flight": "flights",
    "hotel": "hotels",
    "insurance": "insurance",
    "pharmacy": "pharmacy",
    "restaurant": "restaurants",
    "activity": "activities",
    "transfer": "transfers",
}

NEED_TO_FILE = {
    "flight": "flights.json",
    "hotel": "hotels.json",
    "insurance": "insurance.json",
    "pharmacy": "pharmacy.json",
    "restaurant": "restaurants.json",
    "activity": "activities.json",
    "transfer": "transfer.json",
}

CATEGORY_ORDER = ("flight", "hotel", "insurance", "transfer", "pharmacy", "activity", "restaurant")
