import ollama
from ollama import Client
from rankings import search_hybrid
from sentence_transformers import SentenceTransformer
import time
import re
MMLW = 'sdadas/mmlw-retrieval-roberta-base'
model = SentenceTransformer(MMLW)
MODEL_NAME = 'SpeakLeash/bielik-1.5b-v3.0-instruct:Q8_0'

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


def context(chunks: list[dict]) -> str:
    return '\n\n'.join(f'[{i}] {c["tekst"]}' for i, c in enumerate(chunks, 1))


def answer(query: str, agent: str, chunks: list[dict]) -> str:

    system_prompt = SYSTEM_PROMPTY[agent]
    teksty = [c for c, _ in chunks]
    kontekst = context(teksty)

    tresc = f'kontekst:\n{kontekst}\n\nPytanie: {query}'
    odp = ollama.chat(
        model=MODEL_NAME,
        messages=[

            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': tresc},
        ],
        stream=False,
        options={'stop': ['Pytanie:', '<|start_header_id|>']}
    )

    pelna = odp['message']['content']
    pelna = re.sub(r'<\|.*?\|>', '', pelna)
    pelna = pelna.removeprefix('Odpowiedź:').strip()
   
    return pelna
   

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
    print(odpowiedz)
    print(f'⏱ generacja: {czas:.1f}s')


if __name__ == '__main__':

    query = 'jak zmienić hasło'
    agent = 'konto'
    query_emb = model.encode(['zapytanie: ' + query]).astype('float32')
    chunks = search_hybrid(query, query_emb, agent, k=3)
    zapytaj(query, agent, chunks, 'demo')