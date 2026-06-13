from fastapi import FastAPI
from pydantic import BaseModel
from invoke_agent import ask_agent

app = FastAPI(title="Business Analyst Agent API")

class Query(BaseModel):
    question: str
    session_id: str | None = None

@app.post("/ask")
def ask(query: Query):
    answer, session_id = ask_agent(query.question, query.session_id)
    return {"answer": answer, "session_id": session_id}

@app.get("/health")
def health():
    return {"status": "ok"}
