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

WZORZEC = re.compile(r'[^\W\d_]+', re.UNICODE)


def polish_word(slowo: str) -> bool:
    return zipf_frequency(slowo, 'pl') >= PROG_PL


def tokenize_words(tekst: str) -> list[str]:
    return WZORZEC.findall(tekst.lower())


def fold(tekst: str) -> str:
    tekst = tekst.replace('ł', 'l')
    tekst = unicodedata.normalize('NFKD', tekst)
    return ''.join(z for z in tekst if not unicodedata.combining(z))


def distance(a: str, b: str) -> int:

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
def folded_index(slownik: Counter) -> list:
    global FOLDED_CACHE
    if FOLDED_CACHE is None:
        FOLDED_CACHE = [(slowo, czestosc, fold(slowo)) for slowo, czestosc in slownik.items()]
    return FOLDED_CACHE


def best_candidate(token: str, slownik: Counter) -> str | None:

    zlozony = fold(token)
    dozwolona = 1 if len(token) <= 6 else MAX_ODLEGLOSC
    najlepszy = None
    najlepsza_odleglosc = dozwolona + 1
    najlepsza_czestosc = 0

    for slowo, czestosc, zlozone in folded_index(slownik):
        if abs(len(zlozone) - len(zlozony)) > dozwolona:
            continue

        odleglosc = distance(zlozony, zlozone)
        if odleglosc < najlepsza_odleglosc or (
            odleglosc == najlepsza_odleglosc and czestosc > najlepsza_czestosc
        ):
            najlepszy = slowo
            najlepsza_odleglosc = odleglosc
            najlepsza_czestosc = czestosc

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


if __name__ == '__main__':
  
    slownik = build_dictionary()
    print(f'słownik: {len(slownik)} słów, zapisano do {SLOWNIK_PLIK}')

    testy = ['jak zmienić haslo do kotno', 'zaplacilem smrtem', 'gdzie jest przesylak']
    for zapytanie in testy:
        wynik = correct(zapytanie)
        print(f'\n"{zapytanie}"')
        print(f'  -> "{wynik["poprawione"]}"')
        print(f'  zmiany: {wynik["zmiany"]} | nieznane: {wynik["nieznane"]}')
