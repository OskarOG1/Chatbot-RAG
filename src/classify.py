from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from rankings import search_route
from rankings import get_faiss
MODEL_NAME = 'sdadas/mmlw-retrieval-roberta-base'
ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'


def classify_top1(query_emb) -> str:

    wyniki = []
    for agent in ['konto', 'zakupy', 'platnosci']:
        
        index = faiss.read_index(str(RAG_DIR / f'{agent}.faiss'))
        D, I = index.search(query_emb, k=3)
        score = D[0].mean()

        wyniki.append((agent, score))

    return max(wyniki, key=lambda x: x[1])[0]


if __name__ == '__main__':
    model = SentenceTransformer(MODEL_NAME)

    testy = [
        ("jak zmienić hasło", "konto"),
        ("nie mogę się zalogować", "konto"),
        ("jak usunąć konto", "konto"),
        ("zapomniałem loginu", "konto"),
        ("jak zmienić adres e-mail przypisany do konta", "konto"),
        ("ktoś włamał się na moje konto", "konto"),
        ("jak założyć konto firmowe", "konto"),

        ("jak śledzić przesyłkę", "zakupy"),
        ("towar nie dotarł", "zakupy"),
        ("chcę zwrócić kupiony produkt", "zakupy"),
        ("jak wystawić opinię sprzedawcy", "zakupy"),
        ("co daje allegro smart", "zakupy"),
        ("paczka przyszła uszkodzona", "zakupy"),
        ("jak złożyć reklamację", "zakupy"),

        ("jak zapłacić blikiem", "platnosci"),
        ("czym jest allegro pay", "platnosci"),
        ("nie działa moja karta", "platnosci"),
        ("jak rozłożyć zakup na raty", "platnosci"),
        ("kiedy dostanę zwrot pieniędzy", "zakupy"),
        ("jak zapłacić przelewem", "platnosci"),
    ]

    trafienia_t = 0
    for pytanie, oczekiwany in testy:

        query_emb = model.encode(["zapytanie: " + pytanie]).astype('float32')
        faiss.normalize_L2(query_emb)

        t = classify_top1(query_emb)
        trafienia_t += (t == oczekiwany)
        zt = 'Trafione' if t == oczekiwany else 'nietrafione'
        
        print(f'{pytanie:42} | ocz {oczekiwany:9} | top1 {t:9} {zt}')

    print(f'\nTop-1: {trafienia_t}/20')