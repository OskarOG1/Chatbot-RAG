import json
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import unicodedata

MODEL_NAME = 'sdadas/mmlw-retrieval-roberta-base'
ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'
K_RRF = 60


def wczytaj_chunki(agent:str) -> list[dict]:
    
    sciezka_chunki = RAG_DIR / f'chunks_{agent}.json'
    with open(sciezka_chunki, 'r', encoding='utf-8' ) as r:
       
        return json.load(r)

def ranking_faiss(query_emb, agent:str, chunki: list[dict]) -> list[int]:
  
  sciezka_faiss = RAG_DIR / f'{agent}.faiss'
  index = faiss.read_index(str(sciezka_faiss))
  
  D, I = index.search(query_emb, len(chunki))
  
  return list(I[0])

def ranking_bm25(query:str, chunki:list[dict]) -> list[int]:

    tokeny = [normalizacja(c['tekst']).split() for c in chunki]
    bm25 = BM25Okapi(tokeny)
    wyniki = bm25.get_scores(normalizacja(query).split())

    return list(np.argsort(wyniki)[::-1])

def normalizacja(tekst:str) -> str:

    tekst = tekst.replace('ł','l').replace('Ł','L')
    tekst = unicodedata.normalize('NFKD', tekst)
    tekst = ''.join(c for c in tekst if not unicodedata.combining(c))
    return tekst.lower()

def rrf(ranking_a: list[int], ranking_b:list[int]) -> dict[int, float]:
    
    punkty = {}
    for pozycja, idx in enumerate(ranking_a):
        punkty[idx] = punkty.get(idx, 0) + 1 / (K_RRF + pozycja)

    for pozycja, idx in enumerate(ranking_b):
        punkty[idx] = punkty.get(idx, 0) + 1 / (K_RRF + pozycja)

    return punkty

def dedup(wyniki):
    widziane = set()

    unikalne = []
    for chunk, score in wyniki:
        
        if chunk['url'] not in widziane:

            widziane.add(chunk['url'])
            unikalne.append((chunk,score))

    return unikalne

def search_hybrid(query:str,query_emb, agent:str, k: int=5) -> list[tuple]:
   
    chunki = wczytaj_chunki(agent)
    r_faiss = ranking_faiss(query_emb, agent, chunki)
    r_bm25 = ranking_bm25(query, chunki)
    punkty = rrf(r_faiss, r_bm25)

    posortowane = sorted(punkty, key=punkty.get, reverse=True)

    wyniki= [(chunki[idx], punkty[idx]) for idx in posortowane] 
    wyniki = dedup(wyniki)

    return wyniki[:k]
    
if __name__ == '__main__':
    
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_NAME)

    testy = [
        ("jak zmienić haslo", "konto"),
    ]

    for query, agent in testy:
        print(f'\n=== "{query}" [{agent}] ===')
       
        q_emb = model.encode([query]).astype('float32')
        faiss.normalize_L2(q_emb)
       
        wyniki = search_hybrid(query, q_emb, agent, k=3)
        for chunk, score in wyniki:
           
            print(f'{score:.4f} | {chunk["tytul"]}')
            print(chunk['tekst'][:200])
            print('---')