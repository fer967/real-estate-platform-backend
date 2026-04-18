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
# modificacion para retornar el id del contacto creado en hubspot, para luego guardarlo en la base de datos local
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            logger.info("HubSpot contact created successfully")
            contact_id=response.json()["id"]
            return contact_id
        else:
            logger.warning(
                f"HubSpot error {response.status_code}: {response.text}"
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"HubSpot connection error: {str(e)}")


def create_note_in_hubspot(contact_id, message):
    url = "https://api.hubapi.com/crm/v3/objects/notes"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "properties": {
            "hs_note_body": message
        },
        "associations": [
            {
                "to": {"id": contact_id},
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 202
                    }
                ]
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()


def update_hubspot_contact(contact_id, properties: dict):
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "properties": properties
    }
    response = requests.patch(url, headers=headers, json=data)
    print("🔵 HUBSPOT UPDATE STATUS:", response.status_code)
    print("🔵 HUBSPOT UPDATE RESPONSE:", response.text)
    return response.json()


def get_hubspot_contact(contact_id):
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    return response.status_code == 200


# def update_hubspot_contact(contact_id, properties: dict):
#     url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
#     headers = {
#         "Authorization": f"Bearer {HUBSPOT_API_KEY}",
#         "Content-Type": "application/json"
#     }
#     data = {
#         "properties": properties
#     }
#     response = requests.patch(url, headers=headers, json=data)
#     return response.json()





