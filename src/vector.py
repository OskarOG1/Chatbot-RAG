import argparse
import json
from pathlib import Path
import numpy as np
import faiss
import pickle
from rankings import tokenizacja
from rank_bm25 import BM25Okapi
from lang_config import LANG

ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'

def wczytaj_chunki(sciezka: Path, suffix: str) -> tuple[list[dict], np.ndarray]:
    with open(sciezka, 'r', encoding='utf-8') as r:
        chunki = json.load(r)

    embeddings = np.load(RAG_DIR / f'embeddings{suffix}.npy')
    return chunki, embeddings.astype('float32')

def zapisz_indeks(nazwa: str, chunki_pod: list[dict], embeddings_pod: np.ndarray, lang: str) -> None:
    embeddings_pod = embeddings_pod.copy()
    faiss.normalize_L2(embeddings_pod)

    index = faiss.IndexFlatIP(embeddings_pod.shape[1])
    index.add(embeddings_pod)
    faiss.write_index(index, str(RAG_DIR / f'{nazwa}.faiss'))

    tokeny = [tokenizacja(f"{c['tytul']}\n{c['tekst']}", lang) for c in chunki_pod]
    bm25 = BM25Okapi(tokeny)

    with open(RAG_DIR / f'{nazwa}.bm25', "wb") as w:
       pickle.dump(bm25, w)

def main(lang: str = 'pl'):
    cfg = LANG[lang]
    suffix = cfg['suffix']

    sciezka_chunks = RAG_DIR / f'chunks{suffix}.json'
    chunki, embeddings = wczytaj_chunki(sciezka_chunks, suffix)

    if lang == 'pl':
        nazwy_agentow = ['konto', 'zakupy', 'platnosci']

        for nazwa in nazwy_agentow:

            indeksy = [i for i, c in enumerate(chunki) if str(c.get('agent', "")).strip().lower() == nazwa]

            if not indeksy:

               print(f"Agent [{nazwa}]: Brak pasujących chunków w pliku.")
               continue

            agenci_chunki = [chunki[i] for i in indeksy]
            agenci_embeddings = embeddings[indeksy]

            zapisz_indeks(nazwa, agenci_chunki, agenci_embeddings, lang)

            vector_json = RAG_DIR / f'chunks_{nazwa}.json'
            with open(vector_json, 'w', encoding='utf-8') as w:
                json.dump(agenci_chunki, w, ensure_ascii=False, indent=4)

            print(f'agent [{nazwa}]: zapisano {len(indeksy)} chunkow i wektorow')

    nazwa_all = f'all{suffix}'
    zapisz_indeks(nazwa_all, chunki, embeddings, lang)
    print(f'{nazwa_all}: zapisano {len(chunki)} chunkow (faiss + bm25)')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', default='pl', choices=list(LANG))
    args = parser.parse_args()
    main(args.lang)
