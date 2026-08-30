import petla


def zgloszenie(ident, status='odpowiedziano', etykieta='luka_w_bazie', strona='kupujacy',
               id_zapytania=None, pytanie='Jak odzyskac konto?', tresc='Odpowiedz operatora.',
               lang='pl'):
    return {
        'zgloszenie': ident,
        'czas': '2026-08-01T10:00:00+00:00',
        'id_zapytania': id_zapytania if id_zapytania is not None else f'q-{ident}',
        'lang': lang,
        'strona': strona,
        'sekcja': None,
        'powod': 'sedzia',
        'pytanie': pytanie,
        'email': 'ktos@example.com',
        'status': status,
        'etykieta': etykieta,
        'tresc': tresc,
        'ticket': None,
        'decyzja_czas': '2026-08-02T09:00:00+00:00',
    }


def wpis_logu(ident, zrodlo_top1='https://allegro.pl/pomoc/artykul-1', rerank_top1=1.5,
              cechy=True):
    wpis = {'id': ident, 'pytanie': 'Jak odzyskac konto?', 'lang': 'pl',
            'strona': 'kupujacy', 'sekcja': None, 'powod': 'sedzia', 'wynik': 'odmowa'}
    if cechy:
        wpis['cechy'] = {'chunkow': 6, 'etap': 'sedzia', 'pokrycie': 0.3,
                         'rerank_top1': rerank_top1, 'sedzia_ok': False,
                         'zrodlo_top1': zrodlo_top1}
    return wpis


def test_odpowiedziano_bez_wpisu_w_logu_trafia_do_kosza_bez_logu():
    stan = {'AAA': zgloszenie('AAA')}
    wynik = petla.klasyfikuj(stan, [])

    assert wynik['do_przegladu'] == []
    assert [w['zgloszenie'] for w in wynik['bez_logu']] == ['AAA']
    assert wynik['podsumowanie']['bez_logu'] == 1
    assert wynik['bez_logu'][0]['propozycja_url'] is None
    assert wynik['bez_logu'][0]['rerank_top1'] is None


def test_log_bez_cech_daje_propozycje_url_none_a_nie_pusty_lancuch():
    stan = {'AAA': zgloszenie('AAA', id_zapytania='q1')}
    wynik = petla.klasyfikuj(stan, [wpis_logu('q1', cechy=False)])

    wiersz = wynik['do_przegladu'][0]
    assert wiersz['propozycja_url'] is None
    assert wiersz['rerank_top1'] is None


def test_cechy_bez_zrodlo_top1_daje_none():
    stan = {'AAA': zgloszenie('AAA', id_zapytania='q1')}
    log = [wpis_logu('q1', zrodlo_top1='', rerank_top1=None)]
    wynik = petla.klasyfikuj(stan, log)

    wiersz = wynik['do_przegladu'][0]
    assert wiersz['propozycja_url'] is None
    assert wiersz['rerank_top1'] is None


def test_pelny_wiersz_ma_wszystkie_pola_kontraktu_a_decyzja_i_url_sa_puste():
    stan = {'AAA': zgloszenie('AAA', strona='sprzedajacy', id_zapytania='q1')}
    wynik = petla.klasyfikuj(stan, [wpis_logu('q1')])

    wiersz = wynik['do_przegladu'][0]
    assert wiersz == {
        'zgloszenie': 'AAA',
        'pytanie': 'Jak odzyskac konto?',
        'lang': 'pl',
        'agent': 'sprzedaz',
        'etykieta': 'luka_w_bazie',
        'odpowiedz_operatora': 'Odpowiedz operatora.',
        'propozycja_url': 'https://allegro.pl/pomoc/artykul-1',
        'rerank_top1': 1.5,
        'decyzja': None,
        'url': None,
    }
    assert 'email' not in wiersz


def test_etykieta_none_idzie_do_kosza_decyzji_czlowieka_nie_do_pomijamy():
    stan = {'AAA': zgloszenie('AAA', etykieta=None, id_zapytania='q1')}
    wynik = petla.klasyfikuj(stan, [wpis_logu('q1')])

    assert wynik['podsumowanie']['wymaga_decyzji_czlowieka'] == 1
    assert wynik['podsumowanie']['etykiety_odpowiedziano'].get('brak_etykiety') == 1
    wiersz = wynik['do_przegladu'][0]
    assert wiersz['etykieta'] is None
    assert wiersz['decyzja'] is None


def test_strona_spoza_mapy_daje_jawny_sygnal_a_nie_cichy_kupujacy():
    stan = {'AAA': zgloszenie('AAA', strona='nieznana_strona', id_zapytania='q1')}
    wynik = petla.klasyfikuj(stan, [wpis_logu('q1')])

    wiersz = wynik['do_przegladu'][0]
    assert wiersz['agent'] is None
    assert wynik['podsumowanie']['strona_nieznana'] == 1
    assert wynik['strony_nieznane'] == [{'zgloszenie': 'AAA', 'strona': 'nieznana_strona'}]


def test_odrzucone_i_nowe_sa_liczone_ale_nie_wchodza_do_przegladu():
    stan = {
        'AAA': zgloszenie('AAA', id_zapytania='q1'),
        'BBB': zgloszenie('BBB', status='odrzucone', etykieta='spam'),
        'CCC': zgloszenie('CCC', status='nowe', etykieta=None),
    }
    wynik = petla.klasyfikuj(stan, [wpis_logu('q1')])

    assert [w['zgloszenie'] for w in wynik['do_przegladu']] == ['AAA']
    assert wynik['podsumowanie']['status'] == {
        'nowe': 1, 'odpowiedziano': 1, 'odrzucone': 1, 'inne': 0}
