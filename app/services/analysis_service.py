import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/properties_dataset.json")

def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_market_analysis(city: str, property_type: str):
    data = load_data()

    filtered = [
        p for p in data
        if city.lower() in p["city"].lower()
        and p["property_type"] == property_type
    ]

    if not filtered:
        return None

    prices = [p["price"] for p in filtered]
    price_m2 = [p["price"] / p["surface"] for p in filtered]

    avg_price = sum(prices) / len(prices)
    avg_m2 = sum(price_m2) / len(price_m2)

    return {
        "count": len(filtered),
        "avg_price": round(avg_price, 2),
        "min_price": min(prices),
        "max_price": max(prices),
        "avg_m2": round(avg_m2, 2)
    }