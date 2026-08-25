from sentence_transformers import SentenceTransformer
import faiss
from rankings import search_reranked_multi, normalizacja
from agents import (answer_stream, answer_ogolna_stream, przepisz_zapytanie,
                    czy_kontekst_odpowiada, napisz_email, sedzia_kategoria_mail)
from guards import sprawdz
from spell import correct, tokenize_words, MIN_DLUGOSC
from lang_config import LANG
import ogolna
import strony
import rozmowa
from pathlib import Path
from datetime import datetime, timezone
import json
import math
import os
import pickle
import re
import simplemma
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from functools import lru_cache

class ModeleLeniwe(dict):
    def __missing__(self, lang):
        model = SentenceTransformer(LANG[lang]['embedder'])
        self[lang] = model
        return model


MODELE = ModeleLeniwe()
OKNO_HISTORII = 3
OKNO_JAWNEJ_ODMOWY = 160
K_SUROWE_SEKCJI = int(os.getenv('K_SUROWE_SEKCJI', '12'))
K_CHUNKOW_SEKCJI = int(os.getenv('K_CHUNKOW_SEKCJI', '5'))
SEDZIA_CHUNKOW = int(os.getenv('SEDZIA_CHUNKOW', '3'))
SEDZIA_CZEKANIE = float(os.getenv('SEDZIA_CZEKANIE', '30'))
SEDZIA_ROWNOLEGLE = int(os.getenv('SEDZIA_ROWNOLEGLE', '8'))
SEDZIA_BUFOR_MAX = int(os.getenv('SEDZIA_BUFOR_MAX', '40'))
EGZEKUTOR_SEDZIEGO = ThreadPoolExecutor(max_workers=SEDZIA_ROWNOLEGLE,
                                        thread_name_prefix='sedzia')
SEDZIA_ON = os.getenv('SEDZIA_ON', 'true').lower() in ('1', 'true', 'yes')
OGOLNA_ON = os.getenv('OGOLNA_ON', 'true').lower() in ('1', 'true', 'yes')
POWODY_BLISKO_BAZY = ('pokrycie', 'model_nie_wie', 'jawna_odmowa', 'brak_generacji')
KATALOG_RAG = Path(__file__).resolve().parent.parent / 'RAG'
LOG_TRUDNE = KATALOG_RAG / 'trudne.jsonl'
PII_WZORCE = (
    re.compile(r'[^\s@]+@[^\s@]+\.[^\s@]+'),
    re.compile(r'(?:\+\d{1,3}[\s-]?)?(?:\d[\s.-]?){9,}'),
    re.compile(r'\b(?=[^\W_]*\d)[^\W_]{4,}\b'),
    re.compile(r'\bhttps?://\S+'),
)


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
    return KATALOG_RAG / f'chunks{suffix}.json'


def sekcje_chunks_paths(lang: str) -> list[Path]:
    suffix = LANG[lang]['suffix']
    return [KATALOG_RAG / f'chunks_kupujacy{suffix}.json',
            KATALOG_RAG / f'chunks_sprzedaz{suffix}.json']


def corpus_stamp(lang: str) -> int:
    znaczniki = []
    for sciezka in sekcje_chunks_paths(lang):
        try:
            znaczniki.append(int(sciezka.stat().st_mtime))
        except OSError:
            pass
    return max(znaczniki) if znaczniki else 0


def zaladuj_idf(lang: str) -> tuple[dict, float, bool]:
    chunks_json = chunks_path(lang)
    idf_cache = chunks_json.parent / f'idf{LANG[lang]["suffix"]}.pkl'
    idf, idf_max, powodzenie = {}, 1.0, True
    try:
        stamp = corpus_stamp(lang)
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
        powodzenie = False
    return idf, idf_max, powodzenie


class IdfLeniwe(dict):
    def __missing__(self, lang):
        wartosc = zaladuj_idf(lang)
        self[lang] = wartosc
        return wartosc


IDF_DANE = IdfLeniwe()
OSTRZEZONO_BRAK_IDF: set[str] = set()


def pokrycie_idf(tekst: str, chunks: list, lang: str = 'pl') -> float:
    odp = lematy(tekst, lang)
    if not odp:
        return 0.0
    idf, idf_max, _ = IDF_DANE[lang]
    kontekst = set()
    for c, _ in chunks:
        kontekst |= lematy(c['tekst'], lang)
    licznik = sum(idf.get(w, idf_max) for w in odp & kontekst)
    mianownik = sum(idf.get(w, idf_max) for w in odp)
    return licznik / mianownik if mianownik else 0.0


def model_nie_wie(tekst: str, lang: str = 'pl') -> bool:
    low = tekst.lower()
    return any(fraza in low for fraza in LANG[lang]['nie_wiem_zwroty'])


def jawna_odmowa_frazy(lang: str) -> tuple:
    return tuple(normalizacja(fraza) for fraza in LANG[lang]['jawna_odmowa_zwroty'])


def jawna_odmowa_na_starcie(tekst: str, lang: str = 'pl') -> bool:
    okno = normalizacja(tekst[:OKNO_JAWNEJ_ODMOWY].replace('’', "'"))
    return any(fraza in okno for fraza in jawna_odmowa_frazy(lang))


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

def cytaty_lub_zrodla(cytaty: list[dict], chunks: list[tuple[dict, float]]) -> list[dict]:
    if cytaty:
        return cytaty
    zrodla = list(dict.fromkeys(c['url'] for c, _ in chunks))
    tytuly = {c['url']: c['tytul'] for c, _ in chunks}
    return [{'n': i, 'url': url, 'tytul': tytuly[url]} for i, url in enumerate(zrodla, 1)]


def probuj_sekcje(zapytanie_ret: str, query_emb, strona: str, query: str, history: list[dict],
                   bielik_model: str | None, sedzia: bool | None, lang: str, cfg: dict,
                   styl: str | None = None):
    rejestr = {}
    try:
        yield from sekcja_z_bramkami(zapytanie_ret, query_emb, strona, query, history,
                                      bielik_model, sedzia, lang, cfg, rejestr, styl)
    finally:
        zadanie = rejestr.get('werdykt')
        if zadanie is not None:
            zadanie.cancel()


def sekcja_z_bramkami(zapytanie_ret: str, query_emb, strona: str, query: str, history: list[dict],
                       bielik_model: str | None, sedzia: bool | None, lang: str, cfg: dict,
                       rejestr: dict, styl: str | None = None):
    def krok(t):
        return {'typ': 'krok', 'tekst': t}
    def rezultat(d):
        return {'typ': 'rezultat', 'dane': {'powod_odmowy': None, **d}}

    bramki_pominiete = []
    cechy = {'rerank_top1': None, 'chunkow': 0, 'zrodlo_top1': None,
             'sedzia_ok': None, 'pokrycie': None, 'etap': 1,
             'strona_wybrana': strona, 'przewaga_sekcji': None}

    wyniki = search_reranked_multi(zapytanie_ret, query_emb, strony.agenci_wszystkich_stron(),
                                    k=K_SUROWE_SEKCJI * len(strony.STRONY),
                                    k_surowe=K_SUROWE_SEKCJI, lang=lang)
    strona_wybrana, chunks, przewaga = strony.rozstrzygnij(wyniki, strona, K_CHUNKOW_SEKCJI)
    cechy['strona_wybrana'] = strona_wybrana
    cechy['przewaga_sekcji'] = przewaga
    agent_odp = chunks[0][0]['agent'] if chunks else ''
    cechy['chunkow'] = len(chunks)
    if chunks:
        cechy['rerank_top1'] = round(float(chunks[0][1]), 4)
        cechy['zrodlo_top1'] = chunks[0][0]['url']

    if not chunks or chunks[0][1] < cfg['prog_rerank']:
        yield krok(cfg['kroki']['poza_zakresem'])
        yield {'typ': 'rezultat', 'dane': {'powod_odmowy': 'prog_rerank',
                                            'bramki_pominiete': bramki_pominiete, 'cechy': cechy}}
        return

    yield krok(cfg['kroki']['wybieram_strone'].format(strona=cfg['nazwy_stron'][strona_wybrana]))

    stan_sedziego = {}
    werdykt = None
    if SEDZIA_ON if sedzia is None else sedzia:
        yield krok(cfg['kroki']['sprawdzam_kontekst'])
        kontekst_kosztow = copy_context()
        werdykt = EGZEKUTOR_SEDZIEGO.submit(
            kontekst_kosztow.run,
            czy_kontekst_odpowiada, zapytanie_ret, chunks[:SEDZIA_CHUNKOW], None, lang, stan_sedziego)
        rejestr['werdykt'] = werdykt

    etykieta_sekcji = cfg['nazwy_sekcji'].get(agent_odp, agent_odp)
    yield krok(cfg['kroki']['generuje_odpowiedz'].format(agent=etykieta_sekcji))

    odpowiedz = None
    bufor = []
    licznik_tokenow = 0
    przepuszczone = werdykt is None
    optymistycznie = False

    def werdykt_sedziego(czekaj: bool):
        if not czekaj and not werdykt.done():
            return None
        try:
            return bool(werdykt.result(timeout=SEDZIA_CZEKANIE))
        except TimeoutError:
            print(f'sedzia kontekstu nie zdazyl w {SEDZIA_CZEKANIE} s, przepuszczam dalej', flush=True)
            stan_sedziego['sedzia_pominiety'] = True
            return True
        except Exception as e:
            print(f'sedzia kontekstu zawiodl ({type(e).__name__}: {e}), przepuszczam dalej', flush=True)
            stan_sedziego['sedzia_pominiety'] = True
            return True

    def odmowa_sedziego(przerwano: bool):
        cechy['sedzia_ok'] = False
        cechy['generacja_przerwana'] = przerwano
        cechy['tokeny_stracone'] = licznik_tokenow if przerwano else 0
        if stan_sedziego.get('sedzia_pominiety'):
            bramki_pominiete.append('sedzia')
        return {'typ': 'rezultat', 'dane': {'powod_odmowy': 'sedzia',
                                             'bramki_pominiete': bramki_pominiete, 'cechy': cechy}}

    strumien = answer_stream(query, agent_odp, chunks, bielik_model, history, lang, styl=styl)
    for ev in strumien:
        if ev['typ'] == 'token':
            if przepuszczone and not optymistycznie:
                yield ev
                continue
            licznik_tokenow += 1
            if optymistycznie:
                yield ev
                continue
            bufor.append(ev)
            decyzja = werdykt_sedziego(czekaj=False)
            if decyzja is None:
                if len(bufor) >= SEDZIA_BUFOR_MAX:
                    optymistycznie = True
                    przepuszczone = True
                    for zbuforowany in bufor:
                        yield zbuforowany
                    bufor.clear()
                continue
            if not decyzja:
                strumien.close()
                yield odmowa_sedziego(przerwano=True)
                return
            cechy['sedzia_ok'] = True
            przepuszczone = True
            for zbuforowany in bufor:
                yield zbuforowany
            bufor.clear()
        elif ev['typ'] == 'koniec':
            odpowiedz = ev['dane']

    if not przepuszczone or optymistycznie:
        werdykt_pozytywny = werdykt_sedziego(czekaj=True)
        if not werdykt_pozytywny and not optymistycznie:
            yield odmowa_sedziego(przerwano=False)
            return
        cechy['sedzia_ok'] = werdykt_pozytywny
        for zbuforowany in bufor:
            yield zbuforowany

    if werdykt is not None and stan_sedziego.get('sedzia_pominiety'):
        bramki_pominiete.append('sedzia')

    if odpowiedz is None:
        yield {'typ': 'rezultat', 'dane': {'powod_odmowy': 'brak_generacji',
                                            'bramki_pominiete': bramki_pominiete, 'cechy': cechy}}
        return

    _, _, idf_ok = IDF_DANE[lang]
    if not idf_ok:
        bramki_pominiete.append('pokrycie')
        if lang not in OSTRZEZONO_BRAK_IDF:
            print(f'UWAGA: bramka pokrycia pominieta dla lang={lang}, IDF_DANE nie zaladowane')
            OSTRZEZONO_BRAK_IDF.add(lang)
    else:
        wartosc_pokrycia = pokrycie_idf(odpowiedz['tekst'], chunks, lang)
        cechy['pokrycie'] = round(float(wartosc_pokrycia), 4)
        if wartosc_pokrycia < cfg['prog_pokrycia']:
            yield {'typ': 'rezultat', 'dane': {'powod_odmowy': 'pokrycie',
                                                'bramki_pominiete': bramki_pominiete, 'cechy': cechy}}
            return

    if not odpowiedz['cytaty'] and model_nie_wie(odpowiedz['tekst'], lang):
        yield {'typ': 'rezultat', 'dane': {'powod_odmowy': 'model_nie_wie',
                                            'bramki_pominiete': bramki_pominiete, 'cechy': cechy}}
        return

    if jawna_odmowa_na_starcie(odpowiedz['tekst'], lang):
        yield {'typ': 'rezultat', 'dane': {'powod_odmowy': 'jawna_odmowa',
                                            'bramki_pominiete': bramki_pominiete, 'cechy': cechy}}
        return

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
    yield rezultat({
        'agent': agent_odp,
        'answer': odpowiedz['tekst'],
        'sources': zrodla,
        'citations': cytaty_lub_zrodla(odpowiedz['cytaty'], chunks),
        'oferta': oferta,
        'oferta_kategoria': oferta_kategoria,
        'strona': strona_wybrana,
        'bramki_pominiete': bramki_pominiete,
        'cechy': cechy,
    })


def probuj_ogolna(query: str, history: list[dict], bielik_model: str | None,
                   lang: str, cfg: dict, powod_rag: str | None = None):
    cechy = {'ogolna_temat': None, 'ogolna_domena': False, 'ogolna_znakow': 0,
             'ogolna_konkrety': None}

    if powod_rag in POWODY_BLISKO_BAZY:
        cechy['ogolna_domena'] = True
        yield {'typ': 'rezultat', 'dane': {'powod_odmowy': 'ogolna_blisko_bazy',
                                            'answer': None, 'cechy': cechy}}
        return

    zablokowany = ogolna.temat_zablokowany(query, lang)
    if zablokowany:
        cechy['ogolna_temat'] = zablokowany
        yield {'typ': 'rezultat', 'dane': {'powod_odmowy': 'ogolna_temat',
                                            'answer': ogolna.komunikat_tematu(zablokowany, lang),
                                            'cechy': cechy}}
        return

    if ogolna.pytanie_o_allegro(query, lang):
        cechy['ogolna_domena'] = True
        yield {'typ': 'rezultat', 'dane': {'powod_odmowy': 'ogolna_domena',
                                            'answer': None, 'cechy': cechy}}
        return

    yield {'typ': 'krok', 'tekst': cfg['kroki']['odpowiadam_ogolnie']}

    surowa = None
    for ev in answer_ogolna_stream(query, history, bielik_model, lang):
        if ev['typ'] == 'koniec':
            surowa = ev['dane']
        else:
            yield ev

    if surowa is None:
        yield {'typ': 'rezultat', 'dane': {'powod_odmowy': 'ogolna_brak_generacji',
                                            'answer': None, 'cechy': cechy}}
        return

    sprawdzenie = ogolna.sprawdz_odpowiedz(surowa, lang)
    tekst = sprawdzenie['tekst']
    cechy['ogolna_znakow'] = len(tekst)
    cechy['ogolna_konkrety'] = sprawdzenie['konkrety'] or None

    powod = sprawdzenie['powod']
    if powod is None and model_nie_wie(tekst, lang):
        powod = 'ogolna_model_nie_wie'
    if powod is None and jawna_odmowa_na_starcie(tekst, lang):
        powod = 'ogolna_jawna_odmowa'
    if powod:
        yield {'typ': 'rezultat', 'dane': {'powod_odmowy': powod, 'answer': None, 'cechy': cechy}}
        return

    yield {'typ': 'rezultat', 'dane': {'powod_odmowy': None, 'answer': tekst, 'cechy': cechy}}


def run_stream(query:str, bielik_model:str | None=None,
               history:list[dict] | None=None, agent_poprzedni:str | None=None,
               przepisz:bool=False, bez_korekty:bool=False, sedzia:bool | None=None,
               lang:str='pl', strona:str | None=None, warstwa_ogolna:bool | None=None):

    cfg = LANG[lang]

    def krok(t):
        return {'typ': 'krok', 'tekst': t}
    def wynik(d):
        return {'typ': 'wynik', 'dane': d}

    history = (history or [])[-OKNO_HISTORII:]
    klasa, reszta = rozmowa.klasa_tury(query, history, agent_poprzedni, lang)
    if klasa in ('powitanie', 'powitanie_ponowne', 'podziekowanie', 'meta'):
        yield wynik({'agent': '', 'answer': cfg['rozmowa'][klasa], 'sources': [],
                     'citations': [], 'doprecyzowanie': None, 'tryb': 'rozmowa'})
        return
    query = reszta

    styl = None
    poprzednie_pytanie = None
    if klasa == 'sterowanie':
        styl = rozmowa.podklasa_sterowania(query, lang)
        poprzednie_pytanie = next((w['content'] for w in reversed(history)
                                   if w.get('role') == 'user' and w.get('content')), None)

    yield krok(cfg['kroki']['sprawdzam_pytanie'])
    wynik_guardu = sprawdz(query, cfg['guardy'])
    if wynik_guardu:
        powod, nazwa_guardu = wynik_guardu
        yield wynik({'agent': '', 'answer': powod, 'sources': [], 'citations': [],
                     'doprecyzowanie': None, 'powod_odmowy': f'guard_{nazwa_guardu}'})
        return
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
                             'sources': [], 'citations': [], 'doprecyzowanie': None,
                             'powod_odmowy': 'nie_zrozumialem'})
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
            router_chunks = search_reranked_multi(tekst_ret, router_emb, ['kupujacy'], k=5, k_surowe=12, lang=lang)
            kategoria = sedzia_kategoria_mail(history + [{'role': 'user', 'content': query}], router_chunks, lang)
        if kategoria is None:
            yield wynik({'agent': '', 'answer': cfg['mail_doprecyzuj'],
                         'sources': [], 'citations': [], 'doprecyzowanie': None, 'oferta': None,
                         'tryb': 'rag', 'powod_odmowy': 'mail_doprecyzuj'})
            return
        kat_cfg = cfg['mail_kategorie'][kategoria]
        mail_emb = embed_query(lang, kat_cfg['zapytanie'])
        mail_chunks = search_reranked_multi(kat_cfg['zapytanie'], mail_emb, ['kupujacy'], k=3, k_surowe=12, lang=lang)
        szkic = napisz_email(history + [{'role': 'user', 'content': query}], mail_chunks, lang, kategoria)
        yield wynik({'agent': 'email', 'answer': szkic['tekst'],
                     'sources': list(dict.fromkeys(c['url'] for c, _ in mail_chunks)),
                     'citations': [], 'doprecyzowanie': None, 'oferta': None, 'tryb': 'email',
                     'kategoria': kategoria, 'naglowek_ui': kat_cfg['naglowek_ui']})
        return

    if klasa == 'sterowanie' and poprzednie_pytanie:
        zapytanie_ret = poprzednie_pytanie
    else:
        czy_followup = bool(history) and followup(query, lang)
        if (history and przepisz) or czy_followup:
            yield krok(cfg['kroki']['przepisuje_pytanie'])
            zapytanie_ret = przepisz_zapytanie(query, history, bielik_model, lang)
        else:
            zapytanie_ret = query

    yield krok(cfg['kroki']['zamieniam_na_wektor'])
    query_emb = embed_query(lang, zapytanie_ret)

    yield krok(cfg['kroki']['przeszukuje_baze'])

    strona = strona if strona in strony.STRONY else 'kupujacy'

    wynik_etapu = None
    wyslane_tokeny = False
    for ev in probuj_sekcje(zapytanie_ret, query_emb, strona, query, history,
                             bielik_model, sedzia, lang, cfg, styl=styl):
        if ev['typ'] == 'rezultat':
            wynik_etapu = ev['dane']
        else:
            if ev['typ'] == 'token':
                wyslane_tokeny = True
            yield ev

    bramki_pominiete = list(wynik_etapu.get('bramki_pominiete') or [])
    strona_wybrana = wynik_etapu.get('strona') or strona
    nota = None
    if not wynik_etapu['powod_odmowy'] and strona_wybrana != strona:
        nota = cfg['nota_sekcji'][strona_wybrana]

    if wynik_etapu['powod_odmowy']:
        if wyslane_tokeny:
            yield {'typ': 'reset'}
            wyslane_tokeny = False

        wynik_ogolnej = None
        if OGOLNA_ON if warstwa_ogolna is None else warstwa_ogolna:
            for ev in probuj_ogolna(query, history, bielik_model, lang, cfg,
                                     wynik_etapu['powod_odmowy']):
                if ev['typ'] == 'rezultat':
                    wynik_ogolnej = ev['dane']
                else:
                    if ev['typ'] == 'token':
                        wyslane_tokeny = True
                    yield ev

        cechy_koncowe = dict(wynik_etapu.get('cechy') or {})
        if wynik_ogolnej:
            cechy_koncowe.update(wynik_ogolnej.get('cechy') or {})

        if wynik_ogolnej and wynik_ogolnej['powod_odmowy'] is None:
            cechy_koncowe['etap'] = 3
            dane_ogolnej = {'agent': '', 'answer': wynik_ogolnej['answer'],
                            'sources': [], 'citations': [], 'doprecyzowanie': doprecyzowanie,
                            'nota_sekcji': cfg['ogolna']['nota'], 'tryb': 'ogolna',
                            'powod_rag': wynik_etapu['powod_odmowy'], 'cechy': cechy_koncowe}
            if bramki_pominiete:
                dane_ogolnej['bramki_pominiete'] = bramki_pominiete
            yield wynik(dane_ogolnej)
            return

        if wyslane_tokeny:
            yield {'typ': 'reset'}
            wyslane_tokeny = False

        dane_odmowy = {'agent': '', 'answer': cfg['brak_wiedzy'],
                       'sources': [], 'citations': [], 'doprecyzowanie': doprecyzowanie,
                       'powod_odmowy': wynik_etapu['powod_odmowy']}
        if wynik_ogolnej:
            dane_odmowy['powod_ogolna'] = wynik_ogolnej['powod_odmowy']
            if wynik_ogolnej.get('answer'):
                dane_odmowy['answer'] = wynik_ogolnej['answer']
        if bramki_pominiete:
            dane_odmowy['bramki_pominiete'] = bramki_pominiete
        dane_odmowy['cechy'] = cechy_koncowe
        yield wynik(dane_odmowy)
        return

    dane_sukcesu = {'agent': wynik_etapu['agent'],
                    'answer': wynik_etapu['answer'],
                    'sources': wynik_etapu['sources'],
                    'citations': wynik_etapu['citations'],
                    'doprecyzowanie': doprecyzowanie,
                    'nota_sekcji': nota,
                    'oferta': wynik_etapu['oferta'],
                    'oferta_kategoria': wynik_etapu['oferta_kategoria'],
                    'tryb': 'rag'}
    dane_sukcesu['cechy'] = wynik_etapu.get('cechy')
    if bramki_pominiete:
        dane_sukcesu['bramki_pominiete'] = bramki_pominiete
    yield wynik(dane_sukcesu)


def run(query:str, bielik_model:str | None=None,
        history:list[dict] | None=None, agent_poprzedni:str | None=None,
        przepisz:bool=False, bez_korekty:bool=False, sedzia:bool | None=None,
        lang:str='pl', strona:str | None=None, warstwa_ogolna:bool | None=None) -> dict:
    dane = {}
    for ev in run_stream(query, bielik_model, history,
                         agent_poprzedni, przepisz, bez_korekty, sedzia, lang, strona,
                         warstwa_ogolna):
        if ev['typ'] == 'wynik':
            dane = ev['dane']
    return dane
