# Krok 1 z PLAN_KLASYFIKATOR_FORUM.md: inwentarz RAG/pytania_realne.jsonl.
#
# Bramka planu: dla zrodla 'forum' pola board i url niepuste w co najmniej 0,99
# rekordow. Bez etykiety i bez adresu watku nie ma czego uczyc ani co pokazac.
#
# Liczone na SUROWYM pliku (dane_forum.wczytaj_surowe), nie na przefiltrowanym
# wczytaj(): bramka policzona po filtrze wyszlaby 1,0 z definicji.
#
# Uzycie:
#     python Pomiary/inwentarz_pytan.py

import json
from collections import Counter

import dane_forum

WYJSCIE = dane_forum.OUT_DIR / 'inwentarz_pytan.json'
BRAMKA_POKRYCIA = 0.99


def percentyle(wartosci: list[int]) -> dict:
    """p05, mediana i p95 zamiast sredniej: rozklad dlugosci tytulow jest skosny,
    a interesuje nas jego ksztalt, nie srodek ciezkosci."""
    if not wartosci:
        return {'mediana': 0, 'p05': 0, 'p95': 0}
    posortowane = sorted(wartosci)
    n = len(posortowane)

    def kwantyl(q: float) -> int:
        return posortowane[min(n - 1, max(0, int(round(q * (n - 1)))))]

    return {'mediana': kwantyl(0.50), 'p05': kwantyl(0.05), 'p95': kwantyl(0.95)}


def main() -> None:
    rekordy = dane_forum.wczytaj_surowe()
    forum = [r for r in rekordy if r.get('zrodlo') == 'forum']

    po_zrodle = Counter(r.get('zrodlo') for r in rekordy)
    po_boardzie = Counter(r['board'] for r in forum if r.get('board'))
    po_stronie = Counter(str(r.get('strona')) if r.get('strona') else 'null' for r in rekordy)
    po_roku = Counter((r.get('data') or 'brak')[:4] for r in rekordy)
    po_foldzie = Counter(dane_forum.fold(r['pytanie']) for r in rekordy)

    board_niepusty = sum(1 for r in forum if r.get('board')) / len(forum) if forum else 0.0
    url_niepusty = sum(1 for r in forum if r.get('url')) / len(forum) if forum else 0.0

    znaki = [len(r['pytanie']) for r in rekordy]
    lematy = [len(dane_forum.lematy_pytania(r['pytanie'])) for r in rekordy]

    wynik = {
        'n': len(rekordy),
        'po_zrodle': dict(po_zrodle.most_common()),
        'po_boardzie': dict(po_boardzie.most_common()),
        'po_stronie': dict(po_stronie.most_common()),
        'po_roku': dict(sorted(po_roku.items())),
        'po_foldzie': dict(po_foldzie.most_common()),
        'udzial_foldow': {k: round(v / len(rekordy), 3) for k, v in po_foldzie.most_common()},
        'board_niepusty': round(board_niepusty, 4),
        'url_niepusty': round(url_niepusty, 4),
        'dlugosc_znaki': percentyle(znaki),
        'dlugosc_lematy': percentyle(lematy),
        'boardow': len(po_boardzie),
    }

    dane_forum.OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(WYJSCIE, 'w', encoding='utf-8') as f:
        json.dump(wynik, f, ensure_ascii=False, indent=1)

    print(f'rekordow: {wynik["n"]}')
    print(f'po zrodle: {wynik["po_zrodle"]}')
    print(f'boardow: {wynik["boardow"]}')
    for board, ile in po_boardzie.most_common():
        print(f'  {board:32s} {ile}')
    print(f'po stronie: {wynik["po_stronie"]}')
    print(f'po roku: {wynik["po_roku"]}')
    print(f'po foldzie: {wynik["po_foldzie"]} -> udzial {wynik["udzial_foldow"]}')
    print(f'dlugosc w znakach: {wynik["dlugosc_znaki"]}')
    print(f'dlugosc w lematach: {wynik["dlugosc_lematy"]}')
    print()
    print(f'board niepusty (forum): {wynik["board_niepusty"]}')
    print(f'url niepusty (forum):   {wynik["url_niepusty"]}')

    spelniona = board_niepusty >= BRAMKA_POKRYCIA and url_niepusty >= BRAMKA_POKRYCIA
    print(f'BRAMKA (>= {BRAMKA_POKRYCIA}): ' + ('spelniona' if spelniona else 'NIESPELNIONA'))
    print(f'zapisano {WYJSCIE}')


if __name__ == '__main__':
    main()
