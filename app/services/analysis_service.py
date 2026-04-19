import json
import os
import unicodedata

def normalize(text):
    return unicodedata.normalize('NFKD', text)\
        .encode('ascii', 'ignore')\
        .decode('utf-8')\
        .lower()

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/properties_dataset.json")

def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_market_analysis(city: str, property_type: str):
    data = load_data()
    filtered = [
        p for p in data
        if normalize(city) in normalize(p["city"])
        and normalize(property_type) in normalize(p["property_type"])
    ] 
    print("CITY:", city)
    print("TYPE:", property_type)
    print("RESULT COUNT:", len(filtered))

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


# Extrae ciudad y tipo de propiedad de un mensaje de texto
def extract_data_from_message(message: str):
    city = ""
    property_type = ""
    lines = message.split("\n")
    for line in lines:
        line = line.strip().lower()
        if line.startswith("ciudad"):
            city = line.split(":")[-1].strip()
        if line.startswith("tipo"):
            property_type = line.split(":")[-1].strip()
    return city, property_type


# def extract_data_from_message(message: str):
#     city = ""
#     property_type = ""
#     lines = message.split("\n")
#     for line in lines:
#         if "Ciudad:" in line:
#             city = line.replace("Ciudad:", "").strip()
#         if "Tipo:" in line:
#             property_type = line.replace("Tipo:", "").strip()
#     return city, property_type