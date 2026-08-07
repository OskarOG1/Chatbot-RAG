from pipeline import cytaty_lub_zrodla


def chunk(url, tytul='t'):
    return ({'url': url, 'tytul': tytul}, 0.9)


def test_cytaty_niepuste_zwracane_bez_zmian():
    cytaty = [{'n': 1, 'url': 'https://allegro.pl/a', 'tytul': 't'}]
    chunks = [chunk('https://allegro.pl/a'), chunk('https://allegro.pl/b')]
    assert cytaty_lub_zrodla(cytaty, chunks) == cytaty


def test_cytaty_puste_spadaja_na_zrodla_chunkow():
    chunks = [chunk('https://allegro.pl/a', 'Artykul A'), chunk('https://allegro.pl/b', 'Artykul B')]
    wynik = cytaty_lub_zrodla([], chunks)
    assert wynik == [
        {'n': 1, 'url': 'https://allegro.pl/a', 'tytul': 'Artykul A'},
        {'n': 2, 'url': 'https://allegro.pl/b', 'tytul': 'Artykul B'},
    ]


def test_fallback_deduplikuje_te_sama_strone():
    chunks = [chunk('https://allegro.pl/a', 'X'), chunk('https://allegro.pl/a', 'X')]
    assert cytaty_lub_zrodla([], chunks) == [{'n': 1, 'url': 'https://allegro.pl/a', 'tytul': 'X'}]


def test_brak_chunkow_i_cytatow_daje_pusta_liste():
    assert cytaty_lub_zrodla([], []) == []
