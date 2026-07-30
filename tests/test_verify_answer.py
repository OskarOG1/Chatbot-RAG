from agents import verify_answer


def _chunk(url, tekst='tresc'):
    return ({'url': url, 'tekst': tekst, 'tytul': 't'}, 0.9)


def test_numer_mapuje_na_url():
    chunks = [_chunk('https://allegro.pl/pomoc/dla-kupujacych/x/a-ABCDEF')]
    wynik = verify_answer('Tresc odpowiedzi.\n[1]', chunks)
    assert wynik['cytaty'] == [{'n': 1, 'url': 'https://allegro.pl/pomoc/dla-kupujacych/x/a-ABCDEF', 'tytul': 't'}]
    assert '[1]' not in wynik['tekst']


def test_numer_poza_zakresem_ignorowany():
    chunks = [_chunk('https://allegro.pl/pomoc/dla-kupujacych/x/a-ABCDEF')]
    wynik = verify_answer('Zrob to [5].', chunks)
    assert wynik['cytaty'] == []


def test_duplikaty_cytatow_zwijane():
    chunks = [_chunk('https://allegro.pl/pomoc/dla-kupujacych/x/a-ABCDEF')]
    wynik = verify_answer('Zrob to [1]. Potem znowu [1].', chunks)
    assert wynik['cytaty'] == [{'n': 1, 'url': 'https://allegro.pl/pomoc/dla-kupujacych/x/a-ABCDEF', 'tytul': 't'}]


def test_obce_url_wykryte():
    chunks = [_chunk('https://allegro.pl/pomoc/dla-kupujacych/x/a-ABCDEF')]
    wynik = verify_answer('Zobacz https://inny-sklep.pl/oferta', chunks)
    assert wynik['obce'] == ['https://inny-sklep.pl/oferta']


def test_znaczniki_security_wyciete():
    chunks = [_chunk('https://allegro.pl/pomoc/dla-kupujacych/x/a-ABCDEF')]
    wynik = verify_answer('[Security: uwaga] Tresc odpowiedzi.', chunks)
    assert 'Security' not in wynik['tekst']
    assert wynik['tekst'] == 'Tresc odpowiedzi.'


def test_gole_numery_na_koncu_wyciete():
    chunks = [_chunk('https://allegro.pl/pomoc/dla-kupujacych/x/a-ABCDEF')]
    wynik = verify_answer('Tresc odpowiedzi.\n[1] [1]', chunks)
    assert wynik['tekst'] == 'Tresc odpowiedzi.'


def test_naglowek_zrodlo_bez_listy_wyciety():
    chunks = [_chunk('https://allegro.pl/pomoc/dla-kupujacych/x/a-ABCDEF')]
    wynik = verify_answer('Tresc odpowiedzi. [1]\n\nŹródło:', chunks)
    assert wynik['tekst'] == 'Tresc odpowiedzi.'
    assert wynik['cytaty'] == [{'n': 1, 'url': 'https://allegro.pl/pomoc/dla-kupujacych/x/a-ABCDEF', 'tytul': 't'}]


def test_naglowek_zrodla_z_lista_w_tej_samej_linii_wyciety():
    chunks = [_chunk('https://allegro.pl/pomoc/dla-kupujacych/x/a-ABCDEF')]
    wynik = verify_answer('Tresc odpowiedzi. [1]\nŹródła: [1],', chunks)
    assert wynik['tekst'] == 'Tresc odpowiedzi.'


def test_naglowek_zrodla_wielu_numerow_wyciety():
    chunks = [_chunk('https://allegro.pl/pomoc/dla-kupujacych/x/a-ABCDEF'), _chunk('https://allegro.pl/pomoc/y-GHIJKL')]
    wynik = verify_answer('Tresc odpowiedzi. [1][2]\nŹródła: [3], [2],', chunks)
    assert wynik['tekst'] == 'Tresc odpowiedzi.'


def test_naglowek_zrodla_z_lista_ponizej_wycieta():
    chunks = [_chunk('https://allegro.pl/pomoc/dla-kupujacych/x/a-ABCDEF')]
    wynik = verify_answer('Tresc odpowiedzi. [1]\n\nŹródła:\n[1] tytuł artykułu', chunks)
    assert wynik['tekst'] == 'Tresc odpowiedzi.'


def test_slowo_zrodla_w_srodku_zdania_nie_wyciete():
    chunks = [_chunk('https://allegro.pl/pomoc/dla-kupujacych/x/a-ABCDEF')]
    wynik = verify_answer('Informacje znajdziesz w sekcji źródła centrum pomocy [1].', chunks)
    assert 'źródła' in wynik['tekst']
