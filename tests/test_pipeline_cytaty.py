from agents_core import verify_answer

CHUNKI = [
    ({'url': 'https://allegro.pl/pomoc/a', 'tytul': 'Artykul A'}, 1.0),
    ({'url': 'https://allegro.pl/pomoc/b', 'tytul': 'Artykul B'}, 0.5),
]


def test_odpowiedz_bez_numeru_nie_daje_zadnego_zrodla():
    assert verify_answer('Zrob X, potem Y.', CHUNKI)['cytaty'] == []


def test_zacytowany_jest_tylko_ten_numer_ktory_padl_w_tresci():
    cytaty = verify_answer('Zrob X [1], potem Y.', CHUNKI)['cytaty']
    assert [c['url'] for c in cytaty] == ['https://allegro.pl/pomoc/a']


def test_dwa_numery_daja_dwa_zrodla_w_kolejnosci_wystapienia():
    cytaty = verify_answer('Najpierw Y [2], potem X [1].', CHUNKI)['cytaty']
    assert [c['n'] for c in cytaty] == [2, 1]


def test_numer_spoza_okna_nie_dodaje_zrodla():
    assert verify_answer('Zrob X [9].', CHUNKI)['cytaty'] == []


def test_ten_sam_numer_dwa_razy_daje_jedno_zrodlo():
    cytaty = verify_answer('Zrob X [1], a potem znowu X [1].', CHUNKI)['cytaty']
    assert [c['n'] for c in cytaty] == [1]
