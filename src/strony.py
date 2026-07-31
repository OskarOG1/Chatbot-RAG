from lang_config import LANG
from spell import tokenize_words

STRONY = ('kupujacy', 'sprzedajacy')
STRONA_DO_AGENTA = {'kupujacy': 'kupujacy', 'sprzedajacy': 'sprzedaz'}

BONUS_PRIOR = 0.75
MARGINES_REMIS = 5.0
TOP_N_DECYZJA = 3


def strona_chunka(chunk: dict) -> str:
    return 'sprzedajacy' if chunk.get('agent') == 'sprzedaz' else 'kupujacy'


def prior_strony(query: str, agent_poprzedni: str | None, lang: str = 'pl') -> tuple[str | None, str | None]:
    if agent_poprzedni:
        strona = 'sprzedajacy' if agent_poprzedni == 'sprzedaz' else 'kupujacy'
        return strona, 'lepka'

    cfg = LANG[lang]
    low = query.lower()
    tokeny = set(tokenize_words(low))
    trafienia = set()
    for strona, markery in cfg['markery_stron'].items():
        if tokeny & markery['slowa'] or any(fraza in low for fraza in markery['frazy']):
            trafienia.add(strona)

    if len(trafienia) == 1:
        return next(iter(trafienia)), 'leksykalna'
    return None, None


def przydzial_kandydatow(prior: str | None, sila: str | None) -> dict[str, int]:
    if prior is None:
        return {'kupujacy': 13, 'sprzedaz': 13}

    if sila == 'leksykalna':
        preferowana, inna = 20, 8
    elif sila == 'lepka':
        preferowana, inna = 20, 6
    else:
        preferowana = inna = 13

    inna_strona = next(s for s in STRONY if s != prior)
    return {STRONA_DO_AGENTA[prior]: preferowana, STRONA_DO_AGENTA[inna_strona]: inna}


def rozstrzygnij(chunks: list[tuple[dict, float]], prior: str | None, sila: str | None,
                  k: int = 5) -> tuple[str, list[tuple[dict, float]], bool]:
    if not chunks:
        return 'kupujacy', [], False

    surowe_grupy = {strona: [] for strona in STRONY}
    bonus_grupy = {strona: [] for strona in STRONY}
    for chunk, score in chunks:
        strona = strona_chunka(chunk)
        surowe_grupy[strona].append(score)
        bonus_grupy[strona].append(score + (BONUS_PRIOR if strona == prior else 0.0))

    for strona in STRONY:
        surowe_grupy[strona].sort(reverse=True)
        bonus_grupy[strona].sort(reverse=True)

    def suma_topn(grupa: dict) -> dict:
        return {strona: sum(wartosci[:TOP_N_DECYZJA]) if wartosci else float('-inf')
                for strona, wartosci in grupa.items()}

    wynik_surowy = suma_topn(surowe_grupy)
    wynik_bonus = suma_topn(bonus_grupy)

    zwyciezca = max(STRONY, key=lambda s: wynik_bonus[s])

    if prior is None:
        inna_strona = next(s for s in STRONY if s != zwyciezca)
        czy_pytac = abs(wynik_bonus[zwyciezca] - wynik_bonus[inna_strona]) <= MARGINES_REMIS
    else:
        inna_strona = next(s for s in STRONY if s != prior)
        przewaga_surowa = wynik_surowy[inna_strona] - wynik_surowy[prior]
        czy_pytac = przewaga_surowa > BONUS_PRIOR + MARGINES_REMIS

    chunks_jednorodne = [(c, s) for c, s in chunks if strona_chunka(c) == zwyciezca][:k]
    return zwyciezca, chunks_jednorodne, czy_pytac
