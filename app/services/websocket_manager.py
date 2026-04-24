import json

active_connections = []

async def connect(websocket):
    await websocket.accept()
    active_connections.append(websocket)

def disconnect(websocket):
    if websocket in active_connections:
        active_connections.remove(websocket)

async def notify_admins(event: dict):
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(event))
        except:
            disconnected.append(connection)
    for conn in disconnected:
        disconnect(conn)