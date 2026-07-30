from lang_config import LANG
from agents_core import PROMPTY, klient, context, KATEGORIE_MAIL
import re


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


def sedzia_kategoria_mail(history: list[dict], chunks: list, lang: str = 'pl') -> str | None:
    p = PROMPTY[lang]
    teksty = [c for c, _ in chunks]
    kontekst = context(teksty)
    rozmowa = '\n'.join(f"{w['role']}: {w['content']}" for w in (history or [])
                        if w.get('role') in ('user', 'assistant') and w.get('content'))
    odp = klient.chat.completions.create(
        model=LANG[lang]['router_model'],
        messages=[
            {'role': 'system', 'content': p['router_system']},
            {'role': 'user', 'content': (
                f"{p['sedzia_kontekst_label']}:\n{kontekst}\n\n"
                f"{p['rozmowa_label']}:\n{rozmowa}\n\n{p['router_pytanie']}"
            )},
        ],
        stream=False,
        stop=['\n'],
    )
    tekst = re.sub(r'<\|.*?\|>', '', odp.choices[0].message.content).strip().upper()
    for kategoria in KATEGORIE_MAIL:
        if tekst.startswith(kategoria.upper()):
            return kategoria
    return None
