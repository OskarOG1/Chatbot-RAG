from lang_config import LANG
from agents_core import PROMPTY, klient, MAX_TOKENS, MODEL_FALLBACK, context, verify_answer
import koszty
import itertools
import re


def otworz_strumien(nazwa: str, wiadomosci: list[dict], stop: list[str]):
    return klient.chat.completions.create(
        model=nazwa,
        messages=wiadomosci,
        stream=True,
        max_tokens=MAX_TOKENS,
        stop=stop,
    )


def zbuduj_wiadomosci(query: str, agent: str, chunks: list[dict], bielik_model: str | None,
                       history: list[dict] | None, lang: str,
                       styl: str | None = None) -> tuple[list[dict], list[str], str, dict]:
    p = PROMPTY[lang]
    system_prompt = p['system_prompty'][agent] + p['grounding']
    if styl:
        system_prompt += p['styl_modyfikatory'][styl]
    system_prompt += p['cytaty_instrukcja']
    teksty = [c for c, _ in chunks]
    kontekst = context(teksty)

    tresc = f"{p['kontekst_label']}:\n{kontekst}\n\n{p['pytanie_label']}: {query}"
    nazwa = bielik_model or LANG[lang]['model']

    wiadomosci = [{'role': 'system', 'content': system_prompt}]
    for w in (history or []):
        if w.get('role') in ('user', 'assistant') and w.get('content'):
            wiadomosci.append({'role': w['role'], 'content': w['content']})
    wiadomosci.append({'role': 'user', 'content': tresc})

    stop = [f"{p['pytanie_label']}:", '<|start_header_id|>']
    return wiadomosci, stop, nazwa, p


def sfinalizuj(pelna: str, chunks: list, p: dict) -> dict:
    pelna = re.sub(r'<\|.*?\|>', '', pelna)
    pelna = pelna.removeprefix(p['odpowiedz_prefix']).strip()
    return verify_answer(pelna, chunks)


def answer_stream(query: str, agent: str, chunks: list[dict], bielik_model:str | None=None,
                  history:list[dict] | None=None, lang:str='pl', styl:str | None=None):
    wiadomosci, stop, nazwa, p = zbuduj_wiadomosci(query, agent, chunks, bielik_model, history, lang, styl)

    try:
        strumien = otworz_strumien(nazwa, wiadomosci, stop)
        pierwszy = next(strumien)
        kawalki = itertools.chain([pierwszy], strumien)
    except StopIteration:
        kawalki = iter(())
    except Exception as e:
        print(f'model {nazwa} niedostepny ({type(e).__name__}: {e}), fallback na {MODEL_FALLBACK}')
        nazwa = MODEL_FALLBACK
        kawalki = otworz_strumien(nazwa, wiadomosci, stop)

    pelna = ''
    for kawalek in kawalki:
        if not kawalek.choices:
            continue
        token = kawalek.choices[0].delta.content
        if not token:
            continue
        pelna += token
        yield {'typ': 'token', 'tekst': token}

    koszty.dodaj_z_odpowiedzi(nazwa, None, wiadomosci, pelna)
    yield {'typ': 'koniec', 'dane': sfinalizuj(pelna, chunks, p)}


def answer(query: str, agent: str, chunks: list[dict], bielik_model:str | None=None,
           history:list[dict] | None=None, lang:str='pl', styl:str | None=None) -> dict:
    wiadomosci, stop, nazwa, p = zbuduj_wiadomosci(query, agent, chunks, bielik_model, history, lang, styl)

    try:
        odp = klient.chat.completions.create(
            model=nazwa, messages=wiadomosci, stream=False, max_tokens=MAX_TOKENS, stop=stop,
        )
    except Exception as e:
        print(f'model {nazwa} niedostepny ({type(e).__name__}: {e}), fallback na {MODEL_FALLBACK}')
        nazwa = MODEL_FALLBACK
        odp = klient.chat.completions.create(
            model=nazwa, messages=wiadomosci, stream=False, max_tokens=MAX_TOKENS, stop=stop,
        )

    pelna = odp.choices[0].message.content
    koszty.dodaj_z_odpowiedzi(nazwa, odp, wiadomosci, pelna)
    return sfinalizuj(pelna, chunks, p)


def przepisz_zapytanie(query: str, history: list[dict] | None, bielik_model: str | None = None,
                        lang: str = 'pl') -> str:
    if not history:
        return query
    p = PROMPTY[lang]
    rozmowa = '\n'.join(f"{w['role']}: {w['content']}" for w in history
                        if w.get('role') in ('user', 'assistant') and w.get('content'))
    nazwa = bielik_model or LANG[lang]['model']
    wiadomosci = [
        {'role': 'system', 'content': p['przepisz_system']},
        {'role': 'user', 'content': f"{rozmowa}\nuser: {query}\n\n{p['przepisz_label']}:"},
    ]
    odp = klient.chat.completions.create(
        model=nazwa,
        messages=wiadomosci,
        stream=False,
        stop=['\n', f"{p['pytanie_label']}:"],
    )
    tekst = re.sub(r'<\|.*?\|>', '', odp.choices[0].message.content).strip()
    koszty.dodaj_z_odpowiedzi(nazwa, odp, wiadomosci, tekst)
    return tekst or query
