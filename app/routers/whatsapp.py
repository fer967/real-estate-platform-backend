from fastapi import APIRouter, Request
import os
from dotenv import load_dotenv
from app.services.lead_service import create_lead_service
from app.core.database import SessionLocal
from app.services.whatsapp_service import send_menu_message, send_whatsapp_message 
from app.services.property_service import (
    get_properties_by_type,
    format_properties_message
)


load_dotenv()

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

@router.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    return {"error": "Verification failed"}


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
        # ⚠️ puede no venir texto (ej: botones futuros)
        text = message.get("text", {}).get("body", "")
        text_lower = text.lower().strip()
        print("Cliente:", phone)
        print("Mensaje:", text)
        db = SessionLocal()
        
        contacts = value.get("contacts", [])
        name = "WhatsApp User"
        if contacts:
            name = contacts[0].get("profile", {}).get("name", "WhatsApp User")
        # guardar lead
        create_lead_service(
            db=db,
            name=name,       
            phone=phone,
            message=text
        )
        
        # 🤖 LÓGICA BOT MEJORADA
        if text_lower in ["hola", "menu", "menú", "inicio", "hi"]:
            send_menu_message(phone)
        elif text_lower in ["1", "venta", "comprar"]:
            properties = get_properties_by_type(db, "venta")
            msg = format_properties_message(properties)
            send_whatsapp_message(phone, f"🏠 *Propiedades en venta:*\n\n{msg}")
        elif text_lower in ["2", "alquiler", "alquilar"]:
            properties = get_properties_by_type(db, "alquiler")
            msg = format_properties_message(properties)
            send_whatsapp_message(phone, f"🔑 *Propiedades en alquiler:*\n\n{msg}")
        elif text_lower in ["3", "tasacion", "tasación"]:
            send_whatsapp_message(
                phone,
                "📊 *Tasación de propiedad*\n\nEnvíanos la dirección o zona y te contactamos para cotizarla."
            )
        elif "departamento" in text_lower:
            properties = get_properties_by_type(db, "departamento")
            msg = format_properties_message(properties)
            send_whatsapp_message(phone, msg)
        elif "casa" in text_lower:
            properties = get_properties_by_type(db, "casa")
            msg = format_properties_message(properties)
            send_whatsapp_message(phone, msg)
        elif "local" in text_lower:
            properties = get_properties_by_type(db, "local")
            msg = format_properties_message(properties)
            send_whatsapp_message(phone, msg)
        else:
            # fallback inteligente
            send_whatsapp_message(
                phone,
                "No entendí tu mensaje 🤔\n\nEscribí *menu* para ver opciones."
            )
        db.close()
    except Exception as e:
        print("Error parsing message:", e)
    return {"status": "received"}












