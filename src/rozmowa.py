from guards import bez_ogonkow
from lang_config import LANG
from spell import tokenize_words, MIN_DLUGOSC

MAX_TOKENOW_ROZMOWY = 5
MAKS_WYPELNIACZY = 2
PODKLASY_STEROWANIA = ('prosciej', 'rozwin', 'potwierdzenie')


def fold_tokeny(tekst: str) -> list[str]:
    return [bez_ogonkow(t) for t in tokenize_words(tekst)]


def zawiera_fraze(tokeny: list[str], fraza_tokeny: list[str]) -> bool:
    n = len(fraza_tokeny)
    return any(tokeny[i:i + n] == fraza_tokeny for i in range(len(tokeny) - n + 1))


def dopasuj_liste(tokeny: list[str], frazy: tuple[str, ...],
                  maks_wypelniaczy: int = MAKS_WYPELNIACZY) -> bool:
    for fraza in frazy:
        fraza_tokeny = fold_tokeny(fraza)
        if len(fraza_tokeny) > len(tokeny):
            continue
        if zawiera_fraze(tokeny, fraza_tokeny) and len(tokeny) - len(fraza_tokeny) <= maks_wypelniaczy:
            return True
    return False


def odetnij_powitanie(query: str, lang: str) -> str | None:
    cfg = LANG[lang]['rozmowa_listy']
    znaki = query.strip()
    zloz_pelne = bez_ogonkow(znaki.lower())
    for fraza in cfg['powitania']:
        zloz_fraza = bez_ogonkow(fraza.lower())
        if not zloz_pelne.startswith(zloz_fraza):
            continue
        dalej = znaki[len(fraza):len(fraza) + 1]
        if dalej and dalej.isalpha():
            continue
        reszta = znaki[len(fraza):].lstrip(' ,:;-').strip()
        tresciowe = [t for t in tokenize_words(reszta) if len(t) >= MIN_DLUGOSC]
        if len(tresciowe) >= 2:
            return reszta
        return None
    return None


def podklasa_sterowania(query: str, lang: str = 'pl') -> str:
    cfg = LANG[lang]['rozmowa_listy']
    tokeny = fold_tokeny(query)
    for podklasa in PODKLASY_STEROWANIA:
        if dopasuj_liste(tokeny, cfg['sterowanie'][podklasa]):
            return podklasa
    return 'prosciej'


def klasa_tury(query: str, history: list[dict], agent_poprzedni: str | None,
               lang: str = 'pl') -> tuple[str | None, str]:
    cfg = LANG[lang]['rozmowa_listy']

    reszta_prefiksu = odetnij_powitanie(query, lang)
    if reszta_prefiksu is not None:
        return None, reszta_prefiksu

    tokeny = fold_tokeny(query)

    if len(tokeny) <= MAX_TOKENOW_ROZMOWY:
        if not history and dopasuj_liste(tokeny, cfg['powitania']):
            return 'powitanie', query
        if dopasuj_liste(tokeny, cfg['podziekowania']):
            return 'podziekowanie', query

    if dopasuj_liste(tokeny, cfg['meta']):
        return 'meta', query

    if history and agent_poprzedni:
        for podklasa in PODKLASY_STEROWANIA:
            if dopasuj_liste(tokeny, cfg['sterowanie'][podklasa]):
                return 'sterowanie', query

    return None, query
