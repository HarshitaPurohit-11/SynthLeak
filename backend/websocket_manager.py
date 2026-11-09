"""
SynthLeak Real-Time WebSocket Connection & Broadcasting Manager.
Handles multi-client connections, heartbeats, and frame distribution without
allowing one dropped client to impact others.
"""

import asyncio
import logging
from typing import Set, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("synthleak.websocket")


class ConnectionManager:
    """Manages active WebSocket connections to the real-time telemetry stream."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept incoming client handshake and register connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Unregister closed or disconnected client."""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast JSON payload to all active clients simultaneously.
        Dead connections are detected and purged gracefully without blocking other clients.
        """
        if not self.active_connections:
            return

        async with self._lock:
            clients = list(self.active_connections)

        dead_clients = []
        for client in clients:
            try:
                await client.send_json(message)
            except Exception:
                dead_clients.append(client)

        if dead_clients:
            async with self._lock:
                for dead in dead_clients:
                    self.active_connections.discard(dead)
            logger.info(f"Purged {len(dead_clients)} dead WebSocket connections.")

    @property
    def client_count(self) -> int:
        """Number of active subscribed clients."""
        return len(self.active_connections)


ws_manager = ConnectionManager()

