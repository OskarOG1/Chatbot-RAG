from sentence_transformers import SentenceTransformer
import faiss
from classify import vote
from rankings import search_reranked_multi
from agents import answer
from guards import sprawdz
from spell import correct
MODEL_NAME = 'sdadas/mmlw-retrieval-roberta-base'
model = SentenceTransformer(MODEL_NAME)
MARGINES = 2
OKNO_HISTORII = 3

pytania = [
   
    "Jak sprawdzić, gdzie jest moja przesyłka?",
    "Kupiłem coś przez pomyłkę, da się anulować zamówienie?",
    "Czy mogę odebrać zamówienie w automacie paczkowym?",
    "Towar przyszedł uszkodzony, co mi przysługuje?",
    "Jak długo mam na zwrot po odebraniu paczki?",
    "Sprzedawca chce, żebym zapłacił poza Allegro - czy to bezpieczne?",
    
    "Jak rozłożyć zakup na raty?",
    "Płatność się nie powiodła, a pieniądze zniknęły z konta.",
    "Gdzie znajdę fakturę za zakupy?",
    "Jak dodać nową kartę do płatności?",
    "Czy mogę zapłacić BLIKIEM?",
    "Ile kosztuje przesyłka kurierem?",
]


def run(query:str, agent:str | None=None, bielik_model:str | None=None,
        history:list[dict] | None=None) -> dict:
    powod = sprawdz(query)
    if powod:
        return {'agent': '', 'answer': powod, 'sources': [], 'citations': []}
    history = (history or [])[-OKNO_HISTORII:]
    query = correct(query)['poprawione']

    poprzedni_user = [w['content'] for w in history if w['role'] == 'user'][-1:]
    zapytanie_ret = ' '.join(poprzedni_user + [query])
    query_emb = model.encode(['zapytanie: ' + zapytanie_ret]).astype('float32')
    faiss.normalize_L2(query_emb)

    if agent is None:
        agenci = vote(query_emb, top2=True, margines=MARGINES)
    else:
        agenci = [agent]
    chunks = search_reranked_multi(zapytanie_ret, query_emb, agenci, k=5, k_surowe=20)

    agent_odp = chunks[0][0]['agent'] if chunks else agenci[0]
    odpowiedz = answer(query, agent_odp, chunks, bielik_model, history)

    zrodla = list(dict.fromkeys(c['url'] for c, _ in chunks))
    return {'agent': agent_odp,
            'answer': odpowiedz['tekst'],
            'sources': zrodla,
            'citations': odpowiedz['cytaty']}


if __name__ == '__main__':
    linie = []

    for i, p in enumerate(pytania, 1):
        wynik = run(p)
        blok = (
            f"{'='*60}\n"
            f"[{i}] PYTANIE: {p}\n"
            f"AGENT: {wynik['agent']}\n"
            f"SOURCES: {wynik['sources']}\n"
            f"ODPOWIEDŹ:\n{wynik['answer']}\n"
        )
        print(blok)
        linie.append(blok)

    with open('outputs/eval_1.5b.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(linie))
