from lang_config import LANG
from spell import tokenize_words

STRONY = ('kupujacy', 'sprzedajacy')
STRONA_DO_AGENTA = {'kupujacy': 'kupujacy', 'sprzedajacy': 'sprzedaz'}

BONUS_PRIOR = 3.5
KARA_WYBOR = 7.0
MARGINES_REMIS = 0.5
TOP_N_DECYZJA = 3


def strona_chunka(chunk: dict) -> str:
    return 'sprzedajacy' if chunk.get('agent') == 'sprzedaz' else 'kupujacy'


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


def przydzial_kandydatow(prior: str | None, sila: str | None) -> dict[str, int]:
    if prior is None:
        return {'kupujacy': 13, 'sprzedaz': 13}

    if sila == 'wybor':
        preferowana, inna = 22, 6
    elif sila == 'leksykalna':
        preferowana, inna = 20, 8
    elif sila == 'lepka':
        preferowana, inna = 18, 10
    elif sila == 'llm':
        preferowana, inna = 18, 10
    elif sila == 'leksykalna_slaba':
        preferowana, inna = 16, 11
    else:
        preferowana = inna = 13

    inna_strona = next(s for s in STRONY if s != prior)
    return {STRONA_DO_AGENTA[prior]: preferowana, STRONA_DO_AGENTA[inna_strona]: inna}


def rozstrzygnij(chunks: list[tuple[dict, float]], prior: str | None, sila: str | None,
                  k: int = 5, kara: float = BONUS_PRIOR) -> tuple[str, list[tuple[dict, float]], bool]:
    if not chunks:
        return 'kupujacy', [], False

    surowe_grupy = {strona: [] for strona in STRONY}
    bonus_grupy = {strona: [] for strona in STRONY}
    for chunk, score in chunks:
        strona = strona_chunka(chunk)
        surowe_grupy[strona].append(score)
        bonus_grupy[strona].append(score + (kara if strona == prior else 0.0))

    for strona in STRONY:
        surowe_grupy[strona].sort(reverse=True)
        bonus_grupy[strona].sort(reverse=True)

    def srednia_topn(grupa: dict) -> dict:
        wyniki = {}
        for strona, wartosci in grupa.items():
            gora = wartosci[:TOP_N_DECYZJA]
            wyniki[strona] = sum(gora) / len(gora) if gora else float('-inf')
        return wyniki

    wynik_surowy = srednia_topn(surowe_grupy)
    wynik_bonus = srednia_topn(bonus_grupy)

    zwyciezca = max(STRONY, key=lambda s: wynik_bonus[s])

    if prior is None:
        inna_strona = next(s for s in STRONY if s != zwyciezca)
        czy_pytac = abs(wynik_bonus[zwyciezca] - wynik_bonus[inna_strona]) <= MARGINES_REMIS
    else:
        inna_strona = next(s for s in STRONY if s != prior)
        przewaga_surowa = wynik_surowy[inna_strona] - wynik_surowy[prior]
        czy_pytac = przewaga_surowa > kara + MARGINES_REMIS

    def klucz_kary(para: tuple[dict, float]) -> float:
        chunk, score = para
        return score + (kara if strona_chunka(chunk) == prior else 0.0)

    chunks_top = sorted(chunks, key=klucz_kary, reverse=True)[:k]
    return zwyciezca, chunks_top, czy_pytac
