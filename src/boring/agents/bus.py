import asyncio
import logging
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from boring.agents.protocol import ChatMessage

logger = logging.getLogger(__name__)


class AgentMessage(BaseModel):
    """
    Enhanced message for inter-agent communication.
    """

    id: str = Field(default_factory=lambda: f"msg_{int(time.time() * 1000)}")
    sender: str
    recipient: str | None = None  # None means broadcast
    topic: str = "general"
    payload: str | dict[str, Any] | ChatMessage
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)


class SharedMemory:
    """
    Shared session-wide memory for all agents.
    """

    def __init__(self):
        self._storage: dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._history: list[dict[str, Any]] = []

    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return self._storage.get(key, default)

    async def set(self, key: str, value: Any, metadata: dict[str, Any] | None = None):
        async with self._lock:
            self._storage[key] = value
            self._history.append(
                {
                    "action": "set",
                    "key": key,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": metadata or {},
                }
            )
            logger.debug(f"SharedMemory: set {key}")

    async def delete(self, key: str):
        async with self._lock:
            if key in self._storage:
                del self._storage[key]
                logger.debug(f"SharedMemory: deleted {key}")

    async def clear(self):
        async with self._lock:
            self._storage.clear()
            logger.info("SharedMemory cleared")

    def get_all(self) -> dict[str, Any]:
        return self._storage.copy()


class AgentBus:
    """
    Asynchronous Communication Bus for agents.
    Supports Publish/Subscribe and Direct Messaging.
    """

    def __init__(self):
        self.subscribers: dict[str, list[Callable]] = {}
        self.queues: dict[str, asyncio.Queue] = {}
        self.memory = SharedMemory()
        self._lock = asyncio.Lock()

    async def register_agent(self, agent_name: str):
        """Register an agent to receive direct messages via a queue."""
        async with self._lock:
            if agent_name not in self.queues:
                self.queues[agent_name] = asyncio.Queue()
                logger.info(f"Agent '{agent_name}' registered to Bus.")

    async def subscribe(self, topic: str, callback: Callable):
        """Subscribe a callback to a topic."""
        async with self._lock:
            if topic not in self.subscribers:
                self.subscribers[topic] = []
            self.subscribers[topic].append(callback)
            logger.debug(f"Subscribed to topic '{topic}'")

    async def publish(self, message: AgentMessage):
        """Publish a message to a topic (Broadcast to subscribers)."""
        topic = message.topic
        async with self._lock:
            if topic in self.subscribers:
                tasks = [asyncio.create_task(cb(message)) for cb in self.subscribers[topic]]
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

        logger.debug(f"Published message to topic '{topic}': {message.id}")

    async def send_direct(self, message: AgentMessage):
        """Send a direct message to a specific agent's queue."""
        if not message.recipient:
            await self.publish(message)
            return

        async with self._lock:
            if message.recipient in self.queues:
                await self.queues[message.recipient].put(message)
                logger.debug(f"Sent direct message to {message.recipient}: {message.id}")
            else:
                logger.warning(f"Recipient {message.recipient} not registered on Bus.")

    async def receive(self, agent_name: str, timeout: float | None = None) -> AgentMessage | None:
        """Receive a message from an agent's queue."""
        queue = self.queues.get(agent_name)
        if not queue:
            return None

        try:
            if timeout:
                return await asyncio.wait_for(queue.get(), timeout=timeout)
            return await queue.get()
        except asyncio.TimeoutError:
            return None


# Global Event Bus Instance
_global_bus: AgentBus | None = None


def get_agent_bus() -> AgentBus:
    global _global_bus
    if _global_bus is None:
        _global_bus = AgentBus()
    return _global_bus
