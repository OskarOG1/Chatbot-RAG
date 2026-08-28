import json
import re
from collections import OrderedDict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

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


def test_zapisz_zgloszenie_zwraca_osiem_znakow_hex(kolejka_w_tmp):
    ident = kolejka.zapisz_zgloszenie('c43ecf3bdcc4f7ab', 'pl', 'kupujacy', 'kupujacy',
                                      'sedzia', 'jak zlozyc polecenie zaplaty', 'jan@example.com')
    assert len(ident) == 8
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
    ident = odp.json()
    assert len(ident) == 8
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
    ident = odp.json()
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


def test_lista_powodow_front_zgodna_z_backendem():
    plik_ts = Path(__file__).resolve().parents[1] / 'frontend-next' / 'lib' / 'chat.ts'
    tekst = plik_ts.read_text(encoding='utf-8')
    dopasowanie = re.search(r'POWODY_DO_CZLOWIEKA\s*=\s*\[(.*?)\]', tekst, re.S)
    assert dopasowanie, 'nie znaleziono literalnej listy POWODY_DO_CZLOWIEKA w chat.ts'
    powody_front = set(re.findall(r"'([^']+)'", dopasowanie.group(1)))
    assert powody_front == set(kolejka.POWODY_DO_CZLOWIEKA)
