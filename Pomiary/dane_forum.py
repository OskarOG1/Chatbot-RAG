# Modul wspolny dla PLAN_KLASYFIKATOR_FORUM.md. Jedyne miejsce, ktore czyta
# RAG/pytania_realne.jsonl i liczy embeddingi. Zaden skrypt z tego planu nie robi
# tego samodzielnie, bo trzy kroki (2, 4, 5) potrzebuja tych samych wektorow i bez
# wspolnego cache liczylyby je trzy razy.
#
# Dwie rzeczy sa tu DELEGOWANE, nie skopiowane, i to jest celowe:
#   fold()          -> measure_routing_strony.wycinek_pytania (ten sam podzial co PLAN_WAGI_STRON.md)
#   lematy_pytania()-> pipeline.lematy (ta sama tokenizacja co przyszly runtime)
# Skopiowana logika rozjechalaby sie po pierwszej zmianie po drugiej stronie, a wtedy
# uczenie i produkcja liczylyby cos innego, nie wiedzac o tym.
#
# NIE uzywamy rankings.tokenizacja: ona dokleja trigramy znakowe na potrzeby BM25,
# co tutaj tylko zaszumiloby tablice wag.
#
# NIE importujemy zbierz_pytania: adresy boardow docelowo trafiaja do src/wagi_forum.py,
# a src/ nie moze zalezec od Pomiary/. Dlatego BOARD_DO_URL jest przepisane recznie
# (zrodlo: BOARDS w Pomiary/zbierz_pytania.py:75 sklejone z BASE_URL).

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import faiss  # noqa: E402
from lang_config import LANG  # noqa: E402
from pipeline import lematy  # noqa: E402

RAG_DIR = ROOT / 'RAG'
OUT_DIR = ROOT / 'outputs'
PLIK = RAG_DIR / 'pytania_realne.jsonl'
BATCH_SIZE = 16
JEZYK = 'pl'

CACHE_WEKTORY = OUT_DIR / 'embeddingi_forum.npy'
CACHE_KLUCZ = OUT_DIR / 'embeddingi_forum_klucz.json'

BASE_URL = 'https://spolecznosc.allegro.pl'

# 14 boardow, ktore faktycznie dostarczyly watki. 'wazne-informacje' z BOARDS dal 0 watkow
# i tu go nie ma. Wartosc to pelny adres listingu.
BOARD_DO_URL = {
    'Sprzedajacy1': f'{BASE_URL}/t5/pocz%C4%85tkuj%C4%85cy-sprzedawcy/bd-p/Sprzedajacy1',
    'Sprzedajacy2': f'{BASE_URL}/t5/zaawansowani-sprzedawcy/bd-p/Sprzedajacy2',
    'Smart-sprzedajacy': f'{BASE_URL}/t5/smart-dla-sprzedawc%C3%B3w/bd-p/Smart-sprzedajacy',
    'Sprzedajacy_o_Allegro_Lokalnie': f'{BASE_URL}/t5/sprzedaj%C4%85cy-o-allegro-lokalnie/bd-p/Sprzedajacy_o_Allegro_Lokalnie',
    'allegro-one': f'{BASE_URL}/t5/allegro-one-dla-sprzedawc%C3%B3w/bd-p/allegro-one',
    'WOSP-sprzedajacy': f'{BASE_URL}/t5/wo%C5%9Bp-dla-wystawiaj%C4%85cych/bd-p/WOSP-sprzedajacy',
    'Kupujacy1': f'{BASE_URL}/t5/dyskusje-kupuj%C4%85cych/bd-p/Kupujacy1',
    'Smart-kupujacy': f'{BASE_URL}/t5/smart-dla-kupuj%C4%85cych/bd-p/Smart-kupujacy',
    'Kupujacy_o_Allegro_Lokalnie': f'{BASE_URL}/t5/kupuj%C4%85cy-o-allegro-lokalnie/bd-p/Kupujacy_o_Allegro_Lokalnie',
    'allegro-one-kupujacy': f'{BASE_URL}/t5/allegro-one-dla-kupuj%C4%85cych/bd-p/allegro-one-kupujacy',
    'WOSP-kupujacy': f'{BASE_URL}/t5/wo%C5%9Bp-dla-licytuj%C4%85cych/bd-p/WOSP-kupujacy',
    'allegro-pay': f'{BASE_URL}/t5/allegro-pay/bd-p/allegro-pay',
    'katalog-produktow': f'{BASE_URL}/t5/katalog-produkt%C3%B3w/bd-p/katalog-produktow',
    'allegro-delivery': f'{BASE_URL}/t5/allegro-delivery/bd-p/allegro-delivery',
}

# Strona pytania wg etykiety boardu (BOARDS w zbierz_pytania.py). None = board mieszany.
# Potrzebne dla punktu odniesienia "wiekszosc w obrebie strony" w kroku 4.
BOARD_DO_STRONY = {
    'Sprzedajacy1': 'sprzedaz',
    'Sprzedajacy2': 'sprzedaz',
    'Smart-sprzedajacy': 'sprzedaz',
    'Sprzedajacy_o_Allegro_Lokalnie': 'sprzedaz',
    'allegro-one': 'sprzedaz',
    'WOSP-sprzedajacy': 'sprzedaz',
    'Kupujacy1': 'kupujacy',
    'Smart-kupujacy': 'kupujacy',
    'Kupujacy_o_Allegro_Lokalnie': 'kupujacy',
    'allegro-one-kupujacy': 'kupujacy',
    'WOSP-kupujacy': 'kupujacy',
    'allegro-pay': None,
    'katalog-produktow': None,
    'allegro-delivery': None,
}

# TAKSONOMIA: board -> klasa. Na starcie byla tozsamoscia, zeby krok 2 mierzyl surowe
# boardy, a nie nasze wyobrazenie o nich. To jest jedyne miejsce, gdzie taksonomia zyje.
#
# Stan: po kroku 2 (measure_separowalnosc_boardow.py, przebieg 2026-08-07).
# Wpisane recznie po obejrzeniu macierzy pomylek, nie przepisane z jednego progu sklejania.
# Podstawa, wszystko z outputs/separowalnosc_boardow.json:
#
#  1. Os STRONY jest niewidoczna wewnatrz tematu. Cztery pary "ten sam temat, inna strona"
#     zajmuja czolowke listy najbardziej mylonych: lokalnie 0.157, one 0.132, WOSP 0.122,
#     smart 0.120. Dlatego kazdy temat jest JEDNA klasa, bez rozbicia na strony. Strone
#     i tak daje istniejacy routing (strony.prior_strony), wiec te dwa systemy sie skladaja.
#     Kandydat z planu ({sprzedaz, kupujacy} x {one, smart, lokalnie, ogolne}) zaklada
#     rozbicie, ktorego dane nie potwierdzaja.
#  2. Boardy OGOLNE nie maja tozsamosci tematycznej: Sprzedajacy2 x1.05 losu (czyli
#     dokladnie tyle, ile wynika z jego rozmiaru), Sprzedajacy1 x1.29. Ich sklejenie to
#     wniosek z danych, nie uproszczenie. Kupujacy1 (x1.55) zostaje osobno, bo scalenie
#     go ze sprzedazowymi skasowaloby jedyna os, ktora system juz umie rozstrzygac.
#  3. Boardy TEMATYCZNE trzymaja sie mocno i zostaja: pay x4.70, katalog x4.60,
#     one/delivery x2.6 do x3.0, lokalnie x2.4 do x3.4, smart x2.0 do x2.6, WOSP x5.4.
#  4. allegro-one, allegro-one-kupujacy i allegro-delivery scalone w 'dostawa': trzy pary
#     miedzy nimi sa w pierwszej czworce mylonych (0.155, 0.150, 0.132).
#
# Osiem klas, w bramce planu (4 do 8).
TAKSONOMIA = {
    'Sprzedajacy1': 'sprzedaz_ogolne',
    'Sprzedajacy2': 'sprzedaz_ogolne',
    'Kupujacy1': 'kupujacy_ogolne',
    'Smart-sprzedajacy': 'smart',
    'Smart-kupujacy': 'smart',
    'Sprzedajacy_o_Allegro_Lokalnie': 'lokalnie',
    'Kupujacy_o_Allegro_Lokalnie': 'lokalnie',
    'allegro-one': 'dostawa',
    'allegro-one-kupujacy': 'dostawa',
    'allegro-delivery': 'dostawa',
    'allegro-pay': 'pay',
    'katalog-produktow': 'katalog',
    'WOSP-sprzedajacy': 'wosp',
    'WOSP-kupujacy': 'wosp',
}

# Klasa -> adres listingu boardu reprezentanta, czyli najliczniejszego boardu w klasie.
KLASA_DO_URL = {
    'sprzedaz_ogolne': BOARD_DO_URL['Sprzedajacy2'],
    'kupujacy_ogolne': BOARD_DO_URL['Kupujacy1'],
    'smart': BOARD_DO_URL['Smart-sprzedajacy'],
    'lokalnie': BOARD_DO_URL['Sprzedajacy_o_Allegro_Lokalnie'],
    'dostawa': BOARD_DO_URL['allegro-one'],
    'pay': BOARD_DO_URL['allegro-pay'],
    'katalog': BOARD_DO_URL['katalog-produktow'],
    'wosp': BOARD_DO_URL['WOSP-sprzedajacy'],
}

PAMIEC: dict = {}


def model():
    """SentenceTransformer ladowany leniwie: inwentarz (krok 1) go nie potrzebuje,
    a wczytanie mmlw kosztuje kilkanascie sekund."""
    if 'model' not in PAMIEC:
        from sentence_transformers import SentenceTransformer
        PAMIEC['model'] = SentenceTransformer(LANG[JEZYK]['embedder'])
    return PAMIEC['model']


def wczytaj_surowe() -> list[dict]:
    """Wszystkie rekordy pliku, bez zadnego filtra. Potrzebne wylacznie inwentarzowi
    (krok 1): bramka "board niepusty" liczona na juz przefiltrowanym zbiorze wyszlaby
    1,0 z definicji i nie sprawdzalaby niczego."""
    with open(PLIK, encoding='utf-8') as f:
        return [json.loads(linia) for linia in f]


def wczytaj(zrodla: tuple[str, ...] = ('forum',)) -> list[dict]:
    """Rekordy w kolejnosci z pliku, zeby indeksy byly stabilne miedzy skryptami
    (wektory sa cache'owane po tej samej kolejnosci). Przy zrodle 'forum' pomija
    rekordy z pustym board, bo bez etykiety nie ma czego uczyc ani mierzyc."""
    rekordy = []
    with open(PLIK, encoding='utf-8') as f:
        for linia in f:
            w = json.loads(linia)
            if w.get('zrodlo') not in zrodla:
                continue
            if w.get('zrodlo') == 'forum' and not w.get('board'):
                continue
            rekordy.append(w)
    return rekordy


def fold(pytanie: str) -> str:
    """Deleguje do measure_routing_strony.wycinek_pytania (sha1 z guards.normalizuj
    modulo 100). Import jest leniwy, bo measure_routing_strony ciagnie za soba caly
    stack pomiarowy (kilkanascie sekund), a nie kazdy skrypt potrzebuje foldow."""
    if 'wycinek' not in PAMIEC:
        from measure_routing_strony import wycinek_pytania
        PAMIEC['wycinek'] = wycinek_pytania
    return PAMIEC['wycinek'](pytanie)


def klasa(board: str | None) -> str | None:
    return TAKSONOMIA.get(board) if board else None


def strona(board: str | None) -> str | None:
    return BOARD_DO_STRONY.get(board) if board else None


def lematy_pytania(pytanie: str) -> set[str]:
    """Deleguje do pipeline.lematy: tokenize_words + simplemma + MIN_DLUGOSC.
    Uczenie i przyszly runtime musza wolac dokladnie te sama funkcje."""
    return lematy(pytanie, JEZYK)


def odcisk(pytania: list[str]) -> dict:
    tresc = '\n'.join(pytania).encode('utf-8')
    return {
        'sha256': hashlib.sha256(tresc).hexdigest(),
        'model': LANG[JEZYK]['embedder'],
        'n': len(pytania),
    }


def embeddingi(pytania: list[str]) -> np.ndarray:
    """Wektory znormalizowane L2 (czyli iloczyn skalarny = cosinus). Cache w outputs/
    trzymany razem z odciskiem wejscia; niezgodnosc odcisku to przeliczenie od nowa,
    nie ostrzezenie, zeby nie dalo sie po cichu zmierzyc czegos innego niz dane."""
    klucz = odcisk(pytania)
    if CACHE_WEKTORY.exists() and CACHE_KLUCZ.exists():
        with open(CACHE_KLUCZ, encoding='utf-8') as f:
            if json.load(f) == klucz:
                return np.load(CACHE_WEKTORY)

    prefiks = LANG[JEZYK]['query_prefix']
    wektory = model().encode(
        [prefiks + p for p in pytania],
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
    ).astype('float32')
    faiss.normalize_L2(wektory)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    np.save(CACHE_WEKTORY, wektory)
    with open(CACHE_KLUCZ, 'w', encoding='utf-8') as f:
        json.dump(klucz, f, ensure_ascii=False, indent=1)
    return wektory


def indeks_podzbioru(wektory: np.ndarray, maska: np.ndarray) -> tuple:
    """(indeks FAISS, mapowanie pozycji lokalnej na globalna). Mapowanie jest
    konieczne, bo FAISS zwraca numery wierszy w podzbiorze, a wolajacy mysli
    numerami z pelnej listy rekordow."""
    mapowanie = np.flatnonzero(maska).astype('int64')
    indeks = faiss.IndexFlatIP(wektory.shape[1])
    if mapowanie.size:
        indeks.add(np.ascontiguousarray(wektory[mapowanie]))
    return indeks, mapowanie


def indeks_bez_foldu(wektory: np.ndarray, foldy: list[str], pominiety: str) -> tuple:
    maska = np.array([f != pominiety for f in foldy])
    return indeks_podzbioru(wektory, maska)


def sasiedzi_i_podobienstwa(wektory: np.ndarray, foldy: list[str], k: int) -> tuple[list, list]:
    """Trzy indeksy, kazdy bez jednego foldu. Pytanie z foldu F szuka w indeksie
    zbudowanym bez F. To jest jedyny uczciwy sposob: indeks zawierajacy wlasne pytanie
    zwroci je samo z cosinusem 1,0 i zawyzy kazda metryke ponizej.
    Zwraca (indeksy globalne, podobienstwa)."""
    n = len(foldy)
    sasiedzi: list[list[int]] = [[] for _ in range(n)]
    podobienstwa: list[list[float]] = [[] for _ in range(n)]

    for f in sorted(set(foldy)):
        indeks, mapowanie = indeks_bez_foldu(wektory, foldy, f)
        pozycje = np.flatnonzero(np.array([g == f for g in foldy]))
        if not pozycje.size or not mapowanie.size:
            continue
        wyniki, trafienia = indeks.search(np.ascontiguousarray(wektory[pozycje]), k)
        for wiersz, poz in enumerate(pozycje):
            sasiedzi[poz] = [int(mapowanie[j]) for j in trafienia[wiersz] if j >= 0]
            podobienstwa[poz] = [float(d) for d, j in zip(wyniki[wiersz], trafienia[wiersz]) if j >= 0]

    return sasiedzi, podobienstwa


def sasiedzi_spoza_foldu(wektory: np.ndarray, foldy: list[str], k: int) -> list[list[int]]:
    return sasiedzi_i_podobienstwa(wektory, foldy, k)[0]
