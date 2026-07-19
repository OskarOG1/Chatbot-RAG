import json
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer, CrossEncoder
import unicodedata
import pickle
from collections import Counter
import simplemma

RERANKER_NAME = 'cross-encoder/mmarco-mMiniLMv2-L12-H384-v1'
# Lokalne rozwiązanie: RERANKER_NAME = 'BAAI/bge-reranker-v2-m3'
RERANKER = None
MODEL_NAME = 'sdadas/mmlw-retrieval-roberta-base'

ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'
K_RRF = 60

def get_reranker():
    global RERANKER
    if RERANKER is None:
        RERANKER = CrossEncoder(RERANKER_NAME, max_length=512)
    return RERANKER

def NO_dedup(query, query_emb, agent, k_surowe):

    chunki = wczytaj_chunki(agent)
    r_faiss = ranking_faiss(query_emb, agent, chunki)
    r_bm25 = ranking_bm25(query, agent)
    punkty = rrf([r_faiss, r_bm25])
    posortowane = sorted(punkty, key=punkty.get, reverse=True)
    
    return [(chunki[idx], punkty[idx]) for idx in posortowane][:k_surowe]

def search_reranked(query, query_emb, agent, k=3, k_surowe=20):
    return search_reranked_multi(query, query_emb, [agent], k, k_surowe)

def search_reranked_multi(query, query_emb, agenci, k=3, k_surowe=20):
    linki = []
    for agent in agenci:
        linki.extend(NO_dedup(query, query_emb, agent, k_surowe))

    if not linki:
        return []

    pary = [(query, chunk['tekst']) for chunk, _ in linki]
    scores = get_reranker().predict(pary, batch_size=16)

    najlepszy = {}
    for (chunk, _), s in zip(linki, scores):
        url, s = chunk['url'], float(s)

        if url not in najlepszy or s > najlepszy[url][0]:
            najlepszy[url] = (s, chunk)

    posortowane = sorted(najlepszy.values(), key=lambda p: p[0], reverse=True)

    return [(chunk, score) for score, chunk in posortowane][:k]
    
BM25_CACHE = {}
def get_bm25(agent:str):
    if agent not in BM25_CACHE:
        
        with open(RAG_DIR / f'{agent}.bm25', 'rb') as r:
         BM25_CACHE[agent] = pickle.load(r)

    return BM25_CACHE[agent]

FAISS_CACHE = {}
def get_faiss(agent:str):
   
    if agent not in FAISS_CACHE:
        FAISS_CACHE[agent] = faiss.read_index(str(RAG_DIR / f'{agent}.faiss'))
   
    return FAISS_CACHE[agent]

def wczytaj_chunki(agent:str) -> list[dict]:
    nazwa = 'chunks.json' if agent == 'all' else f'chunks_{agent}.json'
    sciezka_chunki = RAG_DIR / nazwa

    with open(sciezka_chunki, 'r', encoding='utf-8' ) as r:
       
        return json.load(r)

def ranking_faiss(query_emb, agent:str, chunki: list[dict]) -> list[int]:
  
  index = get_faiss(agent)
  D, I = index.search(query_emb, len(chunki))
  
  return list(I[0])

def ortografia(token, n=3):
    t = f'#{token}'
    return [t[i:i+n] for i in range(len(t) - n + 1)] if len(t) >= n else [t]

def tokenizacja(tekst:str) -> list[str]:
    wynik = []

    for slowo in tekst.split():
     
        lemantyzacja = simplemma.lemmatize(slowo, lang='pl')

        wynik.append(normalizacja(lemantyzacja))
        wynik.extend(ortografia(lemantyzacja, 3))
    return wynik

def normalizacja(tekst:str) -> str:

    tekst = tekst.replace('ł','l').replace('Ł','L')
    tekst = unicodedata.normalize('NFKD', tekst)
    tekst = ''.join(c for c in tekst if not unicodedata.combining(c))
    return tekst.lower()

def ranking_bm25(query:str, agent:str) -> list[int]:

    bm25 = get_bm25(agent)
    wyniki = bm25.get_scores(tokenizacja(query))

    return list(np.argsort(wyniki)[::-1])

def rrf(rankingi: list[list[int]]) -> dict[int, float]:

    punkty = {}
    for ranking in rankingi:

        for pozycja, idx in enumerate(ranking):
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
# zostawiony do testów, w produkcji działą search_hybrid
def search_route(query:str, query_emb, k:int=5) -> tuple[str, list[tuple]]:
    
    chunki = wczytaj_chunki('all')
    r_faiss = ranking_faiss(query_emb, 'all', chunki)
    r_bm25 = ranking_bm25(query, 'all')
    punkty = rrf([r_faiss, r_bm25])

    posortowane = sorted(punkty, key=punkty.get, reverse=True)
   
    wyniki = [(chunki[idx], punkty[idx]) for idx in posortowane]
    wyniki = dedup(wyniki)
    wyniki = wyniki[:k]

    agenci = [chunk['agent'] for chunk, _ in wyniki]
    agent = Counter(agenci).most_common(1)[0][0]

    return agent,wyniki

def search_hybrid(query: str, query_emb, agent: str, k:int= 5) -> list[tuple]:

    chunki = wczytaj_chunki(agent)
    r_faiss = ranking_faiss(query_emb, agent, chunki)
    r_bm25 = ranking_bm25(query, agent)
    punkty = rrf([r_faiss, r_bm25])

    posortowane = sorted(punkty, key=punkty.get, reverse=True)
    wyniki = [(chunki[idx], punkty[idx]) for idx in posortowane]
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

        q_emb = model.encode(['zapytanie: ' + query]).astype('float32')
        faiss.normalize_L2(q_emb)

        wybrany_agent, wyniki = search_route(query, q_emb, k=3)
        print(f'oczekiwano: {agent} | routing: {wybrany_agent}')

        for chunk, score in wyniki:
            print(f'{score:.4f} | {chunk["tytul"]}')
            print(chunk['tekst'][:200])
            print('---')
