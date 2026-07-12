from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from pipeline import run
import httpx

class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    agent:str | None = None
    bielik_model: str |None = None

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
def chat(request: ChatRequest):
    try:
        wynik = run(request.message, agent=request.agent, bielik_model=request.bielik_model)
        return wynik
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Brak odpowiedzi ze strony Ollamy")
    except httpx.ReadTimeout:
        raise HTTPException(status_code=504, detail='Zbyt długi czas generowania odpowiedzi')
