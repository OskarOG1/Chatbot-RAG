from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from typing import Literal
from pipeline import run, run_stream, MODELE, corpus_stamp, redaguj
from rankings import get_reranker, get_bm25, get_faiss
from spell import detect_lang
from guards import MAX_ZNAKI, normalizuj
from lang_config import LANG, DOMYSLNY_JEZYK
from collections import deque, OrderedDict
from datetime import datetime, timezone
from pathlib import Path
import os
import time
import json

LIMIT_MIN = int(os.getenv('LIMIT_MIN', '15'))
LIMIT_DZIEN = int(os.getenv('LIMIT_DZIEN', '200'))
_zapytania = deque()

CACHE_MAX = int(os.getenv('CACHE_MAX', '200'))
_cache: 'OrderedDict[tuple, dict]' = OrderedDict()
LOG_ANALYTICS = Path(__file__).resolve().parent.parent / 'RAG' / 'log_analytics.jsonl'


def cache_zdatny(request: 'ChatRequest') -> bool:
    return (not request.history and not request.agent_poprzedni and not request.przepisz
            and request.bielik_model is None and request.sedzia is None)


def cache_klucz(lang: str, message: str) -> tuple:
    return (lang, normalizuj(message), corpus_stamp(lang))


def cache_pobierz(klucz: tuple) -> dict | None:
    wynik = _cache.get(klucz)
    if wynik is not None:
        _cache.move_to_end(klucz)
    return wynik


def cache_zapisz(klucz: tuple, wynik: dict) -> None:
    if not wynik.get('agent'):
        return
    _cache[klucz] = wynik
    _cache.move_to_end(klucz)
    if len(_cache) > CACHE_MAX:
        _cache.popitem(last=False)


def loguj_zapytanie(lang: str, agent: str, latencja: float, cache_hit: bool, query: str) -> None:
    try:
        wpis = {
            'czas': datetime.now(timezone.utc).isoformat(),
            'lang': lang,
            'sekcja': agent or None,
            'wynik': 'odpowiedz' if agent else 'odmowa',
            'latencja_s': round(latencja, 3),
            'cache_hit': cache_hit,
            'pytanie': redaguj(query),
        }
        with open(LOG_ANALYTICS, 'a', encoding='utf-8') as w:
            w.write(json.dumps(wpis, ensure_ascii=False) + '\n')
    except OSError:
        pass


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
   oferta_kategoria: str | None = None
   kategoria: str | None = None
   tryb: Literal['rag', 'email'] = 'rag'

app = FastAPI(lifespan=lifespan)

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest):
    if not w_limicie():
        raise HTTPException(status_code=429, detail='Limit zapytań demo osiągnięty — spróbuj później.')
    start = time.perf_counter()
    try:
        lang = efektywny_jezyk(request.message, request.lang)
        uzyj_cache = cache_zdatny(request)
        klucz = cache_klucz(lang, request.message) if uzyj_cache else None
        wynik = cache_pobierz(klucz) if klucz else None
        cache_hit = wynik is not None
        if wynik is None:
            wynik = run(request.message, bielik_model=request.bielik_model,
                        history=[w.model_dump() for w in request.history],
                        agent_poprzedni=request.agent_poprzedni, przepisz=request.przepisz,
                        bez_korekty=request.bez_korekty, sedzia=request.sedzia, lang=lang)
            if klucz:
                cache_zapisz(klucz, wynik)
        loguj_zapytanie(lang, wynik.get('agent', ''), time.perf_counter() - start, cache_hit, request.message)
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
        start = time.perf_counter()
        try:
            lang = efektywny_jezyk(request.message, request.lang)
            uzyj_cache = cache_zdatny(request)
            klucz = cache_klucz(lang, request.message) if uzyj_cache else None
            cached = cache_pobierz(klucz) if klucz else None
            if cached is not None:
                yield f"data: {json.dumps({'typ': 'wynik', 'dane': cached}, ensure_ascii=False)}\n\n"
                loguj_zapytanie(lang, cached.get('agent', ''), time.perf_counter() - start, True, request.message)
                return
            wynik = {}
            for ev in run_stream(request.message, bielik_model=request.bielik_model,
                                 history=[w.model_dump() for w in request.history],
                                 agent_poprzedni=request.agent_poprzedni, przepisz=request.przepisz,
                                 bez_korekty=request.bez_korekty, sedzia=request.sedzia, lang=lang):
                if ev['typ'] == 'wynik':
                    wynik = ev['dane']
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
            if klucz:
                cache_zapisz(klucz, wynik)
            loguj_zapytanie(lang, wynik.get('agent', ''), time.perf_counter() - start, False, request.message)
        except Exception as e:
            print(f'blad /chat/stream: {type(e).__name__}: {e}')
            yield f"data: {json.dumps({'typ': 'blad', 'kod': 503, 'tekst': 'Model chwilowo niedostępny — spróbuj ponownie.'}, ensure_ascii=False)}\n\n"
    return StreamingResponse(gen(), media_type='text/event-stream')
