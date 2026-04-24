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
from app.services.property_service import get_properties_by_property_type
from time import time

user_context = {}   ## contexto simple en memoria para cada usuario (se pierde si se reinicia el servidor, pero es suficiente para este ejemplo)
recent_messages = {}  ## para evitar mensajes duplicados
processed_messages = set()

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


def send_interactive(to, payload):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    return requests.post(url, headers=headers, json=payload)


def send_main_menu(to):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "Hola 👋 Soy tu asistente inmobiliario\n\n¿Qué querés hacer?"
            },
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "comprar", "title": "Comprar"}},
                    {"type": "reply", "reply": {"id": "alquilar", "title": "Alquilar"}},
                    {"type": "reply", "reply": {"id": "otras", "title": "Otra opción"}}
                ]
            }
        }
    }
    response = send_interactive(to, payload)
    print("📤 STATUS:", response.status_code)
    print("📤 RESPONSE:", response.text)


def send_other_menu(to):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "¿Qué necesitás?"
            },
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "vender", "title": "Vender"}},
                    {"type": "reply", "reply": {"id": "asesor", "title": "Hablar con asesor"}}
                ]
            }
        }
    }
    response = send_interactive(to, payload)
    print("📤 STATUS:", response.status_code)
    print("📤 RESPONSE:", response.text)


def send_property_menu_main(to, operation):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": f"¿Qué tipo buscás para {operation}?"
            },
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "departamento", "title": "Departamento"}},
                    {"type": "reply", "reply": {"id": "casa", "title": "Casa"}},
                    {"type": "reply", "reply": {"id": "mas_tipos", "title": "Otra opción"}}
                ]
            }
        }
    }
    response = send_interactive(to, payload)
    print("📤 STATUS:", response.status_code)
    print("📤 RESPONSE:", response.text)


def send_property_menu_extra(to):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "Más opciones:"
            },
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "local", "title": "Local"}},
                    {"type": "reply", "reply": {"id": "terreno", "title": "Terreno"}},
                    {"type": "reply", "reply": {"id": "asesor", "title": "Hablar con asesor"}}
                ]
            }
        }
    }
    response = send_interactive(to, payload)
    print("📤 STATUS:", response.status_code)
    print("📤 RESPONSE:", response.text)


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
        
        # ✅ evitar duplicados
        message_id = message.get("id")
        if message_id in processed_messages:
            print("⚠️ Mensaje duplicado ignorado")
            return {"status": "duplicate"}
        processed_messages.add(message_id)
        
        # ✅ asegurar contexto SIEMPRE
        is_new_user = phone not in user_context
        if is_new_user:
            user_context[phone] = {
                "operation": None,
                "type": None,
                "step" : "menu"
            }

        ctx = user_context[phone]

        # 👇 detectar texto
        interactive = message.get("interactive", {})
        button_reply = interactive.get("button_reply", {})
        if button_reply:
            text = button_reply.get("title", "")
            text_lower = button_reply.get("id", "").lower()
        else:
            text = message.get("text", {}).get("body", "")
            text_lower = text.lower().strip()
        print("TEXTO:", text)
        
        # ✅ menú SOLO primera vez
        valid_inputs = [
            "hola", "dia", "tardes",
            "comprar", "alquilar", "otras", "menu", "inicio",
            "vender", "buenas", "asesor",
            "departamento", "casa", "local", "terreno",
            "mas_tipos"
        ]

        if is_new_user:
            ctx["step"] = "menu"
            send_main_menu(phone)
            return {"status": "menu auto"}
        if text_lower not in valid_inputs and ctx.get("step") != "results":
            ctx["step"] = "menu"
            send_main_menu(phone)
            return {"status": "menu auto"}

        # 🧠 CONTEXTO (siempre seguro)
        if phone not in user_context:
            
            user_context[phone] = {
                "operation": None,
                "type": None,
                "step" : "menu"
            }

        db = SessionLocal()

        # 👤 nombre
        contacts = value.get("contacts", [])
        name = "WhatsApp User"
        if contacts:
            name = contacts[0].get("profile", {}).get("name", name)

        # 💾 guardar lead
        create_lead_service(
            db=db,
            name=name,
            phone=phone,
            message=text,
            property_id=None,
            source="whatsapp",
        )

        contact = db.query(Contact).filter(Contact.phone == phone).first()

        # 🚫 modo humano
        if contact and contact.status == "human":
            print("👤 Conversación humana activa")
            db.close()
            return {"status": "human"}

        # 🔄 HubSpot
        if contact and contact.hubspot_id:
            update_hubspot_contact(contact.hubspot_id, {
                "hs_lead_status": "IN_PROGRESS"
            })

        # ======================================================
        # 🤖 BOT
        # ======================================================
        step = ctx.get("step")
        # 🔹 MENÚ PRINCIPAL
        if text_lower in [
            "hola", "consulta", "dias", "tardes", "noches", "operaciones",
            "pregunta", "duda", "vender","comprar", "alquilar", "casa", "departamento",
            "local", "terreno", "mas_tipos", "buenas"]:   
            ctx["step"] = "menu"
            send_main_menu(phone)
            return

        # 🔹 OTRAS OPCIONES
        if text_lower == "otras":
            ctx["step"] = "other_menu"
            send_other_menu(phone)
            return

        # 🔹 COMPRAR
        if text_lower == "comprar":
            ctx["operation"] = "venta"
            ctx["step"] = "property_menu"
            send_property_menu_main(phone, "compra")
            db.close()
            return

        # 🔹 ALQUILAR
        if text_lower == "alquilar":
            ctx["operation"] = "alquiler"
            ctx["step"] = "property_menu"
            send_property_menu_main(phone, "alquiler")
            db.close()
            return

        # 🔹 MÁS TIPOS
        if text_lower == "mas_tipos":
            ctx["step"] = "property_menu_extra"
            send_property_menu_extra(phone)
            return

        # 🔹 VENDER
        if text_lower == "vender":
            ctx["step"] = "vender"
            send_whatsapp_message(phone, "📊 Podés buscar tasaciones en la barra de búsqueda o escribir *asesor*")
            db.close()
            return

        # 🔹 TIPO PROPIEDAD
        if text_lower in ["departamento", "casa", "local", "terreno"]:
            ctx["type"] = text_lower
            ctx["step"] = "results"

            operation = ctx.get("operation")

            if operation:
                properties = db.query(Property).filter(
                    Property.operation_type.ilike(f"%{operation}%"),
                    Property.property_type.ilike(f"%{text_lower}%")
            ).limit(3).all()
            else:
                properties = get_properties_by_property_type(db, text_lower)

            msg = "🏡 Propiedades disponibles:\n\n"
            for prop in properties:
                msg += f"📌 {prop.title}\n"
                msg += f"📍 {prop.price}\n"
                msg += f"\n\n🔗 Ver propiedad:\nhttps://frontend-plataforma-inmobiliaria.onrender.com/property/{prop.id}\n\n"
                msg += f" si querés más info escribí *asesor*\n"
            send_whatsapp_message(phone, msg)
            return

        # 🔹 ASESOR
        if "asesor" in text_lower:
            if contact:
                contact.status = "human"
                db.commit()
            send_whatsapp_message(phone, "🙌 Un asesor te escribe en breve.")
            return


        # 🟢 MENÚ PRINCIPAL

        if ctx.get("step") == "results" and text_lower not in ["menu", "inicio"]:
            if contact:
                contact.status = "human"
                db.commit()
            send_whatsapp_message(phone, "🙌 Te paso con un asesor para ayudarte mejor.")
            return {"status": "escalated to human"}

        # 🟡 FALLBACK
        send_main_menu(phone)
        # send_interactive_menu(phone)
        db.close()
        return {"status": "fallback"}

    except Exception as e:
        print("❌ ERROR:", e)
        print(traceback.format_exc())
        return {"status": "error"}


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



























