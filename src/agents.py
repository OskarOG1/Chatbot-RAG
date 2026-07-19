
from huggingface_hub import InferenceClient
from rankings import search_hybrid
from links import ARTYKUL_REGEX
from sentence_transformers import SentenceTransformer
from pathlib import Path
from dotenv import load_dotenv
import time
import re
import os

load_dotenv(Path(__file__).resolve().parent / '.env')

MMLW = 'sdadas/mmlw-retrieval-roberta-base'
MODEL_11B = 'speakleash/Bielik-11B-v3.0-Instruct'
MODEL_7B_LOKALNY = 'SpeakLeash/bielik-minitron-7B-v3.0-instruct:Q4_K_M'
MODEL_1_5B_LOKALNY = 'SpeakLeash/bielik-1.5b-v3.0-instruct:Q8_0'
MODEL_NAME = os.getenv('MODEL', MODEL_11B)
SEDZIA_MODEL = os.getenv('SEDZIA_MODEL', MODEL_NAME)
MAX_TOKENS = int(os.getenv('MAX_TOKENS', '700'))

klient = InferenceClient(
    base_url=os.getenv('LLM_BASE_URL', 'http://localhost:11434/v1'),
    api_key=os.getenv('LLM_API_KEY', 'ollama'),
    timeout=float(os.getenv('LLM_TIMEOUT', '150')),
)

GROUNDING = (
    ' Opieraj każde zdanie wyłącznie na treści z sekcji „kontekst". '
    'Nie dodawaj informacji spoza kontekstu — żadnych kwot, terminów, nazw opcji ani kroków, których tam nie ma. '
    'Trzymaj się słownictwa i nazw dokładnie tak, jak występują w kontekście. '
    'Jeśli kontekst odpowiada tylko na część pytania, odpowiedz na tę część i wprost napisz, czego w materiałach brakuje. '
    'Jeśli kontekst w ogóle nie dotyczy pytania, nie odpowiadaj z własnej wiedzy — napisz, że nie masz tej informacji, '
    'i odeślij do obsługi Allegro. Odpowiadaj zawsze po polsku.'
)

SYSTEM_PROMPTY = {
    'konto': (
        'Jesteś specjalistą Allegro od konta i bezpieczeństwa. '
        'Mówisz rzeczowo i formalnie, pełnymi zdaniami, bez potocznych zwrotów. '
        'Gdy pytanie dotyczy haseł, logowania lub danych osobowych, zaczynasz odpowiedź od aspektu bezpieczeństwa '
        'i wyraźnie sygnalizujesz ryzyko, zanim podasz kroki.'
    ),
    'zakupy': (
        'Jesteś życzliwym doradcą zakupowym Allegro. '
        'Zwracasz się do kupującego bezpośrednio i ciepło, prostym językiem. '
        'Instrukcje rozpisujesz jako kolejne kroki i kończysz krótkim zdaniem, które uspokaja albo zachęca do działania.'
    ),
    'platnosci': (
        'Jesteś technicznym specjalistą Allegro od płatności. '
        'Odpowiadasz krótko i konkretnie: dokładne kroki w kolejności, bez wstępów i bez lania wody. '
        'Podajesz precyzyjne nazwy przycisków i opcji dokładnie tak, jak brzmią w kontekście.'
    ),
}


CYTATY_INSTRUKCJA = (
    ' Po każdej informacji z kontekstu podaj w nawiasie kwadratowym numer źródła, '
    'np. [1] lub [2]. Używaj wyłącznie numerów źródeł z podanego kontekstu. '
    'Nie podawaj żadnych adresów URL — linki zostaną dołączone automatycznie.'
)

URL_REGEX = re.compile(r'https?://\S+|\bwww\.\S+', re.IGNORECASE)
KONCOWKA = '.,;:!?)]}>"\''


def context(chunks: list[dict]) -> str:
    return '\n\n'.join(f'[{i}] {c["tekst"]}' for i, c in enumerate(chunks, 1))


def verify_answer(pelna: str, chunks: list) -> dict:
    mapa = {i: c['url'] for i, (c, _) in enumerate(chunks, 1)}

    obce = []

    def strip_url(dopasowanie):
        surowy = dopasowanie.group(0)
        rdzen = surowy.rstrip(KONCOWKA)
        if not ARTYKUL_REGEX.match(rdzen):
            obce.append(surowy)
        return '' 
    tekst = URL_REGEX.sub(strip_url, pelna)

    numery = []
    for m in re.findall(r'\[(\d+)\]', tekst):
        n = int(m)
        if n in mapa and n not in numery:
            numery.append(n)
    cytaty = [{'n': n, 'url': mapa[n]} for n in numery]

    tekst = re.sub(r'(?m)^[ \t]*(?:\[\d+\][ \t]*)+$\n?', '', tekst)
    tekst = re.sub(r'(?:[ \t]*\[\d+\])+[ \t]*$', '', tekst).rstrip()
    tekst = re.sub(r'[ \t]{2,}', ' ', tekst).strip()

    return {'tekst': tekst, 'cytaty': cytaty, 'obce': obce}


def answer_stream(query: str, agent: str, chunks: list[dict], bielik_model:str | None=None,
                  history:list[dict] | None=None):
    system_prompt = SYSTEM_PROMPTY[agent] + GROUNDING + CYTATY_INSTRUKCJA
    teksty = [c for c, _ in chunks]
    kontekst = context(teksty)

    tresc = f'kontekst:\n{kontekst}\n\nPytanie: {query}'
    nazwa = bielik_model or MODEL_NAME

    wiadomosci = [{'role': 'system', 'content': system_prompt}]
    for w in (history or []):
        if w.get('role') in ('user', 'assistant') and w.get('content'):
            wiadomosci.append({'role': w['role'], 'content': w['content']})
    wiadomosci.append({'role': 'user', 'content': tresc})

    pelna = ''
    for kawalek in klient.chat.completions.create(
        model=nazwa,
        messages=wiadomosci,
        stream=True,
        max_tokens=MAX_TOKENS,
        stop=['Pytanie:', '<|start_header_id|>'],
    ):
        if not kawalek.choices:
            continue
        token = kawalek.choices[0].delta.content
        if not token:
            continue
        pelna += token
        yield {'typ': 'token', 'tekst': token}

    pelna = re.sub(r'<\|.*?\|>', '', pelna)
    pelna = pelna.removeprefix('Odpowiedź:').strip()
    yield {'typ': 'koniec', 'dane': verify_answer(pelna, chunks)}


def answer(query: str, agent: str, chunks: list[dict], bielik_model:str | None=None,
           history:list[dict] | None=None) -> dict:
    system_prompt = SYSTEM_PROMPTY[agent] + GROUNDING + CYTATY_INSTRUKCJA
    teksty = [c for c, _ in chunks]
    kontekst = context(teksty)

    tresc = f'kontekst:\n{kontekst}\n\nPytanie: {query}'
    nazwa = bielik_model or MODEL_NAME

    wiadomosci = [{'role': 'system', 'content': system_prompt}]
    for w in (history or []):
        if w.get('role') in ('user', 'assistant') and w.get('content'):
            wiadomosci.append({'role': w['role'], 'content': w['content']})
    wiadomosci.append({'role': 'user', 'content': tresc})

    odp = klient.chat.completions.create(
        model=nazwa,
        messages=wiadomosci,
        stream=False,
        max_tokens=MAX_TOKENS,
        stop=['Pytanie:', '<|start_header_id|>'],
    )

    pelna = odp.choices[0].message.content
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
    odp = klient.chat.completions.create(
        model=bielik_model or MODEL_NAME,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f'{rozmowa}\nuser: {query}\n\nSamodzielne pytanie:'},
        ],
        stream=False,
        stop=['\n', 'Pytanie:'],
    )
    tekst = re.sub(r'<\|.*?\|>', '', odp.choices[0].message.content).strip()
    return tekst or query


SEDZIA_SYSTEM = (
    'Oceniasz, czy KONTEKST jest z tej samej dziedziny co PYTANIE i pozwala choćby częściowo pomóc. '
    'Odpowiadaj TAK, chyba że pytanie jest wyraźnie z INNEJ dziedziny niż kontekst '
    '(np. gotowanie, sport, inny sklep). W razie wątpliwości odpowiadaj TAK. '
    'Jedno słowo: TAK albo NIE.'
)


def czy_kontekst_odpowiada(query: str, chunks: list, bielik_model: str | None = None) -> bool:
    
    teksty = [c for c, _ in chunks]
    kontekst = context(teksty)
    odp = klient.chat.completions.create(
        model=bielik_model or SEDZIA_MODEL,
        messages=[
            {'role': 'system', 'content': SEDZIA_SYSTEM},
            {'role': 'user', 'content': f'KONTEKST:\n{kontekst}\n\nPYTANIE: {query}\n\nCzy da się odpowiedzieć? (TAK/NIE):'},
        ],
        stream=False,
        stop=['\n', 'Pytanie:'],
    )
    tekst = re.sub(r'<\|.*?\|>', '', odp.choices[0].message.content).strip().upper()
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

    model = SentenceTransformer(MMLW)
    query = 'jak zmienić hasło'
    agent = 'konto'
    query_emb = model.encode(['zapytanie: ' + query]).astype('float32')
    chunks = search_hybrid(query, query_emb, agent, k=3)
    zapytaj(query, agent, chunks, 'demo')