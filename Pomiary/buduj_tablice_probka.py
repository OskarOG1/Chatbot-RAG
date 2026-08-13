# Z4 (PLAN_PRZEGLAD_O8_O11_O12.md): buduje malą tablice rerankera dla wskazanego zestawu pytan,
# na CPU, tym samym oblicz_wpis() co pelna buduj_tablice_wynikow.py. Sluzy do domkniecia bramki
# parytetu Z4 bez karty CUDA: 100 pytan razy dwoch agentow razy top_n par to kilka minut na CPU,
# podczas gdy pelne 5299 pytan wymaga GPU.
#
# Dlaczego to jest uczciwy test bramki: parytet sprawdza, czy replay z tablicy stosuje te sama
# regule dedupu co produkcja. Tablica zbudowana na tym samym urzadzeniu, na ktorym liczy sie
# potem produkcja, izoluje regule od szumu numerycznego GPU kontra CPU (patrz naglowek
# wzbogac_tablice_sha.py), czyli mierzy dokladnie to, o co chodzi w Z4.
#
# Uzycie:
#     python Pomiary/buduj_tablice_probka.py
#     python Pomiary/buduj_tablice_probka.py --top-n 30 --wyjscie outputs/tablica_probka.json

import argparse
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
POMIARY = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(POMIARY))

from sentence_transformers import SentenceTransformer

from lang_config import LANG
from rankings import get_reranker
from buduj_tablice_wynikow import oblicz_wpis, odciski_korpusu, zapisz
from tablica_rerank import klucz


def wczytaj_realne() -> list[str]:
    dane = json.loads((ROOT / 'outputs' / 'measure_md_sedzia.json').read_text(encoding='utf-8'))
    return [x['query'] for x in dane['REALNE']]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--top-n', type=int, default=30)
    parser.add_argument('--wsad', type=int, default=16)
    parser.add_argument('--wyjscie', default=str(ROOT / 'outputs' / 'tablica_probka.json'))
    args = parser.parse_args()

    pytania = [(q, 'pl') for q in wczytaj_realne()]
    print(f'pytan: {len(pytania)}, top_n={args.top_n}, urzadzenie: cpu')

    embedery = {'pl': SentenceTransformer(LANG['pl']['embedder'])}
    reranker = get_reranker()
    sha_chunkow, sha_faiss, sha_bm25 = odciski_korpusu()

    wyniki = {}
    start = time.time()
    for i, (query, lang) in enumerate(pytania, 1):
        wyniki[klucz(lang, query)] = oblicz_wpis(query, lang, embedery, reranker,
                                                  args.top_n, args.wsad)
        if i % 20 == 0:
            tempo = (time.time() - start) / i
            print(f'[{i}/{len(pytania)}] {tempo:.2f} s/pytanie, zostalo '
                  f'{tempo * (len(pytania) - i) / 60:.1f} min', flush=True)

    sciezka = Path(args.wyjscie)
    zapisz(sciezka, wyniki, sha_chunkow, sha_faiss, sha_bm25, 'cpu', args.top_n)
    print(f'\nzbudowano w {(time.time() - start) / 60:.1f} min')
    print(f'zapisano: {sciezka}')


if __name__ == '__main__':
    main()
