from pathlib import Path
import numpy as np
import json
import faiss
from sentence_transformers import SentenceTransformer

MODEL_NAME = 'sdadas/mmlw-retrieval-roberta-base'

def search(query,query_emb, agent, k=5 ):

    sciezka_indexu = Path(__file__).parent / f'{agent}.faiss'
    
    index = faiss.read_index(str(sciezka_indexu))
    D,I = index.search(query_emb, k)

    sciezka_chunki = Path(__file__).parent / f'chunks_{agent}.json'
    with open(sciezka_chunki, 'r', encoding='utf-8') as r:
        agent_chunks = json.load(r)

    wyniki = [(agent_chunks[idx], float(score)) for idx, score in zip(I[0], D[0])]
    return wyniki

if __name__ == '__main__':
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_NAME)
    q = "nie pamiętam hasła do konta Allegro, jak odzyskać dostęp"
    q_emb = model.encode([q]).astype('float32')
    faiss.normalize_L2(q_emb)
    wyniki = search(q, q_emb, "konto", k=3)
    for chunk, score in wyniki:
        print(f'{score:.3f} | {chunk["tytul"]}')
        print(chunk['tekst'][:200])
        print('---')
