from lang_config import LANG, MODEL_DOMYSLNY
from agents_core import PROMPTY, klient, context, KATEGORIE_MAIL, ETYKIETY_STRON
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


def strona_pytania(query: str, history: list[dict] | None = None, lang: str = 'pl') -> str | None:
    p = PROMPTY[lang]
    ostatnia = next((w['content'] for w in reversed(history or [])
                     if w.get('role') == 'user' and w.get('content')), '')
    tresc = f'{ostatnia} {query}'.strip()
    nazwa = LANG[lang]['router_model']
    wiadomosci = [
        {'role': 'system', 'content': p['strona_system']},
        {'role': 'user', 'content': f"{p['pytanie_label']}: {tresc}\n\n{p['strona_pytanie']}"},
    ]
    try:
        odp = klient.chat.completions.create(
            model=nazwa, messages=wiadomosci, stream=False, stop=['\n'], max_tokens=12,
        )
    except Exception as e:
        print(f'model {nazwa} niedostepny ({type(e).__name__}: {e}), fallback na {MODEL_DOMYSLNY}')
        try:
            odp = klient.chat.completions.create(
                model=MODEL_DOMYSLNY, messages=wiadomosci, stream=False, stop=['\n'], max_tokens=12,
            )
        except Exception:
            return None
    tekst = re.sub(r'<\|.*?\|>', '', odp.choices[0].message.content).strip().upper()
    for etykieta, strona in ETYKIETY_STRON[lang].items():
        if tekst.startswith(etykieta):
            return strona
    return None
