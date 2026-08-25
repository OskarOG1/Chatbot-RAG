STRONY = ('kupujacy', 'sprzedajacy')
STRONA_DO_AGENTA = {'kupujacy': 'kupujacy', 'sprzedajacy': 'sprzedaz'}
AGENT_DO_STRONY = {'kupujacy': 'kupujacy', 'konto': 'kupujacy', 'zakupy': 'kupujacy',
                   'platnosci': 'kupujacy', 'sprzedaz': 'sprzedajacy'}


def strona_z_agenta(agent: str) -> str:
    return AGENT_DO_STRONY.get(agent, 'kupujacy')


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
    druga = next(s for s in STRONY if s != strona_uzytkownika)
    ocena_uzytkownika = najlepsze.get(strona_uzytkownika)
    ocena_drugiej = najlepsze.get(druga)
    if ocena_drugiej is not None and (ocena_uzytkownika is None or ocena_drugiej > ocena_uzytkownika):
        wybrana = druga
    else:
        wybrana = strona_uzytkownika
    przewaga = None
    if ocena_uzytkownika is not None and ocena_drugiej is not None:
        przewaga = round(float(abs(ocena_uzytkownika - ocena_drugiej)), 4)
    chunki = [para for para in wyniki if strona_z_agenta(para[0]['agent']) == wybrana][:k]
    return wybrana, chunki, przewaga
