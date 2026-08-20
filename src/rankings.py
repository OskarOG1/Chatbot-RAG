import json
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import CrossEncoder
import unicodedata
import pickle
import os
import simplemma
from lang_config import LANG

RERANKER_NAME = 'cross-encoder/mmarco-mMiniLMv2-L12-H384-v1'
RERANKER = None
RERANKER_BATCH = int(os.getenv('RERANKER_BATCH', '16'))
RERANKER_MAX_LEN = int(os.getenv('RERANKER_MAX_LEN', '192'))

ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'
K_RRF = 60

def get_reranker():
    global RERANKER
    if RERANKER is None:
        RERANKER = CrossEncoder(RERANKER_NAME, max_length=RERANKER_MAX_LEN)
    return RERANKER

def kandydaci_rrf(query, query_emb, agent, k_surowe, lang='pl'):

    chunki = wczytaj_chunki(agent, lang)
    r_faiss = ranking_faiss(query_emb, agent, chunki, lang)
    r_bm25 = ranking_bm25(query, agent, lang)
    punkty = rrf([r_faiss, r_bm25])
    posortowane = sorted(punkty, key=punkty.get, reverse=True)

    return [(chunki[idx], punkty[idx]) for idx in posortowane][:k_surowe]

def klucz_url(chunk):
    return chunk['url']

def klucz_tresci(chunk):
    return (chunk['tytul'], chunk['tekst'])

def dedup_najlepszy(wyniki, klucz):
    najlepsze = {}
    for chunk, score in wyniki:
        k = klucz(chunk)
        if k not in najlepsze or score > najlepsze[k][1]:
            najlepsze[k] = (chunk, score)

    return list(najlepsze.values())

def search_reranked_multi(query, query_emb, agenci, k=3, k_surowe=20, lang='pl'):
    linki = []
    for agent in agenci:
        k_surowe_agenta = k_surowe[agent] if isinstance(k_surowe, dict) else k_surowe
        linki.extend(kandydaci_rrf(query, query_emb, agent, k_surowe_agenta, lang))

    if not linki:
        return []

    pary = [(query, f"{chunk['tytul']}\n{chunk['tekst']}") for chunk, _ in linki]
    scores = get_reranker().predict(pary, batch_size=RERANKER_BATCH)
    ocenione = [(chunk, float(s)) for (chunk, _), s in zip(linki, scores)]

    unikalne = dedup_najlepszy(ocenione, klucz_url)
    unikalne = dedup_najlepszy(unikalne, klucz_tresci)

    return sorted(unikalne, key=lambda p: p[1], reverse=True)[:k]


BM25_CACHE = {}
def get_bm25(agent:str, lang:str='pl'):
    klucz = (lang, agent)
    if klucz not in BM25_CACHE:
        suffix = LANG[lang]['suffix']
        with open(RAG_DIR / f'{agent}{suffix}.bm25', 'rb') as r:
         BM25_CACHE[klucz] = pickle.load(r)

    return BM25_CACHE[klucz]

FAISS_CACHE = {}
def get_faiss(agent:str, lang:str='pl'):
    klucz = (lang, agent)
    if klucz not in FAISS_CACHE:
        suffix = LANG[lang]['suffix']
        FAISS_CACHE[klucz] = faiss.read_index(str(RAG_DIR / f'{agent}{suffix}.faiss'))

    return FAISS_CACHE[klucz]

CHUNKI_CACHE = {}
def wczytaj_chunki(agent:str, lang:str='pl') -> list[dict]:
    klucz = (lang, agent)
    if klucz not in CHUNKI_CACHE:
        suffix = LANG[lang]['suffix']
        nazwa = f'chunks{suffix}.json' if agent == 'all' else f'chunks_{agent}{suffix}.json'
        sciezka_chunki = RAG_DIR / nazwa
        with open(sciezka_chunki, 'r', encoding='utf-8') as r:
            CHUNKI_CACHE[klucz] = json.load(r)

    return CHUNKI_CACHE[klucz]

def ranking_faiss(query_emb, agent:str, chunki: list[dict], lang:str='pl') -> list[int]:

  index = get_faiss(agent, lang)
  _, idx = index.search(query_emb, len(chunki))

  return [i for i in idx[0] if i != -1]

def ortografia(token, n=3):
    t = f'#{token}'
    return [t[i:i+n] for i in range(len(t) - n + 1)] if len(t) >= n else [t]

def tokenizacja(tekst:str, lang:str='pl') -> list[str]:
    wynik = []
    lemma_lang = LANG[lang]['lemma_lang']

    for slowo in tekst.split():

        lemantyzacja = simplemma.lemmatize(slowo, lang=lemma_lang)

        wynik.append(normalizacja(lemantyzacja))
        wynik.extend(ortografia(lemantyzacja, 3))
    return wynik

def normalizacja(tekst:str) -> str:

    tekst = tekst.replace('ł','l').replace('Ł','L')
    tekst = unicodedata.normalize('NFKD', tekst)
    tekst = ''.join(c for c in tekst if not unicodedata.combining(c))
    return tekst.lower()

def ranking_bm25(query:str, agent:str, lang:str='pl') -> list[int]:

    bm25 = get_bm25(agent, lang)
    wyniki = bm25.get_scores(tokenizacja(query, lang))

    return list(np.argsort(wyniki)[::-1])

def rrf(rankingi: list[list[int]]) -> dict[int, float]:

    punkty = {}
    for ranking in rankingi:

        for pozycja, idx in enumerate(ranking):
            punkty[idx] = punkty.get(idx, 0) + 1 / (K_RRF + pozycja)
            
    return punkty

def search_hybrid(query: str, query_emb, agent: str, k:int= 5, lang:str='pl') -> list[tuple]:

    chunki = wczytaj_chunki(agent, lang)
    r_faiss = ranking_faiss(query_emb, agent, chunki, lang)
    r_bm25 = ranking_bm25(query, agent, lang)
    punkty = rrf([r_faiss, r_bm25])

    posortowane = sorted(punkty, key=punkty.get, reverse=True)
    wyniki = [(chunki[idx], punkty[idx]) for idx in posortowane]
    wyniki = dedup_najlepszy(wyniki, klucz_url)
    wyniki = dedup_najlepszy(wyniki, klucz_tresci)
    return wyniki[:k]
