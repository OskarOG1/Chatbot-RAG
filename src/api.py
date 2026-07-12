from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from pipeline import run
import httpx

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
   agent: str
   answer: str
   main_source: str | None
   additional_sources: list[str]

app = FastAPI()

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/chat', response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        wynik = run(req.message)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Brak odpowiedzi ze strony Ollamy"
        )
    return wynik