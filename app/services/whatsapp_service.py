import requests
import os
from app.models.lead import Lead

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

def send_whatsapp_message(to: str, message: str):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": message
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)
    return response.json()


def send_menu_message(to):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": "Hola 👋\n\nGracias por contactar con la inmobiliaria.\n\n1️⃣ Ver propiedades en venta\n2️⃣ Ver alquileres\n3️⃣ Solicitar tasación"
        }
    }
    requests.post(url, headers=headers, json=payload)
    
    
def send_and_save(db, phone, text, contact):
    send_whatsapp_message(phone, text)
    new_msg = Lead(
        name=contact.name,
        phone=phone,
        message=text,
        contact_id=contact.id,
        source="whatsapp",
        status="sent"
    )
    db.add(new_msg)
    db.commit()






