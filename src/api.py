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
from wysylka import wyslij_potwierdzenie, WysylkaCzesciowaError
from collections import deque, OrderedDict
from datetime import datetime, timezone
from pathlib import Path
import httpx
import os
import re
import time
import json

LIMIT_MIN = int(os.getenv('LIMIT_MIN', '15'))
LIMIT_DZIEN = int(os.getenv('LIMIT_DZIEN', '200'))
_zapytania = deque()

LIMIT_WYSYLKA_MIN = int(os.getenv('LIMIT_WYSYLKA_MIN', '5'))
LIMIT_WYSYLKA_DZIEN = int(os.getenv('LIMIT_WYSYLKA_DZIEN', '40'))
LIMIT_WYSYLKA_ADRES_S = int(os.getenv('LIMIT_WYSYLKA_ADRES_S', '600'))
_wysylki = deque()
_wysylki_adres: 'OrderedDict[str, float]' = OrderedDict()
TICKET_MAX = int(os.getenv('TICKET_MAX', '5000'))
_tickety: 'OrderedDict[str, dict]' = OrderedDict()
EMAIL_WZORZEC = re.compile(r'[^\s@]+@[^\s@]+\.[^\s@]+')

CACHE_MAX = int(os.getenv('CACHE_MAX', '200'))
_cache: 'OrderedDict[tuple, dict]' = OrderedDict()
LOG_ANALYTICS = Path(__file__).resolve().parent.parent / 'RAG' / 'log_analytics.jsonl'


def cache_zdatny(request: 'ChatRequest') -> bool:
    return (not request.history and not request.agent_poprzedni and not request.przepisz
            and request.bielik_model is None and request.sedzia is None)


def cache_klucz(lang: str, message: str, strona: str) -> tuple:
    return (lang, normalizuj(message), corpus_stamp(lang), strona)


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


def loguj_zapytanie(lang: str, agent: str, latencja: float, cache_hit: bool, query: str, strona: str) -> None:
    try:
        wpis = {
            'czas': datetime.now(timezone.utc).isoformat(),
            'lang': lang,
            'strona': strona,
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
    return podpowiedz or detect_lang(message) or DOMYSLNY_JEZYK


def w_limicie_wysylki() -> bool:
    teraz = time.time()
    while _wysylki and _wysylki[0] < teraz - 86400:
        _wysylki.popleft()
    ostatnia_minuta = sum(1 for t in _wysylki if t > teraz - 60)
    if ostatnia_minuta >= LIMIT_WYSYLKA_MIN or len(_wysylki) >= LIMIT_WYSYLKA_DZIEN:
        return False
    _wysylki.append(teraz)
    return True


def w_limicie_adresu(email: str) -> bool:
    teraz = time.time()
    klucz = email.lower()
    for k in [k for k, t in _wysylki_adres.items() if t < teraz - LIMIT_WYSYLKA_ADRES_S]:
        del _wysylki_adres[k]
    if klucz in _wysylki_adres:
        return False
    _wysylki_adres[klucz] = teraz
    _wysylki_adres.move_to_end(klucz)
    if len(_wysylki_adres) > 500:
        _wysylki_adres.popitem(last=False)
    return True


def zwolnij_limit_adresu(email: str) -> None:
    _wysylki_adres.pop(email.lower(), None)


def rejestruj_adres(email: str) -> None:
    klucz = email.lower()
    _wysylki_adres[klucz] = time.time()
    _wysylki_adres.move_to_end(klucz)
    if len(_wysylki_adres) > 500:
        _wysylki_adres.popitem(last=False)


def zarejestruj_ticket(ticket: str, email: str) -> None:
    _tickety[ticket] = {'email': email.lower(), 'uzyty': False}
    _tickety.move_to_end(ticket)
    if len(_tickety) > TICKET_MAX:
        _tickety.popitem(last=False)


def w_limicie_korekty(ticket: str, email: str) -> bool:
    wpis = _tickety.get(ticket)
    if wpis is None or wpis['email'] != email.lower() or wpis['uzyty']:
        return False
    wpis['uzyty'] = True
    return True


def zwolnij_limit_korekty(ticket: str) -> None:
    wpis = _tickety.get(ticket)
    if wpis is not None:
        wpis['uzyty'] = False


def loguj_wysylke(lang: str, kategoria: str | None, ticket: str | None, sukces: bool, blad: str | None = None) -> None:
    try:
        wpis = {
            'czas': datetime.now(timezone.utc).isoformat(),
            'typ': 'wysylka',
            'lang': lang,
            'kategoria': kategoria,
            'ticket': ticket,
            'sukces': sukces,
        }
        if blad:
            wpis['blad'] = blad
        with open(LOG_ANALYTICS, 'a', encoding='utf-8') as w:
            w.write(json.dumps(wpis, ensure_ascii=False) + '\n')
    except OSError:
        pass


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
    strona: Literal['auto', 'kupujacy', 'sprzedajacy'] = 'auto'

class Cytat(BaseModel):
   n: int
   url: str
   tytul: str | None = None

class WyslijZadanie(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    temat: str = Field(min_length=1, max_length=200)
    tresc: str = Field(min_length=1, max_length=8000)
    kategoria: str | None = None
    lang: Literal['pl', 'en'] | None = None
    ticket: str | None = Field(default=None, pattern=r'^[A-F0-9]{8}$')

class WyslijOdpowiedz(BaseModel):
    ticket: str

class ChatResponse(BaseModel):
   agent: str
   answer: str
   sources: list[str]
   citations: list[Cytat]
   doprecyzowanie: str | None = None
   oferta: str | None = None
   oferta_kategoria: str | None = None
   kategoria: str | None = None
   naglowek_ui: str | None = None
   tryb: Literal['rag', 'email'] = 'rag'
   pyta_strona: bool = False

app = FastAPI(lifespan=lifespan)

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest):
    lang = efektywny_jezyk(request.message, request.lang)
    if not w_limicie():
        raise HTTPException(status_code=429, detail=LANG[lang]['bledy']['limit_zapytan'])
    start = time.perf_counter()
    strona = None if request.strona == 'auto' else request.strona
    try:
        uzyj_cache = cache_zdatny(request)
        klucz = cache_klucz(lang, request.message, request.strona) if uzyj_cache else None
        wynik = cache_pobierz(klucz) if klucz else None
        cache_hit = wynik is not None
        if wynik is None:
            wynik = run(request.message, bielik_model=request.bielik_model,
                        history=[w.model_dump() for w in request.history],
                        agent_poprzedni=request.agent_poprzedni, przepisz=request.przepisz,
                        bez_korekty=request.bez_korekty, sedzia=request.sedzia, lang=lang, strona=strona)
            if klucz:
                cache_zapisz(klucz, wynik)
        loguj_zapytanie(lang, wynik.get('agent', ''), time.perf_counter() - start, cache_hit, request.message, request.strona)
        return wynik
    except Exception as e:
        print(f'blad /chat: {type(e).__name__}: {e}')
        raise HTTPException(status_code=503, detail=LANG[lang]['bledy']['model_niedostepny'])


@app.post('/chat/stream')
def chat_stream(request: ChatRequest):
    lang = efektywny_jezyk(request.message, request.lang)

    strona = None if request.strona == 'auto' else request.strona

    def gen():
        if not w_limicie():
            yield f"data: {json.dumps({'typ': 'blad', 'kod': 429, 'tekst': LANG[lang]['bledy']['limit_zapytan']}, ensure_ascii=False)}\n\n"
            return
        start = time.perf_counter()
        try:
            uzyj_cache = cache_zdatny(request)
            klucz = cache_klucz(lang, request.message, request.strona) if uzyj_cache else None
            cached = cache_pobierz(klucz) if klucz else None
            if cached is not None:
                yield f"data: {json.dumps({'typ': 'wynik', 'dane': cached}, ensure_ascii=False)}\n\n"
                loguj_zapytanie(lang, cached.get('agent', ''), time.perf_counter() - start, True, request.message, request.strona)
                return
            wynik = {}
            for ev in run_stream(request.message, bielik_model=request.bielik_model,
                                 history=[w.model_dump() for w in request.history],
                                 agent_poprzedni=request.agent_poprzedni, przepisz=request.przepisz,
                                 bez_korekty=request.bez_korekty, sedzia=request.sedzia, lang=lang, strona=strona):
                if ev['typ'] == 'wynik':
                    wynik = ev['dane']
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
            if klucz:
                cache_zapisz(klucz, wynik)
            loguj_zapytanie(lang, wynik.get('agent', ''), time.perf_counter() - start, False, request.message, request.strona)
        except Exception as e:
            print(f'blad /chat/stream: {type(e).__name__}: {e}')
            yield f"data: {json.dumps({'typ': 'blad', 'kod': 503, 'tekst': LANG[lang]['bledy']['model_niedostepny']}, ensure_ascii=False)}\n\n"
    return StreamingResponse(gen(), media_type='text/event-stream')


@app.post('/send-email', response_model=WyslijOdpowiedz)
def send_email(request: WyslijZadanie):
    lang = request.lang or DOMYSLNY_JEZYK
    email = request.email.strip()
    if not EMAIL_WZORZEC.fullmatch(email):
        raise HTTPException(status_code=422, detail=LANG[lang]['bledy']['zly_email'])
    if not w_limicie_wysylki():
        raise HTTPException(status_code=429, detail=LANG[lang]['bledy']['limit_wysylek'])
    korekta = request.ticket is not None
    if korekta:
        if not w_limicie_korekty(request.ticket, email):
            raise HTTPException(status_code=429, detail=LANG[lang]['bledy']['limit_wysylek'])
        rejestruj_adres(email)
    elif not w_limicie_adresu(email):
        raise HTTPException(status_code=429, detail=LANG[lang]['bledy']['limit_wysylek'])
    def zwolnij_limity():
        if korekta:
            zwolnij_limit_korekty(request.ticket)
        else:
            zwolnij_limit_adresu(email)

    try:
        ticket = wyslij_potwierdzenie(email, request.kategoria, request.temat, request.tresc, lang=lang,
                                       ticket=request.ticket)
    except RuntimeError as e:
        zwolnij_limity()
        loguj_wysylke(lang, request.kategoria, None, False, type(e).__name__)
        raise HTTPException(status_code=503, detail=str(e))
    except WysylkaCzesciowaError as e:
        if korekta:
            zwolnij_limit_korekty(request.ticket)
        loguj_wysylke(lang, request.kategoria, e.ticket, False, type(e.oryginalny).__name__)
        raise HTTPException(status_code=502, detail=LANG[lang]['bledy']['wysylka_nieudana'])
    except httpx.HTTPError as e:
        zwolnij_limity()
        loguj_wysylke(lang, request.kategoria, None, False, type(e).__name__)
        raise HTTPException(status_code=502, detail=LANG[lang]['bledy']['wysylka_nieudana'])
    if not korekta:
        zarejestruj_ticket(ticket, email)
    loguj_wysylke(lang, request.kategoria, ticket, True)
    print(f'wysylka: ticket={ticket} kategoria={request.kategoria} sukces=True')
    return WyslijOdpowiedz(ticket=ticket)
