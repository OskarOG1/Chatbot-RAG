from sentence_transformers import SentenceTransformer
import faiss
from rankings import search_reranked_multi, normalizacja
from agents import (answer_stream, answer_ogolna_stream, przepisz_zapytanie,
                    czy_kontekst_odpowiada, napisz_email, sedzia_kategoria_mail)
from guards import sprawdz
from spell import correct, tokenize_words, MIN_DLUGOSC, lematy as lematy_lemma
from lang_config import LANG
import ogolna
import podpowiedzi
import strony
import rozmowa
from pathlib import Path
from datetime import datetime, timezone
import json
import math
import os
import pickle
import re
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
K_SUROWE_SEKCJI = int(os.getenv('K_SUROWE_SEKCJI', '6'))
K_CHUNKOW_SEKCJI = int(os.getenv('K_CHUNKOW_SEKCJI', '5'))
SEDZIA_CHUNKOW = int(os.getenv('SEDZIA_CHUNKOW', '3'))
SEDZIA_CZEKANIE = float(os.getenv('SEDZIA_CZEKANIE', '30'))
SEDZIA_CZEKANIE_KONCOWE = float(os.getenv('SEDZIA_CZEKANIE_KONCOWE', '3'))
SEDZIA_ROWNOLEGLE = int(os.getenv('SEDZIA_ROWNOLEGLE', '8'))
SEDZIA_BUFOR_MAX = int(os.getenv('SEDZIA_BUFOR_MAX', '40'))
EGZEKUTOR_SEDZIEGO = ThreadPoolExecutor(max_workers=SEDZIA_ROWNOLEGLE,
                                        thread_name_prefix='sedzia')
SEDZIA_ON = os.getenv('SEDZIA_ON', 'true').lower() in ('1', 'true', 'yes')
OGOLNA_ON = os.getenv('OGOLNA_ON', 'true').lower() in ('1', 'true', 'yes')
ETAP2_ON = os.getenv('ETAP2_ON', 'true').lower() in ('1', 'true', 'yes')
POWODY_BLISKO_BAZY = ('pokrycie', 'model_nie_wie', 'jawna_odmowa', 'brak_generacji')
POWODY_DRUGA_PROBA = ('sedzia', 'pokrycie', 'model_nie_wie')
KATALOG_RAG = Path(__file__).resolve().parent.parent / 'RAG'
LOG_TRUDNE = KATALOG_RAG / 'trudne.jsonl'
PII_WYJATKI_WIELKA_LITERA = (
    'Allegro', 'Smart', 'Pay', 'Lokalnie', 'Ceny', 'Protect', 'Paczkomat', 'InPost',
    'Strefa', 'Okazji', 'Moje', 'Kup', 'Teraz', 'Dodaj', 'Koszyka', 'Koszyk',
    'How', 'Does', 'Is', 'Are', 'Do', 'What', 'Where', 'When', 'Why', 'Who', 'Which', 'Can',
    'Jak', 'Czy', 'Gdzie', 'Co', 'Kiedy', 'Dlaczego', 'Kto', 'Prosze',
)
PII_WYJATEK_ALT = '|'.join(re.escape(w) for w in PII_WYJATKI_WIELKA_LITERA)
PII_WZORCE = (
    re.compile(r'[^\s@]+@[^\s@]+\.[^\s@]+'),
    re.compile(r'(?:\+\d{1,3}[\s-]?)?(?:\d[\s.-]?){9,}'),
    re.compile(r'\b(?=[^\W_]*\d)[^\W_]{4,}\b'),
    re.compile(r'\bhttps?://\S+'),
    re.compile(r'\b(?!(?:%s)\b)[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+\s+(?!(?:%s)\b)'
               r'[A-ZĄĆĘŁŃÓŚŹŻ][a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+\b' % (PII_WYJATEK_ALT, PII_WYJATEK_ALT)),
    re.compile(r'\b(?i:ulic[aąeęy]|adres(?:u|em)?)\s+[A-ZĄĆĘŁŃÓŚŹŻ][\w]*(?:\s+\d+\w*)?'),
    re.compile(r'\b\d+\s+(?:[A-Z][a-zA-Z]*\s+){1,3}(?i:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr)\b'),
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
    return lematy_lemma(tekst, LANG[lang]['lemma_lang'])


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


@lru_cache(maxsize=None)
def wzorce_fraz(frazy: tuple, wtracenia: tuple) -> tuple:
    wstawka = '(?:%s)' % '|'.join(re.escape(w) for w in wtracenia)
    wzorce = []
    for fraza in frazy:
        slowa = [re.escape(s) for s in fraza.split()]
        warianty = [r'\s+'.join(slowa)]
        for i in range(1, len(slowa)):
            warianty.append(r'\s+'.join(slowa[:i] + [wstawka] + slowa[i:]))
        wzorce.append(re.compile('(?:%s)' % '|'.join(warianty)))
    return tuple(wzorce)


def frazy_odmowy(lang: str, klucz: str) -> tuple:
    return tuple(normalizacja(fraza) for fraza in LANG[lang][klucz])


def jawna_odmowa_frazy(lang: str) -> tuple:
    return frazy_odmowy(lang, 'jawna_odmowa_zwroty')


def wzorce_odmowy(lang: str, klucz: str) -> tuple:
    return wzorce_fraz(frazy_odmowy(lang, klucz),
                       tuple(normalizacja(w) for w in LANG[lang]['wtracenia_odmowy']))


def model_nie_wie(tekst: str, lang: str = 'pl') -> bool:
    tekst = normalizacja(tekst.replace('’', "'"))
    return any(wzorzec.search(tekst) for wzorzec in wzorce_odmowy(lang, 'nie_wiem_zwroty'))


def jawna_odmowa_na_starcie(tekst: str, lang: str = 'pl') -> bool:
    okno = normalizacja(tekst[:OKNO_JAWNEJ_ODMOWY].replace('’', "'"))
    return any(wzorzec.search(okno) for wzorzec in wzorce_odmowy(lang, 'jawna_odmowa_zwroty'))


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


def zadanie_sedziego(stan: dict, zapytanie_ret: str, chunks: list, bielik_model: str | None,
                     lang: str) -> bool:
    stan['sedzia_wystartowal'] = True
    return czy_kontekst_odpowiada(zapytanie_ret, chunks, bielik_model, lang, stan)


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
                                    k=None, k_surowe=K_SUROWE_SEKCJI, lang=lang)
    strona_wybrana, chunks, przewaga = strony.rozstrzygnij(wyniki, strona, K_CHUNKOW_SEKCJI)
    cechy['strona_wybrana'] = strona_wybrana
    cechy['przewaga_sekcji'] = przewaga
    yield krok(cfg['kroki']['wybieram_strone'].format(strona=cfg['nazwy_stron'][strona_wybrana]))
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

    stan_sedziego = {}
    werdykt = None
    if SEDZIA_ON if sedzia is None else sedzia:
        yield krok(cfg['kroki']['sprawdzam_kontekst'])
        kontekst_kosztow = copy_context()
        werdykt = EGZEKUTOR_SEDZIEGO.submit(
            kontekst_kosztow.run,
            zadanie_sedziego, stan_sedziego, zapytanie_ret, chunks[:SEDZIA_CHUNKOW], None, lang)
        rejestr['werdykt'] = werdykt

    etykieta_sekcji = cfg['nazwy_sekcji'].get(agent_odp, agent_odp)
    yield krok(cfg['kroki']['generuje_odpowiedz'].format(agent=etykieta_sekcji))

    odpowiedz = None
    bufor = []
    licznik_tokenow = 0
    przepuszczone = werdykt is None
    optymistycznie = False

    def werdykt_sedziego(czekaj: bool, limit: float = SEDZIA_CZEKANIE):
        if not czekaj and not werdykt.done():
            return None
        try:
            return bool(werdykt.result(timeout=limit))
        except TimeoutError:
            print(f'sedzia kontekstu nie zdazyl w {limit} s, przepuszczam dalej', flush=True)
            stan_sedziego['sedzia_pominiety'] = True
            stan_sedziego.setdefault('sedzia_pominiety_przyczyna',
                                     'model' if stan_sedziego.get('sedzia_wystartowal') else 'kolejka')
            return True
        except Exception as e:
            print(f'sedzia kontekstu zawiodl ({type(e).__name__}: {e}), przepuszczam dalej', flush=True)
            stan_sedziego['sedzia_pominiety'] = True
            stan_sedziego.setdefault('sedzia_pominiety_przyczyna', 'model')
            return True

    def odmowa_sedziego(przerwano: bool, tokeny_wyslane: int = 0):
        cechy['sedzia_ok'] = False
        cechy['generacja_przerwana'] = przerwano
        cechy['tokeny_stracone'] = licznik_tokenow if przerwano else tokeny_wyslane
        if stan_sedziego.get('sedzia_pominiety'):
            bramki_pominiete.append('sedzia')
            cechy['powod_pominiecia_sedziego'] = stan_sedziego.get('sedzia_pominiety_przyczyna', 'model')
        return {'typ': 'rezultat', 'dane': {'powod_odmowy': 'sedzia',
                                             'bramki_pominiete': bramki_pominiete, 'cechy': cechy,
                                             'wyniki': wyniki}}

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

    if not przepuszczone:
        werdykt_pozytywny = werdykt_sedziego(czekaj=True)
        if not werdykt_pozytywny:
            yield odmowa_sedziego(przerwano=False)
            return
        cechy['sedzia_ok'] = werdykt_pozytywny
        for zbuforowany in bufor:
            yield zbuforowany
    elif optymistycznie:
        werdykt_pozytywny = werdykt_sedziego(czekaj=True, limit=SEDZIA_CZEKANIE_KONCOWE)
        if not werdykt_pozytywny:
            yield odmowa_sedziego(przerwano=False, tokeny_wyslane=licznik_tokenow)
            return
        cechy['sedzia_ok'] = werdykt_pozytywny

    if werdykt is not None and stan_sedziego.get('sedzia_pominiety'):
        bramki_pominiete.append('sedzia')
        cechy['powod_pominiecia_sedziego'] = stan_sedziego.get('sedzia_pominiety_przyczyna', 'model')

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
                                                'bramki_pominiete': bramki_pominiete, 'cechy': cechy,
                                                'wyniki': wyniki}}
            return

    if not odpowiedz['cytaty'] and model_nie_wie(odpowiedz['tekst'], lang):
        yield {'typ': 'rezultat', 'dane': {'powod_odmowy': 'model_nie_wie',
                                            'bramki_pominiete': bramki_pominiete, 'cechy': cechy,
                                            'wyniki': wyniki}}
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
        'podpowiedzi': podpowiedzi.zbuduj(chunks, query, lang),
        'oferta': oferta,
        'oferta_kategoria': oferta_kategoria,
        'strona': strona_wybrana,
        'bramki_pominiete': bramki_pominiete,
        'cechy': cechy,
    })


def probuj_druga_sekcje(zapytanie_ret: str, query: str, history: list[dict],
                         bielik_model: str | None, sedzia: bool | None, lang: str, cfg: dict,
                         wynik_etapu: dict, tokeny_wyslane: bool, styl: str | None = None):
    wyniki = wynik_etapu.get('wyniki') or []
    strona_odrzucona = (wynik_etapu.get('cechy') or {}).get('strona_wybrana')
    druga_strona = next((s for s in strony.STRONY if s != strona_odrzucona), None)

    bramki_pominiete = []
    cechy = {'rerank_top1': None, 'chunkow': 0, 'zrodlo_top1': None,
             'sedzia_ok': None, 'pokrycie': None, 'etap': 2,
             'strona_wybrana': druga_strona, 'przewaga_sekcji': None}

    chunks = [para for para in wyniki
              if strony.strona_z_agenta(para[0]['agent']) == druga_strona][:K_CHUNKOW_SEKCJI]
    cechy['chunkow'] = len(chunks)
    if chunks:
        cechy['rerank_top1'] = round(float(chunks[0][1]), 4)
        cechy['zrodlo_top1'] = chunks[0][0]['url']

    def rezultat_odmowy(powod):
        return {'typ': 'rezultat', 'dane': {'powod_odmowy': powod,
                                            'bramki_pominiete': bramki_pominiete, 'cechy': cechy}}

    if not chunks or chunks[0][1] < cfg['prog_rerank']:
        yield rezultat_odmowy('druga_sekcja_prog')
        return

    agent_odp = chunks[0][0]['agent']

    if SEDZIA_ON if sedzia is None else sedzia:
        yield {'typ': 'krok', 'tekst': cfg['kroki']['sprawdzam_kontekst']}
        stan_sedziego = {}
        try:
            werdykt = bool(czy_kontekst_odpowiada(
                zapytanie_ret, chunks[:SEDZIA_CHUNKOW], None, lang, stan_sedziego))
        except Exception as e:
            print(f'sedzia drugiej sekcji zawiodl ({type(e).__name__}: {e}), przepuszczam dalej',
                  flush=True)
            werdykt = True
            stan_sedziego['sedzia_pominiety'] = True
        if stan_sedziego.get('sedzia_pominiety'):
            bramki_pominiete.append('sedzia')
            cechy['powod_pominiecia_sedziego'] = 'model'
        if not werdykt:
            cechy['sedzia_ok'] = False
            yield rezultat_odmowy('sedzia')
            return
        cechy['sedzia_ok'] = True

    etykieta_sekcji = cfg['nazwy_sekcji'].get(agent_odp, agent_odp)
    yield {'typ': 'krok', 'tekst': cfg['kroki']['generuje_odpowiedz'].format(agent=etykieta_sekcji)}

    if tokeny_wyslane:
        yield {'typ': 'reset'}

    odpowiedz = None
    for ev in answer_stream(query, agent_odp, chunks, bielik_model, history, lang, styl=styl):
        if ev['typ'] == 'token':
            yield ev
        elif ev['typ'] == 'koniec':
            odpowiedz = ev['dane']

    if odpowiedz is None:
        yield rezultat_odmowy('brak_generacji')
        return

    _, _, idf_ok = IDF_DANE[lang]
    if not idf_ok:
        bramki_pominiete.append('pokrycie')
    else:
        wartosc_pokrycia = pokrycie_idf(odpowiedz['tekst'], chunks, lang)
        cechy['pokrycie'] = round(float(wartosc_pokrycia), 4)
        if wartosc_pokrycia < cfg['prog_pokrycia']:
            yield rezultat_odmowy('pokrycie')
            return

    if not odpowiedz['cytaty'] and model_nie_wie(odpowiedz['tekst'], lang):
        yield rezultat_odmowy('model_nie_wie')
        return

    if jawna_odmowa_na_starcie(odpowiedz['tekst'], lang):
        yield rezultat_odmowy('jawna_odmowa')
        return

    oferta = None
    oferta_kategoria = None
    artykuly_maila = {kat['artykul'] for kat in cfg['mail_kategorie'].values()}
    if sygnal_maila(query, lang) or (chunks[0][0]['url'] and
                                      any(art in chunks[0][0]['url'] for art in artykuly_maila)):
        kategoria = sedzia_kategoria_mail(history + [{'role': 'user', 'content': query}], chunks, lang)
        if kategoria:
            oferta = cfg['mail_kategorie'][kategoria]['oferta']
            oferta_kategoria = kategoria

    zrodla = list(dict.fromkeys(c['url'] for c, _ in chunks))
    yield {'typ': 'rezultat', 'dane': {
        'powod_odmowy': None,
        'agent': agent_odp,
        'answer': odpowiedz['tekst'],
        'sources': zrodla,
        'citations': cytaty_lub_zrodla(odpowiedz['cytaty'], chunks),
        'podpowiedzi': podpowiedzi.zbuduj(chunks, query, lang),
        'oferta': oferta,
        'oferta_kategoria': oferta_kategoria,
        'strona': druga_strona,
        'bramki_pominiete': bramki_pominiete,
        'cechy': cechy,
    }}


def probuj_ogolna(query: str, history: list[dict], bielik_model: str | None,
                   lang: str, cfg: dict, powod_rag: str | None = None,
                   query_uzytkownika: str | None = None):
    cechy = {'ogolna_temat': None, 'ogolna_domena': False, 'ogolna_znakow': 0,
             'ogolna_konkrety': None}

    if powod_rag in POWODY_BLISKO_BAZY:
        cechy['ogolna_domena'] = True
        yield {'typ': 'rezultat', 'dane': {'powod_odmowy': 'ogolna_blisko_bazy',
                                            'answer': None, 'cechy': cechy}}
        return

    zablokowany = ogolna.temat_zablokowany(
        query if query_uzytkownika is None else query_uzytkownika, lang)
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
               lang:str='pl', strona:str | None=None, warstwa_ogolna:bool | None=None,
               etap2:bool | None=None):

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
    query_uzytkownika = query
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

    if (wynik_etapu['powod_odmowy'] in POWODY_DRUGA_PROBA
            and (ETAP2_ON if etap2 is None else etap2)):
        wynik_drugiej = None
        for ev in probuj_druga_sekcje(zapytanie_ret, query, history, bielik_model,
                                       sedzia, lang, cfg, wynik_etapu, wyslane_tokeny, styl=styl):
            if ev['typ'] == 'rezultat':
                wynik_drugiej = ev['dane']
            else:
                if ev['typ'] == 'reset':
                    wyslane_tokeny = False
                elif ev['typ'] == 'token':
                    wyslane_tokeny = True
                yield ev
        if wynik_drugiej is not None and not wynik_drugiej['powod_odmowy']:
            wynik_etapu = wynik_drugiej
        elif wynik_drugiej is not None:
            cechy_drugiej = wynik_drugiej.get('cechy') or {}
            cechy_etapu = wynik_etapu.setdefault('cechy', {})
            cechy_etapu['etap2_powod'] = wynik_drugiej['powod_odmowy']
            cechy_etapu['etap2_strona'] = cechy_drugiej.get('strona_wybrana')
            cechy_etapu['etap2_chunkow'] = cechy_drugiej.get('chunkow')
            cechy_etapu['etap2_rerank_top1'] = cechy_drugiej.get('rerank_top1')
            cechy_etapu['etap2_zrodlo_top1'] = cechy_drugiej.get('zrodlo_top1')
            cechy_etapu['etap2_sedzia_ok'] = cechy_drugiej.get('sedzia_ok')
            cechy_etapu['etap2_pokrycie'] = cechy_drugiej.get('pokrycie')
            pominiete_etapu = wynik_etapu.setdefault('bramki_pominiete', [])
            for bramka in wynik_drugiej.get('bramki_pominiete') or []:
                if bramka not in pominiete_etapu:
                    pominiete_etapu.append(bramka)

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
                                     wynik_etapu['powod_odmowy'],
                                     query_uzytkownika=query_uzytkownika):
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
                    'podpowiedzi': wynik_etapu.get('podpowiedzi') or [],
                    'tryb': 'rag'}
    dane_sukcesu['cechy'] = wynik_etapu.get('cechy')
    if bramki_pominiete:
        dane_sukcesu['bramki_pominiete'] = bramki_pominiete
    yield wynik(dane_sukcesu)


def run(query:str, bielik_model:str | None=None,
        history:list[dict] | None=None, agent_poprzedni:str | None=None,
        przepisz:bool=False, bez_korekty:bool=False, sedzia:bool | None=None,
        lang:str='pl', strona:str | None=None, warstwa_ogolna:bool | None=None,
        etap2:bool | None=None) -> dict:
    dane = {}
    for ev in run_stream(query, bielik_model, history,
                         agent_poprzedni, przepisz, bez_korekty, sedzia, lang, strona,
                         warstwa_ogolna, etap2):
        if ev['typ'] == 'wynik':
            dane = ev['dane']
    return dane
