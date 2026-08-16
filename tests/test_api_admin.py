import json
from collections import OrderedDict, deque

import pytest
from fastapi.testclient import TestClient

import api


@pytest.fixture(autouse=True)
def reset_stan_api(monkeypatch, tmp_path):
    monkeypatch.setattr(api, '_zapytania', deque())
    monkeypatch.setattr(api, '_zapytania_ip', OrderedDict())
    monkeypatch.setattr(api, '_cache', OrderedDict())
    monkeypatch.setattr(api, 'LOG_ANALYTICS', tmp_path / 'log_analytics_test.jsonl')
    monkeypatch.setattr(api, '_log_cache', {'stempel': None, 'wpisy': [], 'czas': 0.0})
    monkeypatch.setattr(api, 'STATYSTYKI_TTL', 0.0)


@pytest.fixture
def client():
    return TestClient(api.app)


def zapisz_log(sciezka, wpisy):
    with open(sciezka, 'w', encoding='utf-8') as w:
        for x in wpisy:
            w.write(json.dumps(x, ensure_ascii=False) + '\n')


def test_statystyki_pusty_log(client):
    odp = client.get('/admin/statystyki')
    assert odp.status_code == 200
    assert odp.json()['ogolem']['zapytan'] == 0


def test_statystyki_ma_wszystkie_klucze(client):
    odp = client.get('/admin/statystyki')
    dane = odp.json()
    klucze = {'zakres', 'ogolem', 'latencja', 'sekcje', 'strony', 'powody',
              'jezyki', 'dzienne', 'top_pytania', 'oceny', 'koszty'}
    assert klucze <= dane.keys()


def test_statystyki_niepoprawne_parametry(client):
    assert client.get('/admin/statystyki?dni=0').status_code == 422
    assert client.get('/admin/statystyki?lang=de').status_code == 422


def test_eksport_csv_naglowek_i_content_disposition(client):
    odp = client.get('/admin/eksport?format=csv&kolumny=czas,latencja_s')
    tresc = odp.content.decode('utf-8-sig')
    pierwszy_wiersz = tresc.splitlines()[0]
    assert pierwszy_wiersz == 'czas;latencja_s'
    assert 'attachment' in odp.headers['content-disposition']


def test_eksport_nieznana_kolumna_ignorowana_puste_daje_domyslne(client):
    odp = client.get('/admin/eksport?format=csv&kolumny=nieistniejaca')
    tresc = odp.content.decode('utf-8-sig')
    pierwszy_wiersz = tresc.splitlines()[0]
    assert pierwszy_wiersz == ';'.join(api.statystyki.KOLUMNY_DOMYSLNE)


def test_eksport_pomija_wysylki(client):
    zapisz_log(api.LOG_ANALYTICS, [
        {'czas': '2026-08-01T10:00:00+00:00', 'lang': 'pl', 'sekcja': 'konto',
         'wynik': 'odpowiedz', 'latencja_s': 1.0, 'cache_hit': False, 'pytanie': 'test'},
        {'typ': 'wysylka', 'czas': '2026-08-01T10:00:00+00:00', 'lang': 'pl',
         'kategoria': None, 'ticket': 'ABCD1234', 'sukces': True},
    ])
    odp = client.get('/admin/eksport?format=csv')
    tresc = odp.content.decode('utf-8-sig')
    wiersze = tresc.splitlines()
    assert len(wiersze) == 2


def test_log_dopisany_po_pierwszym_get_widoczny_w_drugim(client):
    zapisz_log(api.LOG_ANALYTICS, [
        {'czas': '2026-08-01T10:00:00+00:00', 'lang': 'pl', 'sekcja': 'konto',
         'wynik': 'odpowiedz', 'latencja_s': 1.0, 'cache_hit': False, 'pytanie': 'test'},
    ])
    pierwszy = client.get('/admin/statystyki')
    assert pierwszy.json()['ogolem']['zapytan'] == 1

    zapisz_log(api.LOG_ANALYTICS, [
        {'czas': '2026-08-01T10:00:00+00:00', 'lang': 'pl', 'sekcja': 'konto',
         'wynik': 'odpowiedz', 'latencja_s': 1.0, 'cache_hit': False, 'pytanie': 'test'},
        {'czas': '2026-08-02T10:00:00+00:00', 'lang': 'pl', 'sekcja': 'konto',
         'wynik': 'odpowiedz', 'latencja_s': 1.0, 'cache_hit': False, 'pytanie': 'test2'},
    ])
    drugi = client.get('/admin/statystyki')
    assert drugi.json()['ogolem']['zapytan'] == 2
