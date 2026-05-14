"""Agent module Pydantic schemas."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """Tool definition for agent."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Tool parameters schema")


class AgentCreateRequest(BaseModel):
    """Request to create an agent."""
    name: str = Field(..., description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    tools: List[ToolDefinition] = Field(default_factory=list, description="Agent tools")
    max_iterations: Optional[int] = Field(10, description="Max iterations")


class AgentRunRequest(BaseModel):
    """Request to run an agent."""
    input: str = Field(..., description="Input for agent")
    collection: Optional[str] = Field(None, description="Optional RAG collection for context")


class AgentChatRequest(BaseModel):
    """Request to chat with an agent."""
    message: str = Field(..., description="Message to send")
    collection: Optional[str] = Field(None, description="Optional RAG collection for context")


class HumanFeedbackRequest(BaseModel):
    """Request for human feedback."""
    feedback: str = Field(..., description="Human feedback")


class AgentState(BaseModel):
    """Agent state."""
    agent_id: str
    name: str
    status: str
    current_step: Optional[str] = None
    iterations: int = 0


class AgentResponse(BaseModel):
    """Agent response."""
    agent_id: str
    status: str
    message: Optional[str] = None
    result: Optional[Any] = None


class Message(BaseModel):
    """Chat message."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[str] = None


class AgentHistoryResponse(BaseModel):
    """Agent history response."""
    agent_id: str
    messages: List[Message]


class FileUploadResponse(BaseModel):
    """Response after file upload."""
    file_id: str
    filename: str
    file_type: str
    status: str


class ProcessRequest(BaseModel):
    """Request to process a document."""
    file_id: str
    requirements: str


class ProcessResponse(BaseModel):
    """Response from document processing."""
    status: str
    message: str
    output_file: Optional[str] = None
    data_content: Optional[str] = None