from spell import detect_lang, correct, fold, distance, polish_word


def test_detect_lang_polski_z_ogonkami():
    assert detect_lang('jak zmienić hasło do konta') == 'pl'


def test_detect_lang_polski_bez_ogonkow():
    assert detect_lang('jak zmienic haslo do konta') == 'pl'


def test_detect_lang_angielski():
    assert detect_lang('how do i change my password') == 'en'


def test_detect_lang_za_krotkie():
    assert detect_lang('ab cd') is None


def test_detect_lang_bramka_krytyczna_polski_nigdy_en():
    zdania_pl = [
        'jak zmienić hasło do konta',
        'nie moge sie zalogowac na moje konto',
        'chce zwrocic kupiony produkt',
        'gdzie sledzic moja przesylke',
        'jak zaplacic blikiem za zakupy',
    ]
    for zdanie in zdania_pl:
        assert detect_lang(zdanie) != 'en', zdanie


def test_correct_znana_literowka():
    wynik = correct('jak usunąć kotno')
    assert wynik['zmieniono'] is True
    assert ('kotno', 'konto') in wynik['zmiany']
    assert 'konto' in wynik['poprawione']


def test_correct_nieznane_slowo():
    wynik = correct('xqzvtabc')
    assert wynik['zmieniono'] is False
    assert wynik['nieznane'] == ['xqzvtabc']


def test_correct_polish_word_passthrough():
    wynik = correct('mam dom')
    assert wynik == {
        'poprawione': 'mam dom',
        'zmieniono': False,
        'zmiany': [],
        'nieznane': [],
    }


def test_polish_word():
    assert polish_word('dom') is True
    assert polish_word('xqzvt') is False


def test_fold():
    assert fold('łąka ŁÓDŹ') == 'laka ŁODZ'


def test_distance_transpozycja():
    assert distance('kotno', 'konto') == 1


def test_distance_identyczne():
    assert distance('konto', 'konto') == 0


def test_correct_wiele_roznych_nieznanych_slow_wszystkie_w_nieznane():
    tokeny = [f'xqzvt{chr(97 + i // 26)}{chr(97 + i % 26)}' for i in range(30)]
    zapytanie = ' '.join(tokeny)
    wynik = correct(zapytanie)
    assert wynik['zmieniono'] is False
    assert len(wynik['nieznane']) == len(tokeny)
