# Krok 1 z PLAN_WAGI_STRON.md (Krok 4 kolejnosci z PLAN_POMIARY_GPU.md): audyt szumu etykiet
# strony (kupujacy/sprzedajacy). P0.8 z PLAN_KALIBRACJA_R9.md: pierwsza wersja pokazywala
# etykiete przed ocena i grupowala rekordy strona obok strony, wiec wynik 60/60 byl
# potwierdzeniem etykiety, nie pomiarem szumu. Ta wersja miesza kupujacego ze sprzedajacym,
# nie pokazuje etykiety w pliku do wypelnienia, prawdziwa strona siedzi wylacznie w kluczu
# (KLUCZ), czytanym dopiero przy --policz. Pomiary/sufit_ludzki_strony.py (P5) opiera sie na
# tych samych funkcjach (probka/zapisz/wczytaj_odpowiedzi), z innym ziarnem i wiekszym n.
#
# Uzycie:
#     python audyt_etykiet_stron.py --wypisz
#     (recznie wypelnic pole "ocena" w outputs/audyt_etykiet_stron.txt, na slepo)
#     python audyt_etykiet_stron.py --policz

import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'outputs'
sys.path.insert(0, str(Path(__file__).resolve().parent))

from measure_routing_strony import wczytaj_realny

WYJSCIE = OUT_DIR / 'audyt_etykiet_stron.txt'
KLUCZ = OUT_DIR / 'audyt_etykiet_stron_klucz.json'
N_NA_STRONE = 30
SEED = 42
WYCINEK = 'test'
ODPOWIEDZI = ('kupujacy', 'sprzedaz', 'trudno')

WZORZEC_POZYCJI = re.compile(r'^\[(\d+)\]')
WZORZEC_OCENA = re.compile(r'^\s*ocena \([^)]*\):\s*(\S*)\s*$')


def probka(n_na_strone: int, seed: int, wykluczone: frozenset = frozenset()) -> list[dict]:
    """Zwraca liste {'pytanie', 'prawda'} wymieszana kupujacy/sprzedaz. Dla kazdej strony
    swiezy random.Random(seed), zeby dobor jednej strony nie zalezal od tego, ile rekordow
    ciagnie sie z drugiej. wykluczone filtruje PRZED shufflem, wiec przy tym samym seed i
    pustym wykluczone wynik jest identyczny z wczytaj_realny(strona, n_na_strone, seed, ...)."""
    wybrane = []
    for strona_jsonl, etykieta in (('kupujacy', 'kupujacy'), ('sprzedaz', 'sprzedaz')):
        wszystkie = [p for p in wczytaj_realny(strona_jsonl, 0, seed, wycinek=WYCINEK)
                     if p not in wykluczone]
        random.Random(seed).shuffle(wszystkie)
        wybrane += [{'pytanie': p, 'prawda': etykieta} for p in wszystkie[:n_na_strone]]
    random.Random(seed + 1).shuffle(wybrane)
    return wybrane


def zapisz(plik: Path, klucz_plik: Path, pozycje: list[dict], opis: list[str],
           odpowiedzi: tuple[str, ...] = ODPOWIEDZI) -> None:
    plik.parent.mkdir(parents=True, exist_ok=True)
    with open(plik, 'w', encoding='utf-8') as f:
        for linia in opis:
            f.write(linia + '\n')
        f.write('\n')
        for i, poz in enumerate(pozycje, 1):
            f.write(f'[{i:03d}] pytanie: {poz["pytanie"]}\n')
            f.write(f'      ocena ({"/".join(odpowiedzi)}):\n\n')
    klucz = {f'{i:03d}': poz['prawda'] for i, poz in enumerate(pozycje, 1)}
    klucz_plik.write_text(json.dumps(klucz, ensure_ascii=False, indent=2), encoding='utf-8')


def wczytaj_odpowiedzi(plik: Path) -> dict[str, str]:
    odpowiedzi = {}
    numer = None
    with open(plik, encoding='utf-8') as f:
        for linia in f:
            naglowek = WZORZEC_POZYCJI.match(linia)
            if naglowek:
                numer = f'{int(naglowek.group(1)):03d}'
                continue
            ocena = WZORZEC_OCENA.match(linia)
            if ocena and numer is not None and ocena.group(1):
                odpowiedzi[numer] = ocena.group(1).strip().lower()
    return odpowiedzi


def wypisz() -> None:
    wybrane = probka(N_NA_STRONE, SEED)
    opis = [
        f'# Audyt etykiet stron, wycinek {WYCINEK}, ziarno {SEED}, {len(wybrane)} rekordow.',
        '# Etykieta jest UKRYTA, kolejnosc wymieszana. Zgadnij strone z samej tresci pytania,',
        '# na slepo, bez podgladania klucza.',
        f'# Wypelnij pole ocena ({"/".join(ODPOWIEDZI)}), potem: '
        'python Pomiary/audyt_etykiet_stron.py --policz',
    ]
    zapisz(WYJSCIE, KLUCZ, wybrane, opis)
    print(f'zapisano {WYJSCIE} i {KLUCZ}: {len(wybrane)} rekordow '
          f'({N_NA_STRONE} kupujacy, {N_NA_STRONE} sprzedaz)')
    print('Wypelnij pole ocena recznie, na slepo, potem uruchom --policz.')


def policz() -> None:
    if not WYJSCIE.exists() or not KLUCZ.exists():
        raise SystemExit(f'brak {WYJSCIE} albo {KLUCZ}, najpierw --wypisz')

    klucz = json.loads(KLUCZ.read_text(encoding='utf-8'))
    odpowiedzi = wczytaj_odpowiedzi(WYJSCIE)

    zgodne = rozbiezne = trudno = 0
    for numer, prawda in klucz.items():
        ocena = odpowiedzi.get(numer)
        if ocena not in ODPOWIEDZI:
            continue
        if ocena == 'trudno':
            trudno += 1
        elif ocena == prawda:
            zgodne += 1
        else:
            rozbiezne += 1

    ocenione = zgodne + rozbiezne + trudno
    if not ocenione:
        raise SystemExit(f'{WYJSCIE} nie ma zadnej wypelnionej oceny')

    print(f'ocenionych pozycji: {ocenione} z {len(klucz)}')
    print()
    print(f'zgodnosc czlowieka z etykieta (sufit mierzalnej trafnosci): '
          f'{zgodne / ocenione:.3f}  ({zgodne}/{ocenione})')
    print(f'rozbiezne (czlowiek widzi przeciwna strone): {rozbiezne}/{ocenione}')
    print(f'trudno powiedziec: {trudno}/{ocenione}')
    if ocenione < len(klucz):
        print(f'\nUWAGA: niewypelnione pozycje ({len(klucz) - ocenione}), liczby liczone '
              'tylko z wypelnionych.')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--wypisz', action='store_true', help='wygeneruj plik do recznego wypelnienia')
    parser.add_argument('--policz', action='store_true', help='policz zgodnosc z wypelnionego pliku')
    args = parser.parse_args()

    if args.wypisz == args.policz:
        raise SystemExit('podaj dokladnie jedno: --wypisz albo --policz')
    if args.wypisz:
        wypisz()
    else:
        policz()


if __name__ == '__main__':
    main()
