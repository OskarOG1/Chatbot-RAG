from spell import tokenize_words

MARKERY_STRON = {
    'kupujacy': {
        'slowa': {'kupiłem', 'kupilem', 'kupiłam', 'kupilam', 'zamówiłem', 'zamowilem',
                  'zamówiłam', 'zamowilam', 'zamówienie', 'zamowienie', 'zamówienia', 'zamowienia',
                  'zamówień', 'zamowien', 'przesyłka', 'przesylka', 'przesyłkę', 'przesylke',
                  'przesyłki', 'przesylki', 'paczka', 'paczke', 'paczkę', 'paczki'},
        'frazy': ('moja przesyłka', 'moja przesylka', 'moje zamówienie', 'moje zamowienie',
                  'sprzedawca nie', 'moja paczka'),
    },
    'sprzedajacy': {
        'slowa': {'sprzedaję', 'sprzedaje', 'sprzedajesz', 'wystawiam', 'wystawiłem', 'wystawilem',
                  'wystawić', 'wystawic', 'prowizja', 'prowizję', 'prowizje', 'prowizji',
                  'wypłata', 'wyplata', 'wypłatę', 'wyplate', 'wypłaty', 'wyplaty', 'aukcje',
                  'aukcja', 'aukcji'},
        'frazy': ('moja oferta', 'moje oferty', 'mój kupujący', 'moj kupujacy', 'moi kupujący',
                  'moi kupujacy', 'allegro ads', 'moje aukcje', 'wystawić przedmiot',
                  'wystawic przedmiot', 'moja sprzedaż', 'moja sprzedaz', 'mój sklep', 'moj sklep'),
    },
}


def prior_strony(query: str, agent_poprzedni: str | None,
                  czy_followup: bool = False) -> tuple[str | None, str | None]:
    low = query.lower()
    tokeny = set(tokenize_words(low))
    trafienia = set()
    for strona, markery in MARKERY_STRON.items():
        if tokeny & markery['slowa'] or any(fraza in low for fraza in markery['frazy']):
            trafienia.add(strona)

    if len(trafienia) == 1:
        return next(iter(trafienia)), 'leksykalna'

    if agent_poprzedni and (czy_followup or not trafienia):
        strona = 'sprzedajacy' if agent_poprzedni == 'sprzedaz' else 'kupujacy'
        return strona, 'lepka'

    return None, None
