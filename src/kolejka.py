from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import secrets
import threading

KATALOG_RAG = Path(__file__).resolve().parent.parent / 'RAG'
PLIK_KOLEJKI = KATALOG_RAG / 'kolejka.jsonl'

POWODY_DO_CZLOWIEKA = ('prog_rerank', 'sedzia', 'pokrycie', 'model_nie_wie',
                       'jawna_odmowa', 'brak_generacji')
STATUSY = ('nowe', 'odpowiedziano', 'odrzucone')
ETYKIETY = ('luka_w_bazie', 'prog_za_wysoki', 'poza_zakresem', 'spam')

_zamek = threading.Lock()
_cache_kolejki: dict = {'stempel': None, 'wiersze': []}


def nowy_identyfikator() -> str:
    return secrets.token_hex(4).upper()


def dopisz_wiersz(wpis: dict) -> None:
    with _zamek:
        with open(PLIK_KOLEJKI, 'a', encoding='utf-8') as w:
            w.write(json.dumps(wpis, ensure_ascii=False) + '\n')


def zapisz_zgloszenie(id_zapytania: str, lang: str, strona: str, sekcja: str | None,
                      powod: str, pytanie: str, email: str) -> str:
    zgloszenie = nowy_identyfikator()
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
