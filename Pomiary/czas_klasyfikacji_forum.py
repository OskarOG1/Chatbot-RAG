# Bramka czasu z PLAN_KLASYFIKATOR_FORUM.md: klasyfikacja ponizej 1 ms na pytanie,
# swiezy proces, 1000 powtorzen.
#
# Osobny plik, bo "swiezy proces" znaczy proces, ktory NIE ma w pamieci niczego
# z uczenia. Mierzymy sama sciezke runtime: lematyzacja pytania plus sumowanie wag
# ze slownika. Import modelu i wczytanie tablicy sa poza pomiarem, bo w produkcji
# dzieja sie raz na start kontenera.
#
# Uzycie:
#     python Pomiary/czas_klasyfikacji_forum.py

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

from pipeline import lematy  # noqa: E402
import wagi_forum  # noqa: E402

POWTORZEN = 1000
BRAMKA_MS = 1.0

PYTANIA = [
    r['pytanie']
    for r in (json.loads(l) for l in open(ROOT / 'RAG' / 'pytania_realne.jsonl', encoding='utf-8'))
    if r.get('zrodlo') == 'forum'
][:POWTORZEN]


def klasyfikuj(pytanie: str) -> tuple[str | None, float, float]:
    """Dokladnie ta sciezka, ktora poszlaby do produkcji: lematy z pipeline.lematy
    (ta sama funkcja co przy uczeniu) plus sumowanie po tablicy wag."""
    tokeny = lematy(pytanie, 'pl')
    wyniki = sorted(
        ((sum(tablica[t] for t in tokeny if t in tablica), klasa)
         for klasa, tablica in wagi_forum.WAGI.items()),
        reverse=True,
    )
    if not wyniki:
        return None, 0.0, 0.0
    najlepszy, klasa = wyniki[0]
    drugi = wyniki[1][0] if len(wyniki) > 1 else 0.0
    return klasa, najlepszy, najlepszy - drugi


def main() -> None:
    for p in PYTANIA[:20]:
        klasyfikuj(p)

    start = time.perf_counter()
    for p in PYTANIA:
        klasyfikuj(p)
    calkowity = time.perf_counter() - start

    na_pytanie_ms = calkowity / len(PYTANIA) * 1000
    print(f'pytan: {len(PYTANIA)}')
    print(f'klas w tablicy: {len(wagi_forum.WAGI)}')
    print(f'wpisow razem: {sum(len(t) for t in wagi_forum.WAGI.values())}')
    print(f'czas calkowity: {calkowity:.3f} s')
    print(f'czas na pytanie: {na_pytanie_ms:.4f} ms')
    print(f'BRAMKA (< {BRAMKA_MS} ms): ' + ('spelniona' if na_pytanie_ms < BRAMKA_MS else 'NIESPELNIONA'))


if __name__ == '__main__':
    main()
