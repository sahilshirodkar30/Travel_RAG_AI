
from fastapi import Depends,FastAPI,Header,HTTPException, status
from pydantic import BaseModel,Field
import logfire
from app.agent.graph import handle_question
from app.observability import setup_observability

app = FastAPI(title="Goa Travel Guide API",version="1.0.0")

@app.on_event("startup")
def _startup() -> None:
    setup_observability()

class AskRequest(BaseModel):
    question:str = Field(...,min_length=1,max_length=1000)

class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    blocked: bool

def get_user_id(x_user_id: str = Header(..., description="Caller identity, e.g. the user's email")) -> str:
    """Identify the caller. Replace this with real token verification (see notes below)."""
    if not x_user_id.strip():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing user id")
    return x_user_id.strip().lower()

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

def get_thread_id(x_thread_id: str = Header(..., description="Conversation id, one per chat")) -> str:
    return x_thread_id.strip()

@logfire.log_function("ask questions")
@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest, user_id: str = Depends(get_user_id),
        thread_id: str = Depends(get_thread_id)) -> AskResponse:
    result = handle_question(user_id, body.question, thread_id)
    return AskResponse(**result)