from sentence_transformers import SentenceTransformer
import faiss

from retriver import search
from rankings import search_hybrid 
from rankings import search_route
from classify import classify_top1

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
    {'query': 'czy mogę mieć dwa konta na allegro', 'agent': 'konto',
     'zrodlo_url': 'czy-mozna-uzywac-kilku-kont-na-allegro-mGwAg1dKEtr'},

    {'query': 'chcę żeby moje dane zniknęły z allegro', 'agent': 'konto',
     'zrodlo_url': 'rodo-kiedy-i-jak-mozna-usunac-swoje-dane-osobowe-z-allegro-vKvmgODrvcl'},

    {'query': 'jak włączyć dwuetapowe potwierdzanie logowania', 'agent': 'konto',
     'zrodlo_url': 'czym-jest-dwustopniowe-logowanie-i-jak-pomaga-chronic-twoje-konto-dykqg9nMKSZ'},

    {'query': 'gdzie zobaczę kiedy przyjdzie paczka', 'agent': 'zakupy',
     'zrodlo_url': 'przewidywany-czas-dostawy-twojej-przesylki-z8alPejWRt7'},

    {'query': 'jak oddać rzecz kupioną ze smartem', 'agent': 'zakupy',
     'zrodlo_url': ['jak-zwrocic-produkty-kupione-w-ramach-allegro-smart-dykrmbo5qTz',
     "metody-dostawy-i-zwrotu-przesylek-w-ramach-allegro-smart-a1WrzwbOXf6"]},

    {'query': 'czy sprzedawca jest wiarygodny', 'agent': 'zakupy',
     'zrodlo_url': ['czym-wyroznia-sie-dobry-sprzedajacy-BvGD0e6znC1',
                    'gdzie-i-jak-sprawdzic-opinie-o-sprzedajacym-5VZxXzGyas1']},

    {'query': 'nie zapłaciłem na czas za zamówienie', 'agent': 'zakupy',
     'zrodlo_url': 'co-sie-stanie-jesli-nie-oplacisz-zamowienia-9dGRXL4DBHb'},

    {'query': 'czy allegro pay kosztuje', 'agent': 'platnosci',
     'zrodlo_url': 'czy-korzystanie-z-allegro-pay-wiaze-sie-z-jakimis-oplatami-ZMWdW0Ga3ib'},

    {'query': 'chcę usunąć kartę z konta', 'agent': 'platnosci',
     'zrodlo_url': 'jak-usunac-zapisana-karte-platnicza-jDejgzrRBsd'},

    {'query': 'ile kosztują raty', 'agent': 'platnosci',
     'zrodlo_url': 'jakie-sa-koszty-zakupow-na-raty-yVBR0DY6bTv'},
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

def routing_acc():

    trafienia = 0
    for g in GOLDEN:
        
        query = g['query']
        query_emb = model.encode(['zapytanie: ' + query]).astype('float32')
        faiss.normalize_L2(query_emb)

        agent_wybrany, _ = search_route(query, query_emb, k=5)
        
        trafienia += (agent_wybrany == g['agent'])

    return trafienia / len(GOLDEN)

def routing_acc_classify():

    trafienia = 0
    for g in GOLDEN:

        query_emb = model.encode(['zapytanie: ' + g['query']]).astype('float32')
        faiss.normalize_L2(query_emb)

        agent = classify_top1(query_emb)
        trafienia += (agent == g['agent'])

    return trafienia / len(GOLDEN)

if __name__ == '__main__':

    acc_v1, pudla_v1 = search_k(search, k=3)
    acc_v2, pudla_v2 = search_k(search_hybrid, k=5)
    print('\n=== DIAGNOSTYKA PROGU ===')
    diag = []

    for g in GOLDEN:
        query = g['query']
        query_emb = model.encode(['zapytanie: ' + query]).astype('float32')
        faiss.normalize_L2(query_emb)

        wyniki = search_hybrid(query, query_emb, g['agent'], k=5)
        top_score = wyniki[0][1]

        trafil = query not in pudla_v2
        diag.append((top_score, trafil, query))

    diag.sort()
    
    for score, trafil, query in diag:
        znacznik = 'OK ' if trafil else 'PUD'
        print(f'{score:.4f} | {znacznik} | {query}')
    print(f'v1 (pure vector) Hit@3: {acc_v1:.2f}')
    print(f'v2 (hybrid)      Hit@3: {acc_v2:.2f}')
    print(f'\nv1 pudła ({len(pudla_v1)}): {pudla_v1}')
    print(f'v2 pudła ({len(pudla_v2)}): {pudla_v2}')
    print(f'\nrouting (hybrid) acc: {routing_acc():.2f}')
    print(f'routing classify_top1: {routing_acc_classify():.2f}')
    
