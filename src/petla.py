import argparse
import json
import sys
from pathlib import Path

import kolejka
from strony import STRONA_DO_AGENTA

DECYZJE_CZLOWIEKA = ('artykul', 'alias', 'pomijamy')
KATALOG_WYJSCIA = Path(__file__).resolve().parent.parent / 'Pomiary' / 'petla'
NAZWA_DO_PRZEGLADU = 'do_przegladu.json'
NAZWA_BEZ_LOGU = 'bez_logu.json'


def indeks_logu(wpisy_logu: list[dict]) -> dict[str, dict]:
    indeks: dict[str, dict] = {}
    for wpis in wpisy_logu:
        if wpis.get('typ'):
            continue
        ident = wpis.get('id')
        if ident and ident not in indeks:
            indeks[ident] = wpis
    return indeks


def propozycja_z_logu(wpis: dict) -> tuple[str | None, float | None]:
    cechy = wpis.get('cechy') or {}
    zrodlo = cechy.get('zrodlo_top1')
    rerank = cechy.get('rerank_top1')
    url = zrodlo if isinstance(zrodlo, str) and zrodlo else None
    ocena = rerank if isinstance(rerank, (int, float)) and not isinstance(rerank, bool) else None
    return url, ocena


def wiersz_do_przegladu(zgloszenie: dict, wpis: dict | None) -> dict:
    url, rerank = (None, None)
    if wpis is not None:
        url, rerank = propozycja_z_logu(wpis)
    return {
        'zgloszenie': zgloszenie.get('zgloszenie'),
        'pytanie': zgloszenie.get('pytanie'),
        'lang': zgloszenie.get('lang'),
        'agent': STRONA_DO_AGENTA.get(zgloszenie.get('strona')),
        'etykieta': zgloszenie.get('etykieta'),
        'odpowiedz_operatora': zgloszenie.get('tresc'),
        'propozycja_url': url,
        'rerank_top1': rerank,
        'decyzja': None,
        'url': None,
    }


def klasyfikuj(stan: dict[str, dict], wpisy_logu: list[dict]) -> dict:
    indeks = indeks_logu(wpisy_logu)
    do_przegladu: list[dict] = []
    bez_logu: list[dict] = []
    strony_nieznane: list[dict] = []
    liczniki_status = {'nowe': 0, 'odpowiedziano': 0, 'odrzucone': 0, 'inne': 0}
    liczniki_etykiet: dict[str, int] = {}
    for zgloszenie in stan.values():
        status = zgloszenie.get('status')
        liczniki_status[status if status in liczniki_status else 'inne'] += 1
        if status != 'odpowiedziano':
            continue
        etykieta = zgloszenie.get('etykieta')
        klucz_etykiety = etykieta if etykieta is not None else 'brak_etykiety'
        liczniki_etykiet[klucz_etykiety] = liczniki_etykiet.get(klucz_etykiety, 0) + 1
        wpis = indeks.get(zgloszenie.get('id_zapytania') or '')
        wiersz = wiersz_do_przegladu(zgloszenie, wpis)
        if wiersz['agent'] is None:
            strony_nieznane.append({
                'zgloszenie': wiersz['zgloszenie'],
                'strona': zgloszenie.get('strona'),
            })
        if wpis is None:
            bez_logu.append(wiersz)
        else:
            do_przegladu.append(wiersz)
    podsumowanie = {
        'status': liczniki_status,
        'etykiety_odpowiedziano': liczniki_etykiet,
        'do_przegladu': len(do_przegladu),
        'bez_logu': len(bez_logu),
        'wymaga_decyzji_czlowieka': liczniki_etykiet.get('brak_etykiety', 0),
        'strona_nieznana': len(strony_nieznane),
    }
    return {
        'do_przegladu': do_przegladu,
        'bez_logu': bez_logu,
        'strony_nieznane': strony_nieznane,
        'podsumowanie': podsumowanie,
    }


def wczytaj_jsonl(sciezka: Path) -> list[dict]:
    wiersze: list[dict] = []
    try:
        with open(sciezka, encoding='utf-8') as f:
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
    return wiersze


def zawiera_prace_czlowieka(sciezka: Path) -> bool:
    if not sciezka.exists():
        return False
    try:
        with open(sciezka, encoding='utf-8') as f:
            dane = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(dane, list):
        return False
    return any(isinstance(w, dict) and w.get('decyzja') for w in dane)


def zapisz_wynik(wynik: dict, katalog: Path) -> Path:
    katalog.mkdir(parents=True, exist_ok=True)
    plik = katalog / NAZWA_DO_PRZEGLADU
    if zawiera_prace_czlowieka(plik):
        raise SystemExit(
            f'Plik {plik} ma juz wypelnione pole decyzja. Przerywam, zeby nie skasowac pracy '
            f'czlowieka. Przenies go lub usun recznie, jesli chcesz zbudowac liste od nowa.'
        )
    plik.write_text(
        json.dumps(wynik['do_przegladu'], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if wynik['bez_logu']:
        (katalog / NAZWA_BEZ_LOGU).write_text(
            json.dumps(wynik['bez_logu'], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return plik


def wypisz_podsumowanie(wynik: dict) -> None:
    podsumowanie = wynik['podsumowanie']
    print('Zgloszenia wedlug statusu:')
    for status, ile in podsumowanie['status'].items():
        print(f'  {status}: {ile}')
    print('Odpowiedziane wedlug etykiety:')
    etykiety = podsumowanie['etykiety_odpowiedziano']
    if etykiety:
        for etykieta, ile in sorted(etykiety.items()):
            print(f'  {etykieta}: {ile}')
    else:
        print('  brak')
    print(f"Do przegladu z wpisem w logu: {podsumowanie['do_przegladu']}")
    print(f"Odpowiedziane bez wpisu w logu: {podsumowanie['bez_logu']}")
    print(f"Bez etykiety, do decyzji czlowieka: {podsumowanie['wymaga_decyzji_czlowieka']}")
    print(f"Strona spoza STRONA_DO_AGENTA: {podsumowanie['strona_nieznana']}")
    for wpis in wynik['strony_nieznane']:
        print(
            f"UWAGA: zgloszenie {wpis['zgloszenie']} ma strone {wpis['strona']!r} spoza mapy "
            f"agentow, pole agent zostaje puste",
            file=sys.stderr, flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Laczy odpowiedziane zgloszenia z kolejki z logiem zapytan, dzieli je wedlug etykiety '
            'i zapisuje plik roboczy do przegladu przez czlowieka.'))
    parser.add_argument(
        '--log', type=Path, default=kolejka.KATALOG_RAG / 'log_analytics.jsonl',
        help='sciezka do log_analytics.jsonl, domyslnie obok kolejki w katalogu RAG')
    parser.add_argument(
        '--wyjscie', type=Path, default=KATALOG_WYJSCIA,
        help='katalog na plik do_przegladu.json')
    args = parser.parse_args(argv)

    stan = kolejka.zloz_stan()
    wpisy_logu = wczytaj_jsonl(args.log)
    wynik = klasyfikuj(stan, wpisy_logu)
    wypisz_podsumowanie(wynik)

    if not wynik['do_przegladu'] and not wynik['bez_logu']:
        print('Brak odpowiedzianych zgloszen, nie zapisuje pliku.')
        return 0

    plik = zapisz_wynik(wynik, args.wyjscie)
    print(f'Zapisano {plik}, pozycji do przegladu: {len(wynik["do_przegladu"])}.')
    if wynik['bez_logu']:
        print(f'Zapisano {args.wyjscie / NAZWA_BEZ_LOGU}, pozycji bez logu: {len(wynik["bez_logu"])}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
