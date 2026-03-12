import requests
import os
from dotenv import load_dotenv
from app.core.logger import logger

load_dotenv()

HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")

def create_hubspot_contact(name, email, phone):
    url = "https://api.hubapi.com/crm/v3/objects/contacts"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "properties": {
            "firstname": name,
            "email": email,
            "phone": phone
        }
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            logger.info("HubSpot contact created successfully")
        else:
            logger.warning(
                f"HubSpot error {response.status_code}: {response.text}"
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"HubSpot connection error: {str(e)}")



