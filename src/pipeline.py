from sentence_transformers import SentenceTransformer
import faiss
from rankings import search_reranked_multi
from agents import answer_stream, przepisz_zapytanie, czy_kontekst_odpowiada, napisz_email, czy_oferowac_mail
from guards import sprawdz
from spell import correct, tokenize_words, MIN_DLUGOSC
from lang_config import LANG
from pathlib import Path
from datetime import datetime, timezone
import json
import math
import os
import pickle
import re
import simplemma
from collections import Counter

MODELE = {lang: SentenceTransformer(cfg['embedder']) for lang, cfg in LANG.items()}
model = MODELE['pl']
OKNO_HISTORII = 3
SEDZIA_ON = os.getenv('SEDZIA_ON', 'true').lower() in ('1', 'true', 'yes')
LOG_TRUDNE = Path(__file__).resolve().parent.parent / 'RAG' / 'trudne.jsonl'
PII_WZORCE = (
    re.compile(r'[^\s@]+@[^\s@]+\.[^\s@]+'),
    re.compile(r'(?:\+\d{1,3}[\s-]?)?(?:\d[\s.-]?){9,}'),
    re.compile(r'\b(?=[^\W_]*\d)[^\W_]{4,}\b'),
    re.compile(r'\bhttps?://\S+'),
)
PROG_POKRYCIA = LANG['pl']['prog_pokrycia']
PROG_RERANK = LANG['pl']['prog_rerank']
# Lokalne rozwiązanie (bge-v2-m3 + Bielik 1.5B): PROG_POKRYCIA = 0.65, PROG_RERANK = 0.05
ARTYKUL_REKLAMACJA = 'jak-rozpoczac-dyskusje-i-wyjasnic-problem-ze-sprzedajacym-WEDKYqnEvik'


def _followup(query: str, lang: str = 'pl') -> bool:
    cfg = LANG[lang]
    low = query.lower().strip()
    if low.startswith(cfg['followup_prefiksy']):
        return True
    return bool(set(tokenize_words(low)) & cfg['zaimki'])


def _ma_sygnal_reklamacji(query: str, lang: str = 'pl') -> bool:
    cfg = LANG[lang]
    low = query.lower()
    if set(tokenize_words(low)) & cfg['reklamacja_slowa']:
        return True
    return any(fraza in low for fraza in cfg['reklamacja_frazy'])


def _jawna_prosba_o_mail(query: str, lang: str = 'pl') -> bool:
    cfg = LANG[lang]
    low = query.strip().lower()
    if low == cfg['oferta_wiadomosc'].lower():
        return True
    tokeny = set(tokenize_words(low))
    return bool(tokeny & cfg['mail_czasowniki']) and bool(tokeny & cfg['mail_obiekty'])


def _lematy(tekst: str, lang: str = 'pl') -> set:
    lemma_lang = LANG[lang]['lemma_lang']
    return {simplemma.lemmatize(t, lang=lemma_lang)
            for t in tokenize_words(tekst) if len(t) >= MIN_DLUGOSC}


def _chunks_path(lang: str) -> Path:
    suffix = LANG[lang]['suffix']
    return Path(__file__).resolve().parent.parent / 'RAG' / f'chunks{suffix}.json'


def corpus_stamp(lang: str) -> int:
    try:
        return int(_chunks_path(lang).stat().st_mtime)
    except OSError:
        return 0


def _zaladuj_idf(lang: str) -> tuple[dict, float]:
    chunks_json = _chunks_path(lang)
    idf_cache = chunks_json.parent / f'idf{LANG[lang]["suffix"]}.pkl'
    idf, idf_max = {}, 1.0
    try:
        stamp = int(chunks_json.stat().st_mtime)
        zapis = None
        if idf_cache.exists():
            with open(idf_cache, 'rb') as plik:
                kandydat = pickle.load(plik)
            if kandydat.get('stamp') == stamp:
                zapis = kandydat
        if zapis is None:
            with open(chunks_json, encoding='utf-8') as plik:
                chunki = json.load(plik)
            n = len(chunki) or 1
            df = Counter()
            for chunk in chunki:
                for lemat in _lematy(chunk.get('tekst', ''), lang):
                    df[lemat] += 1
            idf = {lemat: math.log((1 + n) / (1 + liczba)) for lemat, liczba in df.items()}
            idf_max = math.log(1 + n)
            with open(idf_cache, 'wb') as plik:
                pickle.dump({'stamp': stamp, 'idf': idf, 'idf_max': idf_max}, plik)
        else:
            idf = zapis['idf']
            idf_max = zapis['idf_max']
    except Exception:
        pass
    return idf, idf_max


IDF_DANE = {lang: _zaladuj_idf(lang) for lang in LANG}


def pokrycie_idf(tekst: str, chunks: list, lang: str = 'pl') -> float:
    odp = _lematy(tekst, lang)
    if not odp:
        return 0.0
    idf, idf_max = IDF_DANE[lang]
    kontekst = set()
    for c, _ in chunks:
        kontekst |= _lematy(c['tekst'], lang)
    licznik = sum(idf.get(w, idf_max) for w in odp & kontekst)
    mianownik = sum(idf.get(w, idf_max) for w in odp)
    return licznik / mianownik if mianownik else 0.0


def skazone_tokeny(query: str) -> set:
    trafienia = set()
    for wzorzec in PII_WZORCE:
        for dopasowanie in wzorzec.finditer(query):
            trafienia.update(tokenize_words(dopasowanie.group(0)))
    return trafienia


def redaguj(query: str) -> str:
    tekst = query
    for wzorzec in PII_WZORCE:
        tekst = wzorzec.sub('[ukryte]', tekst)
    return tekst


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


def run_stream(query:str, bielik_model:str | None=None,
               history:list[dict] | None=None, agent_poprzedni:str | None=None,
               przepisz:bool=False, bez_korekty:bool=False, sedzia:bool | None=None,
               lang:str='pl'):

    cfg = LANG[lang]

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
    bez_korekty = bez_korekty or lang != 'pl'
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
                yield wynik({'agent': '', 'answer': cfg['nie_zrozumialem'],
                             'sources': [], 'citations': [], 'doprecyzowanie': None})
                return
        doprecyzowanie = f'Szukam dla: „{query}" — czy o to chodziło?' if korekta['zmieniono'] else None

    if _jawna_prosba_o_mail(query, lang):
        yield krok('Przygotowuję szkic maila do sprzedawcy')
        mail_emb = MODELE[lang].encode([cfg['query_prefix'] + cfg['reklamacja_zapytanie']]).astype('float32')
        faiss.normalize_L2(mail_emb)
        mail_chunks = search_reranked_multi(cfg['reklamacja_zapytanie'], mail_emb, ['all'], k=3, k_surowe=20, lang=lang)
        szkic = napisz_email(history + [{'role': 'user', 'content': query}], mail_chunks, lang)
        yield wynik({'agent': 'email', 'answer': szkic['tekst'],
                     'sources': list(dict.fromkeys(c['url'] for c, _ in mail_chunks)),
                     'citations': [], 'doprecyzowanie': None, 'oferta': None, 'tryb': 'email'})
        return

    if history and (przepisz or _followup(query, lang)):
        yield krok('Przepisuję pytanie z kontekstu rozmowy')
        zapytanie_ret = przepisz_zapytanie(query, history, bielik_model, lang)
    else:
        zapytanie_ret = query

    yield krok('Zamieniam pytanie na wektor')
    query_emb = MODELE[lang].encode([cfg['query_prefix'] + zapytanie_ret]).astype('float32')
    faiss.normalize_L2(query_emb)

    yield krok('Przeszukuję bazę wiedzy i porządkuję wyniki')
    chunks = search_reranked_multi(zapytanie_ret, query_emb, ['all'], k=5, k_surowe=20, lang=lang)

    agenci_chunkow = [c['agent'] for c, _ in chunks]
    if agent_poprzedni and agent_poprzedni in agenci_chunkow:
        agent_odp = agent_poprzedni
    else:
        agent_odp = chunks[0][0]['agent'] if chunks else ''

    if not chunks or chunks[0][1] < cfg['prog_rerank']:
        yield krok('Poza zakresem bazy pomocy — odmawiam')
        yield wynik({'agent': '', 'answer': cfg['brak_wiedzy'],
                     'sources': [], 'citations': [], 'doprecyzowanie': doprecyzowanie})
        return

    if (SEDZIA_ON if sedzia is None else sedzia) and chunks:
        yield krok('Sprawdzam, czy kontekst odpowiada na pytanie')
        if not czy_kontekst_odpowiada(zapytanie_ret, chunks, lang=lang):
            yield wynik({'agent': '', 'answer': cfg['brak_wiedzy'],
                         'sources': [], 'citations': [], 'doprecyzowanie': doprecyzowanie})
            return

    yield krok(f'Generuję odpowiedź (sekcja: {agent_odp})')
    odpowiedz = None
    for ev in answer_stream(query, agent_odp, chunks, bielik_model, history, lang):
        if ev['typ'] == 'token':
            yield ev
        elif ev['typ'] == 'koniec':
            odpowiedz = ev['dane']

    if odpowiedz is None or pokrycie_idf(odpowiedz['tekst'], chunks, lang) < cfg['prog_pokrycia']:
        yield wynik({'agent': '', 'answer': cfg['brak_wiedzy'],
                     'sources': [], 'citations': [], 'doprecyzowanie': doprecyzowanie})
        return

    oferta = None
    if _ma_sygnal_reklamacji(query, lang) or (chunks and ARTYKUL_REKLAMACJA in chunks[0][0]['url']):
        yield krok('Sprawdzam, czy zaproponować pomoc z reklamacją')
        if czy_oferowac_mail(history + [{'role': 'user', 'content': query}], chunks, lang):
            oferta = cfg['oferta_wiadomosc']

    zrodla = list(dict.fromkeys(c['url'] for c, _ in chunks))
    yield wynik({'agent': agent_odp,
                 'answer': odpowiedz['tekst'],
                 'sources': zrodla,
                 'citations': odpowiedz['cytaty'],
                 'doprecyzowanie': doprecyzowanie,
                 'oferta': oferta,
                 'tryb': 'rag'})


def run(query:str, bielik_model:str | None=None,
        history:list[dict] | None=None, agent_poprzedni:str | None=None,
        przepisz:bool=False, bez_korekty:bool=False, sedzia:bool | None=None,
        lang:str='pl') -> dict:
    dane = {}
    for ev in run_stream(query, bielik_model, history,
                         agent_poprzedni, przepisz, bez_korekty, sedzia, lang):
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
