# Wybor 50 "sensownych" pytan z outputs/pytania_realne_czyste.jsonl (etap 1 juz
# odsial obcy alfabet i tytuly bez tresci). Tu odsiewamy dalej regula: tylko forum,
# PL, i tylko tytuly, ktore wygladaja jak pytanie o Allegro (znak zapytania albo
# typowe slowo pytajne/proszace na poczatku), nie ogloszenie/skarga/dyskusja ogolna.
#
# To jest kandydatura do RECZNEGO przegladu, nie finalna lista: wypisuje kandydatow
# do pliku, zeby moc je przejrzec i odrzucic reszte spamu/zartow/nie-pytan, ktorych
# regula dlugosci nie lapie (patrz komentarz w oczysc_pytania_realne.py).
#
# Uzycie:
#     python Pomiary/filtruj_pytania_sensowne.py

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEJSCIE = ROOT / 'outputs' / 'pytania_realne_czyste.jsonl'
WYJSCIE = ROOT / 'outputs' / 'pytania_realne_kandydaci.json'

SLOWA_PYTAJNE = (
    'jak ', 'czy ', 'gdzie ', 'co ', 'kiedy ', 'ile ', 'dlaczego ', 'ktory ', 'ktora ',
    'ktore ', 'po co ', 'skad ', 'czemu ', 'w jaki ', 'na jaki ', 'jaki ', 'jaka ', 'jakie ',
)


def wyglada_jak_pytanie(tekst: str) -> bool:
    t = tekst.strip().lower()
    if '?' in t:
        return True
    return t.startswith(SLOWA_PYTAJNE)


def main() -> None:
    with open(WEJSCIE, encoding='utf-8') as f:
        wpisy = [json.loads(linia) for linia in f]

    forum_pl = [w for w in wpisy if w.get('zrodlo') == 'forum' and w.get('lang') == 'pl']
    kandydaci = [w for w in forum_pl if wyglada_jak_pytanie(w['pytanie'])]

    # Deduplikacja po tresci znormalizowanej (biale znaki), zeby nie liczyc tego samego
    # pytania dwa razy jesli powtarza sie na forum.
    widziane = set()
    unikalni = []
    for w in kandydaci:
        klucz = ' '.join(w['pytanie'].split()).lower()
        if klucz in widziane:
            continue
        widziane.add(klucz)
        unikalni.append(w)

    WYJSCIE.write_text(
        json.dumps([w['pytanie'] for w in unikalni], ensure_ascii=False, indent=1),
        encoding='utf-8',
    )
    print(f'forum PL po etapie 1: {len(forum_pl)}')
    print(f'wyglada jak pytanie: {len(kandydaci)}')
    print(f'po deduplikacji: {len(unikalni)}')
    print(f'zapisano: {WYJSCIE}')


if __name__ == '__main__':
    main()
