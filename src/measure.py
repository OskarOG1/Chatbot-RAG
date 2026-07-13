from sentence_transformers import SentenceTransformer
import faiss
import math
import unicodedata
import simplemma
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
    {"query": "czy mogę mieć dwa konta na allegro", "agent": "konto",
     "zrodlo_url": "czy-mozna-uzywac-kilku-kont-na-allegro-mGwAg1dKEtr"},
    {"query": "chcę żeby moje dane zniknęły z allegro", "agent": "konto",
     "zrodlo_url": "rodo-kiedy-i-jak-mozna-usunac-swoje-dane-osobowe-z-allegro-vKvmgODrvcl"},
    {"query": "jak włączyć dwuetapowe potwierdzanie logowania", "agent": "konto",
     "zrodlo_url": "czym-jest-dwustopniowe-logowanie-i-jak-pomaga-chronic-twoje-konto-dykqg9nMKSZ"},
    {"query": "gdzie zobaczę kiedy przyjdzie paczka", "agent": "zakupy",
     "zrodlo_url": "przewidywany-czas-dostawy-twojej-przesylki-z8alPejWRt7"},
    {"query": "jak oddać rzecz kupioną ze smartem", "agent": "zakupy",
     "zrodlo_url": ["jak-zwrocic-produkty-kupione-w-ramach-allegro-smart-dykrmbo5qTz",
                    "metody-dostawy-i-zwrotu-przesylek-w-ramach-allegro-smart-a1WrzwbOXf6"]},
    {"query": "czy sprzedawca jest wiarygodny", "agent": "zakupy",
     "zrodlo_url": ["czym-wyroznia-sie-dobry-sprzedajacy-BvGD0e6znC1",
                    "gdzie-i-jak-sprawdzic-opinie-o-sprzedajacym-5VZxXzGyas1"]},
    {"query": "nie zapłaciłem na czas za zamówienie", "agent": "zakupy",
     "zrodlo_url": "co-sie-stanie-jesli-nie-oplacisz-zamowienia-9dGRXL4DBHb"},
    {"query": "czy allegro pay kosztuje", "agent": "platnosci",
     "zrodlo_url": "czy-korzystanie-z-allegro-pay-wiaze-sie-z-jakimis-oplatami-ZMWdW0Ga3ib"},
    {"query": "chcę usunąć kartę z konta", "agent": "platnosci",
     "zrodlo_url": "jak-usunac-zapisana-karte-platnicza-jDejgzrRBsd"},
    {"query": "ile kosztują raty", "agent": "platnosci",
     "zrodlo_url": "jakie-sa-koszty-zakupow-na-raty-yVBR0DY6bTv"},
]


def embed(query):

    query_emb = model.encode(['zapytanie: ' + query]).astype('float32')
    faiss.normalize_L2(query_emb)

    return query_emb


def zrodla_jako_lista(g):
    z = g['zrodlo_url']

    return z if isinstance(z, list) else [z]

def ogonki(tekst):

    tekst = tekst.replace("ł", 'l').replace('Ł', 'L')
    normalizacja = unicodedata.normalize('NFKD', tekst)
    
    return ''.join(znak for znak in normalizacja if not unicodedata.combining(znak))

def zapytania(query):

    slowa = query.split()
    wynik = set()

    for slowo in slowa:
        lemat = simplemma.lemmatize(slowo, lang='pl')
        lemat = ogonki(lemat).lower()
        wynik.add(lemat)
   
    return wynik

def slowa_url(url):

    cut_url = url.split('/')[-1]
    czesci_url = cut_url.split('-')

    return {ogonki(slowo).lower() for slowo in czesci_url}


def hit_at_k(k=5):
  
    trafienia = 0

    for g in GOLDEN:

        emb = embed(g['query'])
        wyniki = search_hybrid(g['query'], emb, g['agent'], k)
        urls = [chunk['url'] for chunk, score in wyniki]
        zrodla = zrodla_jako_lista(g)

        if any(z in u for z in zrodla for u in urls):
            trafienia += 1
        
        else:
            print(f'  BRAK w top-{k}: {g["query"]!r}')

    acc = trafienia / len(GOLDEN)
    
    print(f'\nHit@{k}: {trafienia}/{len(GOLDEN)} = {acc:.3f}')
    return acc

STOP = {'jak', 'na', 'co', 'i', 'w', 'z', 'do', 'sie', 'czy', 'moje', 'za'}

def leksyka(query, url):
    
    q = zapytania(query)
    u = slowa_url(url)

    wspolne = q & u 
    wspolne = wspolne - STOP

    return len(wspolne)

def wybierz_main(wyniki, strategia, query=None):
    if not wyniki:

        return None

    if strategia == 'baseline':
       return wyniki[0][0]['url']

    if strategia == 'leks':
        najlepszy = max(
            enumerate(wyniki),
            key=lambda para: (leksyka(query, para[1][0]['url']), -para[0])
         )
        return najlepszy[1][0]['url']
    

    per_url = {}
    for i, (chunk, score) in enumerate(wyniki):
        url = chunk['url']

        if strategia == 'count':
            waga = 1

        elif strategia == 'suma':
            waga = score

        elif strategia == 'dyskont':
            waga = score / math.log2(i + 2)

        else:
            raise ValueError(f'nieznana strategia: {strategia}')

        per_url[url] = per_url.get(url, 0) + waga

    return max(per_url, key=per_url.get)

def main_accuracy(strategia, k=5):

    
    trafienia = 0
    pudla = []
    for g in GOLDEN:

        emb = embed(g['query'])
        wyniki = search_hybrid(g['query'], emb, g['agent'], k)
        main_url = wybierz_main(wyniki, strategia, query=g['query'])
        zrodla = zrodla_jako_lista(g)

        if main_url and any(z in main_url for z in zrodla):
           
            trafienia += 1
        else:
            pudla.append(g['query'])

    acc = trafienia / len(GOLDEN)

    return acc, pudla


def porownaj_strategie(k=5):
  
    print(f'\n--- MAIN-accuracy (k={k}) ---')
    
    for strategia in ['baseline', 'count', 'suma', 'dyskont', 'leks']:
        acc, pudla = main_accuracy(strategia, k)
       
        print(f'{strategia:10s} = {acc:.3f}  ({len(pudla)} pudeł)')


if __name__ == '__main__':
    hit_at_k(k=5)
    porownaj_strategie(k=5)
  