# Kolejnosc krok 1 z PLAN_POMIARY_GPU.md: bramka przed serwerem GPU. Na 50 pytaniach z
# RAG/pytania_realne.jsonl liczy chunks_szerokie i strony.rozstrzygnij() dwoma sciezkami,
# zywym modelem (rankings.search_reranked_multi) i odczytem z ad hoc policzonej tablicy
# (tablica_rerank.search_reranked_multi_z_tablicy), i porownuje zwyciezce oraz czy_pytac
# bit w bit. Sprawdzenie fingerprintu jest tu pominiete celowo: tablica jest liczona w
# pamieci na potrzeby tego testu, nie wczytywana z outputs/tablica_rerank.json.
#
# Uzycie:
#     python weryfikuj_tablice.py --n 25

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import faiss
from sentence_transformers import SentenceTransformer

import rankings
import strony
import tablica_rerank
from lang_config import LANG
from rankings import get_reranker
from buduj_tablice_wynikow import oblicz_wpis
from measure_routing_strony import wczytaj_realny
from tablica_rerank import klucz


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, default=25, help='pytan na strone, razem 2x tyle')
    parser.add_argument('--top-n', type=int, default=30)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    zapytania = (wczytaj_realny('kupujacy', args.n, args.seed)
                 + wczytaj_realny('sprzedaz', args.n, args.seed))
    print(f'pytan do porownania: {len(zapytania)}')

    embedery = {'pl': SentenceTransformer(LANG['pl']['embedder'])}
    reranker = get_reranker()

    tablica_wyniki = {}
    for query in zapytania:
        tablica_wyniki[klucz('pl', query)] = oblicz_wpis(query, 'pl', embedery, reranker, args.top_n, 16)
    tablica = {'odcisk': {'top_n': args.top_n}, 'wyniki': tablica_wyniki}

    niezgodne = []
    for query in zapytania:
        prior, sila = strony.prior_strony(query, None, 'pl', False)
        kwoty = strony.przydzial_kandydatow(prior, sila)

        emb = embedery['pl'].encode([LANG['pl']['query_prefix'] + query]).astype('float32')
        faiss.normalize_L2(emb)
        chunks_model = rankings.search_reranked_multi(query, emb, list(kwoty), k=10, k_surowe=kwoty, lang='pl')
        zwyciezca_model, _, pytac_model = strony.rozstrzygnij(chunks_model, prior, sila, k=5)

        chunks_tabela = tablica_rerank.search_reranked_multi_z_tablicy(
            tablica, query, list(kwoty), k=10, k_surowe=kwoty, lang='pl')
        zwyciezca_tabela, _, pytac_tabela = strony.rozstrzygnij(chunks_tabela, prior, sila, k=5)

        if (zwyciezca_model, pytac_model) != (zwyciezca_tabela, pytac_tabela):
            niezgodne.append({
                'query': query,
                'model': (zwyciezca_model, pytac_model),
                'tabela': (zwyciezca_tabela, pytac_tabela),
            })

    print(f'zgodnosc bit w bit: {len(zapytania) - len(niezgodne)}/{len(zapytania)}')
    for n in niezgodne:
        print(f'  NIEZGODNE: {n["query"][:60]!r} model={n["model"]} tabela={n["tabela"]}')

    if not niezgodne:
        print('BRAMKA PRZESZLA: tablica i zywy model daja identyczne rozstrzygnij() na tej probce.')
    else:
        print('BRAMKA NIE PRZESZLA: architektura tablicy nie jest bit w bit zgodna z modelem.')


if __name__ == '__main__':
    main()
