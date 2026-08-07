# Krok 1 z PLAN_WAGI_STRON.md: audyt szumu etykiet. Losuje 60 rekordow (30 na strone, ziarno 42,
# wycinek testowy) z RAG/pytania_realne.jsonl i tylko je wypisuje. Ocene ("czy pytanie faktycznie
# jest od tej strony") robi czlowiek, skrypt nic nie rozstrzyga.
#
# Uzycie:
#     python audyt_etykiet_stron.py

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'outputs'
sys.path.insert(0, str(Path(__file__).resolve().parent))

from measure_routing_strony import wczytaj_realny

N_NA_STRONE = 30
SEED = 42


def main() -> None:
    kupujacy = wczytaj_realny('kupujacy', N_NA_STRONE, SEED, wycinek='test')
    sprzedaz = wczytaj_realny('sprzedaz', N_NA_STRONE, SEED, wycinek='test')

    linie = []
    linie.append(f'kupujacy: {len(kupujacy)} rekordow (oczekiwano {N_NA_STRONE})')
    linie.append(f'sprzedaz: {len(sprzedaz)} rekordow (oczekiwano {N_NA_STRONE})')
    linie.append('')

    i = 1
    for pytanie in kupujacy:
        linie.append(f'{i:2d}. [kupujacy]  {pytanie}')
        i += 1
    for pytanie in sprzedaz:
        linie.append(f'{i:2d}. [sprzedaz]  {pytanie}')
        i += 1

    OUT_DIR.mkdir(exist_ok=True)
    plik_wyjsciowy = OUT_DIR / 'audyt_etykiet_stron.txt'
    plik_wyjsciowy.write_text('\n'.join(linie), encoding='utf-8')
    print(f'zapisano: {plik_wyjsciowy}')


if __name__ == '__main__':
    main()
