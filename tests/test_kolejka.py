import json
import re
from collections import OrderedDict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

import api
import kolejka


@pytest.fixture(autouse=True)
def kolejka_w_tmp(monkeypatch, tmp_path):
    plik = tmp_path / 'kolejka_test.jsonl'
    monkeypatch.setattr(kolejka, 'PLIK_KOLEJKI', plik)
    monkeypatch.setattr(kolejka, '_cache_kolejki', {'stempel': None, 'wiersze': []})
    return plik


def zapisz_linie(plik, wiersze):
    with open(plik, 'w', encoding='utf-8') as w:
        for x in wiersze:
            if isinstance(x, str):
                w.write(x + '\n')
            else:
                w.write(json.dumps(x, ensure_ascii=False) + '\n')


def zgloszenie(ident, czas='2026-08-27T10:00:00+00:00', **nad):
    wiersz = {
        'czas': czas, 'typ': 'zgloszenie', 'zgloszenie': ident,
        'id_zapytania': 'c43ecf3bdcc4f7ab', 'lang': 'pl', 'strona': 'kupujacy',
        'sekcja': 'kupujacy', 'powod': 'sedzia', 'pytanie': 'jak zlozyc polecenie zaplaty',
        'email': 'jan@example.com',
    }
    wiersz.update(nad)
    return wiersz


def decyzja(ident, status='odpowiedziano', czas='2026-08-27T11:30:00+00:00', **nad):
    wiersz = {
        'czas': czas, 'typ': 'decyzja', 'zgloszenie': ident, 'status': status,
        'etykieta': 'luka_w_bazie', 'tresc': 'Polecenie zaplaty zakladasz w ...',
        'ticket': 'A1B2C3D4',
    }
    wiersz.update(nad)
    return wiersz


def test_plik_nie_istnieje(kolejka_w_tmp):
    assert kolejka.stan_kolejki() == []
    assert kolejka.zgloszenie_po_id('9F3A2B1C') is None


def test_plik_pusty(kolejka_w_tmp):
    kolejka_w_tmp.write_text('', encoding='utf-8')
    assert kolejka.stan_kolejki() == []


def test_uszkodzony_wiersz_w_srodku_nie_wywala(kolejka_w_tmp):
    zapisz_linie(kolejka_w_tmp, [
        zgloszenie('AAAAAAAA'),
        '{ to nie jest json',
        zgloszenie('BBBBBBBB'),
    ])
    identy = {z['zgloszenie'] for z in kolejka.stan_kolejki()}
    assert identy == {'AAAAAAAA', 'BBBBBBBB'}


def test_decyzja_bez_zgloszenia_ignorowana(kolejka_w_tmp):
    zapisz_linie(kolejka_w_tmp, [decyzja('WIDMO0000')])
    assert kolejka.stan_kolejki() == []
    assert kolejka.zgloszenie_po_id('WIDMO0000') is None


def test_dwie_decyzje_liczy_sie_pozniejsza_wg_kolejnosci_w_pliku(kolejka_w_tmp):
    zapisz_linie(kolejka_w_tmp, [
        zgloszenie('CCCCCCCC'),
        decyzja('CCCCCCCC', status='odrzucone', czas='2026-08-27T20:00:00+00:00'),
        decyzja('CCCCCCCC', status='odpowiedziano', czas='2026-08-27T09:00:00+00:00'),
    ])
    stan = kolejka.zgloszenie_po_id('CCCCCCCC')
    assert stan['status'] == 'odpowiedziano'


def test_swieze_zgloszenie_ma_status_nowe(kolejka_w_tmp):
    zapisz_linie(kolejka_w_tmp, [zgloszenie('DDDDDDDD')])
    assert kolejka.zgloszenie_po_id('DDDDDDDD')['status'] == 'nowe'


def test_po_decyzji_znika_z_filtra_nowe(kolejka_w_tmp):
    zapisz_linie(kolejka_w_tmp, [
        zgloszenie('EEEEEEEE'),
        zgloszenie('FFFFFFFF'),
        decyzja('EEEEEEEE', status='odpowiedziano'),
    ])
    nowe = {z['zgloszenie'] for z in kolejka.stan_kolejki(status='nowe')}
    assert nowe == {'FFFFFFFF'}


def test_filtr_dni_odcina_po_czasie_zgloszenia_nie_decyzji(kolejka_w_tmp):
    stare = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    swieze = datetime.now(timezone.utc).isoformat()
    zapisz_linie(kolejka_w_tmp, [
        zgloszenie('11111111', czas=stare),
        decyzja('11111111', status='odpowiedziano', czas=swieze),
    ])
    assert kolejka.stan_kolejki(dni=3) == []
    assert len(kolejka.stan_kolejki(dni=30)) == 1


def test_stan_kolejki_od_najnowszego(kolejka_w_tmp):
    zapisz_linie(kolejka_w_tmp, [
        zgloszenie('22222222', czas='2026-08-20T10:00:00+00:00'),
        zgloszenie('33333333', czas='2026-08-25T10:00:00+00:00'),
        zgloszenie('44444444', czas='2026-08-22T10:00:00+00:00'),
    ])
    kolejnosc = [z['zgloszenie'] for z in kolejka.stan_kolejki()]
    assert kolejnosc == ['33333333', '44444444', '22222222']


def test_zapisz_zgloszenie_zwraca_dwanascie_znakow_hex(kolejka_w_tmp):
    ident = kolejka.zapisz_zgloszenie('c43ecf3bdcc4f7ab', 'pl', 'kupujacy', 'kupujacy',
                                      'sedzia', 'jak zlozyc polecenie zaplaty', 'jan@example.com')
    assert len(ident) == 12
    assert all(z in '0123456789ABCDEF' for z in ident)
    stan = kolejka.zgloszenie_po_id(ident)
    assert stan['status'] == 'nowe'
    assert stan['pytanie'] == 'jak zlozyc polecenie zaplaty'
    assert stan['email'] == 'jan@example.com'


def test_zapisz_decyzje_domyka_zgloszenie(kolejka_w_tmp):
    ident = kolejka.zapisz_zgloszenie('c43ecf3bdcc4f7ab', 'pl', 'kupujacy', 'kupujacy',
                                      'pokrycie', 'pytanie testowe', 'jan@example.com')
    kolejka.zapisz_decyzje(ident, 'odrzucone', 'spam', '', None)
    stan = kolejka.zgloszenie_po_id(ident)
    assert stan['status'] == 'odrzucone'
    assert stan['etykieta'] == 'spam'
    assert kolejka.stan_kolejki(status='nowe') == []


ID_LOGU = 'c43ecf3bdcc4f7ab'


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(api, 'LOG_ANALYTICS', tmp_path / 'log_analytics_test.jsonl')
    monkeypatch.setattr(api, '_log_cache', {'stempel': None, 'wpisy': [], 'czas': 0.0})
    monkeypatch.setattr(api, '_zgloszenia', deque())
    monkeypatch.setattr(api, '_zgloszenia_ip', OrderedDict())
    monkeypatch.setattr(api, '_oceny_ip', OrderedDict())
    monkeypatch.setattr(api, 'LIMIT_ZGLOSZEN_MIN', 100)
    monkeypatch.setattr(api, 'LIMIT_ZGLOSZEN_DZIEN', 1000)
    monkeypatch.setattr(api, 'LIMIT_ZGLOSZEN_IP_MIN', 100)
    monkeypatch.setattr(api, 'LIMIT_ZGLOSZEN_IP_DZIEN', 1000)
    monkeypatch.setattr(api, '_admin_ip', OrderedDict())
    return TestClient(api.app)


def wpis_logu(sciezka, ident=ID_LOGU, powod='sedzia', **nad):
    rekord = {
        'czas': '2026-08-23T16:03:56.504779+00:00', 'id': ident, 'lang': 'pl',
        'strona': 'kupujacy', 'sekcja': 'kupujacy', 'wynik': 'odmowa', 'powod': powod,
        'pytanie': 'jak zlozyc nowe polecenie zaplaty',
    }
    rekord.update(nad)
    with open(sciezka, 'a', encoding='utf-8') as w:
        w.write(json.dumps(rekord, ensure_ascii=False) + '\n')


def cialo(**nad):
    dane = {'id_zapytania': ID_LOGU, 'email': 'jan@example.com', 'lang': 'pl', 'strona': 'kupujacy'}
    dane.update(nad)
    return dane


@pytest.mark.parametrize('powod', list(kolejka.POWODY_DO_CZLOWIEKA))
def test_zgloszenie_powod_kwalifikujacy_zwraca_identyfikator(client, powod):
    wpis_logu(api.LOG_ANALYTICS, powod=powod)
    odp = client.post('/zgloszenie', json=cialo())
    assert odp.status_code == 200
    dane = odp.json()
    assert dane.keys() == {'zgloszenie'}
    ident = dane['zgloszenie']
    assert len(ident) == 12
    assert all(z in '0123456789ABCDEF' for z in ident)
    assert kolejka.zgloszenie_po_id(ident)['status'] == 'nowe'


@pytest.mark.parametrize('powod', [
    'guard_dlugosc', 'nie_zrozumialem', 'mail_doprecyzuj', 'pytanie_o_strone',
    'odpowiedz', 'rozmowa', 'ogolna',
])
def test_zgloszenie_powod_odrzucajacy_nie_daje_200(client, powod):
    wpis_logu(api.LOG_ANALYTICS, powod=powod)
    odp = client.post('/zgloszenie', json=cialo())
    assert odp.status_code == 422
    assert kolejka.stan_kolejki() == []


def test_zgloszenie_powod_null_nie_daje_200(client):
    wpis_logu(api.LOG_ANALYTICS, powod=None)
    odp = client.post('/zgloszenie', json=cialo())
    assert odp.status_code == 422
    assert kolejka.stan_kolejki() == []


def test_zgloszenie_nieznane_id_daje_404(client):
    wpis_logu(api.LOG_ANALYTICS, ident='ffffffffffffffff', powod='sedzia')
    odp = client.post('/zgloszenie', json=cialo(id_zapytania='0000000000000000'))
    assert odp.status_code == 404


def test_zgloszenie_drugie_do_tego_samego_id_daje_409(client):
    wpis_logu(api.LOG_ANALYTICS, powod='sedzia')
    assert client.post('/zgloszenie', json=cialo()).status_code == 200
    odp = client.post('/zgloszenie', json=cialo())
    assert odp.status_code == 409


def test_zgloszenie_pytanie_z_logu_nie_z_ciala(client):
    wpis_logu(api.LOG_ANALYTICS, powod='sedzia')
    odp = client.post('/zgloszenie', json=cialo(pytanie='PODMIENIONA TRESC OD KLIENTA'))
    assert odp.status_code == 200
    ident = odp.json()['zgloszenie']
    stan = kolejka.zgloszenie_po_id(ident)
    assert stan['pytanie'] == 'jak zlozyc nowe polecenie zaplaty'
    tekst_pliku = kolejka.PLIK_KOLEJKI.read_text(encoding='utf-8')
    assert 'PODMIENIONA TRESC OD KLIENTA' not in tekst_pliku


def test_zgloszenie_zly_email_daje_422(client):
    wpis_logu(api.LOG_ANALYTICS, powod='sedzia')
    odp = client.post('/zgloszenie', json=cialo(email='to-nie-jest-email'))
    assert odp.status_code == 422


def test_zgloszenie_id_spoza_wzorca_daje_422(client):
    wpis_logu(api.LOG_ANALYTICS, powod='sedzia')
    odp = client.post('/zgloszenie', json=cialo(id_zapytania='ZZZZ'))
    assert odp.status_code == 422


def test_zgloszenie_niepoprawne_zadania_nie_zuzywaja_limitu_ip(client, monkeypatch):
    monkeypatch.setattr(api, 'LIMIT_ZGLOSZEN_IP_MIN', 2)
    monkeypatch.setattr(api, 'LIMIT_ZGLOSZEN_IP_DZIEN', 5)
    wpis_logu(api.LOG_ANALYTICS, powod='sedzia')
    for _ in range(5):
        odp = client.post('/zgloszenie', json=cialo(email='to-nie-jest-email'))
        assert odp.status_code == 422
    odp = client.post('/zgloszenie', json=cialo())
    assert odp.status_code == 200


def test_zgloszenie_blad_zapisu_daje_503_i_nie_zwraca_numeru(client, monkeypatch):
    monkeypatch.setattr(api, 'OSTRZEZONO_O_KOLEJCE', False)
    wpis_logu(api.LOG_ANALYTICS, powod='sedzia')

    def rzuca(*a, **k):
        raise OSError('dysk pelny')

    monkeypatch.setattr(kolejka, 'dopisz_wiersz', rzuca)
    odp = client.post('/zgloszenie', json=cialo())
    assert odp.status_code == 503
    assert kolejka.stan_kolejki() == []


def test_kolejka_lista_bez_tokenu_daje_401(client, monkeypatch):
    monkeypatch.setattr(api, 'ADMIN_TOKEN', 'tajne')
    assert client.get('/admin/kolejka').status_code == 401


def test_kolejka_lista_bez_admin_token_w_srodowisku_daje_503(client, monkeypatch):
    monkeypatch.setattr(api, 'ADMIN_TOKEN', '')
    odp = client.get('/admin/kolejka', headers={'x-admin-token': 'cokolwiek'})
    assert odp.status_code == 503


def test_kolejka_lista_z_tokenem_zwraca_zgloszenia_i_slad(client, kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(api, 'ADMIN_TOKEN', 'tajne')
    wpis_logu(api.LOG_ANALYTICS, powod='sedzia',
              cechy={'rerank_top1': 1.23, 'pokrycie': 0.4})
    zapisz_linie(kolejka_w_tmp, [zgloszenie('AAAAAAAA')])
    odp = client.get('/admin/kolejka', headers={'x-admin-token': 'tajne'})
    assert odp.status_code == 200
    dane = odp.json()
    assert dane['otwarte'] == 1
    z = dane['zgloszenia'][0]
    assert z['pytanie'] == 'jak zlozyc polecenie zaplaty'
    assert z['powod'] == 'sedzia'
    assert z['diagnoza'] == 'sedzia'
    assert z['cechy']['rerank_top1'] == 1.23


def test_kolejka_otwarte_respektuje_filtr_dni(client, kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(api, 'ADMIN_TOKEN', 'tajne')
    stare = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    swieze = datetime.now(timezone.utc).isoformat()
    zapisz_linie(kolejka_w_tmp, [
        zgloszenie('AAAAAAAA', czas=stare),
        zgloszenie('BBBBBBBB', czas=swieze),
    ])
    odp = client.get('/admin/kolejka', headers={'x-admin-token': 'tajne'}, params={'dni': 30})
    assert odp.status_code == 200
    dane = odp.json()
    assert dane['razem'] == 1
    assert dane['otwarte'] == 1


def test_kolejka_odpowiedz_nieznane_zgloszenie_daje_404(client, monkeypatch):
    monkeypatch.setattr(api, 'ADMIN_TOKEN', 'tajne')
    odp = client.post('/admin/kolejka/odpowiedz', headers={'x-admin-token': 'tajne'},
                      json={'zgloszenie': 'DEADBEEF', 'status': 'odrzucone'})
    assert odp.status_code == 404


def test_kolejka_odpowiedz_powtorna_decyzja_daje_409(client, kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(api, 'ADMIN_TOKEN', 'tajne')
    monkeypatch.setattr(api, 'wyslij_odpowiedz_operatora', lambda *a, **k: 'TICKET01')
    zapisz_linie(kolejka_w_tmp, [zgloszenie('AAAAAAAA'), decyzja('AAAAAAAA', status='odrzucone')])
    odp = client.post('/admin/kolejka/odpowiedz', headers={'x-admin-token': 'tajne'},
                      json={'zgloszenie': 'AAAAAAAA', 'status': 'odrzucone'})
    assert odp.status_code == 409


def test_kolejka_odpowiedz_pusta_tresc_przy_odpowiedziano_daje_422(client, kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(api, 'ADMIN_TOKEN', 'tajne')
    zapisz_linie(kolejka_w_tmp, [zgloszenie('AAAAAAAA')])
    odp = client.post('/admin/kolejka/odpowiedz', headers={'x-admin-token': 'tajne'},
                      json={'zgloszenie': 'AAAAAAAA', 'status': 'odpowiedziano', 'tresc': '   '})
    assert odp.status_code == 422
    assert kolejka.zgloszenie_po_id('AAAAAAAA')['status'] == 'nowe'


def test_kolejka_odpowiedz_blad_wysylki_nie_zapisuje_decyzji(client, kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(api, 'ADMIN_TOKEN', 'tajne')

    def rzuca(*a, **k):
        raise httpx.HTTPError('resend padl')

    monkeypatch.setattr(api, 'wyslij_odpowiedz_operatora', rzuca)
    zapisz_linie(kolejka_w_tmp, [zgloszenie('AAAAAAAA')])
    odp = client.post('/admin/kolejka/odpowiedz', headers={'x-admin-token': 'tajne'},
                      json={'zgloszenie': 'AAAAAAAA', 'status': 'odpowiedziano',
                            'tresc': 'odpowiedz operatora'})
    assert odp.status_code == 502
    assert kolejka.zgloszenie_po_id('AAAAAAAA')['status'] == 'nowe'
    wiersze = [json.loads(linia) for linia in kolejka_w_tmp.read_text(encoding='utf-8').splitlines() if linia.strip()]
    assert all(w.get('typ') != 'decyzja' for w in wiersze)


def test_kolejka_odpowiedz_wysyla_maila_i_domyka_zgloszenie(client, kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(api, 'ADMIN_TOKEN', 'tajne')
    przekazane = {}

    def falszywa(email, pytanie, odpowiedz, zgl, lang='pl'):
        przekazane.update(email=email, pytanie=pytanie, odpowiedz=odpowiedz, zgl=zgl, lang=lang)
        return 'TICKET01'

    monkeypatch.setattr(api, 'wyslij_odpowiedz_operatora', falszywa)
    zapisz_linie(kolejka_w_tmp, [zgloszenie('AAAAAAAA')])
    odp = client.post('/admin/kolejka/odpowiedz', headers={'x-admin-token': 'tajne'},
                      json={'zgloszenie': 'AAAAAAAA', 'status': 'odpowiedziano',
                            'etykieta': 'luka_w_bazie', 'tresc': 'Polecenie zaplaty zakladasz w ...'})
    assert odp.status_code == 200
    assert odp.json()['ticket'] == 'TICKET01'
    assert przekazane['email'] == 'jan@example.com'
    assert przekazane['zgl'] == 'AAAAAAAA'
    stan = kolejka.zgloszenie_po_id('AAAAAAAA')
    assert stan['status'] == 'odpowiedziano'
    assert stan['etykieta'] == 'luka_w_bazie'
    assert stan['ticket'] == 'TICKET01'


def test_kolejka_odpowiedz_blad_zapisu_decyzji_po_wyslanym_mailu(client, kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(api, 'ADMIN_TOKEN', 'tajne')
    monkeypatch.setattr(api, 'wyslij_odpowiedz_operatora', lambda *a, **k: 'TICKET02')
    zapisz_linie(kolejka_w_tmp, [zgloszenie('AAAAAAAA')])

    def rzuca(*a, **k):
        raise OSError('dysk pelny')

    monkeypatch.setattr(kolejka, 'dopisz_wiersz', rzuca)
    odp = client.post('/admin/kolejka/odpowiedz', headers={'x-admin-token': 'tajne'},
                      json={'zgloszenie': 'AAAAAAAA', 'status': 'odpowiedziano',
                            'tresc': 'odpowiedz operatora'})
    assert odp.status_code == 500
    assert kolejka.zgloszenie_po_id('AAAAAAAA')['status'] == 'nowe'


def test_kolejka_odrzucenie_nie_wysyla_maila(client, kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(api, 'ADMIN_TOKEN', 'tajne')

    def rzuca(*a, **k):
        raise AssertionError('odrzucenie nie moze wysylac maila')

    monkeypatch.setattr(api, 'wyslij_odpowiedz_operatora', rzuca)
    zapisz_linie(kolejka_w_tmp, [zgloszenie('AAAAAAAA')])
    odp = client.post('/admin/kolejka/odpowiedz', headers={'x-admin-token': 'tajne'},
                      json={'zgloszenie': 'AAAAAAAA', 'status': 'odrzucone',
                            'etykieta': 'spam', 'tresc': 'powod odrzucenia'})
    assert odp.status_code == 200
    stan = kolejka.zgloszenie_po_id('AAAAAAAA')
    assert stan['status'] == 'odrzucone'
    assert stan['ticket'] is None


def test_kolejka_eksport_bez_adresu_email(client, kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(api, 'ADMIN_TOKEN', 'tajne')
    zapisz_linie(kolejka_w_tmp, [
        zgloszenie('AAAAAAAA', email='jan.kowalski@example.com'),
        decyzja('AAAAAAAA', status='odpowiedziano', tresc='Polecenie zaplaty zakladasz w ustawieniach.'),
    ])
    odp = client.get('/admin/kolejka/eksport', headers={'x-admin-token': 'tajne'})
    assert odp.status_code == 200
    tekst = odp.content.decode('utf-8-sig')
    assert '@' not in tekst
    assert 'jan.kowalski' not in tekst
    assert 'Polecenie zaplaty zakladasz' in tekst


def test_kolejka_eksport_wymaga_tokenu(client, monkeypatch):
    monkeypatch.setattr(api, 'ADMIN_TOKEN', 'tajne')
    assert client.get('/admin/kolejka/eksport').status_code == 401


def test_czyszczenie_zgloszenie_z_decyzja_traci_adres_zachowuje_reszte(kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(kolejka, 'DNI_RETENCJI_EMAIL', 30)
    zapisz_linie(kolejka_w_tmp, [
        zgloszenie('AAAAAAAA'),
        decyzja('AAAAAAAA', status='odpowiedziano'),
    ])
    wyczyszczone = kolejka.wyczysc_przeterminowane_adresy()
    assert wyczyszczone == 1
    stan = kolejka.zgloszenie_po_id('AAAAAAAA')
    assert stan['email'] is None
    assert stan['pytanie'] == 'jak zlozyc polecenie zaplaty'
    assert stan['powod'] == 'sedzia'
    assert stan['status'] == 'odpowiedziano'


def test_czyszczenie_bez_decyzji_mlodsze_niz_limit_zachowuje_adres(kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(kolejka, 'DNI_RETENCJI_EMAIL', 5)
    swieze = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    zapisz_linie(kolejka_w_tmp, [zgloszenie('BBBBBBBB', czas=swieze)])
    wyczyszczone = kolejka.wyczysc_przeterminowane_adresy()
    assert wyczyszczone == 0
    assert kolejka.zgloszenie_po_id('BBBBBBBB')['email'] == 'jan@example.com'


def test_czyszczenie_bez_decyzji_starsze_niz_limit_traci_adres(kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(kolejka, 'DNI_RETENCJI_EMAIL', 5)
    stare = (datetime.now(timezone.utc) - timedelta(days=6)).isoformat()
    zapisz_linie(kolejka_w_tmp, [zgloszenie('CCCCCCCC', czas=stare)])
    wyczyszczone = kolejka.wyczysc_przeterminowane_adresy()
    assert wyczyszczone == 1
    stan = kolejka.zgloszenie_po_id('CCCCCCCC')
    assert stan['email'] is None
    assert stan['status'] == 'nowe'


def test_czyszczenie_nie_gubi_wierszy_ani_decyzji(kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(kolejka, 'DNI_RETENCJI_EMAIL', 30)
    stare = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    zapisz_linie(kolejka_w_tmp, [
        zgloszenie('DDDDDDDD', czas=stare),
        zgloszenie('EEEEEEEE'),
        decyzja('EEEEEEEE', status='odrzucone'),
        zgloszenie('FFFFFFFF'),
    ])
    przed = kolejka.stan_kolejki()
    statusy_przed = sorted((z['zgloszenie'], z['status']) for z in przed)
    liczba_wierszy_przed = len(kolejka_w_tmp.read_text(encoding='utf-8').splitlines())
    kolejka.wyczysc_przeterminowane_adresy()
    po = kolejka.stan_kolejki()
    statusy_po = sorted((z['zgloszenie'], z['status']) for z in po)
    liczba_wierszy_po = len(kolejka_w_tmp.read_text(encoding='utf-8').splitlines())
    assert statusy_przed == statusy_po
    assert liczba_wierszy_przed == liczba_wierszy_po


def test_czyszczenie_uszkodzony_wiersz_przetrwa(kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(kolejka, 'DNI_RETENCJI_EMAIL', 30)
    stare = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    zapisz_linie(kolejka_w_tmp, [
        zgloszenie('GGGGGGGG', czas=stare),
        '{ to nie jest json',
        zgloszenie('HHHHHHHH'),
    ])
    wyczyszczone = kolejka.wyczysc_przeterminowane_adresy()
    assert wyczyszczone == 1
    tekst = kolejka_w_tmp.read_text(encoding='utf-8')
    assert '{ to nie jest json' in tekst
    identy = {z['zgloszenie'] for z in kolejka.stan_kolejki()}
    assert identy == {'GGGGGGGG', 'HHHHHHHH'}


def test_kolejka_odpowiedz_bez_adresu_daje_409_i_nie_wysyla_maila(client, kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(api, 'ADMIN_TOKEN', 'tajne')

    def rzuca(*a, **k):
        raise AssertionError('adres wygasl, nie wolno wysylac maila')

    monkeypatch.setattr(api, 'wyslij_odpowiedz_operatora', rzuca)
    zapisz_linie(kolejka_w_tmp, [zgloszenie('AAAAAAAA', email=None)])
    odp = client.post('/admin/kolejka/odpowiedz', headers={'x-admin-token': 'tajne'},
                      json={'zgloszenie': 'AAAAAAAA', 'status': 'odpowiedziano', 'tresc': 'odpowiedz operatora'})
    assert odp.status_code == 409
    assert kolejka.zgloszenie_po_id('AAAAAAAA')['status'] == 'nowe'


def test_kolejka_odrzucenie_bez_adresu_daje_200(client, kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(api, 'ADMIN_TOKEN', 'tajne')
    zapisz_linie(kolejka_w_tmp, [zgloszenie('AAAAAAAA', email=None)])
    odp = client.post('/admin/kolejka/odpowiedz', headers={'x-admin-token': 'tajne'},
                      json={'zgloszenie': 'AAAAAAAA', 'status': 'odrzucone',
                            'etykieta': 'spam', 'tresc': 'powod odrzucenia'})
    assert odp.status_code == 200
    stan = kolejka.zgloszenie_po_id('AAAAAAAA')
    assert stan['status'] == 'odrzucone'
    assert stan['email'] is None


def test_kolejka_odpowiedz_czysci_adres_z_pliku(client, kolejka_w_tmp, monkeypatch):
    monkeypatch.setattr(api, 'ADMIN_TOKEN', 'tajne')
    monkeypatch.setattr(api, 'wyslij_odpowiedz_operatora', lambda *a, **k: 'TICKET09')
    zapisz_linie(kolejka_w_tmp, [zgloszenie('AAAAAAAA', email='jan.retencja@example.com')])
    odp = client.post('/admin/kolejka/odpowiedz', headers={'x-admin-token': 'tajne'},
                      json={'zgloszenie': 'AAAAAAAA', 'status': 'odpowiedziano',
                            'tresc': 'odpowiedz operatora'})
    assert odp.status_code == 200
    tekst = kolejka_w_tmp.read_text(encoding='utf-8')
    assert 'jan.retencja@example.com' not in tekst


def test_lista_powodow_front_zgodna_z_backendem():
    plik_ts = Path(__file__).resolve().parents[1] / 'frontend-next' / 'lib' / 'chat.ts'
    tekst = plik_ts.read_text(encoding='utf-8')
    dopasowanie = re.search(r'POWODY_DO_CZLOWIEKA\s*=\s*\[(.*?)\]', tekst, re.S)
    assert dopasowanie, 'nie znaleziono literalnej listy POWODY_DO_CZLOWIEKA w chat.ts'
    powody_front = set(re.findall(r"'([^']+)'", dopasowanie.group(1)))
    assert powody_front == set(kolejka.POWODY_DO_CZLOWIEKA)


@pytest.mark.parametrize('ident,oczekiwane', [
    ('A1B2C3D4', True),
    ('A1B2C3D4E5F6', True),
    ('A1B2C3D4E', False),
    ('a1b2c3d4', False),
])
def test_model_odpowiedzi_kolejki_przyjmuje_obie_dlugosci(ident, oczekiwane):
    if oczekiwane:
        model = api.OdpowiedzKolejkiZadanie(zgloszenie=ident, status='odpowiedziano')
        assert model.zgloszenie == ident
    else:
        with pytest.raises(Exception):
            api.OdpowiedzKolejkiZadanie(zgloszenie=ident, status='odpowiedziano')


def test_zapisz_zgloszenie_przy_kolizji_identyfikatora_nie_nadpisuje_pierwszego(monkeypatch, kolejka_w_tmp):
    stale = ['AAAAAAAAAAAA', 'AAAAAAAAAAAA', 'BBBBBBBBBBBB']
    monkeypatch.setattr(kolejka, 'nowy_identyfikator', lambda: stale.pop(0))

    pierwszy = kolejka.zapisz_zgloszenie('c43ecf3bdcc4f7ab', 'pl', 'kupujacy', 'kupujacy',
                                         'sedzia', 'pierwsze pytanie', 'jan@example.com')
    drugi = kolejka.zapisz_zgloszenie('9999999999999999', 'pl', 'kupujacy', 'kupujacy',
                                      'sedzia', 'drugie pytanie', 'ola@example.com')

    assert pierwszy == 'AAAAAAAAAAAA'
    assert drugi != pierwszy

    stan = kolejka.zloz_stan()
    assert stan[pierwszy]['pytanie'] == 'pierwsze pytanie'
    assert stan[pierwszy]['email'] == 'jan@example.com'
    assert stan[drugi]['pytanie'] == 'drugie pytanie'
