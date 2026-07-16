from pathlib import Path
import numpy as np
import json
import faiss
from sentence_transformers import SentenceTransformer

MODEL_NAME = 'sdadas/mmlw-retrieval-roberta-base'
ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'


def search(query_emb, agent, k=5):

    sciezka_indexu = RAG_DIR / f'{agent}.faiss'
    
    index = faiss.read_index(str(sciezka_indexu))
    D,I = index.search(query_emb, k)

    sciezka_chunki = RAG_DIR / f'chunks_{agent}.json'
    with open(sciezka_chunki, 'r', encoding='utf-8') as r:
        agent_chunks = json.load(r)

    wyniki = [(agent_chunks[idx], float(score)) for idx, score in zip(I[0], D[0])]
    return wyniki

if __name__ == '__main__':

    model = SentenceTransformer(MODEL_NAME)

    q = "nie pamiętam hasła do konta Allegro, jak odzyskać dostęp"
    q_emb = model.encode(['zapytanie: ' + q]).astype('float32')
    faiss.normalize_L2(q_emb)
   
    wyniki = search(q, q_emb, "konto", k=3)
    for chunk, score in wyniki:
        
        print(f'{score:.3f} | {chunk["tytul"]}')
        print(chunk['tekst'][:200])
        print('---')
