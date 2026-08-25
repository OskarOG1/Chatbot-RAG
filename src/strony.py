import sys

STRONY = ('kupujacy', 'sprzedajacy')
STRONA_DO_AGENTA = {'kupujacy': 'kupujacy', 'sprzedajacy': 'sprzedaz'}
AGENT_DO_STRONY = {'kupujacy': 'kupujacy', 'konto': 'kupujacy', 'zakupy': 'kupujacy',
                   'platnosci': 'kupujacy', 'sprzedaz': 'sprzedajacy'}
STRONA_ZAPASOWA = 'kupujacy'
AGENCI_NIEZNANI = set()


def strona_z_agenta(agent: str) -> str:
    strona = AGENT_DO_STRONY.get(agent)
    if strona is not None:
        return strona
    if agent not in AGENCI_NIEZNANI:
        AGENCI_NIEZNANI.add(agent)
        print(f'UWAGA: nieznany agent {agent!r}, przypisuje do strony {STRONA_ZAPASOWA}',
              file=sys.stderr, flush=True)
    return STRONA_ZAPASOWA


def agenci_wszystkich_stron() -> list[str]:
    return [STRONA_DO_AGENTA[s] for s in STRONY]


def rozstrzygnij(wyniki: list, strona_uzytkownika: str, k: int) -> tuple[str, list, float | None]:
    if not wyniki:
        return strona_uzytkownika, [], None
    najlepsze = {}
    for chunk, ocena in wyniki:
        strona = strona_z_agenta(chunk['agent'])
        if strona not in najlepsze or ocena > najlepsze[strona]:
            najlepsze[strona] = ocena
    wybrana = max(najlepsze, key=lambda s: (najlepsze[s], s == strona_uzytkownika))
    ocena_uzytkownika = najlepsze.get(strona_uzytkownika)
    oceny_obce = [ocena for s, ocena in najlepsze.items() if s != strona_uzytkownika]
    przewaga = None
    if ocena_uzytkownika is not None and oceny_obce:
        przewaga = round(float(abs(ocena_uzytkownika - max(oceny_obce))), 4)
    chunki = [para for para in wyniki if strona_z_agenta(para[0]['agent']) == wybrana][:k]
    return wybrana, chunki, przewaga
