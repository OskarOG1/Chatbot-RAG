import ollama
from pathlib import Path
import sys
from rankings import search_hybrid

import time

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
    teksty = [c for c, score in chunks]
    kontekst = context(teksty)

    tresc = f'kontekst:\n{kontekst}\n\nPytanie: {query}'
    strumien = ollama.chat(
        model=MODEL_NAME,
        messages=[

            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': tresc},
        ],
        stream=True,
    )
    pelna = ''

    for kawalek in strumien:

        tekst = kawalek['message']['content']
        print(tekst, end='', flush=True)

        pelna += tekst

    print()
    return pelna


def zapytaj(query, agent, chunks, etykieta):

    print(f'\n===== {etykieta} =====')
    print(f'PYTANIE: {query}  |  AGENT: {agent}')
    print('--- KONTEKST ---')

    for c, score in chunks:
        print(f'{score:.3f} | {c["tekst"][:200]}')

    print('--- ODPOWIEDŹ ---')

    start = time.perf_counter()
    answer(query, agent, chunks)
    czas = time.perf_counter() - start

    print(f'⏱ generacja: {czas:.1f}s')


if __name__ == '__main__':

    query = 'jak zmienić hasło'
    agent = 'konto'
    chunks = search_hybrid(query, agent, k=3)
    zapytaj(query, agent, chunks, 'demo')