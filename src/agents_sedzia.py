from lang_config import LANG
from agents_core import (PROMPTY, czat, context, skroc_tekst, KATEGORIE_MAIL,
                         SEDZIA_TIMEOUT, SEDZIA_ZNAKOW)
import re


def czy_kontekst_odpowiada(query: str, chunks: list, bielik_model: str | None = None,
                            lang: str = 'pl', stan: dict | None = None,
                            limit_znakow: int | None = None) -> bool:
    p = PROMPTY[lang]
    limit = SEDZIA_ZNAKOW if limit_znakow is None else limit_znakow
    teksty = [dict(c, tekst=skroc_tekst(c['tekst'], limit)) for c, _ in chunks]
    kontekst = context(teksty)
    wiadomosci = [
        {'role': 'system', 'content': p['sedzia_system']},
        {'role': 'user', 'content': (
            f"{p['sedzia_kontekst_label']}:\n{kontekst}\n\n"
            f"{p['sedzia_pytanie_label']}: {query}\n\n{p['sedzia_pytanie']}"
        )},
    ]
    try:
        odp = czat(bielik_model or LANG[lang]['sedzia_model'], wiadomosci,
                   limit_czasu=SEDZIA_TIMEOUT,
                   stop=['\n', f"{p['pytanie_label']}:"], max_tokens=12)
    except Exception as e:
        print(f'sedzia kontekstu niedostepny ({type(e).__name__}: {e}), przepuszczam dalej',
              flush=True)
        if stan is not None:
            stan['sedzia_pominiety'] = True
        return True
    tekst = re.sub(r'<\|.*?\|>', '', odp.choices[0].message.content).strip().upper()
    return not tekst.startswith(p['nie_marker'])


def sedzia_kategoria_mail(history: list[dict], chunks: list, lang: str = 'pl') -> str | None:
    p = PROMPTY[lang]
    teksty = [c for c, _ in chunks]
    kontekst = context(teksty)
    rozmowa = '\n'.join(f"{w['role']}: {w['content']}" for w in (history or [])
                        if w.get('role') in ('user', 'assistant') and w.get('content'))
    wiadomosci = [
        {'role': 'system', 'content': p['router_system']},
        {'role': 'user', 'content': (
            f"{p['sedzia_kontekst_label']}:\n{kontekst}\n\n"
            f"{p['rozmowa_label']}:\n{rozmowa}\n\n{p['router_pytanie']}"
        )},
    ]
    try:
        odp = czat(LANG[lang]['router_model'], wiadomosci, stop=['\n'])
    except Exception as e:
        print(f'router kategorii maila niedostepny ({type(e).__name__}: {e})', flush=True)
        return None
    tekst = re.sub(r'<\|.*?\|>', '', odp.choices[0].message.content).strip().upper()
    for kategoria in KATEGORIE_MAIL:
        if tekst.startswith(kategoria.upper()):
            return kategoria
    return None
