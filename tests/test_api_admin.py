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
    monkeypatch.setattr(api, '_oceny', deque())


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


def wczytaj_log(sciezka):
    with open(sciezka, encoding='utf-8') as p:
        return [json.loads(w) for w in p if w.strip()]


def test_ocena_zapisuje_wpis(client):
    odp = client.post('/ocena', json={
        'ocena': 'gora', 'pytanie': 'jak zmienic haslo', 'odpowiedz': 'kroki',
        'sekcja': 'konto', 'lang': 'pl', 'strona': 'kupujacy',
    })
    assert odp.status_code == 200
    wpisy = wczytaj_log(api.LOG_ANALYTICS)
    assert len(wpisy) == 1
    assert wpisy[0]['typ'] == 'ocena'


def test_ocena_redaguje_pytanie(client):
    odp = client.post('/ocena', json={
        'ocena': 'dol', 'pytanie': 'zadzwon pod 501234567', 'odpowiedz': 'x',
    })
    assert odp.status_code == 200
    wpisy = wczytaj_log(api.LOG_ANALYTICS)
    assert '[ukryte]' in wpisy[0]['pytanie']
    assert '501234567' not in wpisy[0]['pytanie']


def test_ocena_niepoprawna_wartosc(client):
    odp = client.post('/ocena', json={'ocena': 'moze', 'pytanie': 'test'})
    assert odp.status_code == 422


def test_ocena_puste_pytanie(client):
    odp = client.post('/ocena', json={'ocena': 'gora', 'pytanie': ''})
    assert odp.status_code == 422


def test_ocena_limit(client, monkeypatch):
    monkeypatch.setattr(api, 'LIMIT_OCEN_MIN', 2)
    for _ in range(2):
        assert client.post('/ocena', json={'ocena': 'gora', 'pytanie': 'test'}).status_code == 200
    odp = client.post('/ocena', json={'ocena': 'gora', 'pytanie': 'test'})
    assert odp.status_code == 429


def test_statystyki_blok_oceny(client):
    client.post('/ocena', json={'ocena': 'gora', 'pytanie': 'a'})
    client.post('/ocena', json={'ocena': 'gora', 'pytanie': 'b'})
    client.post('/ocena', json={'ocena': 'dol', 'pytanie': 'c'})
    odp = client.get('/admin/statystyki')
    dane = odp.json()
    assert dane['oceny'] == {'gora': 2, 'dol': 1, 'razem': 3, 'trafnosc': 0.6667, 'pokrycie': 0.0}
    assert dane['ogolem']['zapytan'] == 0


def test_eksport_pomija_oceny(client):
    zapisz_log(api.LOG_ANALYTICS, [
        {'czas': '2026-08-01T10:00:00+00:00', 'lang': 'pl', 'sekcja': 'konto',
         'wynik': 'odpowiedz', 'latencja_s': 1.0, 'cache_hit': False, 'pytanie': 'test'},
        {'typ': 'ocena', 'czas': '2026-08-01T10:00:00+00:00', 'ocena': 'gora', 'lang': 'pl',
         'strona': 'kupujacy', 'sekcja': 'konto', 'pytanie': 'test', 'odpowiedz': 'x'},
    ])
    odp = client.get('/admin/eksport?format=csv')
    tresc = odp.content.decode('utf-8-sig')
    wiersze = tresc.splitlines()
    assert len(wiersze) == 2
