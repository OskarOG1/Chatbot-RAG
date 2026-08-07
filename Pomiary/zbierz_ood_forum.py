# Dozbieranie kontroli OOD dla kroku 4 z PLAN_KLASYFIKATOR_FORUM.md.
#
# Numizmatyka i EkoGadka to boardy spoza domeny pomocy (OOD_BOARDS w zbierz_pytania.py).
# Klasyfikator sekcji nie moze na nich przekraczac progow oferty, inaczej produkcja
# bedzie proponowac watek z forum pod pytaniem, ktore z pomoca Allegro nie ma nic wspolnego.
#
# Skrypt NIE duplikuje warstwy limitow: importuje ja z zbierz_pytania (robots.txt, odstep
# 5 s liczony od zakonczenia poprzedniego zadania, backoff na 429/5xx, log do
# log_zbieranie_pytan.txt). Przepisana warstwa limitow to szybka droga do zbanowania.
#
# Rekordy dopisywane sa do RAG/pytania_realne.jsonl z zrodlo='ood'. Kolejnosc rekordow
# forum sie nie zmienia (dopisujemy na koniec), wiec cache embeddingow z outputs/ zostaje
# wazny.
#
# Uzycie:
#     python Pomiary/zbierz_ood_forum.py --max-stron 5

import argparse
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from zbierz_pytania import (  # noqa: E402
    HEADER,
    ODSTEP_S,
    OOD_BOARDS,
    loguj,
    strona_z_boardu,
    wczytaj_robots,
    wyczysc_i_scal,
    zbierz_board,
)

PLIK = ROOT / 'RAG' / 'pytania_realne.jsonl'


def istniejace() -> tuple[list[dict], set[str]]:
    rekordy = []
    with open(PLIK, encoding='utf-8') as f:
        for linia in f:
            rekordy.append(json.loads(linia))
    return rekordy, {r['hash'] for r in rekordy if r.get('hash')}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-stron', type=int, default=5)
    parser.add_argument('--odstep', type=float, default=ODSTEP_S)
    args = parser.parse_args()

    if args.odstep < ODSTEP_S:
        raise SystemExit(f'--odstep nie moze byc mniejszy niz {ODSTEP_S}')

    stare, znane = istniejace()
    if any(r.get('zrodlo') == 'ood' for r in stare):
        raise SystemExit('w pliku sa juz rekordy zrodlo=ood, nic nie robie')

    rp = wczytaj_robots()
    loguj(f'START OOD, boardy={list(OOD_BOARDS)}, odstep={args.odstep}, max_stron={args.max_stron}')

    watki = []
    stan = {'ostatnie': 0.0}
    with httpx.Client(headers=HEADER, timeout=20, follow_redirects=True) as client:
        for board, sciezka in OOD_BOARDS.items():
            zebrane = zbierz_board(client, rp, board, sciezka, stan, args.odstep, args.max_stron)
            loguj(f'OOD {board}: zebrano {len(zebrane)} watkow')
            print(f'{board}: {len(zebrane)} watkow')
            watki.extend(zebrane)

    surowe = [{
        'pytanie': w['tytul'],
        'strona': strona_z_boardu(w['board']),
        'lang': 'pl',
        'zrodlo': 'ood',
        'board': w['board'],
        'url': w['url'],
        'rozwiazane': w['rozwiazane'],
        'odpowiedzi': w['odpowiedzi'],
        'data': w['data'],
    } for w in watki]

    czyste = wyczysc_i_scal(surowe)
    nowe = [r for r in czyste if r['hash'] not in znane]
    print(f'po czyszczeniu {len(czyste)}, po odjeciu duplikatow z pliku {len(nowe)}')

    with open(PLIK, 'a', encoding='utf-8') as f:
        for r in nowe:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    loguj(f'OOD: dopisano {len(nowe)} rekordow do {PLIK}')
    print(f'dopisano {len(nowe)} rekordow OOD do {PLIK}')


if __name__ == '__main__':
    main()
