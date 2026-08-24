# Wybor 50 z outputs/pytania_realne_kandydaci.json (1627 kandydatow po filtrze
# strukturalnym w filtruj_pytania_sensowne.py). Indeksy wybrane recznie po przegladzie
# pierwszych ~150 kandydatow: pytania trzymajace sie tematu Allegro (konto, oferty,
# wysylka, zwroty, platnosci), bez zartow/skarg bez pytania i bez duplikatow tematu
# ponad dwa warianty. Wybor przez INDEKS, nie przez przepisanie tresci, zeby nie
# zmienic ani jednego znaku oryginalnego pytania (polskie ogonki, literowki uzytkownika).
#
# Uzycie:
#     python Pomiary/wybierz_50_realnych.py

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEJSCIE = ROOT / 'outputs' / 'pytania_realne_kandydaci.json'
WYJSCIE = ROOT / 'outputs' / 'pytania_realne_50.json'

INDEKSY = [
    0, 2, 3, 4, 9, 10, 11, 12, 13, 14, 18, 22, 23, 25, 26, 28, 31, 33, 35, 37,
    41, 47, 49, 54, 55, 56, 61, 64, 67, 69, 70, 71, 73, 75, 78, 80, 84, 92, 95, 97,
    103, 107, 113, 116, 124, 136, 140, 141, 145, 147,
]


def main() -> None:
    kandydaci = json.loads(WEJSCIE.read_text(encoding='utf-8'))
    assert len(INDEKSY) == 50, len(INDEKSY)
    assert len(set(INDEKSY)) == 50, 'powtorzony indeks'
    wybrane = [kandydaci[i] for i in INDEKSY]
    WYJSCIE.write_text(json.dumps(wybrane, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'wybrano {len(wybrane)} pytan, zapisano {WYJSCIE}')
    for i, p in enumerate(wybrane, 1):
        print(f'{i:2d}. {p}')


if __name__ == '__main__':
    main()
