from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from typing import Literal
import pipeline
from pipeline import run, run_stream, MODELE, corpus_stamp, redaguj, IDF_DANE, EGZEKUTOR_SEDZIEGO
from rankings import get_reranker, get_bm25, get_faiss
from spell import detect_lang, load_dictionary
from guards import MAX_ZNAKI, normalizuj
from lang_config import LANG, DOMYSLNY_JEZYK
from wysylka import wyslij_potwierdzenie, WysylkaCzesciowaError
from collections import deque, OrderedDict
from datetime import datetime, timezone
from pathlib import Path
import csv
import httpx
import io
import os
import re
import koszty
import secrets
import statystyki
import sys
import threading
import time
import traceback
import json

AGENCI_ROZGRZEWKA = ('kupujacy', 'sprzedaz')
AGENCI_ROZGRZEWKA_PL = AGENCI_ROZGRZEWKA

_zamek = threading.Lock()

LIMIT_MIN = int(os.getenv('LIMIT_MIN', '15'))
LIMIT_DZIEN = int(os.getenv('LIMIT_DZIEN', '200'))
_zapytania = deque()

LIMIT_IP_MIN = int(os.getenv('LIMIT_IP_MIN', '10'))
LIMIT_IP_DZIEN = int(os.getenv('LIMIT_IP_DZIEN', '40'))
IP_SLOWNIK_MAX = int(os.getenv('IP_SLOWNIK_MAX', '5000'))
_zapytania_ip: 'OrderedDict[str, deque]' = OrderedDict()

LIMIT_WYSYLKA_MIN = int(os.getenv('LIMIT_WYSYLKA_MIN', '5'))
LIMIT_WYSYLKA_DZIEN = int(os.getenv('LIMIT_WYSYLKA_DZIEN', '40'))
LIMIT_WYSYLKA_ADRES_S = int(os.getenv('LIMIT_WYSYLKA_ADRES_S', '600'))
WYSYLKA_ADRES_MAX = int(os.getenv('WYSYLKA_ADRES_MAX', '500'))
_wysylki = deque()
_wysylki_adres: 'OrderedDict[str, float]' = OrderedDict()
TICKET_MAX = int(os.getenv('TICKET_MAX', '5000'))
_tickety: 'OrderedDict[str, dict]' = OrderedDict()
EMAIL_WZORZEC = re.compile(r'[^\s@]+@[^\s@]+\.[^\s@]+')

CACHE_MAX = int(os.getenv('CACHE_MAX', '200'))
_cache: 'OrderedDict[tuple, dict]' = OrderedDict()
def sciezka_log_analytics() -> Path:
    zmienna = os.getenv('LOG_ANALYTICS_PLIK')
    if zmienna:
        sciezka = Path(zmienna)
        if not sciezka.is_absolute():
            sciezka = Path(__file__).resolve().parent.parent / sciezka
        return sciezka
    return Path(__file__).resolve().parent.parent / 'RAG' / 'log_analytics.jsonl'


LOG_ANALYTICS = sciezka_log_analytics()
OSTRZEZONO_O_LOGU = False
OSTRZEZONO_O_LOGU_WYSYLKI = False

SYGNAL_POMINIETE_OKNO = int(os.getenv('SYGNAL_POMINIETE_OKNO', '50'))
SYGNAL_POMINIETE_PROG = float(os.getenv('SYGNAL_POMINIETE_PROG', '0.2'))
_bramki_pominiete_historia: deque = deque(maxlen=SYGNAL_POMINIETE_OKNO)
_sygnal_bramki_pominiete_aktywny = False

STATYSTYKI_TTL = float(os.getenv('STATYSTYKI_TTL', '30'))
_log_cache: dict = {'stempel': None, 'wpisy': [], 'czas': 0.0}
_statystyki_cache: dict = {'stempel': None, 'czas': 0.0, 'wyniki': {}}
STATYSTYKI_CACHE_MAX = 64

LIMIT_OCEN_MIN = int(os.getenv('LIMIT_OCEN_MIN', '30'))
LIMIT_OCEN_DZIEN = int(os.getenv('LIMIT_OCEN_DZIEN', '500'))
LIMIT_OCEN_IP_MIN = int(os.getenv('LIMIT_OCEN_IP_MIN', '10'))
LIMIT_OCEN_IP_DZIEN = int(os.getenv('LIMIT_OCEN_IP_DZIEN', '60'))
LIMIT_ADMIN_IP_MIN = int(os.getenv('LIMIT_ADMIN_IP_MIN', '60'))
LIMIT_ADMIN_IP_DZIEN = int(os.getenv('LIMIT_ADMIN_IP_DZIEN', '2000'))
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN', '')
_oceny = deque()
_oceny_ip: OrderedDict = OrderedDict()
_admin_ip: OrderedDict = OrderedDict()
OSTRZEZONO_O_LOGU_OCEN = False


def zglos_bramki_pominiete(bramki_pominiete: list, cache_hit: bool = False) -> None:
    global _sygnal_bramki_pominiete_aktywny
    if cache_hit:
        return
    with _zamek:
        _bramki_pominiete_historia.append(bool(bramki_pominiete))
        if len(_bramki_pominiete_historia) < SYGNAL_POMINIETE_OKNO:
            return
        udzial = sum(_bramki_pominiete_historia) / len(_bramki_pominiete_historia)
        aktywny = udzial > SYGNAL_POMINIETE_PROG
        if aktywny and not _sygnal_bramki_pominiete_aktywny:
            print(f'UWAGA: {udzial:.0%} z ostatnich {SYGNAL_POMINIETE_OKNO} zadan ma pominiete bramki',
                  file=sys.stderr, flush=True)
        _sygnal_bramki_pominiete_aktywny = aktywny


def sygnal_bramki_pominiete_aktywny() -> bool:
    with _zamek:
        return _sygnal_bramki_pominiete_aktywny


def cache_zdatny(request: 'ChatRequest') -> bool:
    return (not request.history and not request.agent_poprzedni and not request.przepisz
            and request.bielik_model is None and request.sedzia is None
            and request.ogolna is None and not request.bez_korekty)


def cache_klucz(lang: str, message: str, strona: str) -> tuple:
    return (lang, normalizuj(message), corpus_stamp(lang), strona)


def cache_pobierz(klucz: tuple) -> dict | None:
    with _zamek:
        wynik = _cache.get(klucz)
        if wynik is not None:
            _cache.move_to_end(klucz)
        return wynik


def cache_zapisz(klucz: tuple, wynik: dict) -> None:
    if (not wynik.get('agent') and wynik.get('tryb') != 'ogolna'
            and wynik.get('powod_odmowy') != 'prog_rerank'):
        return
    with _zamek:
        _cache[klucz] = wynik
        _cache.move_to_end(klucz)
        if len(_cache) > CACHE_MAX:
            _cache.popitem(last=False)


def powod_wyniku(dane: dict) -> str:
    if not dane:
        return 'brak_wyniku'
    if dane.get('tryb') == 'rozmowa':
        return 'rozmowa'
    if dane.get('tryb') == 'ogolna':
        return dane.get('powod_rag') or 'ogolna'
    if dane.get('agent'):
        return 'odpowiedz'
    return dane.get('powod_odmowy') or 'odmowa'


def dopisz_do_logu(wpis: dict) -> None:
    with _zamek:
        with open(LOG_ANALYTICS, 'a', encoding='utf-8') as w:
            w.write(json.dumps(wpis, ensure_ascii=False) + '\n')


def loguj_zapytanie(lang: str, dane: dict, latencja: float, cache_hit: bool, query: str, strona: str,
                    zuzycie: dict | None = None, id_zapytania: str | None = None) -> None:
    dane = dane or {}
    zglos_bramki_pominiete(dane.get('bramki_pominiete') or [], cache_hit)
    try:
        agent = dane.get('agent') or ''
        tryb = dane.get('tryb')
        wynik = tryb if tryb in ('rozmowa', 'ogolna') else ('odpowiedz' if agent else 'odmowa')
        zuzycie = zuzycie or {}
        try:
            ustawienia_jezyka = LANG.get(lang) or {}
            konfiguracja = {
                'model': ustawienia_jezyka.get('model'),
                'sedzia_model': ustawienia_jezyka.get('sedzia_model'),
                'prog_rerank': ustawienia_jezyka.get('prog_rerank'),
                'prog_pokrycia': ustawienia_jezyka.get('prog_pokrycia'),
                'k_surowe_sekcji': pipeline.K_SUROWE_SEKCJI,
                'k_chunkow_sekcji': pipeline.K_CHUNKOW_SEKCJI,
                'sedzia_bufor_max': pipeline.SEDZIA_BUFOR_MAX,
                'sedzia_on': pipeline.SEDZIA_ON,
                'ogolna_on': pipeline.OGOLNA_ON,
            }
        except Exception:
            konfiguracja = None
        wpis = {
            'czas': datetime.now(timezone.utc).isoformat(),
            'id': id_zapytania,
            'lang': lang,
            'strona': strona,
            'sekcja': agent or None,
            'wynik': wynik,
            'powod': powod_wyniku(dane),
            'powod_ogolna': dane.get('powod_ogolna'),
            'bramki_pominiete': dane.get('bramki_pominiete') or [],
            'latencja_s': round(latencja, 3),
            'tokeny_we': zuzycie.get('tokeny_we', 0),
            'tokeny_wy': zuzycie.get('tokeny_wy', 0),
            'koszt_usd': zuzycie.get('koszt_usd', 0.0),
            'tokeny_szacowane': zuzycie.get('szacowane', False),
            'cache_hit': cache_hit,
            'pytanie': redaguj(query),
            'cechy': dane.get('cechy') or None,
            'konfiguracja': konfiguracja,
        }
        dopisz_do_logu(wpis)
    except OSError as e:
        global OSTRZEZONO_O_LOGU
        if not OSTRZEZONO_O_LOGU:
            print(f'UWAGA: nie moge pisac do {LOG_ANALYTICS}: {e}', file=sys.stderr, flush=True)
            OSTRZEZONO_O_LOGU = True


def w_limicie() -> bool:
    teraz = time.time()
    with _zamek:
        while _zapytania and _zapytania[0] < teraz - 86400:
            _zapytania.popleft()
        ostatnia_minuta = sum(1 for t in _zapytania if t > teraz - 60)
        if ostatnia_minuta >= LIMIT_MIN or len(_zapytania) >= LIMIT_DZIEN:
            return False
        _zapytania.append(teraz)
        return True


def adres_klienta(request: Request) -> str:
    naglowek = request.headers.get('x-forwarded-for')
    if naglowek:
        return naglowek.split(',')[-1].strip()
    return request.client.host if request.client else ''


def w_limicie_kolejki(slownik: OrderedDict, ip: str, limit_min: int, limit_dzien: int) -> bool:
    teraz = time.time()
    with _zamek:
        kolejka = slownik.setdefault(ip, deque())
        while kolejka and kolejka[0] < teraz - 86400:
            kolejka.popleft()
        ostatnia_minuta = sum(1 for t in kolejka if t > teraz - 60)
        if ostatnia_minuta >= limit_min or len(kolejka) >= limit_dzien:
            return False
        kolejka.append(teraz)
        slownik.move_to_end(ip)
        if len(slownik) > IP_SLOWNIK_MAX:
            slownik.popitem(last=False)
        return True


def w_limicie_ip(ip: str) -> bool:
    return w_limicie_kolejki(_zapytania_ip, ip, LIMIT_IP_MIN, LIMIT_IP_DZIEN)


def efektywny_jezyk(message: str, podpowiedz: str | None) -> str:
    return podpowiedz or detect_lang(message) or DOMYSLNY_JEZYK


def w_limicie_wysylki() -> bool:
    teraz = time.time()
    with _zamek:
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
    with _zamek:
        for k in [k for k, t in _wysylki_adres.items() if t < teraz - LIMIT_WYSYLKA_ADRES_S]:
            del _wysylki_adres[k]
        if klucz in _wysylki_adres:
            return False
        _wysylki_adres[klucz] = teraz
        _wysylki_adres.move_to_end(klucz)
        if len(_wysylki_adres) > WYSYLKA_ADRES_MAX:
            _wysylki_adres.popitem(last=False)
        return True


def zwolnij_limit_adresu(email: str) -> None:
    with _zamek:
        _wysylki_adres.pop(email.lower(), None)


def rejestruj_adres(email: str) -> None:
    klucz = email.lower()
    with _zamek:
        _wysylki_adres[klucz] = time.time()
        _wysylki_adres.move_to_end(klucz)
        if len(_wysylki_adres) > WYSYLKA_ADRES_MAX:
            _wysylki_adres.popitem(last=False)


def zarejestruj_ticket(ticket: str, email: str) -> None:
    with _zamek:
        _tickety[ticket] = {'email': email.lower(), 'uzyty': False}
        _tickety.move_to_end(ticket)
        if len(_tickety) > TICKET_MAX:
            _tickety.popitem(last=False)


def w_limicie_korekty(ticket: str, email: str) -> bool:
    with _zamek:
        wpis = _tickety.get(ticket)
        if wpis is None or wpis['email'] != email.lower() or wpis['uzyty']:
            return False
        wpis['uzyty'] = True
        return True


def zwolnij_limit_korekty(ticket: str) -> None:
    with _zamek:
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
        dopisz_do_logu(wpis)
    except OSError as e:
        global OSTRZEZONO_O_LOGU_WYSYLKI
        if not OSTRZEZONO_O_LOGU_WYSYLKI:
            print(f'UWAGA: nie moge pisac do {LOG_ANALYTICS}: {e}', file=sys.stderr, flush=True)
            OSTRZEZONO_O_LOGU_WYSYLKI = True


def loguj_ocene(ocena: str, pytanie: str, odpowiedz: str, sekcja: str | None, lang: str,
                 strona: str | None, id_zapytania: str | None = None) -> None:
    try:
        wpis = {
            'czas': datetime.now(timezone.utc).isoformat(),
            'typ': 'ocena',
            'ocena': ocena,
            'id_zapytania': id_zapytania,
            'lang': lang,
            'strona': strona,
            'sekcja': sekcja,
            'pytanie': redaguj(pytanie),
            'odpowiedz': redaguj(odpowiedz),
        }
        dopisz_do_logu(wpis)
    except OSError as e:
        global OSTRZEZONO_O_LOGU_OCEN
        if not OSTRZEZONO_O_LOGU_OCEN:
            print(f'UWAGA: nie moge pisac do {LOG_ANALYTICS}: {e}', file=sys.stderr, flush=True)
            OSTRZEZONO_O_LOGU_OCEN = True


def w_limicie_ocen() -> bool:
    teraz = time.time()
    with _zamek:
        while _oceny and _oceny[0] < teraz - 86400:
            _oceny.popleft()
        ostatnia_minuta = sum(1 for t in _oceny if t > teraz - 60)
        if ostatnia_minuta >= LIMIT_OCEN_MIN or len(_oceny) >= LIMIT_OCEN_DZIEN:
            return False
        _oceny.append(teraz)
        return True


def wpisy_logu() -> list[dict]:
    try:
        stan = LOG_ANALYTICS.stat()
    except OSError:
        return []
    stempel = (stan.st_mtime_ns, stan.st_size)
    teraz = time.time()
    with _zamek:
        if _log_cache['stempel'] == stempel and teraz - _log_cache['czas'] < STATYSTYKI_TTL:
            return _log_cache['wpisy']
    wpisy = statystyki.wczytaj(LOG_ANALYTICS)
    with _zamek:
        _log_cache['stempel'] = stempel
        _log_cache['wpisy'] = wpisy
        _log_cache['czas'] = teraz
    return wpisy


def kolumny_eksportu(kolumny: str | None) -> tuple:
    if not kolumny:
        return statystyki.KOLUMNY_DOMYSLNE
    wybrane = {k.strip() for k in kolumny.split(',') if k.strip()}
    zgodne = tuple(k for k in statystyki.KOLUMNY_EKSPORTU if k in wybrane)
    return zgodne or statystyki.KOLUMNY_DOMYSLNE


def statystyki_z_cache(dni: int | None, lang: str | None, strona: str | None) -> dict:
    wpisy = wpisy_logu()
    klucz = (dni, lang, strona)
    stempel = _log_cache['stempel']
    teraz = time.time()
    with _zamek:
        swiezy = (_statystyki_cache['stempel'] == stempel
                  and teraz - _statystyki_cache['czas'] < STATYSTYKI_TTL)
        if swiezy and klucz in _statystyki_cache['wyniki']:
            return _statystyki_cache['wyniki'][klucz]
    wynik = statystyki.statystyki(statystyki.filtruj(wpisy, dni=dni, lang=lang, strona=strona))
    with _zamek:
        if _statystyki_cache['stempel'] != stempel or not swiezy:
            _statystyki_cache['stempel'] = stempel
            _statystyki_cache['czas'] = teraz
            _statystyki_cache['wyniki'] = {}
        if len(_statystyki_cache['wyniki']) < STATYSTYKI_CACHE_MAX:
            _statystyki_cache['wyniki'][klucz] = wynik
    return wynik


def ostrzez_o_rozgrzewce(co: str, blad: Exception) -> None:
    print(f'UWAGA: rozgrzewka {co} nieudana ({type(blad).__name__}: {blad})',
          file=sys.stderr, flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):

    try:
        get_reranker().predict([('rozgrzewka', 'rozgrzewka')])
    except Exception as e:
        ostrzez_o_rozgrzewce('rerankera', e)
    for lang, cfg in LANG.items():
        try:
            MODELE[lang].encode([cfg['query_prefix'] + 'rozgrzewka'])
        except Exception as e:
            ostrzez_o_rozgrzewce(f'embeddera {lang}', e)
    try:
        load_dictionary()
    except Exception as e:
        ostrzez_o_rozgrzewce('slownika literowek', e)
    for lang, agenci in (('pl', AGENCI_ROZGRZEWKA), ('en', AGENCI_ROZGRZEWKA)):
        try:
            IDF_DANE[lang]
        except Exception as e:
            ostrzez_o_rozgrzewce(f'IDF {lang}', e)
        for agent in agenci:
            try:
                get_faiss(agent, lang)
                get_bm25(agent, lang)
            except Exception as e:
                ostrzez_o_rozgrzewce(f'indeksow {agent} {lang}', e)
    yield
    EGZEKUTOR_SEDZIEGO.shutdown(wait=False, cancel_futures=True)

MAX_ZNAKI_WPISU = int(os.getenv('MAX_ZNAKI_WPISU', '8000'))
MAX_WPISOW_HISTORII = int(os.getenv('MAX_WPISOW_HISTORII', '100'))

class Wiadomosc(BaseModel):
   role: Literal['user', 'assistant']
   content: str = Field(min_length=1, max_length=MAX_ZNAKI_WPISU)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_ZNAKI * 2)
    bielik_model: str |None = None
    history: list[Wiadomosc] = Field(default=[], max_length=MAX_WPISOW_HISTORII)
    agent_poprzedni: str | None = None
    przepisz: bool = False
    bez_korekty: bool = False
    sedzia: bool | None = None
    lang: Literal['pl', 'en'] | None = None
    strona: Literal['kupujacy', 'sprzedajacy'] = 'kupujacy'
    ogolna: bool | None = None

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

class OcenaZadanie(BaseModel):
    ocena: Literal['gora', 'dol']
    id_zapytania: str | None = Field(default=None, pattern=r'^[0-9a-f]{16}$')
    pytanie: str = Field(min_length=1, max_length=MAX_ZNAKI * 2)
    odpowiedz: str = Field(default='', max_length=MAX_ZNAKI_WPISU)
    sekcja: str | None = Field(default=None, max_length=40)
    lang: Literal['pl', 'en'] | None = None
    strona: Literal['kupujacy', 'sprzedajacy'] | None = None

class ChatResponse(BaseModel):
   id: str | None = None
   agent: str
   answer: str
   sources: list[str]
   citations: list[Cytat]
   doprecyzowanie: str | None = None
   nota_sekcji: str | None = None
   oferta: str | None = None
   oferta_kategoria: str | None = None
   kategoria: str | None = None
   naglowek_ui: str | None = None
   tryb: Literal['rag', 'email', 'rozmowa', 'ogolna'] = 'rag'
   powod_odmowy: str | None = None
   powod_rag: str | None = None

class LicznikKosztow:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            koszty.zacznij()
        await self.app(scope, receive, send)


app = FastAPI(lifespan=lifespan)
app.add_middleware(LicznikKosztow)

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest, http_request: Request):
    lang = efektywny_jezyk(request.message, request.lang)
    if not w_limicie_ip(adres_klienta(http_request)):
        raise HTTPException(status_code=429, detail=LANG[lang]['bledy']['limit_zapytan'])
    if not w_limicie():
        raise HTTPException(status_code=429, detail=LANG[lang]['bledy']['limit_zapytan'])
    start = time.perf_counter()
    strona = request.strona
    id_zapytania = secrets.token_hex(8)
    try:
        uzyj_cache = cache_zdatny(request)
        klucz = cache_klucz(lang, request.message, request.strona) if uzyj_cache else None
        wynik = cache_pobierz(klucz) if klucz else None
        cache_hit = wynik is not None
        zuzycie = None
        if wynik is None:
            wynik = run(request.message, bielik_model=request.bielik_model,
                        history=[w.model_dump() for w in request.history],
                        agent_poprzedni=request.agent_poprzedni, przepisz=request.przepisz,
                        bez_korekty=request.bez_korekty, sedzia=request.sedzia, lang=lang, strona=strona,
                        warstwa_ogolna=request.ogolna)
            zuzycie = koszty.podsumowanie()
            if klucz:
                cache_zapisz(klucz, wynik)
        loguj_zapytanie(lang, wynik, time.perf_counter() - start, cache_hit, request.message, request.strona,
                        zuzycie, id_zapytania)
        return dict(wynik, id=id_zapytania)
    except Exception as e:
        print(f'blad /chat: {type(e).__name__}: {e}\n{traceback.format_exc()}', file=sys.stderr, flush=True)
        raise HTTPException(status_code=503, detail=LANG[lang]['bledy']['model_niedostepny'])


@app.post('/chat/stream')
def chat_stream(request: ChatRequest, http_request: Request):
    lang = efektywny_jezyk(request.message, request.lang)

    strona = request.strona

    def gen():
        if not w_limicie_ip(adres_klienta(http_request)):
            yield f"data: {json.dumps({'typ': 'blad', 'kod': 429, 'tekst': LANG[lang]['bledy']['limit_zapytan']}, ensure_ascii=False)}\n\n"
            return
        if not w_limicie():
            yield f"data: {json.dumps({'typ': 'blad', 'kod': 429, 'tekst': LANG[lang]['bledy']['limit_zapytan']}, ensure_ascii=False)}\n\n"
            return
        start = time.perf_counter()
        id_zapytania = secrets.token_hex(8)
        try:
            uzyj_cache = cache_zdatny(request)
            klucz = cache_klucz(lang, request.message, request.strona) if uzyj_cache else None
            cached = cache_pobierz(klucz) if klucz else None
            if cached is not None:
                dane_wysylki = {k: v for k, v in cached.items() if k != 'cechy'}
                dane_wysylki['id'] = id_zapytania
                yield f"data: {json.dumps({'typ': 'wynik', 'dane': dane_wysylki}, ensure_ascii=False)}\n\n"
                loguj_zapytanie(lang, cached, time.perf_counter() - start, True, request.message, request.strona,
                                None, id_zapytania)
                return
            wynik = {}
            for ev in run_stream(request.message, bielik_model=request.bielik_model,
                                 history=[w.model_dump() for w in request.history],
                                 agent_poprzedni=request.agent_poprzedni, przepisz=request.przepisz,
                                 bez_korekty=request.bez_korekty, sedzia=request.sedzia, lang=lang, strona=strona,
                                 warstwa_ogolna=request.ogolna):
                if ev['typ'] == 'wynik':
                    wynik = ev['dane']
                    dane_wysylki = {k: v for k, v in wynik.items() if k != 'cechy'}
                    dane_wysylki['id'] = id_zapytania
                    ev = {'typ': 'wynik', 'dane': dane_wysylki}
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
            if klucz:
                cache_zapisz(klucz, wynik)
            loguj_zapytanie(lang, wynik, time.perf_counter() - start, False, request.message, request.strona,
                            koszty.podsumowanie(), id_zapytania)
        except Exception as e:
            print(f'blad /chat/stream: {type(e).__name__}: {e}\n{traceback.format_exc()}', file=sys.stderr, flush=True)
            yield f"data: {json.dumps({'typ': 'blad', 'kod': 503, 'tekst': LANG[lang]['bledy']['model_niedostepny']}, ensure_ascii=False)}\n\n"
    return StreamingResponse(gen(), media_type='text/event-stream')


@app.post('/send-email', response_model=WyslijOdpowiedz)
def send_email(request: WyslijZadanie):
    lang = request.lang or DOMYSLNY_JEZYK
    email = request.email.strip()
    if not EMAIL_WZORZEC.fullmatch(email):
        raise HTTPException(status_code=422, detail=LANG[lang]['bledy']['zly_email'])
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

    if not w_limicie_wysylki():
        zwolnij_limity()
        raise HTTPException(status_code=429, detail=LANG[lang]['bledy']['limit_wysylek'])

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


@app.post('/ocena')
def ocena(request: OcenaZadanie, http_request: Request):
    lang = request.lang or DOMYSLNY_JEZYK
    if not w_limicie_kolejki(_oceny_ip, adres_klienta(http_request),
                             LIMIT_OCEN_IP_MIN, LIMIT_OCEN_IP_DZIEN):
        raise HTTPException(status_code=429, detail=LANG[lang]['bledy']['limit_zapytan'])
    if not w_limicie_ocen():
        raise HTTPException(status_code=429, detail=LANG[lang]['bledy']['limit_zapytan'])
    loguj_ocene(request.ocena, request.pytanie, request.odpowiedz,
                request.sekcja, lang, request.strona, request.id_zapytania)
    return {'status': 'ok'}


@app.get('/admin/statystyki')
def admin_statystyki(http_request: Request, dni: int | None = Query(default=None, ge=1, le=3650),
                     lang: Literal['pl', 'en'] | None = None,
                     strona: Literal['kupujacy', 'sprzedajacy'] | None = None):
    if not w_limicie_kolejki(_admin_ip, adres_klienta(http_request),
                             LIMIT_ADMIN_IP_MIN, LIMIT_ADMIN_IP_DZIEN):
        raise HTTPException(status_code=429, detail=LANG[DOMYSLNY_JEZYK]['bledy']['limit_zapytan'])
    return statystyki_z_cache(dni, lang, strona)


@app.get('/admin/oceny')
def admin_oceny(http_request: Request, dni: int | None = Query(default=None, ge=1, le=3650)):
    if not w_limicie_kolejki(_admin_ip, adres_klienta(http_request),
                             LIMIT_ADMIN_IP_MIN, LIMIT_ADMIN_IP_DZIEN):
        raise HTTPException(status_code=429, detail=LANG[DOMYSLNY_JEZYK]['bledy']['limit_zapytan'])
    przypadki = statystyki.przypadki_ocen(wpisy_logu(), dni=dni)
    return {'razem': len(przypadki), 'przypadki': przypadki}


@app.post('/admin/resetuj-statystyki')
def admin_resetuj_statystyki(http_request: Request):
    if not w_limicie_kolejki(_admin_ip, adres_klienta(http_request),
                             LIMIT_ADMIN_IP_MIN, LIMIT_ADMIN_IP_DZIEN):
        raise HTTPException(status_code=429, detail=LANG[DOMYSLNY_JEZYK]['bledy']['limit_zapytan'])
    if not ADMIN_TOKEN:
        raise HTTPException(status_code=503,
                            detail='Reset statystyk wylaczony, brak ADMIN_TOKEN w konfiguracji.')
    podany = http_request.headers.get('x-admin-token', '')
    if not secrets.compare_digest(podany.encode('utf-8'), ADMIN_TOKEN.encode('utf-8')):
        raise HTTPException(status_code=401, detail='Brak uprawnien do resetu statystyk.')
    znacznik = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%f')
    archiwum = LOG_ANALYTICS.with_name(f'{LOG_ANALYTICS.name}.przed-resetem-{znacznik}')
    with _zamek:
        if archiwum.exists():
            raise HTTPException(status_code=409,
                                detail='Archiwum o tej nazwie juz istnieje, reset przerwany.')
        zarchiwizowano = LOG_ANALYTICS.exists()
        if zarchiwizowano:
            LOG_ANALYTICS.rename(archiwum)
        LOG_ANALYTICS.touch()
        _log_cache['stempel'] = None
        _log_cache['wpisy'] = []
        _statystyki_cache['stempel'] = None
        _statystyki_cache['wyniki'] = {}
    return {'status': 'ok', 'archiwum': archiwum.name if zarchiwizowano else None}


@app.get('/admin/eksport')
def admin_eksport(http_request: Request, format: Literal['csv', 'json'] = 'csv',
                  kolumny: str | None = None,
                  dni: int | None = Query(default=None, ge=1, le=3650),
                  lang: Literal['pl', 'en'] | None = None,
                  strona: Literal['kupujacy', 'sprzedajacy'] | None = None):
    if not w_limicie_kolejki(_admin_ip, adres_klienta(http_request),
                             LIMIT_ADMIN_IP_MIN, LIMIT_ADMIN_IP_DZIEN):
        raise HTTPException(status_code=429, detail=LANG[DOMYSLNY_JEZYK]['bledy']['limit_zapytan'])
    wybrane = kolumny_eksportu(kolumny)
    wpisy = [w for w in statystyki.filtruj(wpisy_logu(), dni=dni, lang=lang, strona=strona)
             if not w.get('typ')]
    stempel = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')
    if format == 'json':
        tresc = json.dumps([{k: statystyki.komorka_eksportu(w, k) for k in wybrane} for w in wpisy],
                           ensure_ascii=False, indent=2)
        typ_tresci = 'application/json; charset=utf-8'
        nazwa = f'statystyki_{stempel}.json'
    else:
        bufor = io.StringIO()
        pisarz = csv.writer(bufor, delimiter=';', lineterminator='\n')
        pisarz.writerow(wybrane)
        for w in wpisy:
            pisarz.writerow([statystyki.bezpieczna_komorka(statystyki.komorka_eksportu(w, k)) for k in wybrane])
        tresc = '﻿' + bufor.getvalue()
        typ_tresci = 'text/csv; charset=utf-8'
        nazwa = f'statystyki_{stempel}.csv'
    return Response(content=tresc, media_type=typ_tresci,
                    headers={'content-disposition': f'attachment; filename="{nazwa}"'})
