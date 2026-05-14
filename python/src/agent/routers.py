"""Agent API routers."""

from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse

from src.agent.service import agent_service
from src.agent.schemas import (
    AgentCreateRequest,
    AgentRunRequest,
    AgentChatRequest,
    HumanFeedbackRequest,
    AgentResponse,
    AgentState,
    AgentHistoryResponse,
    FileUploadResponse,
    ProcessRequest,
    ProcessResponse,
)

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/create")
async def create_agent(request: AgentCreateRequest) -> dict:
    """Create a new agent."""
    try:
        result = agent_service.create_agent(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_agents() -> List[dict]:
    """List all agents."""
    try:
        return agent_service.list_agents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str) -> dict:
    """Delete an agent."""
    try:
        return agent_service.delete_agent(agent_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/run")
async def run_agent(agent_id: str, request: AgentRunRequest) -> AgentResponse:
    """Run an agent with input."""
    try:
        return agent_service.run_agent(agent_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/chat")
async def chat(agent_id: str, request: AgentChatRequest) -> AgentResponse:
    """Chat with an agent."""
    try:
        return agent_service.chat(agent_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/state")
async def get_state(agent_id: str) -> AgentState:
    """Get agent state."""
    try:
        return agent_service.get_state(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/human-feedback")
async def human_feedback(agent_id: str, request: HumanFeedbackRequest) -> dict:
    """Provide human feedback to an agent."""
    try:
        return agent_service.human_feedback(agent_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/history")
async def get_history(agent_id: str) -> AgentHistoryResponse:
    """Get agent conversation history."""
    try:
        return agent_service.get_history(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/conversations")
async def get_conversations(agent_id: str, limit: int = 50, offset: int = 0) -> dict:
    """Get agent conversation history from database (paginated)."""
    try:
        from src.memory.persistence import persistence
        conversations = await persistence.get_conversations(agent_id, limit, offset)
        count = await persistence.get_conversation_count(agent_id)
        return {"conversations": conversations, "total": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/memory/search")
async def search_memory(agent_id: str, query: str, k: int = 5, memory_type: str = None) -> dict:
    """Search long-term memories for an agent."""
    try:
        from src.memory.persistence import persistence
        results = await persistence.search_long_term_memory(agent_id, query, k, memory_type)
        return {"results": results, "query": query}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}/memory")
async def clear_memory(agent_id: str) -> dict:
    """Clear all long-term memories for an agent."""
    try:
        from src.memory.persistence import persistence
        await persistence.clear_long_term_memory(agent_id)
        return {"status": "success", "agent_id": agent_id, "message": "Long-term memory cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/file-upload")
async def upload_file(
    file: UploadFile = File(...),
    requirements: str = Form("")
) -> FileUploadResponse:
    """Upload a Word or Excel file for processing."""
    try:
        from src.agent.file_service import file_service

        contents = await file.read()
        file_id, path, file_type = await file_service.save_upload(contents, file.filename)

        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_type=file_type,
            status="uploaded"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_document(request: ProcessRequest) -> ProcessResponse:
    """Process an uploaded document with requirements and return analysis results."""
    import asyncio
    from functools import partial

    try:
        from src.agent.file_service import file_service
        from src.agent.doc_agent import DocumentAgent
        from src.agent.tools import get_document_tools
        from pathlib import Path

        file_path = await file_service.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(status_code=404, detail="File not found")

        ext = Path(file_path).suffix.lower()
        file_type = file_service._get_file_type(ext)

        tools = get_document_tools()
        agent = DocumentAgent(
            file_id=request.file_id,
            file_path=file_path,
            file_type=file_type,
            requirements=request.requirements
        )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, partial(agent.run, tools))

        # Handle needs_confirmation status
        if result.get("needs_confirmation"):
            return ProcessResponse(
                status="needs_confirmation",
                message=result.get("message", "结果可能不完整"),
                output_file=None,
                data_content=result.get("data_content", "")
            )

        return ProcessResponse(
            status="success",
            message=result.get("data_content", "分析完成"),
            output_file=None,
            data_content=result.get("data_content", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/file/{file_id}")
async def delete_file(file_id: str) -> dict:
    """Delete an uploaded file by file_id."""
    try:
        from src.agent.file_service import file_service
        await file_service.cleanup_file(file_id)
        return {"status": "success", "file_id": file_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_file(filename: str):
    """Download a generated output file."""
    from src.agent.file_service import OUTPUT_DIR
    from fastapi.responses import FileResponse

    output_path = OUTPUT_DIR / filename
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(output_path, filename=filename)


@router.get("/chart/{image_id}")
async def get_chart_image(image_id: str):
    """Get a generated chart image by image_id."""
    from src.agent.file_service import OUTPUT_DIR
    from fastapi.responses import FileResponse

    chart_path = OUTPUT_DIR / f"{image_id}_chart.png"
    print(f"[get_chart_image] Requested image_id: {image_id}, path: {chart_path}, exists: {chart_path.exists()}")
    if not chart_path.exists():
        raise HTTPException(status_code=404, detail="Chart not found")
    return FileResponse(chart_path, media_type="image/png")


@router.get("/graph")
async def get_agent_graph():
    """Get the document processing agent graph structure as mermaid diagram."""
    try:
        mermaid = """flowchart TD
    Start([开始]) --> Read["Step 1: 读取文件"]
    Read --> Analyze["Step 2: LLM分析"]
    Analyze --> Chart{"Step 3: 生成图表?"}
    Chart -->|"是"| GenChart[generate_chart]
    Chart -->|"否"| Validate
    GenChart --> Validate["Step 4: 验证结果"]
    Validate -->|"合格"| Format["Step 5: 整理输出"]
    Validate -->|"不合格"| Confirm{询问用户}
    Confirm -->|"继续"| Retry[重新分析]
    Confirm -->|"结束"| End[结束]
    Retry --> Analyze
    Format --> End([结束])

    subgraph 工具列表
        ReadExcel["read_excel_file"]
        ReadWord["read_word_file"]
        GenChart["generate_chart"]
    end"""

        return {
            "mermaid": mermaid,
            "nodes": [
                {"id": "start", "label": "开始", "type": "start"},
                {"id": "upload", "label": "上传文件", "type": "process"},
                {"id": "read", "label": "Step 1: 读取文件", "type": "process"},
                {"id": "analyze", "label": "Step 2: LLM分析", "type": "process"},
                {"id": "chart", "label": "Step 3: 生成图表?", "type": "decision"},
                {"id": "GenChart", "label": "生成图表", "type": "tool"},
                {"id": "validate", "label": "Step 4: 验证结果", "type": "process"},
                {"id": "format", "label": "Step 5: 整理输出", "type": "process"},
                {"id": "confirm", "label": "询问用户", "type": "decision"},
                {"id": "retry", "label": "重新分析", "type": "process"},
                {"id": "end", "label": "结束", "type": "end"},
                # {"id": "end_fail", "label": "结束(不完整)", "type": "end"},
            ],
            "edges": [
                {"from": "start", "to": "upload"},
                {"from": "upload", "to": "read"},
                {"from": "read", "to": "analyze"},
                {"from": "analyze", "to": "chart"},
                {"from": "chart", "to": "gen_chart", "label": "是"},
                {"from": "chart", "to": "validate", "label": "否"},
                {"from": "gen_chart", "to": "validate"},
                {"from": "validate", "to": "format", "label": "合格"},
                {"from": "validate", "to": "confirm", "label": "不合格"},
                {"from": "confirm", "to": "retry", "label": "继续"},
                {"from": "confirm", "to": "end_fail", "label": "结束"},
                {"from": "retry", "to": "analyze"},
                {"from": "format", "to": "end"},
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))