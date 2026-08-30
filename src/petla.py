from strony import STRONA_DO_AGENTA

DECYZJE_CZLOWIEKA = ('artykul', 'alias', 'pomijamy')


def indeks_logu(wpisy_logu: list[dict]) -> dict[str, dict]:
    indeks: dict[str, dict] = {}
    for wpis in wpisy_logu:
        if wpis.get('typ'):
            continue
        ident = wpis.get('id')
        if ident and ident not in indeks:
            indeks[ident] = wpis
    return indeks


def propozycja_z_logu(wpis: dict) -> tuple[str | None, float | None]:
    cechy = wpis.get('cechy') or {}
    zrodlo = cechy.get('zrodlo_top1')
    rerank = cechy.get('rerank_top1')
    url = zrodlo if isinstance(zrodlo, str) and zrodlo else None
    ocena = rerank if isinstance(rerank, (int, float)) and not isinstance(rerank, bool) else None
    return url, ocena


def wiersz_do_przegladu(zgloszenie: dict, wpis: dict | None) -> dict:
    url, rerank = (None, None)
    if wpis is not None:
        url, rerank = propozycja_z_logu(wpis)
    return {
        'zgloszenie': zgloszenie.get('zgloszenie'),
        'pytanie': zgloszenie.get('pytanie'),
        'lang': zgloszenie.get('lang'),
        'agent': STRONA_DO_AGENTA.get(zgloszenie.get('strona')),
        'etykieta': zgloszenie.get('etykieta'),
        'odpowiedz_operatora': zgloszenie.get('tresc'),
        'propozycja_url': url,
        'rerank_top1': rerank,
        'decyzja': None,
        'url': None,
    }


def klasyfikuj(stan: dict[str, dict], wpisy_logu: list[dict]) -> dict:
    indeks = indeks_logu(wpisy_logu)
    do_przegladu: list[dict] = []
    bez_logu: list[dict] = []
    strony_nieznane: list[dict] = []
    liczniki_status = {'nowe': 0, 'odpowiedziano': 0, 'odrzucone': 0, 'inne': 0}
    liczniki_etykiet: dict[str, int] = {}
    for zgloszenie in stan.values():
        status = zgloszenie.get('status')
        liczniki_status[status if status in liczniki_status else 'inne'] += 1
        if status != 'odpowiedziano':
            continue
        etykieta = zgloszenie.get('etykieta')
        klucz_etykiety = etykieta if etykieta is not None else 'brak_etykiety'
        liczniki_etykiet[klucz_etykiety] = liczniki_etykiet.get(klucz_etykiety, 0) + 1
        wpis = indeks.get(zgloszenie.get('id_zapytania') or '')
        wiersz = wiersz_do_przegladu(zgloszenie, wpis)
        if wiersz['agent'] is None:
            strony_nieznane.append({
                'zgloszenie': wiersz['zgloszenie'],
                'strona': zgloszenie.get('strona'),
            })
        if wpis is None:
            bez_logu.append(wiersz)
        else:
            do_przegladu.append(wiersz)
    podsumowanie = {
        'status': liczniki_status,
        'etykiety_odpowiedziano': liczniki_etykiet,
        'do_przegladu': len(do_przegladu),
        'bez_logu': len(bez_logu),
        'wymaga_decyzji_czlowieka': liczniki_etykiet.get('brak_etykiety', 0),
        'strona_nieznana': len(strony_nieznane),
    }
    return {
        'do_przegladu': do_przegladu,
        'bez_logu': bez_logu,
        'strony_nieznane': strony_nieznane,
        'podsumowanie': podsumowanie,
    }
