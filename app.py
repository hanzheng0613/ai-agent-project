from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mangum import Mangum
from invoke_agent import ask_agent

app = FastAPI(title="Business Analyst Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    question: str
    session_id: str | None = None

@app.post("/ask")
def ask(query: Query):
    answer, session_id, tool_calls = ask_agent(query.question, query.session_id)
    return {
        "answer": answer,
        "session_id": session_id,
        "tool_calls": tool_calls
    }

@app.get("/health")
def health():
    return {"status": "ok"}

handler = Mangum(app)
