
import os
import secrets

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    HTTPException,
    Security
)
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from core.timing_and_timetable import Period
import secrets
import os

from fastapi import HTTPException
from pydantic import BaseModel


app = FastAPI()

# -----------------------------
# REGISTRATION AND AUTHORIZATION
# -----------------------------

REGISTRATION_TOKEN = os.environ.get("ATTENDANCE_REGISTRATION_TOKEN")

if not REGISTRATION_TOKEN:
    raise RuntimeError("Registration token not configured")

# Store authorized API keys
authorized_keys = {}


class RegistrationRequest(BaseModel):
    registration_token: str
    device_name: str


@app.post("/register")
async def register_client(request: RegistrationRequest):
    if not secrets.compare_digest(
        request.registration_token,
        REGISTRATION_TOKEN
    ):
        raise HTTPException(
            status_code=403,
            detail="Registration not authorized"
        )

    api_key = secrets.token_urlsafe(32)

    authorized_keys[api_key] = {
        "device_name": request.device_name,
        "active": True
    }

    return {
        "message": "Registration successful",
        "api_key": api_key
    }



api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)


# -----------------------------
# DATABASE
# -----------------------------

attendance_database = {}


# Connected WebSocket clients
connected_clients = set()


# -----------------------------
# AUTHENTICATION
# -----------------------------

async def verify_api_key(
    api_key: str = Security(api_key_header)
):
    client = authorized_keys.get(api_key)

    if not client or not client["active"]:
        raise HTTPException(
            status_code=401,
            detail="Invalid or revoked API key"
        )

    return api_key

# -----------------------------
# CONNECTION MANAGER
# -----------------------------

async def broadcast(message: dict):

    disconnected = set()

    for client in connected_clients.copy():
        try:
            await client.send_json(message)

        except Exception:
            disconnected.add(client)

    connected_clients.difference_update(disconnected)


# -----------------------------
# DATA MODEL
# -----------------------------

class AttendanceRecord(BaseModel):
    staffID: str
    period: Period


# -----------------------------
# REST API ENDPOINTS
# -----------------------------

@app.get(
    "/attendance",
    dependencies=[Depends(verify_api_key)]
)
async def get_records():
    return attendance_database

@app.post(
    "/attendance/{staff_id}",
    dependencies=[Depends(verify_api_key)]
)
async def add_attendance(staff_id: str, record: AttendanceRecord):

    attendance_database[staff_id] = record.model_dump(mode="json")

    await broadcast({
        "event": "Attendance",
        "id": staff_id,
        "data": attendance_database[staff_id]
    })

    return {"message": "Attendance Record created successfully"}

# -----------------------------
# WEBSOCKET ENDPOINT
# -----------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    api_key = websocket.headers.get("X-API-Key")
    
    client = authorized_keys.get(api_key)
    
    if not client or not client["active"]:
        await websocket.close(code=1008)
        return
    
    await websocket.accept()
    connected_clients.add(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        connected_clients.discard(websocket)
