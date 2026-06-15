from __future__ import annotations
import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime


class ConnectionManager:
    def __init__(self):
        # visitor_id → WebSocket
        self._visitors: Dict[str, WebSocket] = {}
        # agent_id → WebSocket
        self._agents: Dict[int, WebSocket] = {}
        # conversation_id → set of agent_ids watching it
        self._watching: Dict[int, Set[int]] = {}

    # ── Visitor ──────────────────────────────────────────────────────────────

    async def connect_visitor(self, visitor_id: str, ws: WebSocket):
        await ws.accept()
        self._visitors[visitor_id] = ws

    def disconnect_visitor(self, visitor_id: str):
        self._visitors.pop(visitor_id, None)

    async def send_to_visitor(self, visitor_id: str, data: dict):
        ws = self._visitors.get(visitor_id)
        if ws:
            try:
                await ws.send_text(json.dumps(data, ensure_ascii=False, default=str))
            except Exception:
                self.disconnect_visitor(visitor_id)

    # ── Agent ────────────────────────────────────────────────────────────────

    async def connect_agent(self, agent_id: int, ws: WebSocket):
        await ws.accept()
        self._agents[agent_id] = ws

    def disconnect_agent(self, agent_id: int):
        self._agents.pop(agent_id, None)
        for watchers in self._watching.values():
            watchers.discard(agent_id)

    async def send_to_agent(self, agent_id: int, data: dict):
        ws = self._agents.get(agent_id)
        if ws:
            try:
                await ws.send_text(json.dumps(data, ensure_ascii=False, default=str))
            except Exception:
                self.disconnect_agent(agent_id)

    async def broadcast_to_agents(self, data: dict):
        dead = []
        for agent_id, ws in list(self._agents.items()):
            try:
                await ws.send_text(json.dumps(data, ensure_ascii=False, default=str))
            except Exception:
                dead.append(agent_id)
        for aid in dead:
            self.disconnect_agent(aid)

    # ── Watch / Unwatch ──────────────────────────────────────────────────────

    def watch(self, agent_id: int, conversation_id: int):
        self._watching.setdefault(conversation_id, set()).add(agent_id)

    def unwatch(self, agent_id: int, conversation_id: int):
        if conversation_id in self._watching:
            self._watching[conversation_id].discard(agent_id)

    async def broadcast_to_watchers(self, conversation_id: int, data: dict):
        for agent_id in list(self._watching.get(conversation_id, set())):
            await self.send_to_agent(agent_id, data)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def online_agents(self) -> list[int]:
        return list(self._agents.keys())

    def visitor_online(self, visitor_id: str) -> bool:
        return visitor_id in self._visitors

    def agent_count(self) -> int:
        return len(self._agents)

    def visitor_count(self) -> int:
        return len(self._visitors)


manager = ConnectionManager()
