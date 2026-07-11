from sentence_transformers import SentenceTransformer
import faiss
from classify import classify_top1
from rankings import search_hybrid
from agents import answer

MODEL_NAME = 'sdadas/mmlw-retrieval-roberta-base'
model = SentenceTransformer(MODEL_NAME)

def run(query:str) -> dict:
    query_emb = model.encode(['zapytanie: ' + query]).astype('float32')
    faiss.normalize_L2(query_emb)

    agent = classify_top1(query_emb)
    chunks = search_hybrid(query, query_emb, agent, k=5)


    odpowiedz = answer(query, agent, chunks)

    zrodlo = list(dict.fromkeys(c['url'] for c, score in chunks))
    return {'agent': agent, 
            "odpowiedz": odpowiedz, 
            'zrodla_glowne': zrodlo[0] if zrodlo else None,
            'zrodla_pozostale': zrodlo[1:]}


if __name__ == '__main__':
    wynik = run("nie pamiętam hasła do konta Allegro, jak odzyskać dostęp")
    print(f"\n[agent: {wynik['agent']}]")
    print('Źródła:')
    for url in wynik['zrodla']:
        print(url)
 