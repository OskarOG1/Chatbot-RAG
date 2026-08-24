from functools import lru_cache
from guards import bez_ogonkow
from lang_config import LANG
from spell import tokenize_words
import re

MIN_ZNAKI_ODPOWIEDZI = 20
KONIEC_ZDANIA = re.compile(r'(?<=[.!?])\s+')
NUMER_CYTATU = re.compile(r'\[\d+\]')
NAGLOWEK_MD = re.compile(r'(?m)^[ \t]*#{1,6}[ \t]*')
ZNACZNIK_CZATU = re.compile(r'<\|.*?\|>')

WZORCE_KONKRETOW = (
    re.compile(r'\d+(?:[.,]\d+)?\s*(?:zl|pln|gr|eur|usd|%|proc)\b'),
    re.compile(r'\b\d{1,3}\s*(?:dni|dzien|dnia|godz|godzin|godziny|godzinach|tygodni|tygodnie|'
               r'tygodnia|miesiac|miesiace|miesiecy|miesiacu|rok|roku|lat|lata|roboczych|'
               r'day|days|hour|hours|week|weeks|month|months|year|years|business)\b'),
    re.compile(r'\bart\s*\.?\s*\d+|§\s*\d+'),
    re.compile(r'[^\s@]+@[^\s@]+\.[^\s@]+'),
    re.compile(r'(?:\+\d{1,3}[\s-]?)?(?:\d[\s.-]?){9,}'),
    re.compile(r'https?://\S+|www\.\S+'),
)


def fold(tekst: str) -> str:
    return bez_ogonkow(tekst.lower())


@lru_cache(maxsize=8)
def listy_zablokowane(lang: str) -> tuple:
    cfg = LANG[lang]['ogolna']['tematy_zablokowane']
    return tuple((nazwa,
                  frozenset(fold(s) for s in kat['slowa']),
                  tuple(fold(f) for f in kat['frazy']))
                 for nazwa, kat in cfg.items())


def temat_zablokowany(query: str, lang: str = 'pl') -> str | None:
    plaski = fold(query)
    tokeny = set(tokenize_words(plaski))
    for nazwa, slowa, frazy in listy_zablokowane(lang):
        if tokeny & slowa:
            return nazwa
        if any(fraza in plaski for fraza in frazy):
            return nazwa
    return None


@lru_cache(maxsize=8)
def listy_domeny(lang: str) -> tuple:
    cfg = LANG[lang]['ogolna']['domena']
    return (frozenset(fold(s) for s in cfg['slowa']),
            tuple(fold(f) for f in cfg['frazy']))


def pytanie_o_allegro(query: str, lang: str = 'pl') -> bool:
    plaski = fold(query)
    slowa, frazy = listy_domeny(lang)
    if set(tokenize_words(plaski)) & slowa:
        return True
    return any(fraza in plaski for fraza in frazy)


def komunikat_tematu(nazwa: str, lang: str = 'pl') -> str:
    cfg = LANG[lang]['ogolna']
    return cfg['tematy_zablokowane'][nazwa].get('komunikat') or cfg['poza_zakresem']


def oczysc(tekst: str) -> str:
    tekst = ZNACZNIK_CZATU.sub('', tekst)
    tekst = NAGLOWEK_MD.sub('', tekst)
    tekst = NUMER_CYTATU.sub('', tekst)
    tekst = re.sub(r'[ \t]{2,}', ' ', tekst)
    tekst = re.sub(r'\n{3,}', '\n\n', tekst)
    tekst = re.sub(r'[ \t]+([,.;:!?])', r'\1', tekst)
    return tekst.strip()


def skroc_do_zdan(tekst: str, maks: int) -> str:
    zdania = KONIEC_ZDANIA.split(tekst.strip())
    if len(zdania) <= maks:
        return tekst.strip()
    return ' '.join(zdania[:maks]).strip()


def konkrety(tekst: str) -> list[str]:
    plaski = fold(tekst)
    znalezione = []
    for wzorzec in WZORCE_KONKRETOW:
        for dopasowanie in wzorzec.finditer(plaski):
            trafienie = dopasowanie.group(0).strip()
            if trafienie and trafienie not in znalezione:
                znalezione.append(trafienie)
    return znalezione


def sprawdz_odpowiedz(surowa: str, lang: str = 'pl') -> dict:
    cfg = LANG[lang]['ogolna']
    tekst = skroc_do_zdan(oczysc(surowa), cfg['maks_zdan'])
    if len(tekst) < MIN_ZNAKI_ODPOWIEDZI:
        return {'tekst': tekst, 'powod': 'ogolna_pusta', 'konkrety': []}
    if len(tekst) > cfg['maks_znakow']:
        return {'tekst': tekst, 'powod': 'ogolna_dluga', 'konkrety': []}
    znalezione = konkrety(tekst)
    if znalezione:
        return {'tekst': tekst, 'powod': 'ogolna_konkrety', 'konkrety': znalezione}
    return {'tekst': tekst, 'powod': None, 'konkrety': []}
