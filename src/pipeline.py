from sentence_transformers import SentenceTransformer
import faiss
from rankings import search_reranked_multi
from agents import answer_stream, przepisz_zapytanie, czy_kontekst_odpowiada
from guards import sprawdz
from spell import correct, tokenize_words, MIN_DLUGOSC
from pathlib import Path
from datetime import datetime, timezone
import json
import math
import os
import pickle
import re
import simplemma
from collections import Counter

MODEL_NAME = 'sdadas/mmlw-retrieval-roberta-base'
model = SentenceTransformer(MODEL_NAME)
MARGINES = 2
OKNO_HISTORII = 3
SEDZIA_ON = os.getenv('SEDZIA_ON', 'true').lower() in ('1', 'true', 'yes')
LOG_TRUDNE = Path(__file__).resolve().parent.parent / 'RAG' / 'trudne.jsonl'
PII_WZORCE = (
    re.compile(r'[^\s@]+@[^\s@]+\.[^\s@]+'),
    re.compile(r'(?:\+\d{1,3}[\s-]?)?(?:\d[\s.-]?){9,}'),
    re.compile(r'\b(?=[^\W_]*\d)[^\W_]{4,}\b'),
    re.compile(r'\bhttps?://\S+'),
)
BRAK_WIEDZY = ('Nie znalazłem tej informacji w bazie pomocy Allegro. '
               'Sprawdź bezpośrednio w Centrum Pomocy: https://allegro.pl/pomoc')
PROG_POKRYCIA = 0.20
PROG_RERANK = -4.3
# Lokalne rozwiązanie (bge-v2-m3 + Bielik 1.5B): PROG_POKRYCIA = 0.65, PROG_RERANK = 0.05
ZAIMKI = {'to', 'tego', 'tym', 'tam', 'ten', 'ta', 'te', 'nim', 'niej', 'nich'}


def _followup(query: str) -> bool:
    low = query.lower().strip()
    if low.startswith('a '):
        return True
    return bool(set(tokenize_words(low)) & ZAIMKI)


def _lematy(tekst: str) -> set:
    return {simplemma.lemmatize(t, lang='pl')
            for t in tokenize_words(tekst) if len(t) >= MIN_DLUGOSC}


def pokrycie_leksykalne(tekst: str, chunks: list) -> float:
    
    odp = _lematy(tekst)
    if not odp:
        return 0.0
    kontekst = set()
    for c, _ in chunks:
        kontekst |= _lematy(c['tekst'])
    return len(odp & kontekst) / len(odp)


CHUNKS_JSON = Path(__file__).resolve().parent.parent / 'RAG' / 'chunks.json'
IDF_CACHE = CHUNKS_JSON.parent / 'idf.pkl'
IDF = {}
IDF_MAX = 1.0
try:
    _stamp = int(CHUNKS_JSON.stat().st_mtime)
    _zapis = None
    if IDF_CACHE.exists():
        with open(IDF_CACHE, 'rb') as _plik:
            _kandydat = pickle.load(_plik)
        if _kandydat.get('stamp') == _stamp:
            _zapis = _kandydat
    if _zapis is None:
        with open(CHUNKS_JSON, encoding='utf-8') as _plik:
            _chunki = json.load(_plik)
        _n = len(_chunki) or 1
        _df = Counter()
        for _chunk in _chunki:
            for _lemat in _lematy(_chunk.get('tekst', '')):
                _df[_lemat] += 1
        IDF = {_lemat: math.log((1 + _n) / (1 + _liczba)) for _lemat, _liczba in _df.items()}
        IDF_MAX = math.log(1 + _n)
        with open(IDF_CACHE, 'wb') as _plik:
            pickle.dump({'stamp': _stamp, 'idf': IDF, 'idf_max': IDF_MAX}, _plik)
    else:
        IDF = _zapis['idf']
        IDF_MAX = _zapis['idf_max']
except Exception:
    pass


def pokrycie_idf(tekst: str, chunks: list) -> float:
    odp = _lematy(tekst)
    if not odp:
        return 0.0
    kontekst = set()
    for c, _ in chunks:
        kontekst |= _lematy(c['tekst'])
    licznik = sum(IDF.get(w, IDF_MAX) for w in odp & kontekst)
    mianownik = sum(IDF.get(w, IDF_MAX) for w in odp)
    return licznik / mianownik if mianownik else 0.0


def skazone_tokeny(query: str) -> set:
    trafienia = set()
    for wzorzec in PII_WZORCE:
        for dopasowanie in wzorzec.finditer(query):
            trafienia.update(tokenize_words(dopasowanie.group(0)))
    return trafienia


def loguj_trudne(query: str, nieznane: list) -> None:
    skazone = skazone_tokeny(query)
    tokeny = sorted({t.lower() for t in nieznane} - skazone)
    if not tokeny:
        return
    try:
        wpis = {'czas': datetime.now(timezone.utc).isoformat(), 'nieznane': tokeny}
        with open(LOG_TRUDNE, 'a', encoding='utf-8') as w:
            w.write(json.dumps(wpis, ensure_ascii=False) + '\n')
    except OSError:
        pass

pytania = [
   
    "Jak sprawdzić, gdzie jest moja przesyłka?",
    "Kupiłem coś przez pomyłkę, da się anulować zamówienie?",
    "Czy mogę odebrać zamówienie w automacie paczkowym?",
    "Towar przyszedł uszkodzony, co mi przysługuje?",
    "Jak długo mam na zwrot po odebraniu paczki?",
    "Sprzedawca chce, żebym zapłacił poza Allegro - czy to bezpieczne?",
    
    "Jak rozłożyć zakup na raty?",
    "Płatność się nie powiodła, a pieniądze zniknęły z konta.",
    "Gdzie znajdę fakturę za zakupy?",
    "Jak dodać nową kartę do płatności?",
    "Czy mogę zapłacić BLIKIEM?",
    "Ile kosztuje przesyłka kurierem?",
]


def run_stream(query:str, agent:str | None=None, bielik_model:str | None=None,
               history:list[dict] | None=None, agent_poprzedni:str | None=None,
               przepisz:bool=False, bez_korekty:bool=False, sedzia:bool | None=None):
   
    def krok(t):
        return {'typ': 'krok', 'tekst': t}
    def wynik(d):
        return {'typ': 'wynik', 'dane': d}

    yield krok('Sprawdzam pytanie')
    powod = sprawdz(query)
    if powod:
        yield wynik({'agent': '', 'answer': powod, 'sources': [], 'citations': [], 'doprecyzowanie': None})
        return
    history = (history or [])[-OKNO_HISTORII:]
    if bez_korekty:
       
        doprecyzowanie = None
    else:
        yield krok('Poprawiam literówki')
        korekta = correct(query)
        query = korekta['poprawione']
        if korekta['nieznane']:
            loguj_trudne(query, korekta['nieznane'])
            tokeny = [t for t in tokenize_words(query) if len(t) >= MIN_DLUGOSC]
           
            if tokeny and len(korekta['nieznane']) >= len(tokeny):
                yield wynik({'agent': '', 'answer': 'Przepraszam, nie zrozumiałem pytania — czy możesz napisać je inaczej?',
                             'sources': [], 'citations': [], 'doprecyzowanie': None})
                return
        doprecyzowanie = f'Szukam dla: „{query}" — czy o to chodziło?' if korekta['zmieniono'] else None

    if przepisz and history:
        yield krok('Przepisuję pytanie z kontekstu rozmowy')
        zapytanie_ret = przepisz_zapytanie(query, history, bielik_model)
    elif history and _followup(query):
        poprzedni_user = [w['content'] for w in history if w['role'] == 'user'][-1:]
        zapytanie_ret = ' '.join(poprzedni_user + [query])
    else:
        zapytanie_ret = query

    yield krok('Zamieniam pytanie na wektor')
    query_emb = model.encode(['zapytanie: ' + zapytanie_ret]).astype('float32')
    faiss.normalize_L2(query_emb)

    yield krok('Przeszukuję bazę wiedzy i porządkuję wyniki')
    chunks = search_reranked_multi(zapytanie_ret, query_emb, ['all'], k=5, k_surowe=20)

    agenci_chunkow = [c['agent'] for c, _ in chunks]
    if agent is None and agent_poprzedni and agent_poprzedni in agenci_chunkow:
        agent_odp = agent_poprzedni
    else:
        agent_odp = chunks[0][0]['agent'] if chunks else ''

    if not chunks or chunks[0][1] < PROG_RERANK:
        yield krok('Poza zakresem bazy pomocy — odmawiam')
        yield wynik({'agent': '', 'answer': BRAK_WIEDZY,
                     'sources': [], 'citations': [], 'doprecyzowanie': doprecyzowanie})
        return

    if (SEDZIA_ON if sedzia is None else sedzia) and chunks:
        yield krok('Sprawdzam, czy kontekst odpowiada na pytanie')
        if not czy_kontekst_odpowiada(zapytanie_ret, chunks):
            yield wynik({'agent': '', 'answer': BRAK_WIEDZY,
                         'sources': [], 'citations': [], 'doprecyzowanie': doprecyzowanie})
            return

    yield krok(f'Generuję odpowiedź (sekcja: {agent_odp})')
    odpowiedz = None
    for ev in answer_stream(query, agent_odp, chunks, bielik_model, history):
        if ev['typ'] == 'token':
            yield ev
        elif ev['typ'] == 'koniec':
            odpowiedz = ev['dane']

    if odpowiedz is None or pokrycie_idf(odpowiedz['tekst'], chunks) < PROG_POKRYCIA:
        yield wynik({'agent': '', 'answer': BRAK_WIEDZY,
                     'sources': [], 'citations': [], 'doprecyzowanie': doprecyzowanie})
        return

    zrodla = list(dict.fromkeys(c['url'] for c, _ in chunks))
    yield wynik({'agent': agent_odp,
                 'answer': odpowiedz['tekst'],
                 'sources': zrodla,
                 'citations': odpowiedz['cytaty'],
                 'doprecyzowanie': doprecyzowanie})


def run(query:str, agent:str | None=None, bielik_model:str | None=None,
        history:list[dict] | None=None, agent_poprzedni:str | None=None,
        przepisz:bool=False, bez_korekty:bool=False, sedzia:bool | None=None) -> dict:
    dane = {}
    for ev in run_stream(query, agent, bielik_model, history,
                         agent_poprzedni, przepisz, bez_korekty, sedzia):
        if ev['typ'] == 'wynik':
            dane = ev['dane']
    return dane


if __name__ == '__main__':
    linie = []

    for i, p in enumerate(pytania, 1):
        wynik = run(p)
        blok = (
            f"{'='*60}\n"
            f"[{i}] PYTANIE: {p}\n"
            f"AGENT: {wynik['agent']}\n"
            f"SOURCES: {wynik['sources']}\n"
            f"ODPOWIEDŹ:\n{wynik['answer']}\n"
        )
        print(blok)
        linie.append(blok)

    out = Path(__file__).resolve().parent.parent / 'outputs' / 'eval.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(linie))
