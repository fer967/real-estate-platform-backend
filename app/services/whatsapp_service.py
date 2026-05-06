import requests
import os
from app.models.lead import Lead

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")


def send_messenger_message(psid: str, message: str):
    url = "https://graph.facebook.com/v19.0/me/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",  # ⚠️ mismo token si usás app unificada
        "Content-Type": "application/json"
    }
    payload = {
        "recipient": {"id": psid},
        "message": {"text": message}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Messenger Status:", response.status_code)
    print("Messenger Response:", response.text)
    return response.json()


def send_message(contact, message):
    """
    Envío inteligente según canal disponible
    """
    if not contact.phone or len(contact.phone) < 10:
        return {"error": "Contacto sin teléfono válido"}
    
    if contact.phone:
        print("📲 Enviando por WhatsApp")
        return send_whatsapp_message(contact.phone, message)
    elif contact.messenger_id:
        print("💬 Enviando por Messenger")
        return send_messenger_message(contact.messenger_id, message)
    else:
        print("❌ Contacto sin canal disponible")
        return None


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


def send_and_save(db, contact, text):
    response = send_message(contact, text)
    new_msg = Lead(
        name=contact.name,
        phone=contact.phone if contact.phone else f"messenger:{contact.messenger_id}",
        message=text,
        contact_id=contact.id,
        source="whatsapp" if contact.phone else "messenger",
        status="sent"
    )
    db.add(new_msg)
    db.commit()

    return response









