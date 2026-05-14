"""FastAPI main application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.rag.routers import router as rag_router
from src.rag.session_routers import router as rag_session_router
from src.rag.document_routers import router as rag_document_router
from src.agent.routers import router as agent_router
from src.db.mysql import init_database, MySQLPool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🚀 Starting AI RAG & Agent Service...")
    try:
        await init_database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}")
        print("   Service will continue without database persistence")

    yield

    # Shutdown
    print("🛑 Shutting down...")
    await MySQLPool.close_pool()
    print("✅ Database connections closed")


app = FastAPI(
    title=settings.app_name,
    description="RAG and Agent API Service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rag_router)
app.include_router(rag_session_router)
app.include_router(rag_document_router)
app.include_router(agent_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)