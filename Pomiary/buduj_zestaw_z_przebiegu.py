"""Zamienia oceny z przebiegu 2026-09-03 na pozycje zestawu regresyjnego.

Po co: `buduj_zestaw_regresji.py` czyta kciuki z logu (`ocena` gora albo dol,
`cechy.zrodlo_top1`, `id_zapytania`). Przebieg z `measure_przebieg_ocen.py` ma inny
ksztalt: oceny D, Z, X w pliku przegladu plus zapisane odpowiedzi z cytatami.
Ten skrypt tlumaczy jedno na drugie, zeby `measure_regresja.py` mial na czym pracowac.

Regula przypisania zrodla, w tej kolejnosci:
  1. ZRODLA_RECZNE     pytania, dla ktorych znam wlasciwy artykul i wpisalem go tutaj
  2. ocena D z cytatem serwowane zrodlo bylo dobre, bo odpowiedz uznano za dobra
  3. reszta            zrodlo nieznane, pozycja idzie do uzupelnienia i nie jest mierzona

Ocena D staje sie `gora`, Z i X staja sie `dol`, zeby `measure_regresja.py` mogl
raportowac obie grupy osobno tak jak dla kciukow.

Uruchomienie:
    python Pomiary/buduj_zestaw_z_przebiegu.py
    python Pomiary/measure_regresja.py
"""

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
POMIARY = ROOT / 'Pomiary'
PRZEGLAD = POMIARY / 'PRZEGLAD_PRZEBIEG_OCEN.md'
ODPOWIEDZI = POMIARY / 'WYNIK_PRZEBIEG_OCEN.json'
ZESTAW = ROOT / 'RAG' / 'zestaw_regresji.json'

# Artykul, ktory ma wygrywac rodzine pytan o czas kupujacego na zwrot. Ustalony recznie
# przy naprawie retrievalu terminu zwrotu i potwierdzony na produkcji 6/6, wiec te pozycje
# sa mierzalne mimo oceny Z, ktora dostaly przed naprawa.
TERMIN_ZWROTU = ('https://allegro.pl/pomoc/dla-kupujacych/zasady-zwrotow-i-reklamacji/'
                 'jak-zwrocic-zakup-i-odeslac-produkt-do-sprzedajacego-GDeq5VeKRHD')

ZRODLA_RECZNE = {
    0: TERMIN_ZWROTU,
    2: TERMIN_ZWROTU,
    8: TERMIN_ZWROTU,
    14: TERMIN_ZWROTU,
    19: TERMIN_ZWROTU,
}

OCENA_NA_KCIUK = {'D': 'gora', 'Z': 'dol', 'X': 'dol'}


def wczytaj_oceny() -> dict:
    tekst = PRZEGLAD.read_text(encoding='utf-8')
    oceny, biezacy = {}, None
    for linia in tekst.splitlines():
        naglowek = re.match(r'^#{2,4} (\d+)\.', linia)
        if naglowek:
            biezacy = int(naglowek.group(1))
            oceny.setdefault(biezacy, {})
            continue
        if biezacy is None:
            continue
        for pole, wzor in (('istnieje', r'^ISTNIEJE:\s*([TNtn?])\s*$'),
                           ('ocena', r'^OCENA:\s*([DZXdzx?])\s*$')):
            trafienie = re.match(wzor, linia)
            if trafienie:
                oceny[biezacy][pole] = trafienie.group(1).upper()
    return oceny


def zbuduj() -> list[dict]:
    oceny = wczytaj_oceny()
    odpowiedzi = {p['id']: p for p in json.loads(ODPOWIEDZI.read_text(encoding='utf-8'))}

    pozycje = []
    for identyfikator, odp in sorted(odpowiedzi.items()):
        ocena = oceny.get(identyfikator, {}).get('ocena', '?')
        cytaty = odp['cytaty'] or odp['zrodla']

        if identyfikator in ZRODLA_RECZNE:
            zrodlo, skad = ZRODLA_RECZNE[identyfikator], 'reczne'
        elif ocena == 'D' and cytaty:
            zrodlo, skad = cytaty[0], 'serwowane'
        else:
            zrodlo, skad = None, None

        pozycje.append({
            'query': odp['pytanie'],
            'agent': odp['agent'] or odp['sekcja_logu'],
            'zrodlo_url': zrodlo,
            'skad_zrodlo': skad,
            'ocena': OCENA_NA_KCIUK.get(ocena, 'dol'),
            'ocena_przebiegu': ocena,
            'diagnoza': ('odmowa: ' + str(odp['powod'])) if odp['odmowa'] else f'tryb {odp["tryb"]}',
            'czas': '2026-09-03',
            'id_zapytania': f'przebieg-2026-09-03-{identyfikator:02d}',
            'do_uzupelnienia': zrodlo is None,
            'tryb': odp['tryb'],
        })
    return pozycje


if __name__ == '__main__':
    pozycje = zbuduj()
    ZESTAW.write_text(json.dumps(pozycje, ensure_ascii=False, indent=2), encoding='utf-8')

    mierzalne = [p for p in pozycje if p['zrodlo_url']]
    print(f'pozycji razem: {len(pozycje)}')
    print(f'mierzalnych (jest zrodlo_url): {len(mierzalne)}')
    print(f'  z tego reczne: {sum(1 for p in mierzalne if p["skad_zrodlo"] == "reczne")}')
    print(f'  z tego serwowane: {sum(1 for p in mierzalne if p["skad_zrodlo"] == "serwowane")}')
    print(f'do uzupelnienia: {sum(1 for p in pozycje if p["do_uzupelnienia"])}')
    print()
    print('do uzupelnienia, czyli czekaja na wskazanie wlasciwego artykulu:')
    for p in pozycje:
        if p['do_uzupelnienia']:
            print(f'  [{p["ocena_przebiegu"]}] {p["query"][:58]:60} ({p["tryb"]})')
    print(f'\nzapisano: {ZESTAW}')
