"""Agent service layer with memory integration."""

from typing import Dict, Optional, List
import uuid
from datetime import datetime

from src.agent.graph import AgentGraph, AgentState
from src.agent.schemas import (
    AgentCreateRequest,
    AgentRunRequest,
    AgentChatRequest,
    HumanFeedbackRequest,
    AgentResponse,
    AgentState as AgentStateSchema,
    Message,
    AgentHistoryResponse,
)
from src.config import settings
from src.memory.persistence import persistence
from src.memory.short_term import memory_manager


class AgentService:
    """Service for managing agents with three-tier memory."""

    def __init__(self):
        self._agents: Dict[str, AgentGraph] = {}

    def create_agent(self, request: AgentCreateRequest) -> dict:
        """
        Create a new agent with permanent storage.

        Args:
            request: Agent creation request

        Returns:
            Agent info dict
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._create_agent_async(request))

    async def _create_agent_async(self, request: AgentCreateRequest) -> dict:
        """Async version of create_agent."""
        agent_id = str(uuid.uuid4())

        tools = []
        for tool_def in request.tools:
            tools.append({
                "name": tool_def.name,
                "description": tool_def.description,
                "parameters": tool_def.parameters,
            })

        # Create agent graph
        agent = AgentGraph(
            agent_id=agent_id,
            name=request.name,
            tools=tools,
        )
        self._agents[agent_id] = agent

        # Persist to MySQL
        await persistence.create_agent(
            name=request.name,
            description=request.description,
            tools=tools,
            max_iterations=request.max_iterations or settings.max_iterations,
        )

        # Initialize short-term memory
        short_mem = memory_manager.get_or_create(agent_id)
        await persistence.load_short_term_memory(agent_id, settings.short_term_max_messages)

        return {
            "agent_id": agent_id,
            "name": request.name,
            "status": "ready",
        }

    async def run_agent_async(self, agent_id: str, request: AgentRunRequest) -> AgentResponse:
        """Run an agent with memory integration (async)."""
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self._agents[agent_id]

        # Get short-term memory
        short_mem = memory_manager.get_or_create(agent_id)

        # Add user message to short-term memory
        short_mem.add_message("user", request.input)

        # Check if should persist short-term memory
        if short_mem.should_persist():
            await persistence.persist_short_term_memory(agent_id)

        # Get conversation context from short-term memory
        messages = short_mem.get_messages()

        # Build input with context
        input_with_context = request.input
        if messages:
            context = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            input_with_context = f"上下文：\n{context}\n\n当前问题：{request.input}"

        # Run agent
        result = agent.run(input_with_context)

        # Extract response
        response_content = result.get("result", "")
        if isinstance(response_content, list) and len(response_content) > 0:
            response_content = response_content[-1].content if hasattr(response_content[-1], 'content') else str(response_content[-1])

        # Add assistant response to short-term memory
        short_mem.add_message("assistant", response_content)

        # Periodically summarize and store long-term memory
        if len(messages) >= settings.short_term_max_messages:
            summary = await persistence.summarize_and_store(agent_id, messages)
            print(f"📝 Conversation summary: {summary[:50]}...")

        return AgentResponse(
            agent_id=agent_id,
            status="success",
            message=response_content,
            result=result,
        )

    def run_agent(self, agent_id: str, request: AgentRunRequest) -> AgentResponse:
        """Run an agent (sync wrapper)."""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.run_agent_async(agent_id, request))

    async def chat_async(self, agent_id: str, request: AgentChatRequest) -> AgentResponse:
        """Chat with an agent (async)."""
        return await self.run_agent_async(
            agent_id,
            AgentRunRequest(input=request.message, collection=request.collection),
        )

    def chat(self, agent_id: str, request: AgentChatRequest) -> AgentResponse:
        """Chat with an agent."""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.chat_async(agent_id, request))

    async def get_state_async(self, agent_id: str) -> AgentStateSchema:
        """Get agent state (async)."""
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self._agents[agent_id]
        state = agent.get_state()

        return AgentStateSchema(
            agent_id=agent_id,
            name=state["name"],
            status=state["status"],
            iterations=state.get("iterations", 0),
        )

    def get_state(self, agent_id: str) -> AgentStateSchema:
        """Get agent state."""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.get_state_async(agent_id))

    async def human_feedback_async(self, agent_id: str, request: HumanFeedbackRequest) -> dict:
        """Provide human feedback to an agent (async)."""
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        # Add feedback to short-term memory
        short_mem = memory_manager.get_or_create(agent_id)
        short_mem.add_message("human", request.feedback)

        return {
            "status": "received",
            "feedback": request.feedback,
        }

    def human_feedback(self, agent_id: str, request: HumanFeedbackRequest) -> dict:
        """Provide human feedback to an agent."""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.human_feedback_async(agent_id, request))

    async def get_history_async(self, agent_id: str) -> AgentHistoryResponse:
        """Get agent conversation history from both memory layers (async)."""
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        # Get short-term memory
        short_mem = memory_manager.get_or_create(agent_id)
        short_messages = short_mem.get_messages()

        # Get persistent history
        db_messages = await persistence.get_conversations(agent_id, limit=100)

        # Combine (preferring short-term for recent messages)
        all_messages = []
        seen_ids = set()
        for msg in db_messages:
            all_messages.append(Message(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg.get("created_at", "").isoformat() if msg.get("created_at") else None,
            ))
            seen_ids.add(msg["id"])

        for msg in short_messages:
            all_messages.append(Message(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg.get("timestamp"),
            ))

        return AgentHistoryResponse(
            agent_id=agent_id,
            messages=all_messages,
        )

    def get_history(self, agent_id: str) -> AgentHistoryResponse:
        """Get agent conversation history."""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.get_history_async(agent_id))

    async def list_agents_async(self) -> List[dict]:
        """List all agents from persistent storage (async)."""
        agents = await persistence.get_all_agents()
        return [
            {
                "agent_id": agent["id"],
                "name": agent["name"],
                "status": agent["status"],
            }
            for agent in agents
        ]

    def list_agents(self) -> List[dict]:
        """List all agents."""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.list_agents_async())

    async def delete_agent_async(self, agent_id: str) -> dict:
        """Delete an agent and all associated data (async)."""
        if agent_id in self._agents:
            del self._agents[agent_id]

        await persistence.delete_agent(agent_id)

        return {"status": "success", "agent_id": agent_id}

    def delete_agent(self, agent_id: str) -> dict:
        """Delete an agent."""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.delete_agent_async(agent_id))

    async def load_agent_async(self, agent_id: str) -> bool:
        """Load an agent from persistent storage (async)."""
        agent_data = await persistence.get_agent(agent_id)
        if not agent_data:
            return False

        agent = AgentGraph(
            agent_id=agent_id,
            name=agent_data["name"],
            tools=agent_data.get("tools", []),
        )
        self._agents[agent_id] = agent

        # Load short-term memory
        await persistence.load_short_term_memory(agent_id)

        return True

    def load_agent(self, agent_id: str) -> bool:
        """Load an agent from persistent storage."""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.load_agent_async(agent_id))


# Global service instance
agent_service = AgentService()