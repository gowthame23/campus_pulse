import asyncio
from typing import Dict, Set

from fastapi import WebSocket

from utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections per user and role for real-time notification broadcasting."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = (
            {}
        )  # target (user_id or role_lower) -> set(WebSocket)
        self._loop = None  # server event loop, captured at startup via set_loop()

    def set_loop(self, loop):
        """Registers the server's running event loop. Must be called once at
        app startup (see api/main.py lifespan). FastAPI runs sync `def`
        route handlers in a threadpool, so push_sync() is usually invoked
        from a thread with no event loop of its own — without this, it has
        nothing to schedule the broadcast onto and the push is dropped."""
        self._loop = loop

    def is_online(self, target_id: str) -> bool:
        key = (target_id or "").lower()
        return key in self.active_connections and len(self.active_connections[key]) > 0

    async def connect(self, websocket: WebSocket, target_id: str):
        await websocket.accept()
        key = target_id.lower()
        if key not in self.active_connections:
            self.active_connections[key] = set()
        self.active_connections[key].add(websocket)
        logger.info(f"WebSocket connected: {key}")

    def disconnect(self, websocket: WebSocket, target_id: str):
        key = target_id.lower()
        if key in self.active_connections:
            self.active_connections[key].discard(websocket)
            if not self.active_connections[key]:
                del self.active_connections[key]
        logger.info(f"WebSocket disconnected: {key}")

    async def broadcast_to_target(self, target_id: str, message: dict):
        key = target_id.lower()
        if key in self.active_connections:
            to_remove = set()
            for connection in self.active_connections[key]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send WS message: {e}")
                    to_remove.add(connection)
            for dead in to_remove:
                self.active_connections[key].discard(dead)

    def push_sync(self, target_id: str, message: dict):
        """Thread-safe synchronous push to a specific target_id (user_id or role)."""
        loop = self._loop
        if loop is None or loop.is_closed():
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = None

        if loop is None or loop.is_closed():
            logger.debug(f"WS push to '{target_id}' deferred: no active event loop running.")
            return

        try:
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.broadcast_to_target(target_id, message), loop
                )
            else:
                loop.run_until_complete(self.broadcast_to_target(target_id, message))
        except Exception as err:
            logger.warning(f"WS push to '{target_id}' failed: {err}")

    async def broadcast_all(self, message: dict):
        """Broadcasts a message to all currently connected WebSocket clients across all roles."""
        all_conns = set()
        for conns in self.active_connections.values():
            all_conns.update(conns)
        to_remove = set()
        for connection in all_conns:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send WS broadcast: {e}")
                to_remove.add(connection)
        for dead in to_remove:
            for conns in self.active_connections.values():
                conns.discard(dead)

    def broadcast_sync(self, message: dict):
        """Thread-safe synchronous push to all connected WebSocket clients."""
        loop = self._loop
        if loop is None or loop.is_closed():
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = None

        if loop is None or loop.is_closed():
            return

        try:
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast_all(message), loop)
            else:
                loop.run_until_complete(self.broadcast_all(message))
        except Exception as err:
            logger.warning(f"WS broadcast_sync failed: {err}")

manager = ConnectionManager()
