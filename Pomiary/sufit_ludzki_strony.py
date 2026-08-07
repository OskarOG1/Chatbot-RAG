# P5 z PLAN_KALIBRACJA_R9.md: sufit ludzki dla trafnosci pierwszej tury, strona
# kupujacy/sprzedajacy. Bramki 1 i 2 tamtego planu maja przyjac wartosc "nie nizej niz
# odsetek trafnych czlowieka na tym samym zestawie, minus jeden blad standardowy" zamiast
# zgadnietych 0.70/0.75 z PLAN_POMIARY_GPU.md.
#
# Reuzywa Pomiary/audyt_etykiet_stron.py (probka/zapisz/wczytaj_odpowiedzi): inne ziarno niz
# audyt Kroku 1 (tam 42), z wykluczeniem tamtych 60 rekordow, bo uzytkownik widzial je juz
# z etykieta i sa skazone. audyt_etykiet_stron.probka(N_AUDYTU, SEED_AUDYTU) odtwarza
# dokladnie te 60. Trzecia odpowiedz (trudno) to odpowiednik czy_pytac: czlowiek tez ma
# prawo prosic o doprecyzowanie zamiast zgadywac, porownanie ma byc trojka na trojke.
#
# Przy 60 na strone blad standardowy ~0.065 (sqrt(0.5*0.5/60)), tyle wynosi rozdzielczosc tej
# bramki - nie czytac roznicy 0.03 jako roznicy.
#
# Uzycie:
#     python sufit_ludzki_strony.py --wypisz
#     (recznie wypelnic pole "ocena" w outputs/sufit_ludzki_strony.txt, ok. 20-25 minut)
#     python sufit_ludzki_strony.py --policz

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'outputs'
sys.path.insert(0, str(Path(__file__).resolve().parent))

import audyt_etykiet_stron as aes

WYJSCIE = OUT_DIR / 'sufit_ludzki_strony.txt'
KLUCZ = OUT_DIR / 'sufit_ludzki_strony_klucz.json'
N_NA_STRONE = 60
SEED = 43
N_AUDYTU = aes.N_NA_STRONE
SEED_AUDYTU = aes.SEED


def wykluczone_z_audytu() -> frozenset:
    audyt = aes.probka(N_AUDYTU, SEED_AUDYTU)
    return frozenset(poz['pytanie'] for poz in audyt)


def blad_standardowy(n: int) -> float:
    return math.sqrt(0.5 * 0.5 / n) if n else 0.0


def wypisz() -> None:
    wykluczone = wykluczone_z_audytu()
    wybrane = aes.probka(N_NA_STRONE, SEED, wykluczone=wykluczone)
    opis = [
        f'# Sufit ludzki (P5 PLAN_KALIBRACJA_R9.md), wycinek {aes.WYCINEK}, ziarno {SEED}, '
        f'{len(wybrane)} rekordow.',
        f'# Wykluczone {len(wykluczone)} rekordow z audytu Kroku 1 (ziarno {SEED_AUDYTU}), '
        'ktore juz widziales z etykieta.',
        '# Etykieta jest UKRYTA, kolejnosc wymieszana. Zgadnij strone z samej tresci pytania,',
        '# na slepo. "trudno" jest pelnoprawna odpowiedzia, nie wymowka: czlowiek tez ma',
        '# prawo poprosic o doprecyzowanie zamiast zgadywac na sile.',
        f'# Wypelnij pole ocena ({"/".join(aes.ODPOWIEDZI)}), potem: '
        'python Pomiary/sufit_ludzki_strony.py --policz',
    ]
    aes.zapisz(WYJSCIE, KLUCZ, wybrane, opis)
    print(f'zapisano {WYJSCIE} i {KLUCZ}: {len(wybrane)} rekordow '
          f'({N_NA_STRONE} kupujacy, {N_NA_STRONE} sprzedaz), {len(wykluczone)} wykluczonych '
          f'z audytu Kroku 1')
    print('Wypelnij pole ocena recznie, na slepo (ok. 20-25 minut), potem uruchom --policz.')


def policz() -> None:
    if not WYJSCIE.exists() or not KLUCZ.exists():
        raise SystemExit(f'brak {WYJSCIE} albo {KLUCZ}, najpierw --wypisz')

    klucz = json.loads(KLUCZ.read_text(encoding='utf-8'))
    odpowiedzi = aes.wczytaj_odpowiedzi(WYJSCIE)

    def policz_strone(prawda_strona: str) -> dict:
        zgodne = rozbiezne = trudno = 0
        for numer, prawda in klucz.items():
            if prawda != prawda_strona:
                continue
            ocena = odpowiedzi.get(numer)
            if ocena not in aes.ODPOWIEDZI:
                continue
            if ocena == 'trudno':
                trudno += 1
            elif ocena == prawda:
                zgodne += 1
            else:
                rozbiezne += 1
        n = zgodne + rozbiezne + trudno
        return {'n': n, 'zgodne': zgodne, 'rozbiezne': rozbiezne, 'trudno': trudno,
                'trafnosc': zgodne / n if n else 0.0, 'blad_standardowy': blad_standardowy(n)}

    kupujacy = policz_strone('kupujacy')
    sprzedaz = policz_strone('sprzedaz')
    ocenione = kupujacy['n'] + sprzedaz['n']

    if not ocenione:
        raise SystemExit(f'{WYJSCIE} nie ma zadnej wypelnionej oceny')

    print(f'ocenionych pozycji: {ocenione} z {len(klucz)}')
    print()
    for nazwa, w in (('kupujacy', kupujacy), ('sprzedaz', sprzedaz)):
        print(f'[{nazwa}] trafnosc={w["trafnosc"]:.4f} ({w["zgodne"]}/{w["n"]})  '
              f'rozbiezne={w["rozbiezne"]}  trudno={w["trudno"]}  '
              f'blad_std={w["blad_standardowy"]:.4f}')
        print(f'  bramka sugerowana (sufit minus 1 blad std.): '
              f'{max(0.0, w["trafnosc"] - w["blad_standardowy"]):.4f}')

    if ocenione < len(klucz):
        print(f'\nUWAGA: niewypelnione pozycje ({len(klucz) - ocenione}), liczby liczone '
              'tylko z wypelnionych.')

    OUT_DIR.mkdir(exist_ok=True)
    wynik = {'kupujacy': kupujacy, 'sprzedaz': sprzedaz}
    (OUT_DIR / 'sufit_ludzki_strony.json').write_text(
        json.dumps(wynik, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\nzapisano: {OUT_DIR / 'sufit_ludzki_strony.json'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--wypisz', action='store_true', help='wygeneruj plik do recznego wypelnienia')
    parser.add_argument('--policz', action='store_true', help='policz sufit z wypelnionego pliku')
    args = parser.parse_args()

    if args.wypisz == args.policz:
        raise SystemExit('podaj dokladnie jedno: --wypisz albo --policz')
    if args.wypisz:
        wypisz()
    else:
        policz()


if __name__ == '__main__':
    main()
