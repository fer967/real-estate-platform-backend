from fastapi import APIRouter, Request
import os
from dotenv import load_dotenv
from app.services.lead_service import create_lead_service
from app.core import SessionLocal


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
        message = value["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]
        print("Cliente:", phone)
        print("Mensaje:", text)
        db = SessionLocal()
        create_lead_service(
            db=db,
            name="WhatsApp User",
            phone=phone,
            message=text
        )
    except Exception as e:
        print("Error parsing message:", e)
    return {"status": "received"}


# @router.post("/webhook")
# async def receive_message(request: Request):
#     body = await request.json()
#     try:
#         entry = body["entry"][0]
#         changes = entry["changes"][0]
#         value = changes["value"]
#         message = value["messages"][0]
#         phone = message["from"]
#         text = message["text"]["body"]
#         print("Cliente:", phone)
#         print("Mensaje:", text)
#     except Exception as e:
#         print("Error parsing message:", e)
#     return {"status": "received"}



# @router.post("/webhook")
# async def receive_message(request: Request):
#     body = await request.json()
#     print("WhatsApp message received:")
#     print(body)
#     return {"status": "received"}