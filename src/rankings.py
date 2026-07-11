import json
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import unicodedata
from rank_bm25 import BM25Okapi
import pickle
from collections import Counter
import simplemma

MODEL_NAME = 'sdadas/mmlw-retrieval-roberta-base'
ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'
K_RRF = 60

BM25_CACHE = {}

def get_bm25(agent:str):
    if agent not in BM25_CACHE:
        with open(RAG_DIR / f'{agent}.bm25', 'rb') as r:
         BM25_CACHE[agent] = pickle.load(r)
    return BM25_CACHE[agent]

def wczytaj_chunki(agent:str) -> list[dict]:
    
    nazwa = 'chunks.json' if agent == 'all' else f'chunks_{agent}.json'
    sciezka_chunki = RAG_DIR / nazwa
    with open(sciezka_chunki, 'r', encoding='utf-8' ) as r:
       
        return json.load(r)

def ranking_faiss(query_emb, agent:str, chunki: list[dict]) -> list[int]:
  
  sciezka_faiss = RAG_DIR / f'{agent}.faiss'
  index = faiss.read_index(str(sciezka_faiss))
  
  D, I = index.search(query_emb, len(chunki))
  
  return list(I[0])

def ranking_bm25(query:str, agent:str) -> list[int]:

    bm25 = get_bm25(agent)
    wyniki = bm25.get_scores(tokenizacja(query))

    return list(np.argsort(wyniki)[::-1])

def tokenizacja(tekst:str) -> list[str]:
    slowa = tekst.split()
    wynik = []

    for slowo in slowa:

        lemantyzacja = simplemma.lemmatize(slowo, lang='pl')
        wynik.append(normalizacja(lemantyzacja))

    return wynik

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
    r_bm25 = ranking_bm25(query, agent)
    punkty = rrf(r_faiss, r_bm25)

    posortowane = sorted(punkty, key=punkty.get, reverse=True)

    wyniki= [(chunki[idx], punkty[idx]) for idx in posortowane] 
    wyniki = dedup(wyniki)

    return wyniki[:k]

def search_route(query:str, query_emb, k:int=5) -> tuple[str, list[tuple]]:
    
    chunki = wczytaj_chunki('all')
    r_faiss = ranking_faiss(query_emb, 'all', chunki)
    r_bm25 = ranking_bm25(query, 'all')
    punkty = rrf(r_faiss, r_bm25)

    posortowane = sorted(punkty, key=punkty.get, reverse=True)
   
    wyniki = [(chunki[idx], punkty[idx]) for idx in posortowane]
    wyniki = dedup(wyniki)
    wyniki = wyniki[:k]

    agenci = [chunk['agent'] for chunk, score in wyniki]
    agent = Counter(agenci).most_common(1)[0][0]

    return agent,wyniki

if __name__ == '__main__':
    
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_NAME)

    testy = [
        ("jak zmienić haslo", "konto"),
    ]

    for query, agent in testy:
        print(f'\n=== "{query}" [{agent}] ===')
       
        q_emb = model.encode(['zapytanie: ' + query]).astype('float32')
        faiss.normalize_L2(q_emb)
       
        wybrany_agent, wyniki = search_route(query, q_emb, k=3)
        print(f'oczekiwano: {agent} | routing: {wybrany_agent}')
        
        for chunk, score in wyniki:

            print(f'{score:.4f} | {chunk["tytul"]}')
            print(chunk['tekst'][:200])
            print('---')