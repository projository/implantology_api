# app/routes/socket_routes.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.socket_manager import manager

router = APIRouter()


@router.websocket("/ws/chat/{chat_id}")
async def websocket_chat(websocket: WebSocket, chat_id: str):

    await manager.connect_chat(chat_id, websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect_chat(chat_id, websocket)


@router.websocket("/ws/admin")
async def websocket_admin(websocket: WebSocket):

    await manager.connect_admin(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect_admin(websocket)