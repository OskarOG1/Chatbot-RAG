from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from pipeline import run, run_stream
import httpx
import json

class Wiadomosc(BaseModel):
   role: str
   content: str

class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    agent:str | None = None
    bielik_model: str |None = None
    history: list[Wiadomosc] = []
    agent_poprzedni: str | None = None
    przepisz: bool = False
    bez_korekty: bool = False
    sedzia: bool = False

class Cytat(BaseModel):
   n: int
   url: str

class ChatResponse(BaseModel):
   agent: str
   answer: str
   sources: list[str]
   citations: list[Cytat]
   doprecyzowanie: str | None = None

app = FastAPI()

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        wynik = run(request.message, agent=request.agent, bielik_model=request.bielik_model,
                    history=[w.model_dump() for w in request.history],
                    agent_poprzedni=request.agent_poprzedni, przepisz=request.przepisz,
                    bez_korekty=request.bez_korekty, sedzia=request.sedzia)
        return wynik
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Brak odpowiedzi ze strony Ollamy")
    except httpx.ReadTimeout:
        raise HTTPException(status_code=504, detail='Zbyt długi czas generowania odpowiedzi')


@app.post('/chat/stream')
def chat_stream(request: ChatRequest):
    def gen():
        try:
            for ev in run_stream(request.message, agent=request.agent, bielik_model=request.bielik_model,
                                 history=[w.model_dump() for w in request.history],
                                 agent_poprzedni=request.agent_poprzedni, przepisz=request.przepisz,
                                 bez_korekty=request.bez_korekty, sedzia=request.sedzia):
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
        except httpx.ConnectError:
            yield f"data: {json.dumps({'typ': 'blad', 'kod': 503, 'tekst': 'Brak odpowiedzi ze strony Ollamy'}, ensure_ascii=False)}\n\n"
        except httpx.ReadTimeout:
            yield f"data: {json.dumps({'typ': 'blad', 'kod': 504, 'tekst': 'Zbyt długi czas generowania odpowiedzi'}, ensure_ascii=False)}\n\n"
    return StreamingResponse(gen(), media_type='text/event-stream')
