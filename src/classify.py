from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from collections import Counter
from rankings import get_bm25
from rankings import get_faiss
from rankings import wczytaj_chunki
from rankings import tokenizacja
from rankings import rrf
MODEL_NAME = 'sdadas/mmlw-retrieval-roberta-base'
ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'

# stara metoda 17/20 pytań
"""""
def classify_top1(query_emb) -> str:

    wyniki = []
    for agent in ['konto', 'zakupy', 'platnosci']:
        
        index = faiss.read_index(str(RAG_DIR / f'{agent}.faiss'))
        D, _ = index.search(query_emb, k=5)
        score = D[0].mean()

        wyniki.append((agent, score))

    return max(wyniki, key=lambda x: x[1])[0]


def vote(query_emb, k=5) -> str:
    index = get_faiss('all')
    chunki = wczytaj_chunki('all')
    _, I = index.search(query_emb, k=k)

    agenci = [chunki[i]['agent'] for i in I[0]]
    return Counter(agenci).most_common(1)[0][0]
"""""
def vot_bm(query:str, query_emb, k=5) -> str:
 chunki = wczytaj_chunki('all')
 _, I = get_faiss('all').search(query_emb, k=5)
 r_faiss = list(I[0])
 bm25 = get_bm25('all')
 scores = bm25.get_scores(tokenizacja(query))
 r_bm25 = list(np.argsort(scores)[::-1])

 punkty = rrf([r_faiss, r_bm25])
 top = sorted(punkty, key=punkty.get, reverse=True)[:k]
 agenci = [chunki[i]['agent'] for i in top]
 return Counter(agenci).most_common(1)[0][0]

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
    """""
    trafienia_t = 0
    for pytanie, oczekiwany in testy:

        query_emb = model.encode(["zapytanie: " + pytanie]).astype('float32')
        faiss.normalize_L2(query_emb)

        t = classify_top1(query_emb)
        trafienia_t += (t == oczekiwany)
        zt = 'Trafione' if t == oczekiwany else 'nietrafione'
        
        print(f'{pytanie:42} | ocz {oczekiwany:9} | top1 {t:9} {zt}')
    
    print(f'\nTop-1: {trafienia_t}/20')
   
    trafienia_v = 0
    for pytanie, oczekiwany in testy:
        query_emb = model.encode(["zapytanie: " + pytanie]).astype('float32')
        faiss.normalize_L2(query_emb)
        v = vote(query_emb)
        trafienia_v += (v == oczekiwany)
        zv = 'Trafione' if v == oczekiwany else 'nietrafione'
        print(f'{pytanie:42} | ocz {oczekiwany:9} | vote {v:9} {zv}')
    print(f'\nvote: {trafienia_v}/20')

"""""
    trafienia_b = 0
    for pytanie, oczekiwany in testy:
        query_emb = model.encode(["zapytanie: " + pytanie]).astype('float32')
        faiss.normalize_L2( query_emb)
        b = vot_bm(pytanie, query_emb)
        trafienia_b += (b == oczekiwany)
        zb = 'Trafione' if b == oczekiwany else 'nietrafione'
        print(f'{pytanie:42} | ocz {oczekiwany:9} | vote {b:9} {zb}')
    print(f'\nvote: {trafienia_b}/20')