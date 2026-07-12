from sentence_transformers import SentenceTransformer
import faiss
from classify import vote
from rankings import search_hybrid
from agents import answer
from rankings import normalizacja
MODEL_NAME = 'sdadas/mmlw-retrieval-roberta-base'
model = SentenceTransformer(MODEL_NAME)

pytania = [
   
    "Zapomniałem hasła, jak je odzyskać?",
    "Jak skasować swoje konto?",
    "Ktoś mógł włamać się na moje konto, co robić?",
    "Gdzie zmienię adres e-mail przypisany do konta?",
    "Jak włączyć logowanie dwuskładnikowe?",
  
    "Paczka nie dotarła, a status mówi że dostarczono - co teraz?",
    "Chcę oddać towar, który mi nie pasuje.",
    "Sprzedawca nie odpowiada na wiadomości, jak złożyć reklamację?",
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
    linie = []

    for i, p in enumerate(pytania, 1):
        wynik = run(p)
        blok = (
            f"{'='*60}\n"
            f"[{i}] PYTANIE: {p}\n"
            f"AGENT: {wynik['agent']}\n"
            f"MAIN: {wynik['main_source']}\n"
            f"ODPOWIEDŹ:\n{wynik['answer']}\n"
        )
        print(blok)
        linie.append(blok)

    with open('outputs/eval_1.5b.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(linie))