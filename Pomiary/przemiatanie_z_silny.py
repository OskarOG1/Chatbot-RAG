# P4 z PLAN_KALIBRACJA_R9.md: przemiatanie po Z_SILNY (prog dowodu z P2). Dla kazdej wartosci
# TAU_MOCNY/TAU_SLABY dostrajaja sie automatycznie per fold (P0.5/P0.6, patrz
# ucz_wagi_stron.przebieg), wiec siatka (TAU_MOCNY, TAU_SLABY, Z_SILNY) z planu sprowadza sie w
# praktyce do jednego wolnego parametru: dla kazdego Z_SILNY tau's sa pochodna danych, nie
# osobna osia przemiatania. Ten wybor jest opisany w POMIAR_WAGI_STRON.md.
#
# Dla kazdego kandydata: (1) ucz_wagi_stron.przebieg trenuje tabele na calej bazie (Krok 5,
# lekskalne, bez rerankera), (2) src/wagi_stron.py nadpisany i przeladowany, (3)
# macierz_ramion liczy trafnosc/zla_cicha/zbyte/precyzja per strona na danych realnych (poza
# foldem) i zlapane OOD, oba przez tablica_rerank (cache, bez GPU/modelu).
#
# Cel z P4: minimalizuj zla_cicha (wazona skladem bazy, 2267 sprzedaz + 1629 kupujacy) przy:
# odsetek_zbytych < 0.15 (obie strony), zlapane OOD (odmowa przez prog_rerank, bramka 8
# poprawiona przez P1) nie mniej niz dzis (r5) dla pl i en, precyzja poziomu mocnego >= 0.85
# (obie strony, gdy n_leksykalna_mocny > 0). Do raportu idzie cala powierzchnia, nie sam
# wybrany punkt.
#
# Uzycie:
#     python przemiatanie_z_silny.py

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
OUT_DIR = ROOT / 'outputs'
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ucz_wagi_stron as uws
import macierz_ramion as mr

SIATKA_Z_SILNY = [0.0, 1.0, 1.5, 1.96, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]


def przeladuj_wagi_stron():
    if 'wagi_stron' in sys.modules:
        importlib.reload(sys.modules['wagi_stron'])
    else:
        import wagi_stron  # noqa: F401


def ocen_kandydata(z_silny: float, rekordy_wszystkie: list[dict]) -> dict:
    wynik_uczenia = uws.przebieg(rekordy_wszystkie, z_silny, cichy=True)
    uws.zapisz_modul(wynik_uczenia['tabela_prod'], wynik_uczenia['tau_mocny_produkcyjne'],
                      wynik_uczenia['tau_slaby_produkcyjne'], z_silny, wynik_uczenia['n_razem'])
    przeladuj_wagi_stron()

    tabele_foldow = mr.buduj_tabele_foldow(rekordy_wszystkie, z_silny)
    macierz_r = mr.macierz_realny(rekordy_wszystkie, tabele_foldow)

    ood_pl = mr.przygotuj_ood(mr.OOD, 'pl', 'r9')
    ood_en = mr.przygotuj_ood(list(mr.ood_en()), 'en', 'r9')

    kupujacy = macierz_r['kupujacy_pl']['brak_r9']
    sprzedaz = macierz_r['sprzedaz_pl']['brak_r9']
    n_kupujacy, n_sprzedaz = kupujacy['n'], sprzedaz['n']
    zla_cicha_wazona = (sprzedaz['zla_cicha'] * n_sprzedaz + kupujacy['zla_cicha'] * n_kupujacy) \
        / (n_sprzedaz + n_kupujacy)

    return {
        'z_silny': z_silny,
        'tau_mocny_produkcyjne': wynik_uczenia['tau_mocny_produkcyjne'],
        'tau_slaby_produkcyjne': wynik_uczenia['tau_slaby_produkcyjne'],
        'rozmiar_tabeli': wynik_uczenia['rozmiar_tabeli_produkcyjnej'],
        'trafnosc_r9_out_of_fold_srednia': wynik_uczenia['trafnosc_r9_srednia'],
        'zla_cicha_wazona': round(zla_cicha_wazona, 4),
        'kupujacy_pl': {k: kupujacy[k] for k in
                         ('trafnosc', 'zla_cicha', 'odsetek_zbytych',
                          'precyzja_leksykalna_mocny', 'n_leksykalna_mocny')},
        'sprzedaz_pl': {k: sprzedaz[k] for k in
                         ('trafnosc', 'zla_cicha', 'odsetek_zbytych',
                          'precyzja_leksykalna_mocny', 'n_leksykalna_mocny')},
        'ood_pl_odmowa': ood_pl['odmowa'], 'ood_en_odmowa': ood_en['odmowa'],
    }


def spelnia_ograniczenia(kandydat: dict, ood_dzis_pl: int, ood_dzis_en: int) -> list[str]:
    naruszenia = []
    for nazwa in ('kupujacy_pl', 'sprzedaz_pl'):
        if kandydat[nazwa]['odsetek_zbytych'] >= mr.BRAMKA_ODSETEK_ZBYTYCH:
            naruszenia.append(f'{nazwa}: odsetek_zbytych {kandydat[nazwa]["odsetek_zbytych"]:.4f} '
                               f'>= {mr.BRAMKA_ODSETEK_ZBYTYCH}')
        precyzja = kandydat[nazwa]['precyzja_leksykalna_mocny']
        if precyzja is not None and precyzja < mr.BRAMKA_PRECYZJA_MOCNY:
            naruszenia.append(f'{nazwa}: precyzja_leksykalna_mocny {precyzja:.4f} '
                               f'< {mr.BRAMKA_PRECYZJA_MOCNY}')
    if kandydat['ood_pl_odmowa'] < ood_dzis_pl:
        naruszenia.append(f'ood_pl: odmowa {kandydat["ood_pl_odmowa"]} < dzis {ood_dzis_pl}')
    if kandydat['ood_en_odmowa'] < ood_dzis_en:
        naruszenia.append(f'ood_en: odmowa {kandydat["ood_en_odmowa"]} < dzis {ood_dzis_en}')
    return naruszenia


def main() -> None:
    print('=== Wczytywanie tablicy rerankera ===')
    tablica = mr.wczytaj_tablice_z_odciskiem()
    print(f"odcisk zgodny, {len(tablica['wyniki'])} pytan w tablicy")
    mr.podmien_search(tablica)

    rekordy_wszystkie = uws.wczytaj_wszystkie()

    print('\n=== Dzisiejsze odmowy OOD (r5), punkt odniesienia stalej dla calej siatki ===')
    ood_dzis_pl = mr.przygotuj_ood(mr.OOD, 'pl', 'r5')['odmowa']
    ood_dzis_en = mr.przygotuj_ood(list(mr.ood_en()), 'en', 'r5')['odmowa']
    print(f'  pl odmowa={ood_dzis_pl}  en odmowa={ood_dzis_en}')

    powierzchnia = []
    try:
        for z_silny in SIATKA_Z_SILNY:
            print(f'\n=== Z_SILNY={z_silny} ===')
            kandydat = ocen_kandydata(z_silny, rekordy_wszystkie)
            naruszenia = spelnia_ograniczenia(kandydat, ood_dzis_pl, ood_dzis_en)
            kandydat['naruszenia'] = naruszenia
            kandydat['dopuszczalny'] = not naruszenia
            powierzchnia.append(kandydat)
            print(f'  TAU_MOCNY={kandydat["tau_mocny_produkcyjne"]:.3f} '
                  f'TAU_SLABY={kandydat["tau_slaby_produkcyjne"]:.3f} '
                  f'tabela={kandydat["rozmiar_tabeli"]} '
                  f'zla_cicha_wazona={kandydat["zla_cicha_wazona"]:.4f}')
            print(f'  kupujacy_pl: trafnosc={kandydat["kupujacy_pl"]["trafnosc"]:.4f} '
                  f'zla_cicha={kandydat["kupujacy_pl"]["zla_cicha"]:.4f} '
                  f'zbyte={kandydat["kupujacy_pl"]["odsetek_zbytych"]:.4f}')
            print(f'  sprzedaz_pl: trafnosc={kandydat["sprzedaz_pl"]["trafnosc"]:.4f} '
                  f'zla_cicha={kandydat["sprzedaz_pl"]["zla_cicha"]:.4f} '
                  f'zbyte={kandydat["sprzedaz_pl"]["odsetek_zbytych"]:.4f}')
            print(f'  ood_pl_odmowa={kandydat["ood_pl_odmowa"]} ood_en_odmowa={kandydat["ood_en_odmowa"]} '
                  f'dopuszczalny={kandydat["dopuszczalny"]}')
            if naruszenia:
                for n in naruszenia:
                    print(f'    narusza: {n}')

        dopuszczalni = [k for k in powierzchnia if k['dopuszczalny']]
        if dopuszczalni:
            najlepszy = min(dopuszczalni, key=lambda k: k['zla_cicha_wazona'])
            print(f'\n=== Wybor: Z_SILNY={najlepszy["z_silny"]} (dopuszczalny, min. zla_cicha_wazona) ===')
        else:
            najlepszy = min(powierzchnia, key=lambda k: len(k['naruszenia']))
            print(f'\n=== Zaden kandydat nie spelnia wszystkich ograniczen, wybor to rozstrzygniecie '
                  f'remisu na liczbie naruszen, nie spelnienie ograniczen. Najblizszy: '
                  f'Z_SILNY={najlepszy["z_silny"]} ({len(najlepszy["naruszenia"])} naruszen) ===')

        OUT_DIR.mkdir(exist_ok=True)
        wynik = {
            'siatka_z_silny': SIATKA_Z_SILNY,
            'ood_dzis_pl_odmowa': ood_dzis_pl, 'ood_dzis_en_odmowa': ood_dzis_en,
            'powierzchnia': powierzchnia,
            'z_silny_wybrany': najlepszy['z_silny'],
            'wszyscy_dopuszczalni': [k['z_silny'] for k in dopuszczalni],
        }
        plik = OUT_DIR / 'przemiatanie_z_silny.json'
        plik.write_text(json.dumps(wynik, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'\nzapisano: {plik}')
    finally:
        print(f'\nPrzywracanie tabeli produkcyjnej (Z_SILNY={uws.Z_SILNY_PRODUKCYJNY})...')
        ocen_kandydata(uws.Z_SILNY_PRODUKCYJNY, rekordy_wszystkie)


if __name__ == '__main__':
    main()
