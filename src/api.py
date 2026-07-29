from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from typing import Literal
from pipeline import run, run_stream, MODELE
from rankings import get_reranker, get_bm25, get_faiss
from spell import detect_lang
from guards import MAX_ZNAKI
from lang_config import LANG, DOMYSLNY_JEZYK
from collections import deque
import os
import time
import json

LIMIT_MIN = int(os.getenv('LIMIT_MIN', '15'))
LIMIT_DZIEN = int(os.getenv('LIMIT_DZIEN', '200'))
_zapytania = deque()


def w_limicie() -> bool:
    teraz = time.time()
    while _zapytania and _zapytania[0] < teraz - 86400:
        _zapytania.popleft()
    ostatnia_minuta = sum(1 for t in _zapytania if t > teraz - 60)
    if ostatnia_minuta >= LIMIT_MIN or len(_zapytania) >= LIMIT_DZIEN:
        return False
    _zapytania.append(teraz)
    return True


def efektywny_jezyk(message: str, podpowiedz: str | None) -> str:
    return detect_lang(message) or podpowiedz or DOMYSLNY_JEZYK


@asynccontextmanager
async def lifespan(app: FastAPI):

    try:
        get_reranker().predict([('rozgrzewka', 'rozgrzewka')])
    except Exception:
        pass
    for lang, cfg in LANG.items():
        try:
            MODELE[lang].encode([cfg['query_prefix'] + 'rozgrzewka'])
        except Exception:
            pass
    for lang in LANG:
        try:
            get_faiss('all', lang)
            get_bm25('all', lang)
        except Exception:
            pass
    yield

MAX_ZNAKI_WPISU = int(os.getenv('MAX_ZNAKI_WPISU', '8000'))
MAX_WPISOW_HISTORII = int(os.getenv('MAX_WPISOW_HISTORII', '100'))

class Wiadomosc(BaseModel):
   role: Literal['user', 'assistant']
   content: str = Field(min_length=1, max_length=MAX_ZNAKI_WPISU)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_ZNAKI)
    bielik_model: str |None = None
    history: list[Wiadomosc] = Field(default=[], max_length=MAX_WPISOW_HISTORII)
    agent_poprzedni: str | None = None
    przepisz: bool = False
    bez_korekty: bool = False
    sedzia: bool | None = None
    lang: Literal['pl', 'en'] | None = None

class Cytat(BaseModel):
   n: int
   url: str

class ChatResponse(BaseModel):
   agent: str
   answer: str
   sources: list[str]
   citations: list[Cytat]
   doprecyzowanie: str | None = None
   oferta: str | None = None
   tryb: Literal['rag', 'email'] = 'rag'

app = FastAPI(lifespan=lifespan)

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest):
    if not w_limicie():
        raise HTTPException(status_code=429, detail='Limit zapytań demo osiągnięty — spróbuj później.')
    try:
        lang = efektywny_jezyk(request.message, request.lang)
        wynik = run(request.message, bielik_model=request.bielik_model,
                    history=[w.model_dump() for w in request.history],
                    agent_poprzedni=request.agent_poprzedni, przepisz=request.przepisz,
                    bez_korekty=request.bez_korekty, sedzia=request.sedzia, lang=lang)
        return wynik
    except Exception as e:
        print(f'blad /chat: {type(e).__name__}: {e}')
        raise HTTPException(status_code=503, detail='Model chwilowo niedostępny — spróbuj ponownie za chwilę.')


@app.post('/chat/stream')
def chat_stream(request: ChatRequest):
    def gen():
        if not w_limicie():
            yield f"data: {json.dumps({'typ': 'blad', 'kod': 429, 'tekst': 'Limit zapytań demo osiągnięty — spróbuj później.'}, ensure_ascii=False)}\n\n"
            return
        try:
            lang = efektywny_jezyk(request.message, request.lang)
            for ev in run_stream(request.message, bielik_model=request.bielik_model,
                                 history=[w.model_dump() for w in request.history],
                                 agent_poprzedni=request.agent_poprzedni, przepisz=request.przepisz,
                                 bez_korekty=request.bez_korekty, sedzia=request.sedzia, lang=lang):
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
        except Exception as e:
            print(f'blad /chat/stream: {type(e).__name__}: {e}')
            yield f"data: {json.dumps({'typ': 'blad', 'kod': 503, 'tekst': 'Model chwilowo niedostępny — spróbuj ponownie.'}, ensure_ascii=False)}\n\n"
    return StreamingResponse(gen(), media_type='text/event-stream')
