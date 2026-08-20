# Skrypt zamienia oceny z logu na pozycje zestawu regresyjnego, jedna ocena
# to jeden przypadek, zadnego uczenia modelu tu nie ma.

import sys
import json
import argparse
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

import statystyki
import measure
import rankings

LOG = ROOT / 'RAG' / 'log_analytics.jsonl'
WZORZEC_ARCHIWUM = 'log_analytics.jsonl.przed-resetem-*'
sciezka_zestawu = ROOT / 'RAG' / 'zestaw_regresji.json'


def wczytaj_wszystko(z_archiwami: bool) -> list[dict]:
    wpisy = statystyki.wczytaj(LOG)
    if z_archiwami:
        for plik in sorted((ROOT / 'RAG').glob(WZORZEC_ARCHIWUM)):
            wpisy.extend(statystyki.wczytaj(plik))
    return wpisy


GOLDEN_PO_PYTANIU = {
    rankings.normalizacja(g['query']).strip(): g['zrodlo_url']
    for g in measure.GOLDEN
}


def zrodlo_z_golden(query: str) -> str | None:
    return GOLDEN_PO_PYTANIU.get(rankings.normalizacja(query).strip())


def wczytaj_przypadki(sciezka: Path) -> list[dict]:
    # Endpoint /admin/oceny zwraca {"razem": n, "przypadki": [...]}, czyli to samo,
    # co statystyki.przypadki_ocen. Przyjmujemy tez sama liste, gdyby ktos zapisal wycinek.
    with open(sciezka, encoding='utf-8') as r:
        dane = json.load(r)
    if isinstance(dane, dict):
        dane = dane.get('przypadki') or []
    if not isinstance(dane, list):
        raise SystemExit(f'plik {sciezka} nie zawiera listy przypadkow')
    return dane


def kandydaci_z_ocen(przypadki: list[dict]) -> list[dict]:
    kandydaci = []
    for p in przypadki:
        query = p['pytanie']
        if not query:
            continue

        zrodlo_golden = zrodlo_z_golden(query)
        if zrodlo_golden is not None:
            zrodlo_url = zrodlo_golden
            skad_zrodlo = 'golden'
        elif p['ocena'] == 'gora' and p['cechy']:
            zrodlo_url = p['cechy']['zrodlo_top1']
            skad_zrodlo = 'serwowane'
        else:
            zrodlo_url = None
            skad_zrodlo = None

        do_uzupelnienia = not zrodlo_url or '[ukryte]' in query

        kandydaci.append({
            'query': query,
            'agent': p['sekcja'],
            'zrodlo_url': zrodlo_url,
            'skad_zrodlo': skad_zrodlo,
            'ocena': p['ocena'],
            'diagnoza': p['diagnoza'],
            'czas': p['czas'],
            'id_zapytania': p['id_zapytania'],
            'do_uzupelnienia': do_uzupelnienia,
        })
    return kandydaci


def klucz_pozycji(p: dict) -> str:
    return p.get('id_zapytania') or (p.get('query') or '').strip().lower()


def wczytaj_zestaw() -> list[dict]:
    try:
        with open(sciezka_zestawu, encoding='utf-8') as r:
            return json.load(r)
    except (OSError, json.JSONDecodeError):
        return []


def scal(istniejace: list[dict], kandydaci: list[dict]) -> tuple[list[dict], dict]:
    wynik = list(istniejace)
    indeks = {klucz_pozycji(p): i for i, p in enumerate(wynik)}
    dodane = 0
    zaktualizowane = 0

    for k in kandydaci:
        klucz = klucz_pozycji(k)
        if klucz in indeks:
            i = indeks[klucz]
            wynik[i]['diagnoza'] = k['diagnoza']
            wynik[i]['ocena'] = k['ocena']
            zaktualizowane += 1
        else:
            wynik.append(k)
            indeks[klucz] = len(wynik) - 1
            dodane += 1

    do_uzupelnienia = sum(1 for p in wynik if p.get('do_uzupelnienia'))
    return wynik, {'dodane': dodane, 'zaktualizowane': zaktualizowane, 'do_uzupelnienia': do_uzupelnienia}


def zapisz(zestaw: list[dict]) -> None:
    with open(sciezka_zestawu, 'w', encoding='utf-8') as w:
        json.dump(zestaw, w, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--archiwa', action='store_true')
    parser.add_argument('--sucho', action='store_true')
    parser.add_argument('--przypadki', default=None,
                        help='plik JSON z odpowiedzi GET /admin/oceny, zamiast lokalnego logu')
    args = parser.parse_args()

    # Oceny powstaja na produkcji, a lokalna maszyna tamtego logu moze nigdy nie miec.
    # Endpoint /admin/oceny oddaje gotowa liste przypadkow, wiec sciezka z pliku jest
    # rownorzedna z czytaniem logu, a nie obejsciem.
    if args.przypadki:
        if args.archiwa:
            print('UWAGA: --archiwa nie ma znaczenia przy --przypadki, log nie jest czytany.')
        przypadki = wczytaj_przypadki(Path(args.przypadki))
        zrodlo_danych = f'plik {args.przypadki}'
    else:
        wpisy = wczytaj_wszystko(args.archiwa)
        przypadki = statystyki.przypadki_ocen(wpisy)
        zrodlo_danych = f'log lokalny, {len(wpisy)} wpisow'

    kandydaci = kandydaci_z_ocen(przypadki)
    istniejace = wczytaj_zestaw()
    zestaw, licznik = scal(istniejace, kandydaci)

    if not args.sucho:
        zapisz(zestaw)

    golden = sum(1 for p in zestaw if p.get('skad_zrodlo') == 'golden')
    serwowane = sum(1 for p in zestaw if p.get('skad_zrodlo') == 'serwowane')

    print(f'Zrodlo danych: {zrodlo_danych}')
    print(f'Ocen: {len(przypadki)}')
    print(f"Dodane: {licznik['dodane']}  Zaktualizowane: {licznik['zaktualizowane']}")
    print(f"Link z GOLDEN: {golden}  Serwowane: {serwowane}  Do uzupelnienia: {licznik['do_uzupelnienia']}")
    print(f'Plik: {"(sucho, nie zapisano)" if args.sucho else sciezka_zestawu}')

    print('\nRozbieznosci GOLDEN vs serwowane (ocena "gora", oba zrodla sa, roznia sie):')
    rozbieznosci = [
        (p['pytanie'], zrodlo_z_golden(p['pytanie'] or ''), (p['cechy'] or {}).get('zrodlo_top1'))
        for p in przypadki if p['ocena'] == 'gora'
    ]
    rozbieznosci = [r for r in rozbieznosci if r[1] and r[2] and r[1] != r[2]]
    if not rozbieznosci:
        print('  brak')
    for pytanie, golden_link, serwowany_link in rozbieznosci:
        print(f'  {(pytanie or "")[:70]!r}: golden={golden_link}  serwowane={serwowany_link}')

    print('\nDo recznego uzupelnienia:')
    do_pokazania = [p for p in zestaw if p.get('do_uzupelnienia')]
    if not do_pokazania:
        print('  brak')
    for p in do_pokazania:
        print(f"  {p['czas']}, {p['ocena']}, {p['diagnoza']}, {(p['query'] or '')[:70]}")
