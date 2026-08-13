# Etap 1 czyszczenia RAG/pytania_realne.jsonl (5216 pozycji). Usuwa wylacznie to, co da sie
# rozstrzygnac regula strukturalna, bez modelu: obcy alfabet (cyrylica, chinski) i tytuly bez
# ani jednego prawdziwego slowa. Zarty, posty nie na temat i tytuly typu "Ten.... katalog" maja
# poprawne, prawdziwe slowa, wiec zadna regula dlugosci ani interpunkcji ich nie odroznia od
# realnych pytan (sprawdzone: "Zablokowane konto" i "Wielowariantowaosc" maja te sama dlugosc).
# Etap 2 (semantyczny, modelem przez api.publicai.co) jest osobnym, pozniejszym krokiem.
#
# Uzycie:
#     python Pomiary/oczysc_pytania_realne.py

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
PLIK_WEJSCIOWY = ROOT / 'RAG' / 'pytania_realne.jsonl'
PLIK_WYJSCIOWY = ROOT / 'outputs' / 'pytania_realne_czyste.jsonl'
PLIK_USUNIETYCH = ROOT / 'outputs' / 'pytania_realne_usuniete.json'

WZORZEC_SLOWA = re.compile(r'[^\W\d_]+', flags=re.UNICODE)
WZORZEC_OBCY_ALFABET = re.compile(r'[Ѐ-ӿ一-鿿]')


def realne_slowa(tekst: str) -> list[str]:
    return [w for w in WZORZEC_SLOWA.findall(tekst) if len(w) >= 2]


def powod_odrzucenia(pytanie: str) -> str | None:
    if WZORZEC_OBCY_ALFABET.search(pytanie):
        return 'obcy_alfabet'
    if len(realne_slowa(pytanie)) <= 1:
        return 'bez_tresci'
    return None


def main() -> None:
    with open(PLIK_WEJSCIOWY, encoding='utf-8') as f:
        wpisy = [json.loads(linia) for linia in f]

    zachowane = []
    usuniete = []
    for w in wpisy:
        pytanie = w.get('pytanie', '')
        powod = powod_odrzucenia(pytanie)
        if powod:
            usuniete.append({'pytanie': pytanie, 'powod': powod})
        else:
            zachowane.append(w)

    PLIK_WYJSCIOWY.parent.mkdir(exist_ok=True)
    with open(PLIK_WYJSCIOWY, 'w', encoding='utf-8') as f:
        for w in zachowane:
            f.write(json.dumps(w, ensure_ascii=False) + '\n')
    PLIK_USUNIETYCH.write_text(json.dumps(usuniete, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'wejscie: {len(wpisy)}')
    print(f'zachowane: {len(zachowane)}')
    print(f'usuniete: {len(usuniete)}')
    for powod in ('obcy_alfabet', 'bez_tresci'):
        grupa = [u for u in usuniete if u['powod'] == powod]
        print(f'\n{powod}: {len(grupa)}')
        for u in grupa:
            print('  ', repr(u['pytanie']))

    print(f'\nzapisano: {PLIK_WYJSCIOWY}')
    print(f'zapisano: {PLIK_USUNIETYCH}')
    print('\nUwaga: to tylko etap 1 (regulowy). Zarty, posty nie na temat i tytuly z poprawnymi '
          'slowami ale bez sensu (np. "Ten.... katalog") zostaja w pliku wyjsciowym, bo wymagaja '
          'oceny modelu, nie regul dlugosci/alfabetu.')


if __name__ == '__main__':
    main()
