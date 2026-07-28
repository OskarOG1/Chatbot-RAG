
from huggingface_hub import InferenceClient
from rankings import search_hybrid
from links import ARTYKUL_REGEX
from sentence_transformers import SentenceTransformer
from pathlib import Path
from dotenv import load_dotenv
from lang_config import LANG
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
MAX_TOKENS = int(os.getenv('MAX_TOKENS', '1500'))

klient = InferenceClient(
    base_url=os.getenv('LLM_BASE_URL', 'http://localhost:11434/v1'),
    api_key=os.getenv('LLM_API_KEY', 'ollama'),
    timeout=float(os.getenv('LLM_TIMEOUT', '150')),
)

PROMPTY = {
    'pl': {
        'grounding': (
            ' Opieraj każde zdanie wyłącznie na treści z sekcji „kontekst". '
            'Nie dodawaj informacji spoza kontekstu — żadnych kwot, terminów, nazw opcji ani kroków, których tam nie ma. '
            'Trzymaj się słownictwa i nazw dokładnie tak, jak występują w kontekście. '
            'Jeśli kontekst odpowiada tylko na część pytania, odpowiedz na tę część i wprost napisz, czego w materiałach brakuje. '
            'Jeśli kontekst w ogóle nie dotyczy pytania, nie odpowiadaj z własnej wiedzy — napisz, że nie masz tej informacji, '
            'i odeślij do obsługi Allegro. '
            'Reguły, limity i warunki obowiązują tylko w zakresie artykułu, z którego pochodzą (widocznego w tytule źródła). '
            'Nie przenoś reguły z konkretnej kategorii ani przypadku na sytuację ogólną. '
            'Odpowiadaj zawsze po polsku.'
        ),
        'system_prompty': {
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
        },
        'cytaty_instrukcja': (
            ' Po każdej informacji z kontekstu podaj w nawiasie kwadratowym numer źródła, '
            'np. [1] lub [2]. Używaj wyłącznie numerów źródeł z podanego kontekstu. '
            'Nie podawaj żadnych adresów URL — linki zostaną dołączone automatycznie.'
        ),
        'kontekst_label': 'kontekst',
        'pytanie_label': 'Pytanie',
        'odpowiedz_prefix': 'Odpowiedź:',
        'przepisz_system': (
            'Przepisz OSTATNIE pytanie użytkownika jako samodzielne, pełne pytanie po polsku '
            'na podstawie rozmowy. Rozwiń odwołania typu „to", „tego", „a jak". '
            'Zwróć wyłącznie samo pytanie, bez komentarza.'
        ),
        'przepisz_label': 'Samodzielne pytanie',
        'sedzia_system': (
            'Oceniasz, czy KONTEKST jest z tej samej dziedziny co PYTANIE i pozwala choćby częściowo pomóc. '
            'Odpowiadaj TAK, chyba że pytanie jest wyraźnie z INNEJ dziedziny niż kontekst '
            '(np. gotowanie, sport, inny sklep). W razie wątpliwości odpowiadaj TAK. '
            'Jedno słowo: TAK albo NIE.'
        ),
        'sedzia_kontekst_label': 'KONTEKST',
        'sedzia_pytanie_label': 'PYTANIE',
        'sedzia_pytanie': 'Czy da się odpowiedzieć? (TAK/NIE):',
        'tak_marker': 'TAK',
    },
    'en': {
        'grounding': (
            ' Base every sentence exclusively on the content in the "context" section. '
            'Do not add information beyond the context — no amounts, deadlines, option names, or steps that aren\'t there. '
            'Stick to the vocabulary and names exactly as they appear in the context. '
            'If the context only answers part of the question, answer that part and explicitly state what is missing from the materials. '
            'If the context does not address the question at all, do not answer from your own knowledge — say you do not have that information, '
            'and refer the user to Allegro support. '
            'Rules, limits, and conditions apply only within the scope of the article they come from (visible in the source title). '
            'Do not carry a rule from a specific category or case over to the general situation. '
            'Always answer in English.'
        ),
        'system_prompty': {
            'konto': (
                'You are an Allegro specialist in accounts and security. '
                'You speak factually and formally, in complete sentences, without colloquial phrasing. '
                'When a question involves passwords, logging in, or personal data, you open your answer by addressing '
                'the security aspect and clearly flag the risk before giving the steps.'
            ),
            'zakupy': (
                'You are a friendly Allegro shopping advisor. '
                'You address the buyer directly and warmly, in plain language. '
                'You break instructions into clear steps and end with a short reassuring or encouraging sentence.'
            ),
            'platnosci': (
                'You are a technical Allegro specialist in payments. '
                'You answer briefly and precisely: exact steps in order, no preamble, no filler. '
                'You give precise button and option names exactly as they appear in the context.'
            ),
        },
        'cytaty_instrukcja': (
            ' After each piece of information from the context, give the source number in square brackets, '
            'e.g. [1] or [2]. Use only source numbers from the given context. '
            'Do not include any URLs — links will be added automatically.'
        ),
        'kontekst_label': 'context',
        'pytanie_label': 'Question',
        'odpowiedz_prefix': 'Answer:',
        'przepisz_system': (
            'Rewrite the user\'s LAST question as a standalone, complete question in English, '
            'based on the conversation. Expand references like "it", "that", "what about". '
            'Return only the question itself, with no commentary.'
        ),
        'przepisz_label': 'Standalone question',
        'sedzia_system': (
            'You are a lenient topic filter, not a completeness checker. '
            'Judge only whether the CONTEXT and the QUESTION belong to the same general topic '
            '(Allegro account, shopping, delivery, returns, or payments), so the context could at least '
            'partially or indirectly help. Do not check whether the context fully or perfectly answers '
            'the question, whether every detail is covered, or whether the best matching part is only in '
            'one of several context entries. Answer YES unless the question is clearly about something '
            'unrelated to Allegro shopping, accounts, or payments (for example cooking, sports, or another '
            'store). When in doubt, answer YES. One word: YES or NO.'
        ),
        'sedzia_kontekst_label': 'CONTEXT',
        'sedzia_pytanie_label': 'QUESTION',
        'sedzia_pytanie': 'Can this be answered? (YES/NO):',
        'tak_marker': 'YES',
    },
}

URL_REGEX = re.compile(r'https?://\S+|\bwww\.\S+', re.IGNORECASE)
KONCOWKA = '.,;:!?)]}>"\''


def context(chunks: list[dict]) -> str:
    bloki = []
    for i, c in enumerate(chunks, 1):
        etykieta = c['tytul']
        if c.get('naglowek'):
            etykieta = f"{etykieta} ({c['naglowek']})"
        bloki.append(f'[{i}] {etykieta}\n{c["tekst"]}')
    return '\n\n'.join(bloki)


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
    tekst = re.sub(r'\[(?:Security|Note|Disclaimer|Warning)[^\[\]]*:[^\[\]]*\]\s*', '',
                    tekst, flags=re.IGNORECASE).lstrip()

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
                  history:list[dict] | None=None, lang:str='pl'):
    p = PROMPTY[lang]
    system_prompt = p['system_prompty'][agent] + p['grounding'] + p['cytaty_instrukcja']
    teksty = [c for c, _ in chunks]
    kontekst = context(teksty)

    tresc = f"{p['kontekst_label']}:\n{kontekst}\n\n{p['pytanie_label']}: {query}"
    nazwa = bielik_model or LANG[lang]['model']

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
        stop=[f"{p['pytanie_label']}:", '<|start_header_id|>'],
    ):
        if not kawalek.choices:
            continue
        token = kawalek.choices[0].delta.content
        if not token:
            continue
        pelna += token
        yield {'typ': 'token', 'tekst': token}

    pelna = re.sub(r'<\|.*?\|>', '', pelna)
    pelna = pelna.removeprefix(p['odpowiedz_prefix']).strip()
    yield {'typ': 'koniec', 'dane': verify_answer(pelna, chunks)}


def answer(query: str, agent: str, chunks: list[dict], bielik_model:str | None=None,
           history:list[dict] | None=None, lang:str='pl') -> dict:
    p = PROMPTY[lang]
    system_prompt = p['system_prompty'][agent] + p['grounding'] + p['cytaty_instrukcja']
    teksty = [c for c, _ in chunks]
    kontekst = context(teksty)

    tresc = f"{p['kontekst_label']}:\n{kontekst}\n\n{p['pytanie_label']}: {query}"
    nazwa = bielik_model or LANG[lang]['model']

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
        stop=[f"{p['pytanie_label']}:", '<|start_header_id|>'],
    )

    pelna = odp.choices[0].message.content
    pelna = re.sub(r'<\|.*?\|>', '', pelna)
    pelna = pelna.removeprefix(p['odpowiedz_prefix']).strip()
    return verify_answer(pelna, chunks)


def przepisz_zapytanie(query: str, history: list[dict] | None, bielik_model: str | None = None,
                        lang: str = 'pl') -> str:
    if not history:
        return query
    p = PROMPTY[lang]
    rozmowa = '\n'.join(f"{w['role']}: {w['content']}" for w in history
                        if w.get('role') in ('user', 'assistant') and w.get('content'))
    odp = klient.chat.completions.create(
        model=bielik_model or LANG[lang]['model'],
        messages=[
            {'role': 'system', 'content': p['przepisz_system']},
            {'role': 'user', 'content': f"{rozmowa}\nuser: {query}\n\n{p['przepisz_label']}:"},
        ],
        stream=False,
        stop=['\n', f"{p['pytanie_label']}:"],
    )
    tekst = re.sub(r'<\|.*?\|>', '', odp.choices[0].message.content).strip()
    return tekst or query


def czy_kontekst_odpowiada(query: str, chunks: list, bielik_model: str | None = None,
                            lang: str = 'pl') -> bool:
    p = PROMPTY[lang]
    teksty = [c for c, _ in chunks]
    kontekst = context(teksty)
    odp = klient.chat.completions.create(
        model=bielik_model or LANG[lang]['sedzia_model'],
        messages=[
            {'role': 'system', 'content': p['sedzia_system']},
            {'role': 'user', 'content': (
                f"{p['sedzia_kontekst_label']}:\n{kontekst}\n\n"
                f"{p['sedzia_pytanie_label']}: {query}\n\n{p['sedzia_pytanie']}"
            )},
        ],
        stream=False,
        stop=['\n', f"{p['pytanie_label']}:"],
    )
    tekst = re.sub(r'<\|.*?\|>', '', odp.choices[0].message.content).strip().upper()
    return tekst.startswith(p['tak_marker'])


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
