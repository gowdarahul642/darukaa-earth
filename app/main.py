from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.pipeline import PipelineOrchestrator
from app.api.schemas import ChatRequest, ChatResponse, HealthResponse
from app.config import get_settings
from app.db.session import get_db, init_db
from app.memory.manager import ConversationMemoryManager

settings = get_settings()
init_db()

app = FastAPI(
    title=settings.app_name,
    description="DARUKAA.EARTH - Scientific Environmental Intelligence API Engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        environment=settings.environment,
    )


@app.post("/api/v1/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        orchestrator = PipelineOrchestrator(db)
        return orchestrator.process_message(
            message=request.message, conversation_id=request.conversation_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/conversations/{conversation_id}/state")
def get_conversation_state(conversation_id: str, db: Session = Depends(get_db)):
    memory = ConversationMemoryManager(db)
    state = memory.get_profile(conversation_id)
    evidence = memory.get_evidence(conversation_id)
    return {"conversation_id": conversation_id, "state": state, "evidence": evidence}