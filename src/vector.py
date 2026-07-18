import json
from pathlib import Path
import numpy as np 
import faiss
import pickle
from rankings import tokenizacja
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'

def wczytaj_chunki(sciezka: Path) -> tuple[list[dict], np.ndarray]:
    with open(sciezka, 'r', encoding='utf-8') as r:
        chunki = json.load(r)
   
    embeddings = np.load(RAG_DIR / 'embeddings.npy')
    return chunki, embeddings.astype('float32')

def main():

    sciezka_chunks = RAG_DIR / 'chunks.json'
    chunki, embeddings = wczytaj_chunki(sciezka_chunks)
    nazwy_agentow = ['konto', 'zakupy', 'platnosci']

    for nazwa in nazwy_agentow:

        indeksy = [i for i, c in enumerate(chunki) if str(c.get('agent', "")).strip().lower() == nazwa]
       
        if not indeksy:
           
           print(f"Agent [{nazwa}]: Brak pasujących chunków w pliku.")
           continue

        agenci_chunki = [chunki[i] for i in indeksy]
        agenci_embeddings = embeddings[indeksy]

        faiss.normalize_L2(agenci_embeddings)
      
        index = faiss.IndexFlatIP(768)
        index.add(agenci_embeddings)

        faiss.write_index(index, str(RAG_DIR / f'{nazwa}.faiss'))

        vector_json = RAG_DIR / f'chunks_{nazwa}.json'
        with open(vector_json, 'w', encoding='utf-8') as w:
            json.dump(agenci_chunki, w, ensure_ascii=False, indent=4)
        
        tokeny = [tokenizacja(f"{c['tytul']}\n{c['tekst']}") for c in agenci_chunki]
        bm25 = BM25Okapi(tokeny)
        

        with open(RAG_DIR / f'{nazwa}.bm25', "wb") as w:
           pickle.dump(bm25, w)

    emb_all = embeddings.copy()
    faiss.normalize_L2(emb_all)

    index_all = faiss.IndexFlatIP(emb_all.shape[1])
    index_all.add(emb_all)
    faiss.write_index(index_all, str(RAG_DIR / "all.faiss"))
       
    tokeny_all = [tokenizacja(f"{c['tytul']}\n{c['tekst']}") for c in chunki]
    bm25_all =  BM25Okapi(tokeny_all)
    with open(RAG_DIR / "all.bm25", "wb") as w:
       pickle.dump(bm25_all, w)

    print(f'agent [{nazwa}]:zapisano {len(indeksy)} chunkow i wektorow')
    print(f'all: zapisano {len(chunki)} chunkow (faiss + bm25)' )
if __name__ == '__main__':
    main()