from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import json
import os

LOG_ANALYTICS = Path(__file__).resolve().parent.parent / 'RAG' / 'log_analytics.jsonl'

KOLUMNY_EKSPORTU = ('czas', 'lang', 'strona', 'sekcja', 'wynik', 'powod', 'powod_etap2',
                    'latencja_s', 'cache_hit', 'pytanie', 'tokeny_we', 'tokeny_wy', 'koszt_usd')
KOLUMNY_DOMYSLNE = ('czas', 'lang', 'strona', 'sekcja', 'wynik', 'powod', 'latencja_s', 'cache_hit')
PROGI_LATENCJI = (2.0, 5.0, 10.0, 20.0)
ETYKIETY_LATENCJI = ('0 do 2 s', '2 do 5 s', '5 do 10 s', '10 do 20 s', 'ponad 20 s')
STRONY = ('kupujacy', 'sprzedajacy')
TOP_PYTAN = 15
MAX_DNI_SERII = int(os.getenv('MAX_DNI_SERII', '400'))
ZNAKI_FORMULY = ('=', '+', '-', '@', '\t', '\r')


def formatuj_czas_eksportu(wartosc):
    if not isinstance(wartosc, str):
        return wartosc
    try:
        czas = datetime.fromisoformat(wartosc)
    except ValueError:
        return wartosc
    return czas.strftime('%Y-%m-%d %H:%M:%S')


def komorka_eksportu(wpis: dict, kolumna: str):
    if kolumna == 'czas':
        return formatuj_czas_eksportu(wpis.get('czas'))
    if kolumna == 'strona':
        return normalizuj_strone(wpis.get('strona'))
    return wpis.get(kolumna)


def bezpieczna_komorka(wartosc):
    if wartosc is None:
        return ''
    if isinstance(wartosc, str) and wartosc.startswith(ZNAKI_FORMULY):
        return "'" + wartosc
    return wartosc


def wczytaj(sciezka=None) -> list[dict]:
    sciezka = Path(sciezka) if sciezka else LOG_ANALYTICS
    wpisy = []
    try:
        with open(sciezka, encoding='utf-8') as r:
            for linia in r:
                linia = linia.strip()
                if not linia:
                    continue
                try:
                    wpisy.append(json.loads(linia))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return wpisy


def czas_wpisu(wpis: dict):
    try:
        czas = datetime.fromisoformat(wpis.get('czas') or '')
    except (TypeError, ValueError):
        return None
    return czas if czas.tzinfo else czas.replace(tzinfo=timezone.utc)


def dzien_wpisu(wpis: dict) -> str | None:
    surowy = wpis.get('czas')
    if not isinstance(surowy, str):
        return None
    try:
        return date.fromisoformat(surowy[:10]).isoformat()
    except ValueError:
        return None


def normalizuj_strone(wartosc) -> str:
    return wartosc if wartosc in STRONY else 'nieznana'


def filtruj(wpisy: list[dict], dni: int | None = None, lang: str | None = None,
            strona: str | None = None) -> list[dict]:
    granica = datetime.now(timezone.utc) - timedelta(days=dni) if dni else None
    wynik = []
    for w in wpisy:
        if lang and w.get('lang') != lang:
            continue
        if strona and w.get('typ') != 'wysylka' and normalizuj_strone(w.get('strona')) != strona:
            continue
        if granica is not None:
            czas = czas_wpisu(w)
            if czas is None or czas < granica:
                continue
        wynik.append(w)
    return wynik


def kwantyl(posortowane: list[float], q: float) -> float:
    if not posortowane:
        return 0.0
    if len(posortowane) == 1:
        return float(posortowane[0])
    pozycja = q * (len(posortowane) - 1)
    dol = int(pozycja)
    gora = min(dol + 1, len(posortowane) - 1)
    reszta = pozycja - dol
    return float(posortowane[dol] * (1 - reszta) + posortowane[gora] * reszta)


def rozklad(licznik: Counter, nazwa: str, mianownik: int) -> list[dict]:
    return [{nazwa: klucz, 'ile': ile,
             'udzial': round(ile / mianownik, 4) if mianownik else 0.0}
            for klucz, ile in licznik.most_common()]


def histogram_latencji(wartosci: list[float]) -> list[dict]:
    kubelki = [0] * len(ETYKIETY_LATENCJI)
    for wartosc in wartosci:
        for i, prog in enumerate(PROGI_LATENCJI):
            if wartosc < prog:
                kubelki[i] += 1
                break
        else:
            kubelki[-1] += 1
    return [{'zakres': etykieta, 'ile': ile}
            for etykieta, ile in zip(ETYKIETY_LATENCJI, kubelki)]


def dni_zakresu(pierwszy: str, ostatni: str, limit: int = MAX_DNI_SERII) -> list[str]:
    start = date.fromisoformat(pierwszy)
    koniec = date.fromisoformat(ostatni)
    if (koniec - start).days >= limit:
        start = koniec - timedelta(days=limit - 1)
    dni = []
    while start <= koniec:
        dni.append(start.isoformat())
        start += timedelta(days=1)
    return dni


def liczba(wartosc) -> bool:
    return isinstance(wartosc, (int, float)) and not isinstance(wartosc, bool)


def statystyki(wpisy: list[dict]) -> dict:
    zapytania = [w for w in wpisy if not w.get('typ')]
    wysylki = [w for w in wpisy if w.get('typ') == 'wysylka']
    oceny = [w for w in wpisy if w.get('typ') == 'ocena']

    odpowiedzi = [w for w in zapytania if w.get('wynik') == 'odpowiedz']
    odmowy = [w for w in zapytania if w.get('wynik') == 'odmowa']
    rozmowy = [w for w in zapytania if w.get('wynik') == 'rozmowa']
    pytania_rag = len(odpowiedzi) + len(odmowy)
    n = len(zapytania)

    latencje = sorted(float(w['latencja_s']) for w in zapytania if liczba(w.get('latencja_s')))
    lat_cache = sorted(float(w['latencja_s']) for w in zapytania
                       if w.get('cache_hit') and liczba(w.get('latencja_s')))
    lat_bez = sorted(float(w['latencja_s']) for w in zapytania
                     if not w.get('cache_hit') and liczba(w.get('latencja_s')))

    pytania = {}
    for w in zapytania:
        tekst = (w.get('pytanie') or '').strip()
        if not tekst:
            continue
        pozycja = pytania.setdefault(tekst.lower(), {'pytanie': tekst, 'ile': 0})
        pozycja['ile'] += 1
    top = sorted(pytania.values(), key=lambda p: -p['ile'])[:TOP_PYTAN]

    dni = {}
    for w in zapytania:
        dzien = dzien_wpisu(w)
        if dzien is None:
            continue
        pozycja = dni.setdefault(dzien, {'zapytan': 0, 'odmowy': 0, 'latencje': [], 'koszt_usd': 0.0})
        pozycja['zapytan'] += 1
        if w.get('wynik') == 'odmowa':
            pozycja['odmowy'] += 1
        if liczba(w.get('latencja_s')):
            pozycja['latencje'].append(float(w['latencja_s']))
        pozycja['koszt_usd'] += float(w.get('koszt_usd') or 0.0)

    seria = []
    obciete = False
    if dni:
        okno = dni_zakresu(min(dni), max(dni))
        obciete = (date.fromisoformat(max(dni)) - date.fromisoformat(min(dni))).days + 1 > len(okno)
        for dzien in okno:
            pozycja = dni.get(dzien)
            if pozycja is None:
                seria.append({'dzien': dzien, 'zapytan': 0, 'odmowy': 0,
                              'mediana_latencji': 0.0, 'koszt_usd': 0.0})
            else:
                seria.append({'dzien': dzien, 'zapytan': pozycja['zapytan'],
                              'odmowy': pozycja['odmowy'],
                              'mediana_latencji': round(kwantyl(sorted(pozycja['latencje']), 0.5), 3),
                              'koszt_usd': round(pozycja['koszt_usd'], 6)})

    gora = sum(1 for w in oceny if w.get('ocena') == 'gora')
    dol = sum(1 for w in oceny if w.get('ocena') == 'dol')
    razem_ocen = gora + dol

    bez_cache = [w for w in zapytania if not w.get('cache_hit')]
    z_tokenami = [w for w in bez_cache if w.get('tokeny_we') is not None]
    szacowane = sum(1 for w in z_tokenami if w.get('tokeny_szacowane'))
    koszt = sum(float(w.get('koszt_usd') or 0.0) for w in z_tokenami)
    czasy = [w['czas'] for w in wpisy if isinstance(w.get('czas'), str)]

    return {
        'zakres': {'od': min(czasy) if czasy else None,
                   'do': max(czasy) if czasy else None,
                   'dni': len(seria),
                   'obciete': obciete},
        'ogolem': {
            'zapytan': n,
            'odpowiedzi': len(odpowiedzi),
            'odmowy': len(odmowy),
            'rozmowy': len(rozmowy),
            'trafnosc': round(len(odpowiedzi) / pytania_rag, 4) if pytania_rag else None,
            'cache_hit': round(sum(1 for w in zapytania if w.get('cache_hit')) / n, 4) if n else 0.0,
            'unikalne_pytania': len(pytania),
            'wysylki': len(wysylki),
            'wysylki_ok': sum(1 for w in wysylki if w.get('sukces')),
        },
        'latencja': {
            'mediana': round(kwantyl(latencje, 0.5), 3),
            'p90': round(kwantyl(latencje, 0.9), 3),
            'p95': round(kwantyl(latencje, 0.95), 3),
            'srednia': round(sum(latencje) / len(latencje), 3) if latencje else 0.0,
            'mediana_cache': round(kwantyl(lat_cache, 0.5), 3),
            'mediana_bez_cache': round(kwantyl(lat_bez, 0.5), 3),
            'histogram': histogram_latencji(latencje),
        },
        'sekcje': rozklad(Counter(w['sekcja'] for w in odpowiedzi if w.get('sekcja')),
                          'sekcja', len(odpowiedzi)),
        'strony': rozklad(Counter(normalizuj_strone(w.get('strona')) for w in zapytania),
                          'strona', n),
        'powody': rozklad(Counter(w.get('powod') or 'brak_danych' for w in odmowy),
                          'powod', len(odmowy)),
        'jezyki': rozklad(Counter(w.get('lang') or 'nieznany' for w in zapytania), 'lang', n),
        'dzienne': seria,
        'top_pytania': top,
        'kolumny': {'wszystkie': list(KOLUMNY_EKSPORTU), 'domyslne': list(KOLUMNY_DOMYSLNE)},
        'oceny': {
            'gora': gora,
            'dol': dol,
            'razem': razem_ocen,
            'trafnosc': round(gora / razem_ocen, 4) if razem_ocen else None,
            'pokrycie': round(razem_ocen / len(odpowiedzi), 4) if odpowiedzi else 0.0,
        },
        'koszty': {
            'tokeny_we': sum(int(w.get('tokeny_we') or 0) for w in z_tokenami),
            'tokeny_wy': sum(int(w.get('tokeny_wy') or 0) for w in z_tokenami),
            'koszt_usd': round(koszt, 6),
            'koszt_na_zapytanie': round(koszt / len(z_tokenami), 6) if z_tokenami else 0.0,
            'pokrycie': round(len(z_tokenami) / len(bez_cache), 4) if bez_cache else 0.0,
            'szacowane': szacowane,
            'udzial_szacowanych': round(szacowane / len(z_tokenami), 4) if z_tokenami else 0.0,
        },
    }
