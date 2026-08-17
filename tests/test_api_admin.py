import csv
import io
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
    monkeypatch.setattr(api, '_statystyki_cache', {'stempel': None, 'czas': 0.0, 'wyniki': {}})
    monkeypatch.setattr(api, '_oceny_ip', OrderedDict())
    monkeypatch.setattr(api, '_admin_ip', OrderedDict())


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


def test_chat_wpis_ma_pola_kosztu(client, monkeypatch):
    monkeypatch.setattr(api, 'run', lambda *a, **kw: {'agent': 'konto', 'answer': 'x',
                                                       'sources': [], 'citations': []})
    odp = client.post('/chat', json={'message': 'jak zmienic haslo'})
    assert odp.status_code == 200
    wpis = wczytaj_log(api.LOG_ANALYTICS)[-1]
    assert {'tokeny_we', 'tokeny_wy', 'koszt_usd', 'tokeny_szacowane'} <= wpis.keys()


def test_chat_bez_doliczenia_daje_zera(client, monkeypatch):
    monkeypatch.setattr(api, 'run', lambda *a, **kw: {'agent': 'konto', 'answer': 'x',
                                                       'sources': [], 'citations': []})
    odp = client.post('/chat', json={'message': 'jak zmienic haslo'})
    assert odp.status_code == 200
    wpis = wczytaj_log(api.LOG_ANALYTICS)[-1]
    assert wpis['tokeny_we'] == 0
    assert wpis['tokeny_wy'] == 0
    assert wpis['koszt_usd'] == 0.0
    assert wpis['tokeny_szacowane'] is False


def test_chat_cache_hit_ma_zera_kosztu(client, monkeypatch):
    monkeypatch.setattr(api, 'run', lambda *a, **kw: {'agent': 'konto', 'answer': 'x',
                                                       'sources': [], 'citations': []})
    dane = {'message': 'jak zmienic haslo'}
    pierwszy = client.post('/chat', json=dane)
    assert pierwszy.status_code == 200
    drugi = client.post('/chat', json=dane)
    assert drugi.status_code == 200
    wpis = wczytaj_log(api.LOG_ANALYTICS)[-1]
    assert wpis['cache_hit'] is True
    assert wpis['tokeny_we'] == 0
    assert wpis['tokeny_wy'] == 0
    assert wpis['koszt_usd'] == 0.0
    assert wpis['tokeny_szacowane'] is False


def test_chat_doliczenie_trafia_do_wpisu(client, monkeypatch):
    monkeypatch.setattr(api, 'run', lambda *a, **kw: {'agent': 'konto', 'answer': 'x',
                                                       'sources': [], 'citations': []})
    monkeypatch.setattr(api.koszty, 'podsumowanie', lambda: {
        'tokeny_we': 120, 'tokeny_wy': 40, 'koszt_usd': 0.0012, 'wywolania': 2, 'szacowane': True,
    })
    odp = client.post('/chat', json={'message': 'jak zmienic haslo'})
    assert odp.status_code == 200
    wpis = wczytaj_log(api.LOG_ANALYTICS)[-1]
    assert wpis['tokeny_we'] == 120
    assert wpis['tokeny_wy'] == 40
    assert wpis['koszt_usd'] == 0.0012
    assert wpis['tokeny_szacowane'] is True


def test_statystyki_koszty_pokrycie(client):
    zapisz_log(api.LOG_ANALYTICS, [
        {'czas': '2026-08-01T10:00:00+00:00', 'lang': 'pl', 'sekcja': 'konto',
         'wynik': 'odpowiedz', 'latencja_s': 1.0, 'cache_hit': False, 'pytanie': 'a',
         'tokeny_we': 100, 'tokeny_wy': 50, 'koszt_usd': 0.001},
        {'czas': '2026-08-01T10:00:00+00:00', 'lang': 'pl', 'sekcja': 'konto',
         'wynik': 'odpowiedz', 'latencja_s': 1.0, 'cache_hit': False, 'pytanie': 'b',
         'tokeny_we': 200, 'tokeny_wy': 60, 'koszt_usd': 0.002},
        {'czas': '2026-08-01T10:00:00+00:00', 'lang': 'pl', 'sekcja': 'konto',
         'wynik': 'odpowiedz', 'latencja_s': 1.0, 'cache_hit': False, 'pytanie': 'c'},
    ])
    odp = client.get('/admin/statystyki')
    assert odp.json()['koszty']['pokrycie'] == 0.6667


def test_loguj_zapytanie_bez_parametru_zuzycie_dziala():
    api.loguj_zapytanie('pl', {'agent': '', 'tryb': 'rozmowa'}, 0.01, False, 'test', 'kupujacy')
    wpis = json.loads(api.LOG_ANALYTICS.read_text(encoding='utf-8').strip().splitlines()[-1])
    assert wpis['tokeny_we'] == 0
    assert wpis['tokeny_wy'] == 0
    assert wpis['koszt_usd'] == 0.0
    assert wpis['tokeny_szacowane'] is False


def test_eksport_neutralizuje_formule_rownosci(client):
    zapisz_log(api.LOG_ANALYTICS, [
        {'czas': '2026-08-01T10:00:00+00:00', 'lang': 'pl', 'sekcja': 'konto',
         'wynik': 'odpowiedz', 'latencja_s': 1.0, 'cache_hit': False,
         'pytanie': '=HYPERLINK("http://zle","klik")'},
    ])
    odp = client.get('/admin/eksport?format=csv&kolumny=pytanie')
    tresc = odp.content.decode('utf-8-sig')
    komorka = list(csv.reader(io.StringIO(tresc), delimiter=';'))[1][0]
    assert komorka.startswith("'=")


@pytest.mark.parametrize('znak', ['+', '-', '@'])
def test_eksport_neutralizuje_inne_znaki_formuly(client, znak):
    zapisz_log(api.LOG_ANALYTICS, [
        {'czas': '2026-08-01T10:00:00+00:00', 'lang': 'pl', 'sekcja': 'konto',
         'wynik': 'odpowiedz', 'latencja_s': 1.0, 'cache_hit': False,
         'pytanie': f'{znak}niebezpieczne'},
    ])
    odp = client.get('/admin/eksport?format=csv&kolumny=pytanie')
    tresc = odp.content.decode('utf-8-sig')
    komorka = list(csv.reader(io.StringIO(tresc), delimiter=';'))[1][0]
    assert komorka.startswith(f"'{znak}")


def test_eksport_zwykle_pytanie_bez_apostrofu(client):
    zapisz_log(api.LOG_ANALYTICS, [
        {'czas': '2026-08-01T10:00:00+00:00', 'lang': 'pl', 'sekcja': 'konto',
         'wynik': 'odpowiedz', 'latencja_s': 1.0, 'cache_hit': False,
         'pytanie': 'jak zmienic haslo'},
    ])
    odp = client.get('/admin/eksport?format=csv&kolumny=pytanie')
    tresc = odp.content.decode('utf-8-sig')
    komorka = list(csv.reader(io.StringIO(tresc), delimiter=';'))[1][0]
    assert komorka == 'jak zmienic haslo'


def test_ocena_limit_per_ip(client, monkeypatch):
    monkeypatch.setattr(api, 'LIMIT_OCEN_IP_MIN', 3)
    for _ in range(3):
        odp = client.post('/ocena', json={'ocena': 'gora', 'pytanie': 'test'},
                          headers={'x-forwarded-for': '1.1.1.1'})
        assert odp.status_code == 200
    odp = client.post('/ocena', json={'ocena': 'gora', 'pytanie': 'test'},
                      headers={'x-forwarded-for': '1.1.1.1'})
    assert odp.status_code == 429
    odp_inny = client.post('/ocena', json={'ocena': 'gora', 'pytanie': 'test'},
                           headers={'x-forwarded-for': '2.2.2.2'})
    assert odp_inny.status_code == 200


def test_admin_statystyki_limit_per_ip(client, monkeypatch):
    monkeypatch.setattr(api, 'LIMIT_ADMIN_IP_MIN', 3)
    for _ in range(3):
        odp = client.get('/admin/statystyki', headers={'x-forwarded-for': '3.3.3.3'})
        assert odp.status_code == 200
    odp = client.get('/admin/statystyki', headers={'x-forwarded-for': '3.3.3.3'})
    assert odp.status_code == 429


def test_admin_statystyki_cache_reaguje_na_zmiane_pliku(client):
    zapisz_log(api.LOG_ANALYTICS, [
        {'czas': '2026-08-01T10:00:00+00:00', 'lang': 'pl', 'sekcja': 'konto',
         'wynik': 'odpowiedz', 'latencja_s': 1.0, 'cache_hit': False, 'pytanie': 'a'},
    ])
    pierwszy = client.get('/admin/statystyki')
    drugi = client.get('/admin/statystyki')
    assert pierwszy.json() == drugi.json()

    zapisz_log(api.LOG_ANALYTICS, [
        {'czas': '2026-08-01T10:00:00+00:00', 'lang': 'pl', 'sekcja': 'konto',
         'wynik': 'odpowiedz', 'latencja_s': 1.0, 'cache_hit': False, 'pytanie': 'a'},
        {'czas': '2026-08-02T10:00:00+00:00', 'lang': 'pl', 'sekcja': 'konto',
         'wynik': 'odpowiedz', 'latencja_s': 1.0, 'cache_hit': False, 'pytanie': 'b'},
    ])
    trzeci = client.get('/admin/statystyki')
    assert trzeci.json() != pierwszy.json()


def test_statystyki_kolumny_zgadzaja_sie_z_kolumny_eksportu(client):
    odp = client.get('/admin/statystyki')
    dane = odp.json()
    assert 'kolumny' in dane
    assert set(dane['kolumny'].keys()) == {'wszystkie', 'domyslne'}
    assert tuple(dane['kolumny']['wszystkie']) == api.statystyki.KOLUMNY_EKSPORTU
