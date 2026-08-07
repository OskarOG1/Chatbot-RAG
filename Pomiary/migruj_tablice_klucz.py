# P8 (PLAN_KALIBRACJA_R9.md): migruje istniejacy outputs/tablica_rerank.json ze starego klucza
# (sam tekst pytania) na nowy klucz lang|pytanie (patrz tablica_rerank.klucz). Lang kazdego
# pytania odczytuje z buduj_tablice_wynikow.wczytaj_pytania(), tego samego zrodla, ktore
# zbudowalo tablice, bez potrzeby GPU (tablica juz ma policzone wyniki, migracja tylko
# przepisuje klucze slownika).
#
# Uzycie:
#     python migruj_tablice_klucz.py

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from buduj_tablice_wynikow import wczytaj_pytania
from tablica_rerank import klucz

OUT_DIR = ROOT / 'outputs'
PLIK = OUT_DIR / 'tablica_rerank.json'


def main() -> None:
    with open(PLIK, encoding='utf-8') as f:
        tablica = json.load(f)

    stare_klucze = list(tablica['wyniki'].keys())
    if all('|' in k and k.split('|', 1)[0] in ('pl', 'en') for k in stare_klucze):
        print('tablica juz ma nowy format kluczy (lang|pytanie), migracja niepotrzebna.')
        return

    pytania_lang = dict(wczytaj_pytania())
    print(f'stare wpisy: {len(stare_klucze)}, znane pytania z lang: {len(pytania_lang)}')

    nowe_wyniki = {}
    brak_lang = []
    for query in stare_klucze:
        lang = pytania_lang.get(query)
        if lang is None:
            brak_lang.append(query)
            continue
        nowe_wyniki[klucz(lang, query)] = tablica['wyniki'][query]

    print(f'zmigrowane: {len(nowe_wyniki)}, bez znanego lang (pominiete): {len(brak_lang)}')
    if brak_lang:
        for q in brak_lang[:20]:
            print(f'  BRAK LANG: {q[:80]!r}')
        print('przerwano, plik wejsciowy nietkniety: wpisy bez znanego lang oznaczaja rozjazd '
              'wczytaj_pytania() ze zrodlem tablicy, nie powod do skrocenia artefaktu.')
        sys.exit(1)

    kopia = PLIK.with_suffix('.json.bak')
    shutil.copy2(PLIK, kopia)
    print(f'kopia zapasowa: {kopia}')

    tablica['wyniki'] = nowe_wyniki
    tymczasowy = PLIK.with_suffix('.json.tmp')
    tymczasowy.write_text(json.dumps(tablica, ensure_ascii=False), encoding='utf-8')
    os.replace(tymczasowy, PLIK)
    print(f'zapisano: {PLIK}')


if __name__ == '__main__':
    main()
