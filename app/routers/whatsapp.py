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
    send_message,
    send_whatsapp_message
)
from app.services.property_service import get_properties_by_property_type
from time import time
from app.services.websocket_manager import notify_admins
import re


user_context = {}   ## contexto simple en memoria para cada usuario (se pierde si se reinicia el servidor, pero es suficiente para este ejemplo)
recent_messages = {}  
processed_messages = set()

load_dotenv()

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")
ADMIN_PHONE = os.getenv("ADMIN_PHONE")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")


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


def get_messenger_user_name(psid):
    try:
        url = f"https://graph.facebook.com/v19.0/{psid}"
        params = {
            "fields": "name",
            "access_token": PAGE_ACCESS_TOKEN
        }
        res = requests.get(url, params=params)
        data = res.json()
        return data.get("name", "Facebook User")
    except Exception as e:
        print("❌ Error obteniendo nombre Messenger:", e)
        return "Facebook User"


def extract_phone(text):
    match = re.search(r"\b\d{10,15}\b", text)
    return match.group(0) if match else None


def normalize_phone(phone: str) -> str | None:
    if not phone:
        return None
    # 🔹 dejar solo números
    digits = re.sub(r"\D", "", phone)
    # 🔴 muy corto → inválido
    if len(digits) < 10:
        return None
    # Caso 1: ya viene bien (549...)
    if digits.startswith("549") and len(digits) >= 12:
        return digits
    # Caso 2: viene con +54 sin 9 → agregar 9
    if digits.startswith("54") and not digits.startswith("549"):
        return "549" + digits[2:]
    # Caso 3: empieza con 0 (ej: 0351...)
    if digits.startswith("0"):
        digits = digits[1:]
        return "549" + digits
    # Caso 4: número local (ej: 351...)
    if len(digits) == 10:
        return "549" + digits
    # fallback
    return digits


# 📥 RECEIVE WEBHOOK
@router.post("/webhook")
async def receive_message(request: Request):
    body = await request.json()
    
    try:
        entry = body["entry"][0]

        if "messaging" in entry:
            messaging_event = entry["messaging"][0]
            sender_id = messaging_event["sender"]["id"]
            text = ""
            if "message" in messaging_event:
                text = messaging_event["message"].get("text", "")
            print("📩 Messenger:", text)
            db = SessionLocal()
            name = get_messenger_user_name(sender_id)


            # 🔍 detectar teléfono
            raw_phone = extract_phone(text)
            phone_detected = normalize_phone(raw_phone)
            # 🔍 buscar contacto SIEMPRE primero
            contact = db.query(Contact).filter(
                Contact.messenger_id == sender_id
            ).first()
            if phone_detected:
                print("📱 Teléfono detectado:", phone_detected)
                # buscar si ya existe ese teléfono
                existing_contact = db.query(Contact).filter(
                    Contact.phone == phone_detected
                ).first()
                if existing_contact:
                    print("🔗 Vinculando con contacto existente")
                    # asignar messenger_id al correcto
                    existing_contact.messenger_id = sender_id
                    # migrar leads
                    leads = db.query(Lead).filter(
                        Lead.phone == sender_id
                    ).all()
                    for lead in leads:
                        lead.phone = phone_detected
                    # eliminar duplicado si existe
                    if contact and contact.id != existing_contact.id:
                        db.delete(contact)
                    contact = existing_contact
                else:
                    if contact:
                        print("🆕 Actualizando contacto actual")
                        contact.phone = phone_detected
                    else:
                        print("🆕 Creando contacto completo")
                        contact = Contact(
                            name=name,
                            phone=phone_detected,
                            messenger_id=sender_id,
                            status="human"
                        )
                        db.add(contact)
            else:
                # 🔴 IMPORTANTE: NO crear duplicado
                if contact:
                    print("✔️ Contacto ya existe (solo messenger)")
                else:
                    print("🆕 Creando contacto solo messenger")
                    contact = Contact(
                        name=name,
                        messenger_id=sender_id,
                        status="human"
                    )
                    db.add(contact)
            db.commit()
            db.refresh(contact)


            # detectar propiedad en link
            property_id = None
            match = re.search(r"property/([a-z0-9\-]+)", text.lower())
            if match:
                property_id = match.group(1)

            # crear lead
            name=get_messenger_user_name(sender_id)
            
            create_lead_service(
                db=db,
                name=name,
                phone=contact.phone if contact.phone else sender_id,
                message=text,
                property_id=property_id,
                source="messenger",
            )

            # notificar admin (panel)
            await notify_admins({
                "type": "new_lead",
                "channel": "messenger",
                "phone": contact.phone if contact.phone else sender_id,
                "message": text
            })

            # notificar admin por WhatsApp
            phone = normalize_phone(contact.phone)
            send_whatsapp_message(
                ADMIN_PHONE,
                f"""📩 Nuevo lead desde Messenger
👤 {name}
🆔 {sender_id}
💬 {text}
"""
            )
            db.close()
            return {"status": "messenger_lead"}

        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" not in value:
            return {"status": "no message event"}

        message = value["messages"][0]
        phone = message["from"]
        source = "whatsapp"

        # evitar duplicados
        message_id = message.get("id")
        if message_id in processed_messages:
            print("⚠️ Mensaje duplicado ignorado")
            return {"status": "duplicate"}
        processed_messages.add(message_id)

        # contexto
        is_new_user = phone not in user_context
        if is_new_user:
            user_context[phone] = {
                "operation": None,
                "type": None,
                "step": "menu"
            }
        ctx = user_context[phone]

        # detectar texto
        interactive = message.get("interactive", {})
        button_reply = interactive.get("button_reply", {})

        if button_reply:
            text = button_reply.get("title", "")
            text_lower = button_reply.get("id", "").lower()
        else:
            text = message.get("text", {}).get("body", "")
            text_lower = text.lower().strip()
        print("📲 WhatsApp:", text)

        # detectar property_id
        property_id = None
        match = re.search(r"ref:\s*([a-z0-9\-]+)", text_lower)
        if match:
            property_id = match.group(1)
            print("🏠 Property ID detectado:", property_id)

        if property_id:
            print("🏡 Lead directo desde web detectado")
            db = SessionLocal()
            contacts = value.get("contacts", [])
            name = contacts[0].get("profile", {}).get("name", "WhatsApp User") if contacts else "WhatsApp User"
            contact = db.query(Contact).filter(Contact.phone == phone).first()

            if not contact:
                contact = Contact(name=name, phone=phone, status="human")
                db.add(contact)
                db.commit()
                db.refresh(contact)
            else:
                contact.status = "human"
                db.commit()

            create_lead_service(
                db=db,
                name=name,
                phone=phone,
                message=text,
                property_id=property_id,
                source=source,
            )

            await notify_admins({
                "type": "new_lead",
                "phone": phone,
                "property_id": property_id,
                "message": text
            })

            phone = normalize_phone(contact.phone)
            send_whatsapp_message(
                ADMIN_PHONE,
                f"""📩 Nuevo lead desde web
👤 {name}
📱 {phone}
🏠 Propiedad ID: {property_id}
💬 {text}
"""
            )
            
            send_message(contact, "🙌 Gracias por tu consulta. Un asesor te responde por acá.")
            db.close()
            return {"status": "direct_property_lead"}

        # 💾 GUARDAR LEAD NORMAL
        db = SessionLocal()
        contacts = value.get("contacts", [])
        name = contacts[0].get("profile", {}).get("name", "WhatsApp User") if contacts else "WhatsApp User"
        create_lead_service(
            db=db,
            name=name,
            phone=phone,
            message=text,
            property_id=None,
            source=source,
        )

        contact = db.query(Contact).filter(Contact.phone == phone).first()
        # 🚫 modo humano   
        if contact and contact.status == "human":
            await notify_admins({
                "type": "new_message",
                "phone": phone,
                "message": text,
                "timestamp": time()
            })
            db.close()
            return {"status": "human"}

        # 🔄 HubSpot
        if contact and contact.hubspot_id:
            update_hubspot_contact(contact.hubspot_id, {
                "hs_lead_status": "IN_PROGRESS"
            })

        # 🤖 BOT
        step = ctx.get("step")
        # 🔹 MENÚ PRINCIPAL
        if text_lower in ["hola", "buenas", "menu", "inicio"]:
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
            send_message(contact, "📊 Podés buscar tasaciones en la barra de búsqueda o escribir *asesor*")
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
            
            if not properties:
                print("⚠️ Sin propiedades encontradas")
                # 👤 pasar a humano
                if contact:
                    contact.status = "human"
                    db.commit()
                # 📲 notificar admin
                admin_msg = f"""📩 Lead sin resultados
            👤 {contact.name if contact else 'Unknown'}
            📱 {phone}
            🔎 Búsqueda: {text_lower}
            💬 Mensaje:
            {text}
            """
                phone = normalize_phone(contact.phone)
                send_whatsapp_message(ADMIN_PHONE, admin_msg)
                # 🔔 notificar panel (websocket)
                await notify_admins({
                    "type": "no_results_lead",
                    "phone": phone,
                    "message": text
                })
                # 🤖 responder usuario
                send_message(contact, "😕 No encontramos propiedades con esas características.\n\n🙌 Te paso con un asesor para ayudarte mejor.")
                return

            for prop in properties:
                msg += f"📌 {prop.title}\n"
                msg += f"📍 {prop.price}\n"
                msg += f"\n\n🔗 Ver propiedad:\nhttps://frontend-plataforma-inmobiliaria.onrender.com/property/{prop.id}\n\n"
                msg += f" si querés más info escribí *asesor*\n"
            phone = normalize_phone(contact.phone)
            send_whatsapp_message(contact, msg)
            return

        # 🔹 ASESOR
        if "asesor" in text_lower:
            if contact:
                contact.status = "human"
                db.commit()
            send_message(contact, "🙌 Un asesor te escribe en breve.")
            await notify_admins({
                "type": "new_lead",
                "phone": phone,
                "name": contact.name if contact else "Unknown"
            })

            phone = normalize_phone(contact.phone)
            send_whatsapp_message(
            ADMIN_PHONE,
            f"""📩 Nuevo lead (solicitó asesor)
            👤 {contact.name if contact else 'Unknown'}
            📱 {phone}
            💬 {text}
            """
            )
            return

        # 🟢 MENÚ PRINCIPAL   
        if contact and contact.status != "human":
            if ctx.get("step") == "results" and text_lower not in ["menu", "inicio"]:
                contact.status = "human"
                db.commit()
                send_message(contact, "🙌 Te paso con un asesor para ayudarte mejor.")
                await notify_admins({
                    "type": "new_lead",
                    "phone": phone,
                    "name": contact.name if contact else "Unknown"
                })
                return {"status": "escalated to human"}

        # 🟡 FALLBACK
        send_main_menu(phone)
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
































