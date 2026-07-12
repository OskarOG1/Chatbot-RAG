from sentence_transformers import SentenceTransformer
import faiss
from classify import vote
from rankings import search_hybrid
from agents import answer
from rankings import normalizacja
MODEL_NAME = 'sdadas/mmlw-retrieval-roberta-base'
model = SentenceTransformer(MODEL_NAME)



def run(query:str, agent:str | None=None, bielik_model:str | None=None) -> dict:
    
    query_emb = model.encode(['zapytanie: ' + query]).astype('float32')
    faiss.normalize_L2(query_emb)

    if agent is None:
        agent = vote(query_emb)
    chunks = search_hybrid(query, query_emb, agent, k=5)


    odpowiedz = answer(query, agent, chunks, bielik_model)

    zrodlo = list(dict.fromkeys(c['url'] for c, _ in chunks))
    return {'agent': agent, 
            'answer': odpowiedz, 
            'main_source': zrodlo[0] if zrodlo else None,
            'additional_sources': zrodlo[1:]}


if __name__ == '__main__':
 print(run("jak zmienić hasło", agent="konto")['agent'])
 print(run("jak zmienić hasło?")['agent'])
 print(run("jak zmienić haslo")['agent'])
 