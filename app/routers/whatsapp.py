import traceback
from fastapi import APIRouter, Request, HTTPException  
import os
import requests
from dotenv import load_dotenv
from app.integrations.hubspot import update_hubspot_contact
from app.models.contact import Contact
from app.models.lead import Lead
from app.models.property import Property
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

user_context = {}   ## contexto simple en memoria para cada usuario (se pierde si se reinicia el servidor, pero es suficiente para este ejemplo)

load_dotenv()

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")


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
                "text": "Hola 👋 Gracias por comunicarte con nosotros, que estas buscando?"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "venta",
                            "title": "Ver propiedades en venta"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "alquiler",
                            "title": "Ver propiedades en alquiler"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "tasacion",
                            "title": "Quiero tasar mi propiedad"
                        }
                    }
                ]
            }
        }
    }
    requests.post(url, headers=headers, json=payload)


def send_help_menu(to):
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
                "text": "No entendí del todo 🤔\n\n¿Querés ver opciones o hablar con un asesor?"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "menu",
                            "title": "Ver opciones"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "asesor",
                            "title": "Hablar con asesor"
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
    body = await request.json()
    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        if "messages" not in value:
            return {"status": "no message event"}
        message = value["messages"][0]
        phone = message["from"]

        if phone not in user_context:   #### inicializar contexto para nuevo usuario
            user_context[phone] = {
                "operation": None,
                "type": None
            }
            
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
            message=text,
            property_id=None,     # por ahora no detectamos propiedad específica, pero se podría mejorar con NLP o reglas más avanzadas
            source="whatsapp",
        )
        
        contact = db.query(Contact).filter(Contact.phone == phone).first()
        
        # 🚫 DESPUÉS cortar bot
        if contact.status == "human":
            print("👤 Conversación humana - solo guardo mensaje")
            db.close()
            return {"status": "saved only"}
        
        if contact.hubspot_id:
            update_hubspot_contact(contact.hubspot_id, {
                "hs_lead_status": "IN_PROGRESS"
            })
        
        
        # 🤖 LÓGICA BOT
        # 1️⃣ BOTONES
        if text_lower == "venta":
            user_context[phone]["operation"] = "venta"   ## actualizar contexto
            properties = get_properties_by_operation(db, "venta")
            msg = format_properties_message(properties)
            send_whatsapp_message(phone, f"🏠 *Propiedades en venta:*\n\n{msg}")
            
        elif text_lower == "alquiler":
            user_context[phone]["operation"] = "alquiler"
            user_context[phone]["type"] = None  # reset tipo
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
        elif text_lower in ["departamento", "departamentos"]:
            user_context[phone]["type"] = "departamento"
            operation = user_context[phone].get("operation")
            if operation:
                properties = db.query(Property).filter(
                    Property.operation_type.ilike(f"%{operation}%"),
                    Property.property_type.ilike("%departamento%")
                ).limit(3).all()
            else:
                properties = get_properties_by_property_type(db, "departamento")
            msg = format_properties_message(properties)
            send_whatsapp_message(phone, msg)
            
        elif any(word in text_lower for word in ["casa", "casas"]):
    # si el mensaje es más largo → NO asumir
            if len(text_lower.split()) > 2:
                send_help_menu(phone)
                return {"status": "ambiguous"}
            user_context[phone]["type"] = "casa"
            operation = user_context[phone].get("operation")
            if operation:
                properties = db.query(Property).filter(
                Property.operation_type.ilike(f"%{operation}%"),
                Property.property_type.ilike("%casa%")
            ).limit(3).all()
            else:
                properties = get_properties_by_property_type(db, "casa")
            msg = format_properties_message(properties)
            send_whatsapp_message(phone, msg)

        elif any(word in text_lower for word in ["local", " locales"]):
    # si el mensaje es más largo → NO asumir
            if len(text_lower.split()) > 2:
                send_help_menu(phone)
                return {"status": "ambiguous"}
            user_context[phone]["type"] = " local "
            operation = user_context[phone].get("operation")
            if operation:
                properties = db.query(Property).filter(
                    Property.operation_type.ilike(f"%{operation}%"),
                    Property.property_type.ilike("%local %")
                ).limit(3).all()
            else:
                properties = get_properties_by_property_type(db, " local ")
            msg = format_properties_message(properties)
            send_whatsapp_message(phone, msg)
            
        elif any(word in text_lower for word in ["barrio", "zona", "precio"]):
            send_help_menu(phone)
            
        elif "asesor" in text_lower:
            if contact:
                contact.status = "human"
                print("CONTACT STATUS:", contact.status if contact else "NO CONTACT")
                db.commit()
            send_whatsapp_message(
                phone,
                "🙌 Perfecto, un asesor te va a escribir en breve."
            )

        # 4️⃣ FALLBACK → MENÚ INTERACTIVO
        else:
            send_help_menu(phone)
            
        db.close()
    except Exception as e:
        print("❌ ERROR:", e)
        print(traceback.format_exc())
    return {"status": "received"}


@router.post("/send")
def send_whatsapp(data: dict):
    try:
        to = data.get("to")
        message = data.get("message")
        if not to or not message:
            raise HTTPException(status_code=400, detail="Missing data")
        url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        response = requests.post(url, headers=headers, json=payload)
        print("META RESPONSE:", response.text)
        return response.json()
    except Exception as e:
        print("❌ SEND ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))


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



















