import json
import re
import pickle
import unicodedata
from pathlib import Path
from collections import Counter
from wordfreq import zipf_frequency

ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'
SLOWNIK_PLIK = RAG_DIR / 'slownik.pkl'
CHUNKS_JSON = RAG_DIR / 'chunks.json'

MIN_DLUGOSC = 4
MIN_CZESTOSC = 1
MAX_ODLEGLOSC = 2
PROG_PL = 2.0
MIN_TOKENY_DETEKCJI = 2

WZORZEC = re.compile(r'[^\W\d_]+', re.UNICODE)


def polish_word(slowo: str) -> bool:
    return zipf_frequency(slowo, 'pl') >= PROG_PL


def tokenize_words(tekst: str) -> list[str]:
    return WZORZEC.findall(tekst.lower())


def detect_lang(query: str) -> str | None:
    tokeny = [t for t in tokenize_words(query) if len(t) >= MIN_DLUGOSC]
    if len(tokeny) < MIN_TOKENY_DETEKCJI:
        return None

    pl_suma = sum(zipf_frequency(t, 'pl') for t in tokeny)
    en_suma = sum(zipf_frequency(t, 'en') for t in tokeny)

    if pl_suma == en_suma:
        return None
    return 'pl' if pl_suma > en_suma else 'en'


def fold(tekst: str) -> str:
    tekst = tekst.replace('ł', 'l')
    tekst = unicodedata.normalize('NFKD', tekst)
    return ''.join(z for z in tekst if not unicodedata.combining(z))


def distance(a: str, b: str, dozwolona: int | None = None) -> int:

    dl_a, dl_b = len(a), len(b)
    macierz = [[0] * (dl_b + 1) for _ in range(dl_a + 1)]

    for i in range(dl_a + 1):
        macierz[i][0] = i
    for j in range(dl_b + 1):
        macierz[0][j] = j

    for i in range(1, dl_a + 1):
        for j in range(1, dl_b + 1):
            koszt = 0 if a[i - 1] == b[j - 1] else 1
            macierz[i][j] = min(
                macierz[i - 1][j] + 1,
                macierz[i][j - 1] + 1,
                macierz[i - 1][j - 1] + koszt,
            )
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                macierz[i][j] = min(macierz[i][j], macierz[i - 2][j - 2] + 1)
        if dozwolona is not None and min(macierz[i]) > dozwolona + (dl_a - i):
            return dozwolona + 1

    return macierz[dl_a][dl_b]


def stempel_korpusu() -> int | None:
    try:
        return int(CHUNKS_JSON.stat().st_mtime)
    except OSError:
        return None


def build_dictionary(chunki: list[dict] | None = None) -> Counter:
    if chunki is None:
        with open(CHUNKS_JSON, 'r', encoding='utf-8') as r:
            chunki = json.load(r)

    licznik = Counter()
    for chunk in chunki:
        tekst = f"{chunk.get('tytul', '')}\n{chunk.get('tekst', '')}"
        licznik.update(tokenize_words(tekst))

    slownik = Counter({
        slowo: liczba
        for slowo, liczba in licznik.items()
        if len(slowo) >= MIN_DLUGOSC and liczba >= MIN_CZESTOSC
    })

    try:
        with open(SLOWNIK_PLIK, 'wb') as w:
            pickle.dump({'stamp': stempel_korpusu(), 'slownik': slownik}, w)
    except OSError:
        pass

    global FOLDED_CACHE
    FOLDED_CACHE = None
    return slownik


SLOWNIK_CACHE = None
def load_dictionary() -> Counter:
    global SLOWNIK_CACHE
    if SLOWNIK_CACHE is not None:
        return SLOWNIK_CACHE

    if SLOWNIK_PLIK.exists():
        try:
            with open(SLOWNIK_PLIK, 'rb') as r:
                zapis = pickle.load(r)
            if isinstance(zapis, dict) and zapis.get('stamp') == stempel_korpusu():
                SLOWNIK_CACHE = zapis['slownik']
                return SLOWNIK_CACHE
        except (OSError, pickle.UnpicklingError, KeyError):
            pass

    SLOWNIK_CACHE = build_dictionary()
    return SLOWNIK_CACHE


FOLDED_CACHE = None
def folded_index(slownik: Counter) -> dict[int, list[tuple[str, int, str, int]]]:
    global FOLDED_CACHE
    if FOLDED_CACHE is None:
        kubelki: dict[int, list[tuple[str, int, str, int]]] = {}
        for indeks, (slowo, czestosc) in enumerate(slownik.items()):
            zlozone = fold(slowo)
            kubelki.setdefault(len(zlozone), []).append((slowo, czestosc, zlozone, indeks))
        FOLDED_CACHE = kubelki
    return FOLDED_CACHE


def best_candidate(token: str, slownik: Counter) -> str | None:

    zlozony = fold(token)
    dlugosc = len(zlozony)
    dozwolona = 1 if len(token) <= 6 else MAX_ODLEGLOSC
    najlepszy = None
    najlepsza_odleglosc = dozwolona + 1
    najlepsza_czestosc = 0
    najlepszy_indeks = -1

    kubelki = folded_index(slownik)
    for dlugosc_kubelka in range(dlugosc - dozwolona, dlugosc + dozwolona + 1):
        for slowo, czestosc, zlozone, indeks in kubelki.get(dlugosc_kubelka, []):
            odleglosc = distance(zlozony, zlozone, dozwolona)
            if (odleglosc < najlepsza_odleglosc
                    or (odleglosc == najlepsza_odleglosc and czestosc > najlepsza_czestosc)
                    or (odleglosc == najlepsza_odleglosc and czestosc == najlepsza_czestosc
                        and najlepszy is not None and indeks < najlepszy_indeks)):
                najlepszy = slowo
                najlepsza_odleglosc = odleglosc
                najlepsza_czestosc = czestosc
                najlepszy_indeks = indeks

    if najlepszy is not None and najlepsza_odleglosc <= dozwolona:
        return najlepszy
    return None


def correct(query: str) -> dict:
    
    slownik = load_dictionary()
    zmiany = []
    nieznane = []

    def replace(dopasowanie):
        token = dopasowanie.group(0)
        maly = token.lower()

        if len(maly) < MIN_DLUGOSC or maly in slownik:
            return token

        if polish_word(maly):
            return token

        kandydat = best_candidate(maly, slownik)
        if kandydat is not None and kandydat != maly:
            zmiany.append((token, kandydat))
            return kandydat
        
        nieznane.append(token)
        return token

    poprawione = WZORZEC.sub(replace, query)
    return {
        'poprawione': poprawione,
        'zmieniono': bool(zmiany),
        'zmiany': zmiany,
        'nieznane': nieznane,
    }
