import ollama
from ollama import Client
from rankings import search_hybrid
from links import ARTYKUL_REGEX
from sentence_transformers import SentenceTransformer
import time
import re
import os
MMLW = 'sdadas/mmlw-retrieval-roberta-base'
model = SentenceTransformer(MMLW)
MODEL_NAME = 'SpeakLeash/bielik-1.5b-v3.0-instruct:Q8_0'

klient = Client(
    host=os.getenv('OLLAMA_HOST', 'http://localhost:11434'),
    timeout=int(os.getenv('LLM_TIMEOUT', '6000')),
)

SYSTEM_PROMPTY = {
    'konto': (
        'Jesteś specjalistą wsparcia Allegro od spraw konta i bezpieczeństwa. '
        'Odpowiadasz formalnie, rzeczowo i precyzyjnie. '
        'Przy sprawach logowania, haseł i danych osobowych kładziesz nacisk na bezpieczeństwo. '
        'Odpowiadaj WYŁĄCZNIE na podstawie podanego kontekstu. '
        'Jeśli kontekst nie zawiera odpowiedzi, ODMÓW odpowiedzi '
        'i zaproponuj kontakt z obsługą. NIE odpowiadaj z własnej wiedzy. Odpowiadaj zawsze po POLSKU.'
    ),
    'zakupy': (
        'Jesteś przyjaznym doradcą zakupowym Allegro. '
        'Odpowiadasz ciepło, pomocnie i prostym językiem, jak życzliwy konsultant. '
        'Prowadzisz kupującego krok po kroku przez zakupy, dostawy, zwroty i reklamacje. '
        'Odpowiadaj WYŁĄCZNIE na podstawie podanego kontekstu. '
        'Jeśli kontekst nie zawiera odpowiedzi, ODMÓW odpowiedzi '
        'i zaproponuj kontakt z obsługą. NIE odpowiadaj z własnej wiedzy. Odpowiadaj zawsze po POLSKU.'
    ),
    'platnosci': (
        'Jesteś technicznym specjalistą Allegro od płatności. '
        'Odpowiadasz konkretnie i precyzyjnie, podając dokładne kroki. '
        'Zwięźle, bez lania wody — użytkownik chce wiedzieć dokładnie co zrobić. '
        'Odpowiadaj WYŁĄCZNIE na podstawie podanego kontekstu. '
        'Jeśli kontekst nie zawiera odpowiedzi, ODMÓW odpowiedzi '
        'i zaproponuj kontakt z obsługą. NIE odpowiadaj z własnej wiedzy. Odpowiadaj zawsze po POLSKU.'
    ),
}


CYTATY_INSTRUKCJA = (
    ' Po KAŻDYM zdaniu opartym na kontekście dopisz numer źródła w nawiasie '
    'kwadratowym, np.: „Hasło zmienisz w ustawieniach konta [1].". '
    'Używaj wyłącznie numerów źródeł z podanego kontekstu. '
    'Nie podawaj żadnych adresów URL — linki zostaną dołączone automatycznie. '
    'Odpowiedź MUSI zawierać co najmniej jeden numer źródła w nawiasie [ ].'
)

URL_REGEX = re.compile(r'https?://\S+|\bwww\.\S+', re.IGNORECASE)
KONCOWKA = '.,;:!?)]}>"\''


def context(chunks: list[dict]) -> str:
    return '\n\n'.join(f'[{i}] {c["tekst"]}' for i, c in enumerate(chunks, 1))


def verify_answer(pelna: str, chunks: list) -> dict:
    zrodla = []
    for c, _ in chunks:
        if c['url'] not in zrodla:
            zrodla.append(c['url'])

    obce = []

    def strip_url(dopasowanie):
        surowy = dopasowanie.group(0)
        rdzen = surowy.rstrip(KONCOWKA)
        if not ARTYKUL_REGEX.match(rdzen):
            obce.append(surowy)
        return ''  # usuwamy KAŻDY URL z tekstu — linki są w sources + citations

    tekst = URL_REGEX.sub(strip_url, pelna)

    numery = []
    for m in re.findall(r'\[(\d+)\]', tekst):
        n = int(m)
        if 1 <= n <= len(zrodla) and n not in numery:
            numery.append(n)
    cytaty = [{'n': n, 'url': zrodla[n - 1]} for n in numery]

    # po wycięciu URL-i zostaje osierocona bibliografia "[n] [n] ..." — usuń ją.
    # inline [n] w środku zdań zostają (nie są samodzielną linią ani ciągiem 2+ na końcu).
    tekst = re.sub(r'(?m)^[ \t]*(?:\[\d+\][ \t]*)+$\n?', '', tekst)   # cała linia = same referencje
    tekst = re.sub(r'(?:[ \t]*\[\d+\])+[ \t]*$', '', tekst).rstrip()  # osierocony ciąg na końcu
    tekst = re.sub(r'[ \t]{2,}', ' ', tekst).strip()

    return {'tekst': tekst, 'cytaty': cytaty, 'obce': obce}


def answer(query: str, agent: str, chunks: list[dict], bielik_model:str | None=None,
           history:list[dict] | None=None) -> dict:

    system_prompt = SYSTEM_PROMPTY[agent] + CYTATY_INSTRUKCJA
    teksty = [c for c, _ in chunks]
    kontekst = context(teksty)

    tresc = f'kontekst:\n{kontekst}\n\nPytanie: {query}'
    nazwa = bielik_model or MODEL_NAME

    wiadomosci = [{'role': 'system', 'content': system_prompt}]
    for w in (history or []):
        if w.get('role') in ('user', 'assistant') and w.get('content'):
            wiadomosci.append({'role': w['role'], 'content': w['content']})
    wiadomosci.append({'role': 'user', 'content': tresc})

    odp = klient.chat(
        model=nazwa,
        messages=wiadomosci,
        stream=False,
        keep_alive='30m',
        options={'stop': ['Pytanie:', '<|start_header_id|>']}
    )

    pelna = odp['message']['content']
    pelna = re.sub(r'<\|.*?\|>', '', pelna)
    pelna = pelna.removeprefix('Odpowiedź:').strip()

    return verify_answer(pelna, chunks)
   

def przepisz_zapytanie(query: str, history: list[dict] | None, bielik_model: str | None = None) -> str:
    if not history:
        return query
    rozmowa = '\n'.join(f"{w['role']}: {w['content']}" for w in history
                        if w.get('role') in ('user', 'assistant') and w.get('content'))
    system_prompt = (
        'Przepisz OSTATNIE pytanie użytkownika jako samodzielne, pełne pytanie po polsku '
        'na podstawie rozmowy. Rozwiń odwołania typu „to", „tego", „a jak". '
        'Zwróć wyłącznie samo pytanie, bez komentarza.'
    )
    odp = klient.chat(
        model=bielik_model or MODEL_NAME,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f'{rozmowa}\nuser: {query}\n\nSamodzielne pytanie:'},
        ],
        stream=False,
        keep_alive='30m',
        options={'stop': ['\n', 'Pytanie:']}
    )
    tekst = re.sub(r'<\|.*?\|>', '', odp['message']['content']).strip()
    return tekst or query


SEDZIA_SYSTEM = (
    'Oceniasz, czy KONTEKST zawiera informacje potrzebne do odpowiedzi na PYTANIE. '
    'Odpowiedz jednym słowem: TAK albo NIE. Nic więcej.'
)


def czy_kontekst_odpowiada(query: str, chunks: list, bielik_model: str | None = None) -> bool:
    """Warstwa (b) — semantyczny sędzia pod produkcję (domyślnie NIEUŻYWANY).
    Jeden dodatkowy krótki call LLM: czy pobrany kontekst pozwala odpowiedzieć
    na pytanie. True = tak. Wyłapuje źle dobrany kontekst tematycznie, czego
    próg na score nie umie (kalibracja_progu = brak sygnału)."""
    teksty = [c for c, _ in chunks]
    kontekst = context(teksty)
    odp = klient.chat(
        model=bielik_model or MODEL_NAME,
        messages=[
            {'role': 'system', 'content': SEDZIA_SYSTEM},
            {'role': 'user', 'content': f'KONTEKST:\n{kontekst}\n\nPYTANIE: {query}\n\nCzy da się odpowiedzieć? (TAK/NIE):'},
        ],
        stream=False,
        keep_alive='30m',
        options={'stop': ['\n', 'Pytanie:']},
    )
    tekst = re.sub(r'<\|.*?\|>', '', odp['message']['content']).strip().upper()
    return tekst.startswith('TAK')


def zapytaj(query, agent, chunks, etykieta):

    print(f'\n===== {etykieta} =====')
    print(f'PYTANIE: {query}  |  AGENT: {agent}')
    print('--- KONTEKST ---')

    for c, score in chunks:
        print(f'{score:.3f} | {c["tekst"][:200]}')

    print('--- ODPOWIEDŹ ---')

    start = time.perf_counter()
    odpowiedz = answer(query, agent, chunks)
    czas = time.perf_counter() - start
    print(odpowiedz['tekst'])
    print(f'cytaty: {odpowiedz["cytaty"]}')
    print(f'⏱ generacja: {czas:.1f}s')


if __name__ == '__main__':

    query = 'jak zmienić hasło'
    agent = 'konto'
    query_emb = model.encode(['zapytanie: ' + query]).astype('float32')
    chunks = search_hybrid(query, query_emb, agent, k=3)
    zapytaj(query, agent, chunks, 'demo')