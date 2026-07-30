
from huggingface_hub import InferenceClient
from links import ARTYKUL_REGEX
from pathlib import Path
from dotenv import load_dotenv
import re
import os

load_dotenv(Path(__file__).resolve().parent / '.env')

MODEL_11B = 'speakleash/Bielik-11B-v3.0-Instruct'
MODEL_7B_LOKALNY = 'SpeakLeash/bielik-minitron-7B-v3.0-instruct:Q4_K_M'
MODEL_1_5B_LOKALNY = 'SpeakLeash/bielik-1.5b-v3.0-instruct:Q8_0'
MODEL_NAME = os.getenv('MODEL', MODEL_11B)
MODEL_FALLBACK = os.getenv('MODEL_FALLBACK', MODEL_7B_LOKALNY)
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
            'Gdy pytanie jest ogólne, najpierw opisz ogólną procedurę, a dopiero potem, jeśli kontekst na to pozwala, '
            'wspomnij o przypadkach szczególnych jako dodatek, nie jako całą odpowiedź. '
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
            'Jesteś łagodnym filtrem tematycznym, nie sprawdzasz kompletności odpowiedzi. '
            'Oceniasz wyłącznie, czy KONTEKST i PYTANIE dotyczą tego samego ogólnego tematu '
            '(konto Allegro, zakupy, dostawa, zwroty albo płatności), więc kontekst mógłby choćby '
            'częściowo albo pośrednio pomóc. Nie sprawdzaj, czy kontekst odpowiada na pytanie w pełni, '
            'czy każdy szczegół jest omówiony, ani czy najlepiej pasujący fragment jest tylko w jednym '
            'z kilku podanych źródeł — jeśli choć jedno źródło dotyczy tematu pytania, odpowiedz TAK. '
            'Odpowiadaj TAK, chyba że pytanie jest wyraźnie z INNEJ dziedziny niż kontekst '
            '(np. gotowanie, sport, inny sklep). W razie wątpliwości odpowiadaj TAK. '
            'Jedno słowo: TAK albo NIE.'
        ),
        'sedzia_kontekst_label': 'KONTEKST',
        'sedzia_pytanie_label': 'PYTANIE',
        'sedzia_pytanie': 'Czy da się odpowiedzieć? (TAK/NIE):',
        'tak_marker': 'TAK',
        'email_system_reklamacja': (
            'Piszesz SZKIC maila reklamacyjnego do sprzedawcy w imieniu kupującego. '
            'Zacznij od zdania: „Szkic wiadomości do sprzedawcy (uzupełnij dane przed wysłaniem):", '
            'potem pusta linia, potem treść maila. '
            'Opis problemu weź wyłącznie z rozmowy z kupującym w wiadomościach powyżej, nie zmyślaj szczegółów, '
            'których tam nie ma. Trzymaj się procesu reklamacji opisanego w sekcji „kontekst" (kroki, wymagane elementy zgłoszenia). '
            'Numer zamówienia, datę zakupu i inne konkretne dane, których nie ma w rozmowie, zaznacz placeholderem '
            'w nawiasach kwadratowych, np. [numer zamówienia], [data zakupu], nigdy nie zmyślaj wartości. '
            'Pisz w formie bezosobowej albo bez wskazania rodzaju (unikaj końcówek typu „kupiłem"/„kupiłam"), '
            'a gdy się nie da tego uniknąć, użyj placeholdera w nawiasach kwadratowych, np. [kupiłem/kupiłam]. '
            'Podziel treść na krótkie akapity, jedna myśl w akapicie, pusta linia między nimi: powitanie, opis '
            'sytuacji, konkretna prośba, zakończenie. '
            'Ton uprzejmy i rzeczowy. Zakończ jasną prośbą o rozwiązanie (naprawa, wymiana albo zwrot pieniędzy). '
            'Nie dodawaj żadnych wyjaśnień poza samym szkicem maila. Odpowiadaj po polsku.'
        ),
        'email_system_zwrot': (
            'Piszesz SZKIC wiadomości do sprzedawcy o zwrocie produktu (odstąpienie od umowy) w imieniu kupującego. '
            'Zacznij od zdania: „Szkic wiadomości do sprzedawcy (uzupełnij dane przed wysłaniem):", '
            'potem pusta linia, potem treść wiadomości. '
            'Opis, jaki produkt i dlaczego jest zwracany, weź wyłącznie z rozmowy powyżej, nie zmyślaj szczegółów. '
            'Trzymaj się procesu zwrotu opisanego w sekcji „kontekst" (termin, sposób odstąpienia, co sprzedawca musi zrobić). '
            'Numer zamówienia, datę zakupu i inne konkretne dane, których nie ma w rozmowie, zaznacz placeholderem '
            'w nawiasach kwadratowych, np. [numer zamówienia], [data zakupu], nigdy nie zmyślaj wartości. '
            'Pisz w formie bezosobowej albo bez wskazania rodzaju (unikaj końcówek typu „kupiłem"/„kupiłam"), '
            'a gdy się nie da tego uniknąć, użyj placeholdera w nawiasach kwadratowych, np. [kupiłem/kupiłam]. '
            'Podziel treść na krótkie akapity, jedna myśl w akapicie, pusta linia między nimi: powitanie, opis '
            'sytuacji, konkretna prośba, zakończenie. '
            'Ton uprzejmy i rzeczowy. Zakończ jasnym oświadczeniem o odstąpieniu od umowy i prośbą o instrukcję zwrotu. '
            'Nie dodawaj żadnych wyjaśnień poza samym szkicem wiadomości. Odpowiadaj po polsku.'
        ),
        'email_system_faktura': (
            'Piszesz SZKIC wiadomości do sprzedawcy z prośbą o fakturę za zakup w imieniu kupującego. '
            'Zacznij od zdania: „Szkic wiadomości do sprzedawcy (uzupełnij dane przed wysłaniem):", '
            'potem pusta linia, potem treść wiadomości. '
            'Opis zakupu weź wyłącznie z rozmowy powyżej, nie zmyślaj szczegółów, których tam nie ma. '
            'Trzymaj się procesu wystawiania faktury opisanego w sekcji „kontekst". '
            'Numer zamówienia, datę zakupu, dane do faktury i inne konkretne dane, których nie ma w rozmowie, zaznacz '
            'placeholderem w nawiasach kwadratowych, np. [numer zamówienia], [dane do faktury], nigdy nie zmyślaj wartości. '
            'Pisz w formie bezosobowej albo bez wskazania rodzaju (unikaj końcówek typu „kupiłem"/„kupiłam"), '
            'a gdy się nie da tego uniknąć, użyj placeholdera w nawiasach kwadratowych, np. [kupiłem/kupiłam]. '
            'Podziel treść na krótkie akapity, jedna myśl w akapicie, pusta linia między nimi: powitanie, opis '
            'sytuacji, konkretna prośba, zakończenie. '
            'Ton uprzejmy i rzeczowy. Zakończ jasną prośbą o wystawienie faktury. '
            'Nie dodawaj żadnych wyjaśnień poza samym szkicem wiadomości. Odpowiadaj po polsku.'
        ),
        'email_system_eskalacja': (
            'Piszesz SZKIC wiadomości z prośbą o zaangażowanie Allegro w dyskusję ze sprzedawcą, w imieniu kupującego. '
            'Zacznij od zdania: „Szkic wiadomości do Allegro (uzupełnij dane przed wysłaniem):", '
            'potem pusta linia, potem treść wiadomości. '
            'Opis sytuacji (co kupił, na czym polega problem, dlaczego sprzedawca nie pomógł) weź wyłącznie z rozmowy '
            'powyżej, nie zmyślaj szczegółów. Trzymaj się WYŁĄCZNIE kroków opisanych w sekcji „kontekst": jeśli kontekst '
            'nie opisuje konkretnego kroku eskalacji, nie zmyślaj procedury, użyj placeholdera w nawiasach kwadratowych '
            'albo napisz, że trzeba to sprawdzić w Centrum Pomocy Allegro, zamiast wymyślać proces. '
            'Numer zamówienia, datę zakupu i inne konkretne dane, których nie ma w rozmowie, zaznacz placeholderem '
            'w nawiasach kwadratowych, nigdy nie zmyślaj wartości. '
            'Pisz w formie bezosobowej albo bez wskazania rodzaju (unikaj końcówek typu „kupiłem"/„kupiłam"), '
            'a gdy się nie da tego uniknąć, użyj placeholdera w nawiasach kwadratowych, np. [kupiłem/kupiłam]. '
            'Podziel treść na krótkie akapity, jedna myśl w akapicie, pusta linia między nimi: powitanie, opis '
            'sytuacji, konkretna prośba, zakończenie. '
            'Ton uprzejmy i rzeczowy. Zakończ jasną prośbą o interwencję Allegro. '
            'Nie dodawaj żadnych wyjaśnień poza samym szkicem wiadomości. Odpowiadaj po polsku.'
        ),
        'router_system': (
            'Klasyfikujesz, jakiej pomocy z wiadomością do sprzedawcy/Allegro potrzebuje kupujący, na podstawie ROZMOWY. '
            'Kategorie: REKLAMACJA (towar wadliwy, uszkodzony, niezgodny z opisem), ZWROT (kupujący chce oddać '
            'sprawny towar i odstąpić od umowy, bez wady towaru), FAKTURA (kupujący prosi o fakturę za zakup), '
            'ESKALACJA (sprzedawca nie odpowiada, ignoruje wiadomości albo odmawia pomocy: jeśli kupujący ma '
            'wadliwy towar LUB chce zwrotu, ALE dodatkowo zgłasza brak reakcji sprzedawcy, wybierz ESKALACJA). '
            'Kupujący musi opisywać WŁASNĄ, KONKRETNĄ sytuację, którą ma TERAZ, z własnym zamówieniem. Jeśli pyta '
            'ogólnie o zasady, terminy czy procedury („jak długo mam na zwrot", „ile trwa rozpatrzenie reklamacji"), '
            'bez wskazania własnego problemu, odpowiedz NONE, nawet jeśli w pytaniu pada słowo „zwrot" czy '
            '„reklamacja". Ale gdy kupujący jasno opisuje własny towar i problem lub prośbę („słuchawki przyszły '
            'porysowane, jedna nie działa", „chcę zwrócić te buty, nie pasują", „proszę o fakturę za mój zakup"), '
            'wybierz właściwą kategorię bez wahania, to nie są wątpliwe przypadki. '
            'Odpowiedz WYŁĄCZNIE jednym słowem z listy: REKLAMACJA, ZWROT, FAKTURA, ESKALACJA, NONE.'
        ),
        'router_pytanie': 'Kategoria (REKLAMACJA/ZWROT/FAKTURA/ESKALACJA/NONE):',
        'rozmowa_label': 'ROZMOWA',
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
            'When the question is general, describe the general procedure first, and only then, if the context allows, '
            'mention special cases as an addition, not as the whole answer. '
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
        'email_system_reklamacja': (
            'You write a DRAFT complaint email to the seller on behalf of the buyer. '
            'Start with the sentence: "Draft message to the seller (fill in your details before sending):", '
            'then a blank line, then the email body. '
            'Take the problem description exclusively from the buyer conversation above, do not invent details '
            'that are not there. Follow the complaint process described in the "context" section (steps, required '
            'elements of the complaint). Mark the order number, purchase date, and any other specific data not '
            'present in the conversation with a placeholder in square brackets, e.g. [order number], [purchase date], '
            'never invent values. Write in gender neutral language (use "they" or rephrase to avoid gendered '
            'pronouns for the buyer); if it cannot be avoided, use a placeholder in square brackets. '
            'Split the content into short paragraphs, one idea per paragraph, blank line between them: greeting, '
            'description of the situation, a concrete request, closing. '
            'Keep the tone polite and factual. End with a clear request for resolution '
            '(repair, replacement, or refund). Do not add any explanation beyond the email draft itself. Answer in English.'
        ),
        'email_system_zwrot': (
            'You write a DRAFT message to the seller about returning a product (withdrawal from the contract) on '
            'behalf of the buyer. Start with the sentence: "Draft message to the seller (fill in your details before '
            'sending):", then a blank line, then the message body. '
            'Take the description of what is being returned and why exclusively from the conversation above, do not '
            'invent details. Follow the return process described in the "context" section (deadline, how to withdraw, '
            'what the seller must do). Mark the order number, purchase date, and any other specific data not present '
            'in the conversation with a placeholder in square brackets, never invent values. '
            'Write in gender neutral language (use "they" or rephrase to avoid gendered pronouns for the buyer); '
            'if it cannot be avoided, use a placeholder in square brackets. '
            'Split the content into short paragraphs, one idea per paragraph, blank line between them: greeting, '
            'description of the situation, a concrete request, closing. '
            'Keep the tone polite and factual. End with a clear statement of withdrawal from the contract and a '
            'request for return instructions. Do not add any explanation beyond the message draft itself. Answer in English.'
        ),
        'email_system_faktura': (
            'You write a DRAFT message to the seller requesting an invoice for a purchase, on behalf of the buyer. '
            'Start with the sentence: "Draft message to the seller (fill in your details before sending):", '
            'then a blank line, then the message body. '
            'Take the purchase description exclusively from the conversation above, do not invent details. '
            'Follow the invoicing process described in the "context" section. Mark the order number, purchase date, '
            'billing details, and any other specific data not present in the conversation with a placeholder in '
            'square brackets, never invent values. '
            'Write in gender neutral language (use "they" or rephrase to avoid gendered pronouns for the buyer); '
            'if it cannot be avoided, use a placeholder in square brackets. '
            'Split the content into short paragraphs, one idea per paragraph, blank line between them: greeting, '
            'description of the situation, a concrete request, closing. '
            'Keep the tone polite and factual. End with a clear request to '
            'issue the invoice. Do not add any explanation beyond the message draft itself. Answer in English.'
        ),
        'email_system_eskalacja': (
            'You write a DRAFT message asking Allegro to get involved in a discussion with a seller, on behalf of '
            'the buyer. Start with the sentence: "Draft message to Allegro (fill in your details before sending):", '
            'then a blank line, then the message body. '
            'Take the situation description (what was bought, what the problem is, why the seller did not help) '
            'exclusively from the conversation above, do not invent details. Follow ONLY the steps described in the '
            '"context" section: if the context does not describe a concrete escalation step, do not invent a '
            'procedure, use a placeholder in square brackets or say this needs to be checked in the Allegro Help '
            'Center instead of making up a process. Mark the order number, purchase date, and any other specific '
            'data not present in the conversation with a placeholder, never invent values. '
            'Write in gender neutral language (use "they" or rephrase to avoid gendered pronouns for the buyer); '
            'if it cannot be avoided, use a placeholder in square brackets. '
            'Split the content into short paragraphs, one idea per paragraph, blank line between them: greeting, '
            'description of the situation, a concrete request, closing. '
            'Keep the tone polite and factual. End with a clear request for Allegro to intervene. Do not add any '
            'explanation beyond the message draft itself. Answer in English.'
        ),
        'router_system': (
            'You classify what kind of help with a message to the seller/Allegro the buyer needs, based on the '
            'CONVERSATION. Categories: REKLAMACJA (item is defective, damaged, or not as described), ZWROT (buyer '
            'wants to return a working item and withdraw from the contract, no defect involved), FAKTURA (buyer '
            'asks for an invoice for a purchase), ESKALACJA (seller is not responding, is ignoring messages, or '
            'refuses to help: if the buyer has a defective item OR wants a return, BUT also reports the seller is '
            'not responding, choose ESKALACJA). '
            'The buyer must describe their OWN, CONCRETE situation happening NOW, with their own order. If they '
            'ask a general question about rules, deadlines, or procedures ("how long do I have to return an item", '
            '"how long does a complaint take"), without pointing to their own problem, answer NONE, even if the '
            'question contains the word "return" or "complaint". But when the buyer clearly describes their own '
            'item and problem or request ("the headphones arrived scratched, one earbud does not work", "I want to '
            'return these shoes, they do not fit", "please send me an invoice for my order"), pick the right '
            'category without hesitation, those are not doubtful cases. '
            'Reply with EXACTLY ONE WORD from this list: REKLAMACJA, ZWROT, FAKTURA, ESKALACJA, NONE.'
        ),
        'router_pytanie': 'Category (REKLAMACJA/ZWROT/FAKTURA/ESKALACJA/NONE):',
        'rozmowa_label': 'CONVERSATION',
    },
}

URL_REGEX = re.compile(r'https?://\S+|\bwww\.\S+', re.IGNORECASE)
KONCOWKA = '.,;:!?)]}>"\''
KATEGORIE_MAIL = ('reklamacja', 'zwrot', 'faktura', 'eskalacja')


def context(chunks: list[dict]) -> str:
    bloki = []
    for i, c in enumerate(chunks, 1):
        etykieta = c['tytul']
        if c.get('naglowek'):
            etykieta = f"{etykieta} ({c['naglowek']})"
        bloki.append(f'[{i}] {etykieta}\n{c["tekst"]}')
    return '\n\n'.join(bloki)


def zwin_linki_markdown(tekst: str) -> str:
    def zwin(dopasowanie):
        etykieta = dopasowanie.group(1).strip()
        if re.fullmatch(r'\d+', etykieta):
            return f'[{etykieta}]'
        return etykieta
    return re.sub(r'\[([^\[\]]+)\]\(\s*(?:https?://|www\.)[^\s()]+\s*\)', zwin, tekst)


def verify_answer(pelna: str, chunks: list) -> dict:
    mapa = {i: c['url'] for i, (c, _) in enumerate(chunks, 1)}

    obce = []
    pelna = zwin_linki_markdown(pelna)

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
