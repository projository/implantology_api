# app/core/socket_manager.py

from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:

    def __init__(self):
        self.chat_connections: Dict[str, List[WebSocket]] = {}
        self.admin_connections: List[WebSocket] = []

    async def connect_chat(self, chat_id: str, websocket: WebSocket):
        await websocket.accept()

        if chat_id not in self.chat_connections:
            self.chat_connections[chat_id] = []

        self.chat_connections[chat_id].append(websocket)

    async def connect_admin(self, websocket: WebSocket):
        await websocket.accept()
        self.admin_connections.append(websocket)

    def disconnect_chat(self, chat_id: str, websocket: WebSocket):
        if chat_id in self.chat_connections:
            self.chat_connections[chat_id].remove(websocket)

    def disconnect_admin(self, websocket: WebSocket):
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)

    async def broadcast_chat(self, chat_id: str, message: dict):

        if chat_id not in self.chat_connections:
            return

        for connection in self.chat_connections[chat_id]:
            await connection.send_json(message)

    async def broadcast_admin(self, message: dict):

        for connection in self.admin_connections:
            await connection.send_json(message)


manager = ConnectionManager()