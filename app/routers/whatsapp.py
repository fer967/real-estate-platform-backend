from fastapi import APIRouter, Request
import os
import requests
from dotenv import load_dotenv
from app.models.lead import Lead
from app.services.lead_service import create_lead_service
from app.core.database import SessionLocal
from app.services.whatsapp_service import (
    WHATSAPP_TOKEN,
    PHONE_NUMBER_ID,
    send_whatsapp_message
)
from app.services.property_service import (
    get_properties_by_operation,
    format_properties_message,
    get_properties_by_property_type
)

load_dotenv()

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")


# 🔐 VERIFY WEBHOOK
@router.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    return {"error": "Verification failed"}


# 📩 SEND INTERACTIVE MENU
def send_interactive_menu(to: str):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "Hola 👋 ¿Qué te interesa?"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "venta",
                            "title": "Ver ventas"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "alquiler",
                            "title": "Ver alquileres"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "tasacion",
                            "title": "Tasación"
                        }
                    }
                ]
            }
        }
    }
    requests.post(url, headers=headers, json=payload)


# 📥 RECEIVE WEBHOOK
@router.post("/webhook")
async def receive_message(request: Request):
    print("🔥 WEBHOOK HIT")
    body = await request.json()
    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        if "messages" not in value:
            return {"status": "no message event"}
        message = value["messages"][0]
        phone = message["from"]
        # normalizar número Argentina
        if phone.startswith("549"):
            phone = "54" + phone[3:]
        # 👇 detectar botones o texto
        interactive = message.get("interactive", {})
        button_reply = interactive.get("button_reply", {})
        if button_reply:
            text = button_reply.get("title", "")
            text_lower = button_reply.get("id", "").lower()
        else:
            text = message.get("text", {}).get("body", "")
            text_lower = text.lower().strip()
        print("Cliente:", phone)
        print("Mensaje:", text)
        db = SessionLocal()
        # 👤 obtener nombre real
        contacts = value.get("contacts", [])
        name = "WhatsApp User"
        if contacts:
            name = contacts[0].get("profile", {}).get("name", "WhatsApp User")
        # 💾 guardar lead
        create_lead_service(
            db=db,
            name=name,
            phone=phone,
            message=text
        )
        
        lead = db.query(Lead)\
            .filter(Lead.phone == phone)\
            .order_by(Lead.created_at.desc())\
            .first()
# 🚫 SI YA LO ESTÁ ATENDIENDO UN HUMANO → NO RESPONDER
        if lead and lead.status == "human":
            print("👤 Conversación tomada por humano")
            db.close()
            return {"status": "handled by human"}
        
        # 🤖 LÓGICA BOT
        # 1️⃣ BOTONES
        if text_lower == "venta":
            properties = get_properties_by_operation(db, "venta")
            msg = format_properties_message(properties)
            send_whatsapp_message(phone, f"🏠 *Propiedades en venta:*\n\n{msg}")
        elif text_lower == "alquiler":
            properties = get_properties_by_operation(db, "alquiler")
            msg = format_properties_message(properties)
            send_whatsapp_message(phone, f"🔑 *Propiedades en alquiler:*\n\n{msg}")
        elif text_lower == "tasacion":
            send_whatsapp_message(
                phone,
                "📊 *Tasación de propiedad*\n\nEnvíanos la dirección o zona y te contactamos."
            )
        # 2️⃣ MENÚ
        elif any(word in text_lower for word in ["hola", "menu", "menú", "inicio", "hi"]):
            send_interactive_menu(phone)
        # 3️⃣ DETECCIÓN SIMPLE
        elif "departamento" in text_lower:
            properties = get_properties_by_property_type(db, "departamento")
            msg = format_properties_message(properties)
            send_whatsapp_message(phone, msg)
        elif "casa" in text_lower:
            properties = get_properties_by_property_type(db, "casa")
            msg = format_properties_message(properties)
            send_whatsapp_message(phone, msg)
        elif "local" in text_lower:
            properties = get_properties_by_property_type(db, "local")
            msg = format_properties_message(properties)
            send_whatsapp_message(phone, msg)
            
        elif "asesor" in text_lower:
            lead = db.query(Lead).filter(Lead.phone == phone).first()

            if lead:
                lead.status = "human"
                db.commit()

                send_whatsapp_message(
                phone,
                "🙌 Perfecto, un asesor te va a escribir en breve."
                )

                send_whatsapp_message(
                "5493516271526",
                f"📢 Nuevo lead\n\n👤 {name}\n📞 {phone}\n💬 {text}"
                )
            
        # 4️⃣ FALLBACK → MENÚ INTERACTIVO
        else:
            send_whatsapp_message(
            phone,
            "No terminé de entender 🤔\n\nPodés elegir una opción o escribir *asesor* para hablar con una persona."
            )
        db.close()
    except Exception as e:
        print("Error parsing message:", e)
    return {"status": "received"}














