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
    body = await request.json()
    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        if "messages" not in value:
            return {"status": "no message event"}
        message = value["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]
        if phone.startswith("549"):
            phone = "54" + phone[3:]
        print("Cliente:", phone)
        print("Mensaje:", text)
        # 🔎 interpretar mensaje
        text_lower = text.lower()
        db = SessionLocal()
        create_lead_service(
            db=db,
            name="WhatsApp User",
            phone=phone,
            message=text
        )
        # 🤖 lógica del bot
        if "departamento" in text_lower:
            properties = get_properties_by_type(db, "departamento")
            message = format_properties_message(properties)
            send_whatsapp_message(phone, message)
        elif "casa" in text_lower:
            properties = get_properties_by_type(db, "casa")
            message = format_properties_message(properties)
            send_whatsapp_message(phone, message)
        elif "local" in text_lower:
            properties = get_properties_by_type(db, "local")
            message = format_properties_message(properties)
            send_whatsapp_message(phone, message)
        else:
            send_menu_message(phone)
        db.close()
    except Exception as e:
        print("Error parsing message:", e)
    return {"status": "received"}



# ver despues si usuarios escriben "1", "2" o "3" para enviarles info específica
# elif text == "1":
#             send_whatsapp_message(phone, "Te enviaré propiedades en venta disponibles.")
#         elif text == "2":
#             send_whatsapp_message(phone, "Te enviaré propiedades en alquiler disponibles.")
#         elif text == "3":
#             send_whatsapp_message(phone, "Un asesor se comunicará contigo para la tasación.")






