from lang_config import LANG
from spell import tokenize_words

STRONY = ('kupujacy', 'sprzedajacy')
STRONA_DO_AGENTA = {'kupujacy': 'kupujacy', 'sprzedajacy': 'sprzedaz'}


def prior_strony(query: str, agent_poprzedni: str | None, lang: str = 'pl',
                  czy_followup: bool = False) -> tuple[str | None, str | None]:
    cfg = LANG[lang]
    low = query.lower()
    tokeny = set(tokenize_words(low))
    trafienia = set()
    for strona, markery in cfg['markery_stron'].items():
        if tokeny & markery['slowa'] or any(fraza in low for fraza in markery['frazy']):
            trafienia.add(strona)

    if len(trafienia) == 1:
        return next(iter(trafienia)), 'leksykalna'

    if agent_poprzedni and (czy_followup or not trafienia):
        strona = 'sprzedajacy' if agent_poprzedni == 'sprzedaz' else 'kupujacy'
        return strona, 'lepka'

    return None, None
