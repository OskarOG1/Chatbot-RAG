from sentence_transformers import SentenceTransformer
import faiss
from classify import vote
from rankings import search_reranked_multi
from agents import answer, przepisz_zapytanie, czy_kontekst_odpowiada
from guards import sprawdz
from spell import correct, tokenize_words, MIN_DLUGOSC
from pathlib import Path
from datetime import datetime, timezone
import json
MODEL_NAME = 'sdadas/mmlw-retrieval-roberta-base'
model = SentenceTransformer(MODEL_NAME)
MARGINES = 2
OKNO_HISTORII = 3
LOG_TRUDNE = Path(__file__).resolve().parent.parent / 'RAG' / 'trudne.jsonl'
BRAK_WIEDZY = ('Nie znalazłem tej informacji w bazie pomocy Allegro. '
               'Sprawdź bezpośrednio w Centrum Pomocy: https://allegro.pl/pomoc')


def bez_pokrycia(odpowiedz: dict) -> bool:
    """Warstwa anty-halucynacyjna (a): odpowiedź bez ani jednego cytatu [n]
    = model nie oparł się na żadnym źródle = traktujemy jako brak wiedzy.
    NIE jest to próg geometryczny (te odrzucone na danych — kalibracja_progu
    dała brak sygnału), tylko sygnał z samego cytowania."""
    return not odpowiedz.get('cytaty')


def loguj_trudne(query: str, nieznane: list) -> None:
    try:
        wpis = {'czas': datetime.now(timezone.utc).isoformat(), 'query': query, 'nieznane': nieznane}
        with open(LOG_TRUDNE, 'a', encoding='utf-8') as w:
            w.write(json.dumps(wpis, ensure_ascii=False) + '\n')
    except OSError:
        pass

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


def run_stream(query:str, agent:str | None=None, bielik_model:str | None=None,
               history:list[dict] | None=None, agent_poprzedni:str | None=None,
               przepisz:bool=False, bez_korekty:bool=False, sedzia:bool=False):
    """Generator: yield-uje kroki {'typ':'krok','tekst':...} po drodze,
    a na końcu jeden {'typ':'wynik','dane': <ten sam dict co run()>}.
    run() konsumuje go i zwraca sam wynik — jedna logika, dwa wejścia."""
    def krok(t):
        return {'typ': 'krok', 'tekst': t}
    def wynik(d):
        return {'typ': 'wynik', 'dane': d}

    yield krok('Sprawdzam pytanie')
    powod = sprawdz(query)
    if powod:
        yield wynik({'agent': '', 'answer': powod, 'sources': [], 'citations': [], 'doprecyzowanie': None})
        return
    history = (history or [])[-OKNO_HISTORII:]
    if bez_korekty:
        # użytkownik odrzucił korektę ("nie") → jedziemy na oryginale, bez zgadywania
        doprecyzowanie = None
    else:
        yield krok('Poprawiam literówki')
        korekta = correct(query)
        query = korekta['poprawione']
        if korekta['nieznane']:
            loguj_trudne(query, korekta['nieznane'])
            tokeny = [t for t in tokenize_words(query) if len(t) >= MIN_DLUGOSC]
            # twardy fallback TYLKO dla realnego gibberishu — wszystkie tokeny treści nieznane.
            # Pojedyncze słowo spoza słownika korpusu (np. "pozbyć") jedzie dalej;
            # jeśli naprawdę poza bazą, odetnie je bramka po cytatach (a).
            if tokeny and len(korekta['nieznane']) >= len(tokeny):
                yield wynik({'agent': '', 'answer': 'Przepraszam, nie zrozumiałem pytania — czy możesz napisać je inaczej?',
                             'sources': [], 'citations': [], 'doprecyzowanie': None})
                return
        doprecyzowanie = f'Szukam dla: „{query}" — czy o to chodziło?' if korekta['zmieniono'] else None

    if przepisz and history:
        yield krok('Przepisuję pytanie z kontekstu rozmowy')
        zapytanie_ret = przepisz_zapytanie(query, history, bielik_model)
    else:
        poprzedni_user = [w['content'] for w in history if w['role'] == 'user'][-1:]
        zapytanie_ret = ' '.join(poprzedni_user + [query])

    yield krok('Zamieniam pytanie na wektor')
    query_emb = model.encode(['zapytanie: ' + zapytanie_ret]).astype('float32')
    faiss.normalize_L2(query_emb)

    yield krok('Rozpoznaję sekcję (konto / zakupy / płatności)')
    if agent is None:
        agenci = vote(query_emb, top2=True, margines=MARGINES)
        if agent_poprzedni and agent_poprzedni not in agenci:
            agenci = agenci + [agent_poprzedni]
    else:
        agenci = [agent]

    yield krok('Przeszukuję bazę wiedzy i porządkuję wyniki')
    chunks = search_reranked_multi(zapytanie_ret, query_emb, agenci, k=5, k_surowe=20)

    agenci_chunkow = [c['agent'] for c, _ in chunks]
    if agent is None and agent_poprzedni and agent_poprzedni in agenci_chunkow:
        agent_odp = agent_poprzedni
    else:
        agent_odp = chunks[0][0]['agent'] if chunks else agenci[0]

    # Warstwa (b) — sędzia semantyczny PRZED generacją (pod produkcję, domyślnie off).
    # Łapie źle dobrany kontekst tematycznie — czego próg geometryczny nie umie.
    if sedzia and chunks:
        yield krok('Sprawdzam, czy kontekst odpowiada na pytanie')
        if not czy_kontekst_odpowiada(query, chunks, bielik_model):
            yield wynik({'agent': agent_odp, 'answer': BRAK_WIEDZY,
                         'sources': [], 'citations': [], 'doprecyzowanie': doprecyzowanie})
            return

    yield krok(f'Generuję odpowiedź (sekcja: {agent_odp})')
    odpowiedz = answer(query, agent_odp, chunks, bielik_model, history)

    # Warstwa (a) — brak cytatu => brak oparcia w źródle => nie zmyślamy.
    if bez_pokrycia(odpowiedz):
        yield wynik({'agent': agent_odp, 'answer': BRAK_WIEDZY,
                     'sources': [], 'citations': [], 'doprecyzowanie': doprecyzowanie})
        return

    zrodla = list(dict.fromkeys(c['url'] for c, _ in chunks))
    yield wynik({'agent': agent_odp,
                 'answer': odpowiedz['tekst'],
                 'sources': zrodla,
                 'citations': odpowiedz['cytaty'],
                 'doprecyzowanie': doprecyzowanie})


def run(query:str, agent:str | None=None, bielik_model:str | None=None,
        history:list[dict] | None=None, agent_poprzedni:str | None=None,
        przepisz:bool=False, bez_korekty:bool=False, sedzia:bool=False) -> dict:
    dane = {}
    for ev in run_stream(query, agent, bielik_model, history,
                         agent_poprzedni, przepisz, bez_korekty, sedzia):
        if ev['typ'] == 'wynik':
            dane = ev['dane']
    return dane


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
