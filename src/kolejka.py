from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import os
import secrets
import threading

KATALOG_RAG = Path(__file__).resolve().parent.parent / 'RAG'
PLIK_KOLEJKI = KATALOG_RAG / 'kolejka.jsonl'

POWODY_DO_CZLOWIEKA = ('prog_rerank', 'sedzia', 'pokrycie', 'model_nie_wie',
                       'jawna_odmowa', 'brak_generacji')
STATUSY = ('nowe', 'odpowiedziano', 'odrzucone')
ETYKIETY = ('luka_w_bazie', 'prog_za_wysoki', 'poza_zakresem', 'spam')
DNI_RETENCJI_EMAIL = int(os.getenv('DNI_RETENCJI_EMAIL', '30'))

_zamek = threading.Lock()
_cache_kolejki: dict = {'stempel': None, 'wiersze': []}


PROBY_IDENTYFIKATORA = 10


def nowy_identyfikator() -> str:
    return secrets.token_hex(6).upper()


def dopisz_wiersz(wpis: dict) -> None:
    with _zamek:
        with open(PLIK_KOLEJKI, 'a', encoding='utf-8') as w:
            w.write(json.dumps(wpis, ensure_ascii=False) + '\n')


def zapisz_zgloszenie(id_zapytania: str, lang: str, strona: str, sekcja: str | None,
                      powod: str, pytanie: str, email: str) -> str:
    istniejace = zloz_stan()
    zgloszenie = nowy_identyfikator()
    for _ in range(PROBY_IDENTYFIKATORA - 1):
        if zgloszenie not in istniejace:
            break
        zgloszenie = nowy_identyfikator()
    else:
        if zgloszenie in istniejace:
            raise RuntimeError('nie udalo sie wylosowac wolnego identyfikatora zgloszenia')
    dopisz_wiersz({
        'czas': datetime.now(timezone.utc).isoformat(),
        'typ': 'zgloszenie',
        'zgloszenie': zgloszenie,
        'id_zapytania': id_zapytania,
        'lang': lang,
        'strona': strona,
        'sekcja': sekcja,
        'powod': powod,
        'pytanie': pytanie,
        'email': email,
    })
    return zgloszenie


def zapisz_decyzje(zgloszenie: str, status: str, etykieta: str | None,
                   tresc: str, ticket: str | None) -> None:
    dopisz_wiersz({
        'czas': datetime.now(timezone.utc).isoformat(),
        'typ': 'decyzja',
        'zgloszenie': zgloszenie,
        'status': status,
        'etykieta': etykieta,
        'tresc': tresc,
        'ticket': ticket,
    })


def wczytaj_wiersze() -> list[dict]:
    try:
        stan = PLIK_KOLEJKI.stat()
    except OSError:
        return []
    stempel = (stan.st_mtime_ns, stan.st_size)
    with _zamek:
        if _cache_kolejki['stempel'] == stempel:
            return _cache_kolejki['wiersze']
    wiersze: list[dict] = []
    try:
        with open(PLIK_KOLEJKI, encoding='utf-8') as f:
            for linia in f:
                linia = linia.strip()
                if not linia:
                    continue
                try:
                    wiersze.append(json.loads(linia))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    with _zamek:
        _cache_kolejki['stempel'] = stempel
        _cache_kolejki['wiersze'] = wiersze
    return wiersze


def zloz_stan() -> dict[str, dict]:
    zgloszenia: dict[str, dict] = {}
    for wiersz in wczytaj_wiersze():
        typ = wiersz.get('typ')
        ident = wiersz.get('zgloszenie')
        if not ident:
            continue
        if typ == 'zgloszenie':
            zgloszenia[ident] = {
                'zgloszenie': ident,
                'czas': wiersz.get('czas'),
                'id_zapytania': wiersz.get('id_zapytania'),
                'lang': wiersz.get('lang'),
                'strona': wiersz.get('strona'),
                'sekcja': wiersz.get('sekcja'),
                'powod': wiersz.get('powod'),
                'pytanie': wiersz.get('pytanie'),
                'email': wiersz.get('email'),
                'status': 'nowe',
                'etykieta': None,
                'tresc': None,
                'ticket': None,
                'decyzja_czas': None,
            }
        elif typ == 'decyzja':
            biezace = zgloszenia.get(ident)
            if biezace is None:
                continue
            biezace['status'] = wiersz.get('status') or biezace['status']
            biezace['etykieta'] = wiersz.get('etykieta')
            biezace['tresc'] = wiersz.get('tresc')
            biezace['ticket'] = wiersz.get('ticket')
            biezace['decyzja_czas'] = wiersz.get('czas')
    return zgloszenia


def w_oknie_dni(czas: str | None, granica: datetime | None) -> bool:
    if granica is None:
        return True
    try:
        znacznik = datetime.fromisoformat(czas)
    except (TypeError, ValueError):
        return True
    if znacznik.tzinfo is None:
        znacznik = znacznik.replace(tzinfo=timezone.utc)
    return znacznik >= granica


def stan_kolejki(dni: int | None = None, status: str | None = None) -> list[dict]:
    granica = None
    if dni is not None:
        granica = datetime.now(timezone.utc) - timedelta(days=dni)
    wynik = [
        z for z in zloz_stan().values()
        if w_oknie_dni(z.get('czas'), granica) and (status is None or z['status'] == status)
    ]
    wynik.sort(key=lambda z: z.get('czas') or '', reverse=True)
    return wynik


def zgloszenie_po_id(zgloszenie: str) -> dict | None:
    return zloz_stan().get(zgloszenie)


def wyczysc_przeterminowane_adresy() -> int:
    with _zamek:
        try:
            with open(PLIK_KOLEJKI, encoding='utf-8') as f:
                linie = f.readlines()
        except FileNotFoundError:
            return 0
        surowe: list[tuple[str, dict | None]] = []
        decyzje_ident: set[str] = set()
        for linia in linie:
            surowa = linia.rstrip('\n')
            if not surowa.strip():
                surowe.append((surowa, None))
                continue
            try:
                dane = json.loads(surowa)
            except json.JSONDecodeError:
                surowe.append((surowa, None))
                continue
            surowe.append((surowa, dane))
            if dane.get('typ') == 'decyzja' and dane.get('zgloszenie'):
                decyzje_ident.add(dane['zgloszenie'])
        granica = datetime.now(timezone.utc) - timedelta(days=DNI_RETENCJI_EMAIL)
        wyczyszczone = 0
        nowe_linie: list[str] = []
        for surowa, dane in surowe:
            if dane is None:
                nowe_linie.append(surowa)
                continue
            if (dane.get('typ') == 'zgloszenie' and dane.get('email') is not None
                    and (dane.get('zgloszenie') in decyzje_ident
                         or not w_oknie_dni(dane.get('czas'), granica))):
                dane['email'] = None
                wyczyszczone += 1
            nowe_linie.append(json.dumps(dane, ensure_ascii=False))
        if wyczyszczone == 0:
            return 0
        tymczasowy = PLIK_KOLEJKI.with_name(PLIK_KOLEJKI.name + '.tmp')
        with open(tymczasowy, 'w', encoding='utf-8') as w:
            for linia in nowe_linie:
                w.write(linia + '\n')
        os.replace(tymczasowy, PLIK_KOLEJKI)
        _cache_kolejki['stempel'] = None
        _cache_kolejki['wiersze'] = []
        return wyczyszczone
