from sentence_transformers import SentenceTransformer
import faiss
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from retriver import search
from rankings import search_hybrid 


MODEL_NAME = 'sdadas/mmlw-retrieval-roberta-base'
model = SentenceTransformer(MODEL_NAME)

GOLDEN = [
    {"query": "jak zmienić hasło", "agent": "konto", "zrodlo_url": "jak-zmienic-haslo-na-allegro-B826XYkbXsA"},
    {"query": "nie mogę się zalogować", "agent": "konto", "zrodlo_url": "jak-odzyskac-dostep-do-konta-gdy-nie-mozesz-sie-zalogowac-0KvwX8YAocP"},
    {"query": "jak usunąć konto", "agent": "konto", "zrodlo_url": "jak-zamknac-konto-na-allegro-PDa207G8aun"},
    {"query": "zapomniałem loginu", "agent": "konto", "zrodlo_url": "jak-odzyskac-dostep-do-konta-gdy-nie-mozesz-sie-zalogowac-0KvwX8YAocP"},
    {"query": "jak zmienić adres e-mail przypisany do konta", "agent": "konto", "zrodlo_url": "co-i-kiedy-mozna-zmienic-w-danych-swojego-konta-GDeq5Wq1lSd"},
    {"query": "ktoś włamał się na moje konto", "agent": "konto", "zrodlo_url": "jak-odzyskac-dostep-do-konta-gdy-nie-mozesz-sie-zalogowac-0KvwX8YAocP"},
    {"query": "jak założyć konto firmowe", "agent": "konto", "zrodlo_url": "jakie-sa-roznice-miedzy-kontem-zwyklym-a-kontem-firmowym-Oqxkval7aS7"},

    {"query": "jak śledzić przesyłkę", "agent": "zakupy", "zrodlo_url": "gdzie-sprawdzisz-numer-i-status-swojej-przesylki-LvP7agrzOhw"},
    {"query": "towar nie dotarł", "agent": "zakupy", "zrodlo_url": "co-mozesz-zrobic-gdy-czekasz-na-przesylke-zbyt-dlugo-xG71gn36qC4"},
    {"query": "chcę zwrócić kupiony produkt", "agent": "zakupy", "zrodlo_url": "jak-zwrocic-produkty-kupione-w-ramach-allegro-smart-dykrmbo5qTz"},
    {"query": "jak wystawić opinię sprzedawcy", "agent": "zakupy", "zrodlo_url": "jak-wystawic-ocene-sprzedajacemu-mGwAg1LxPFW"},
    {"query": "co daje allegro smart", "agent": "zakupy", "zrodlo_url": "czym-jest-usluga-allegro-smart-i-jak-z-niej-korzystac-mGwb5Pq6vIL"},
    {"query": "paczka przyszła uszkodzona", "agent": "zakupy", "zrodlo_url": "jak-dziala-allegro-ochrona-kupujacych-qzdAg2Klbsl"},
    {"query": "jak złożyć reklamację", "agent": "zakupy", "zrodlo_url": "jak-rozpoczac-dyskusje-i-wyjasnic-problem-ze-sprzedajacym-WEDKYqnEvik"},

    {"query": "jak zapłacić blikiem", "agent": "platnosci", "zrodlo_url": "jak-zaplacic-za-zakupy-blikiem-1Mk5XgWKMu3"},
    {"query": "czym jest allegro pay", "agent": "platnosci", "zrodlo_url": "czym-jest-i-jak-dziala-allegro-pay-9dmDRk7x7HP"},
    {"query": "nie działa moja karta", "agent": "platnosci", "zrodlo_url": "jak-zaplacic-karta-za-zakupy-z8DmgWz2wIo"},
    {"query": "jak rozłożyć zakup na raty", "agent": "platnosci", "zrodlo_url": "jak-kupowac-na-raty-rKxBgYZnDIX"},
    {"query": "kiedy dostanę zwrot pieniędzy", "agent": "zakupy", "zrodlo_url": [
        "co-zrobic-aby-dostac-rekompensate-w-ramach-allegro-ochrony-kupujacych-KM54xY0avCo",
        "jak-dziala-allegro-ochrona-kupujacych-qzdAg2Klbsl",
    ]},
    {"query": "jak zapłacić przelewem", "agent": "platnosci", "zrodlo_url": "jak-zaplacic-za-przedmiot-kupiony-na-allegro-YLKol7RVxI0"},
]

def search_k(search_fn, k=3):

    trafienia = 0
    pudla = []

    for g in GOLDEN:

        query = g['query']
        query_emb = model.encode(['zapytanie: ' + query]).astype('float32')
        faiss.normalize_L2(query_emb)

        wyniki = search_fn(query, query_emb, g['agent'], k=k)
        url = [chunk['url'] for chunk, score in wyniki]

        zrodla = g['zrodlo_url'] if isinstance(g['zrodlo_url'],list) else [g['zrodlo_url']]                              
        if any(z in u for z in zrodla for u in url):
            trafienia += 1

        else:

            pudla.append(query)

            print(f'\n✗ "{query}" [{g["agent"]}]')
            print(f'  oczekiwano: {zrodla}')

            for chunk, score in wyniki:
                print(f'  {score:.4f} | {chunk["url"].split("/")[-1]}')

    return trafienia / len(GOLDEN), pudla
if __name__ == '__main__':

    acc_v1, pudla_v1 = search_k(search, k=3)
    acc_v2, pudla_v2 = search_k(search_hybrid, k=3)
    
    print(f'v1 (pure vector) Hit@3: {acc_v1:.2f}')
    print(f'v2 (hybrid)      Hit@3: {acc_v2:.2f}')
    print(f'\nv1 pudła ({len(pudla_v1)}): {pudla_v1}')
    print(f'v2 pudła ({len(pudla_v2)}): {pudla_v2}')