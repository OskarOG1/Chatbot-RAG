from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from pipeline import run
import httpx

class Wiadomosc(BaseModel):
   role: str
   content: str

class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    agent:str | None = None
    bielik_model: str |None = None
    history: list[Wiadomosc] = []

class Cytat(BaseModel):
   n: int
   url: str

class ChatResponse(BaseModel):
   agent: str
   answer: str
   sources: list[str]
   citations: list[Cytat]

app = FastAPI()

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        wynik = run(request.message, agent=request.agent, bielik_model=request.bielik_model,
                    history=[w.model_dump() for w in request.history])
        return wynik
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Brak odpowiedzi ze strony Ollamy")
    except httpx.ReadTimeout:
        raise HTTPException(status_code=504, detail='Zbyt długi czas generowania odpowiedzi')
