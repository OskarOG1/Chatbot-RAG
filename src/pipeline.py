from sentence_transformers import SentenceTransformer
import faiss
from rankings import search_reranked_multi
from agents import answer_stream, przepisz_zapytanie, czy_kontekst_odpowiada, napisz_email, sedzia_kategoria_mail, strona_pytania
from guards import sprawdz
from spell import correct, tokenize_words, MIN_DLUGOSC
from lang_config import LANG
import strony
from pathlib import Path
from datetime import datetime, timezone
import json
import math
import os
import pickle
import re
import simplemma
from collections import Counter
from functools import lru_cache

class ModeleLeniwe(dict):
    def __missing__(self, lang):
        model = SentenceTransformer(LANG[lang]['embedder'])
        self[lang] = model
        return model


MODELE = ModeleLeniwe()
OKNO_HISTORII = 3
SEDZIA_ON = os.getenv('SEDZIA_ON', 'true').lower() in ('1', 'true', 'yes')
KLASYFIKATOR_ON = os.getenv('KLASYFIKATOR_STRONY', '0') == '1'
LOG_TRUDNE = Path(__file__).resolve().parent.parent / 'RAG' / 'trudne.jsonl'
PII_WZORCE = (
    re.compile(r'[^\s@]+@[^\s@]+\.[^\s@]+'),
    re.compile(r'(?:\+\d{1,3}[\s-]?)?(?:\d[\s.-]?){9,}'),
    re.compile(r'\b(?=[^\W_]*\d)[^\W_]{4,}\b'),
    re.compile(r'\bhttps?://\S+'),
)
PROG_POKRYCIA = LANG['pl']['prog_pokrycia']
PROG_RERANK = LANG['pl']['prog_rerank']


def followup(query: str, lang: str = 'pl') -> bool:
    cfg = LANG[lang]
    low = query.lower().strip()
    if low.startswith(cfg['followup_prefiksy']):
        return True
    return bool(set(tokenize_words(low)) & cfg['zaimki'])


def sygnal_maila(query: str, lang: str = 'pl') -> bool:
    cfg = LANG[lang]
    low = query.lower()
    tokeny = set(tokenize_words(low))
    for kat in cfg['mail_kategorie'].values():
        if tokeny & kat['slowa']:
            return True
        if any(fraza in low for fraza in kat['frazy']):
            return True
    return False


def kategoria_z_oferty(query: str, lang: str = 'pl') -> str | None:
    cfg = LANG[lang]
    low = query.strip().lower()
    for nazwa, kat in cfg['mail_kategorie'].items():
        if low == kat['oferta'].lower():
            return nazwa
    return None


def jawna_prosba_o_mail(query: str, lang: str = 'pl') -> bool:
    cfg = LANG[lang]
    low = query.strip().lower()
    if kategoria_z_oferty(query, lang):
        return True
    tokeny = set(tokenize_words(low))
    return bool(tokeny & cfg['mail_czasowniki']) and bool(tokeny & cfg['mail_obiekty'])


def lematy(tekst: str, lang: str = 'pl') -> set:
    lemma_lang = LANG[lang]['lemma_lang']
    return {simplemma.lemmatize(t, lang=lemma_lang)
            for t in tokenize_words(tekst) if len(t) >= MIN_DLUGOSC}


EMBED_CACHE_MAX = int(os.getenv('EMBED_CACHE_MAX', '512'))


@lru_cache(maxsize=EMBED_CACHE_MAX)
def embed_query(lang: str, tekst: str):
    emb = MODELE[lang].encode([LANG[lang]['query_prefix'] + tekst]).astype('float32')
    faiss.normalize_L2(emb)
    return emb


def chunks_path(lang: str) -> Path:
    suffix = LANG[lang]['suffix']
    return Path(__file__).resolve().parent.parent / 'RAG' / f'chunks{suffix}.json'


def corpus_stamp(lang: str) -> int:
    try:
        return int(chunks_path(lang).stat().st_mtime)
    except OSError:
        return 0


def zaladuj_idf(lang: str) -> tuple[dict, float]:
    chunks_json = chunks_path(lang)
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
                for lemat in lematy(chunk.get('tekst', ''), lang):
                    df[lemat] += 1
            idf = {lemat: math.log((1 + n) / (1 + liczba)) for lemat, liczba in df.items()}
            idf_max = math.log(1 + n)
            with open(idf_cache, 'wb') as plik:
                pickle.dump({'stamp': stamp, 'idf': idf, 'idf_max': idf_max}, plik)
        else:
            idf = zapis['idf']
            idf_max = zapis['idf_max']
    except Exception as e:
        print(f'blad ladowania idf ({lang}): {type(e).__name__}: {e}')
    return idf, idf_max


class IdfLeniwe(dict):
    def __missing__(self, lang):
        wartosc = zaladuj_idf(lang)
        self[lang] = wartosc
        return wartosc


IDF_DANE = IdfLeniwe()


def pokrycie_idf(tekst: str, chunks: list, lang: str = 'pl') -> float:
    odp = lematy(tekst, lang)
    if not odp:
        return 0.0
    idf, idf_max = IDF_DANE[lang]
    kontekst = set()
    for c, _ in chunks:
        kontekst |= lematy(c['tekst'], lang)
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


def cytaty_lub_zrodla(cytaty: list[dict], chunks: list[tuple[dict, float]]) -> list[dict]:
    if cytaty:
        return cytaty
    zrodla = list(dict.fromkeys(c['url'] for c, _ in chunks))
    tytuly = {c['url']: c['tytul'] for c, _ in chunks}
    return [{'n': i, 'url': url, 'tytul': tytuly[url]} for i, url in enumerate(zrodla, 1)]


def run_stream(query:str, bielik_model:str | None=None,
               history:list[dict] | None=None, agent_poprzedni:str | None=None,
               przepisz:bool=False, bez_korekty:bool=False, sedzia:bool | None=None,
               lang:str='pl', strona:str | None=None):

    cfg = LANG[lang]

    def krok(t):
        return {'typ': 'krok', 'tekst': t}
    def wynik(d):
        return {'typ': 'wynik', 'dane': d}

    yield krok(cfg['kroki']['sprawdzam_pytanie'])
    powod = sprawdz(query, cfg['guardy'])
    if powod:
        yield wynik({'agent': '', 'answer': powod, 'sources': [], 'citations': [], 'doprecyzowanie': None})
        return
    history = (history or [])[-OKNO_HISTORII:]
    bez_korekty = bez_korekty or lang != 'pl'
    if bez_korekty:

        doprecyzowanie = None
    else:
        yield krok(cfg['kroki']['poprawiam_literowki'])
        korekta = correct(query)
        query = korekta['poprawione']
        if korekta['nieznane']:
            loguj_trudne(query, korekta['nieznane'])
            tokeny = [t for t in tokenize_words(query) if len(t) >= MIN_DLUGOSC]

            if tokeny and len(korekta['nieznane']) >= len(tokeny):
                yield wynik({'agent': '', 'answer': cfg['nie_zrozumialem'],
                             'sources': [], 'citations': [], 'doprecyzowanie': None})
                return
        doprecyzowanie = f'Szukam dla: „{query}", czy o to chodziło?' if korekta['zmieniono'] else None

    if jawna_prosba_o_mail(query, lang):
        yield krok(cfg['kroki']['szkic_wiadomosci'])
        kategoria = kategoria_z_oferty(query, lang)
        if kategoria is None:
            ostatnia_tresc = next((w['content'] for w in reversed(history)
                                   if w.get('role') == 'user' and w.get('content')), '')
            tekst_ret = f'{ostatnia_tresc} {query}'.strip()
            router_emb = embed_query(lang, tekst_ret)
            router_chunks = search_reranked_multi(tekst_ret, router_emb, ['kupujacy'], k=5, k_surowe=20, lang=lang)
            kategoria = sedzia_kategoria_mail(history + [{'role': 'user', 'content': query}], router_chunks, lang)
        if kategoria is None:
            yield wynik({'agent': '', 'answer': cfg['mail_doprecyzuj'],
                         'sources': [], 'citations': [], 'doprecyzowanie': None, 'oferta': None, 'tryb': 'rag'})
            return
        kat_cfg = cfg['mail_kategorie'][kategoria]
        mail_emb = embed_query(lang, kat_cfg['zapytanie'])
        mail_chunks = search_reranked_multi(kat_cfg['zapytanie'], mail_emb, ['kupujacy'], k=3, k_surowe=20, lang=lang)
        szkic = napisz_email(history + [{'role': 'user', 'content': query}], mail_chunks, lang, kategoria)
        yield wynik({'agent': 'email', 'answer': szkic['tekst'],
                     'sources': list(dict.fromkeys(c['url'] for c, _ in mail_chunks)),
                     'citations': [], 'doprecyzowanie': None, 'oferta': None, 'tryb': 'email',
                     'kategoria': kategoria, 'naglowek_ui': kat_cfg['naglowek_ui']})
        return

    czy_followup = bool(history) and followup(query, lang)
    if (history and przepisz) or czy_followup:
        yield krok(cfg['kroki']['przepisuje_pytanie'])
        zapytanie_ret = przepisz_zapytanie(query, history, bielik_model, lang)
    else:
        zapytanie_ret = query

    yield krok(cfg['kroki']['zamieniam_na_wektor'])
    query_emb = embed_query(lang, zapytanie_ret)

    yield krok(cfg['kroki']['przeszukuje_baze'])

    if strona in strony.STRONY:
        chunks = search_reranked_multi(zapytanie_ret, query_emb, [strony.STRONA_DO_AGENTA[strona]],
                                        k=5, k_surowe=20, lang=lang)
        strona_wybrana, czy_pytac = strona, False
    else:
        prior, sila = strony.prior_strony(zapytanie_ret, agent_poprzedni, lang, czy_followup)
        if prior is None and KLASYFIKATOR_ON:
            yield krok(cfg['kroki']['rozpoznaje_strone'])
            prior = strona_pytania(zapytanie_ret, history, lang)
            sila = 'llm' if prior else None
        kwoty = strony.przydzial_kandydatow(prior, sila)
        chunks_szerokie = search_reranked_multi(zapytanie_ret, query_emb, list(kwoty),
                                                  k=10, k_surowe=kwoty, lang=lang)
        strona_wybrana, chunks, czy_pytac = strony.rozstrzygnij(chunks_szerokie, prior, sila, k=5)

    if czy_pytac:
        yield wynik({'agent': '', 'answer': cfg['strona_doprecyzuj'],
                     'sources': [], 'citations': [], 'doprecyzowanie': doprecyzowanie,
                     'pyta_strona': True})
        return

    if strona_wybrana:
        yield krok(cfg['kroki']['wybieram_strone'].format(strona=cfg['nazwy_stron'][strona_wybrana]))

    agent_odp = chunks[0][0]['agent'] if chunks else ''

    if not chunks or chunks[0][1] < cfg['prog_rerank']:
        yield krok(cfg['kroki']['poza_zakresem'])
        yield wynik({'agent': '', 'answer': cfg['brak_wiedzy'],
                     'sources': [], 'citations': [], 'doprecyzowanie': doprecyzowanie})
        return

    if (SEDZIA_ON if sedzia is None else sedzia) and chunks:
        yield krok(cfg['kroki']['sprawdzam_kontekst'])
        if not czy_kontekst_odpowiada(zapytanie_ret, chunks, lang=lang):
            yield wynik({'agent': '', 'answer': cfg['brak_wiedzy'],
                         'sources': [], 'citations': [], 'doprecyzowanie': doprecyzowanie})
            return

    etykieta_sekcji = cfg['nazwy_sekcji'].get(agent_odp, agent_odp)
    yield krok(cfg['kroki']['generuje_odpowiedz'].format(agent=etykieta_sekcji))
    odpowiedz = None
    tokeny_bufor = []
    for ev in answer_stream(query, agent_odp, chunks, bielik_model, history, lang):
        if ev['typ'] == 'token':
            tokeny_bufor.append(ev)
        elif ev['typ'] == 'koniec':
            odpowiedz = ev['dane']

    if odpowiedz is None or pokrycie_idf(odpowiedz['tekst'], chunks, lang) < cfg['prog_pokrycia']:
        yield wynik({'agent': '', 'answer': cfg['brak_wiedzy'],
                     'sources': [], 'citations': [], 'doprecyzowanie': doprecyzowanie})
        return

    for ev in tokeny_bufor:
        yield ev

    oferta = None
    oferta_kategoria = None
    artykuly_maila = {kat['artykul'] for kat in cfg['mail_kategorie'].values()}
    if sygnal_maila(query, lang) or (chunks and chunks[0][0]['url'] and
                                      any(art in chunks[0][0]['url'] for art in artykuly_maila)):
        kategoria = sedzia_kategoria_mail(history + [{'role': 'user', 'content': query}], chunks, lang)
        if kategoria:
            oferta = cfg['mail_kategorie'][kategoria]['oferta']
            oferta_kategoria = kategoria

    zrodla = list(dict.fromkeys(c['url'] for c, _ in chunks))
    yield wynik({'agent': agent_odp,
                 'answer': odpowiedz['tekst'],
                 'sources': zrodla,
                 'citations': cytaty_lub_zrodla(odpowiedz['cytaty'], chunks),
                 'doprecyzowanie': doprecyzowanie,
                 'oferta': oferta,
                 'oferta_kategoria': oferta_kategoria,
                 'tryb': 'rag'})


def run(query:str, bielik_model:str | None=None,
        history:list[dict] | None=None, agent_poprzedni:str | None=None,
        przepisz:bool=False, bez_korekty:bool=False, sedzia:bool | None=None,
        lang:str='pl', strona:str | None=None) -> dict:
    dane = {}
    for ev in run_stream(query, bielik_model, history,
                         agent_poprzedni, przepisz, bez_korekty, sedzia, lang, strona):
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
