from fastapi import FastAPI
from app.routers import analisys, properties, leads, dashboard, whatsapp, idecor, security
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect
import json

app = FastAPI(title="Real Estate Platform API")

active_connections = []

@app.websocket("/ws/admin")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)


async def notify_admins(event: dict):
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(event))
        except:
            disconnected.append(connection)
    for conn in disconnected:
        active_connections.remove(conn)

origins = [
    "http://localhost:5173",
    "https://frontend-plataforma-inmobiliaria.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(properties.router)
app.include_router(leads.router)
app.include_router(whatsapp.router)
app.include_router(dashboard.router)
app.include_router(idecor.router)
app.include_router(analisys.router)
app.include_router(security.router)

@app.get("/")
def root():
    return {"message": "API running"}

# uvicorn app.main:app --reload