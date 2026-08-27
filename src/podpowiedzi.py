import re
import unicodedata
from lang_config import LANG
from rankings import RAG_DIR, wczytaj_chunki, z_cache
from spell import lematy

ILE = 3
URLI = 3
MIN_ZNAKI = 15
MAX_ZNAKI = 85
MAX_SLOW = 12
PROG_ZAPYTANIA = 0.5
PROG_MIEDZY = 0.45
WYMAGAJ_WSPOLNEGO_LEMATU = True

WZORCE = {
    'pl': re.compile(
        r'^(?:jak|czy|kiedy|ile|co|gdzie|jaki|jaka|jakie|jakim|jakich|dlaczego|kto|komu|'
        r'sk[aą]d|czym|za co|na czym|w jaki)\b', re.IGNORECASE),
    'en': re.compile(
        r'^(?:how|what|when|where|why|who|which|whose|can|do|does|is|are|should)\b',
        re.IGNORECASE),
}

ODRZUCANE_KONCE = ('.', ':', ';', '!')
INDEKS_CACHE = {}


def bez_ogonkow(s: str) -> str:
    s = s.replace('ł', 'l').replace('Ł', 'L')
    rozlozone = unicodedata.normalize('NFKD', s)
    return ''.join(z for z in rozlozone if not unicodedata.combining(z))


def klucz(linia: str) -> str:
    return re.sub(r'[^a-z0-9 ]', '', bez_ogonkow(linia.lower())).strip()


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def naglowek_pytaniowy(linia: str, wzorzec) -> bool:
    if not (MIN_ZNAKI <= len(linia) <= MAX_ZNAKI):
        return False
    if linia.endswith(ODRZUCANE_KONCE):
        return False
    if len(linia.split()) > MAX_SLOW:
        return False
    if any(z.isdigit() for z in linia) or 'http' in linia.lower():
        return False
    if not linia[0].isupper() or linia.isupper():
        return False
    return bool(wzorzec.match(linia))


def kandydaci(chunk: dict, wzorzec) -> list:
    zrodla = [chunk.get('naglowek') or '']
    zrodla.extend(chunk.get('tekst', '').split('\n'))
    return [linia for linia in (z.strip() for z in zrodla)
            if naglowek_pytaniowy(linia, wzorzec)]


def indeks_artykulow(lang: str) -> dict:
    sciezka = RAG_DIR / f"chunks{LANG[lang]['suffix']}.json"

    def buduj(_):
        wzorzec = WZORCE[lang]
        indeks = {}
        klucze = {}
        for chunk in wczytaj_chunki('all', lang):
            url = chunk.get('url')
            if not url:
                continue
            lista = indeks.setdefault(url, [])
            widziane = klucze.setdefault(url, set())
            for linia in kandydaci(chunk, wzorzec):
                k = klucz(linia)
                if k and k not in widziane:
                    widziane.add(k)
                    lista.append(linia)
        return indeks

    return z_cache(INDEKS_CACHE, lang, sciezka, buduj)


def jako_pytanie(linia: str) -> str:
    tekst = linia.rstrip(' ,')
    return tekst if tekst.endswith('?') else tekst + '?'


def kolejnosc_urli(chunks: list) -> list:
    urle = []
    for chunk, _ in chunks:
        url = chunk.get('url')
        if url and url not in urle:
            urle.append(url)
        if len(urle) >= URLI:
            break
    return urle


def zbuduj(chunks: list, query: str, lang: str = 'pl', ile: int = ILE) -> list:
    if lang not in WZORCE or not chunks:
        return []
    lemma_lang = LANG[lang]['lemma_lang']
    indeks = indeks_artykulow(lang)
    urle = kolejnosc_urli(chunks)
    if not urle:
        return []
    kontekst = lematy(query, lemma_lang) | lematy(chunks[0][0].get('tytul') or '', lemma_lang)
    lem_query = lematy(query, lemma_lang)

    wybrane = []
    lem_wybranych = []
    widziane = set()
    for pozycja, url in enumerate(urle):
        for linia in indeks.get(url, ()):
            k = klucz(linia)
            if not k or k in widziane:
                continue
            widziane.add(k)
            lem = lematy(linia, lemma_lang)
            if not lem or jaccard(lem, lem_query) >= PROG_ZAPYTANIA:
                continue
            if pozycja > 0 and WYMAGAJ_WSPOLNEGO_LEMATU and not (lem & kontekst):
                continue
            if any(jaccard(lem, poprzedni) >= PROG_MIEDZY for poprzedni in lem_wybranych):
                continue
            wybrane.append(jako_pytanie(linia))
            lem_wybranych.append(lem)
            if len(wybrane) >= ile:
                return wybrane
    return wybrane
