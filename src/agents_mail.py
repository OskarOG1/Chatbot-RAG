from agents_core import PROMPTY, klient, MAX_TOKENS, EMAIL_MODEL, context
import re

DRUGI_TEMAT = re.compile(r'\n(?:Temat|Subject):\s')


def napisz_email(history: list[dict], chunks: list, lang: str = 'pl', kategoria: str = 'reklamacja') -> dict:
    p = PROMPTY[lang]
    teksty = [c for c, _ in chunks]
    kontekst = context(teksty)

    wiadomosci = [{'role': 'system', 'content': p[f'email_system_{kategoria}']}]
    for w in (history or []):
        if w.get('role') in ('user', 'assistant') and w.get('content'):
            wiadomosci.append({'role': w['role'], 'content': w['content']})
    tresc = (f"{p['kontekst_label']}:\n{kontekst}\n\n"
             'Napisz teraz szkic wiadomości na podstawie powyższej rozmowy i procesu z kontekstu.'
             if lang == 'pl' else
             f"{p['kontekst_label']}:\n{kontekst}\n\n"
             'Now write the message draft based on the conversation above and the process in the context.')
    wiadomosci.append({'role': 'user', 'content': tresc})

    odp = klient.chat.completions.create(
        model=EMAIL_MODEL,
        messages=wiadomosci,
        stream=False,
        max_tokens=MAX_TOKENS,
    )
    tekst = re.sub(r'<\|.*?\|>', '', odp.choices[0].message.content).strip()
    dopasowania = list(DRUGI_TEMAT.finditer(tekst))
    if len(dopasowania) > 1:
        tekst = tekst[:dopasowania[1].start()].rstrip()
    return {'tekst': tekst}
