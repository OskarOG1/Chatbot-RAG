import json
from collections import OrderedDict, deque

import pytest
from fastapi.testclient import TestClient

import api
import pipeline

POWODY = (
    'prog_rerank', 'sedzia', 'brak_generacji', 'pokrycie', 'model_nie_wie',
    'nie_zrozumialem', 'mail_doprecyzuj',
    'guard_za_krotkie', 'guard_za_dlugie', 'guard_nie_rozumiem',
    'guard_zly_alfabet', 'guard_injekcja',
)


@pytest.fixture(autouse=True)
def reset_stan_api(monkeypatch, tmp_path):
    monkeypatch.setattr(api, '_zapytania', deque())
    monkeypatch.setattr(api, '_zapytania_ip', OrderedDict())
    monkeypatch.setattr(api, '_cache', OrderedDict())
    monkeypatch.setattr(api, 'LOG_ANALYTICS', tmp_path / 'log_analytics_test.jsonl')
    monkeypatch.setattr(pipeline, 'LOG_TRUDNE', tmp_path / 'trudne_test.jsonl')


@pytest.fixture
def client():
    return TestClient(api.app)


def parsuj_sse(tekst):
    zdarzenia = []
    for linia in tekst.splitlines():
        if linia.startswith('data: '):
            zdarzenia.append(json.loads(linia[len('data: '):]))
    return zdarzenia


# powod_wyniku


@pytest.mark.parametrize('powod', POWODY)
def test_powod_wyniku_dla_kazdej_wartosci_odmowy(powod):
    assert api.powod_wyniku({'agent': '', 'powod_odmowy': powod}) == powod


def test_powod_wyniku_pusty_slownik():
    assert api.powod_wyniku({}) == 'brak_wyniku'
    assert api.powod_wyniku(None) == 'brak_wyniku'


def test_powod_wyniku_z_agentem_to_odpowiedz():
    assert api.powod_wyniku({'agent': 'konto', 'answer': 'x'}) == 'odpowiedz'


def test_powod_wyniku_rozmowa_pin_n4():
    dane = {'agent': '', 'answer': 'Cześć', 'sources': [], 'citations': [],
            'doprecyzowanie': None, 'tryb': 'rozmowa'}
    assert api.powod_wyniku(dane) == 'rozmowa'


def test_loguj_zapytanie_zapisuje_wynik_rozmowa():
    api.loguj_zapytanie('pl', {'agent': '', 'tryb': 'rozmowa'}, 0.01, False, 'cześć', 'kupujacy')
    linie = api.LOG_ANALYTICS.read_text(encoding='utf-8').strip().splitlines()
    wpis = json.loads(linie[-1])
    assert wpis['wynik'] == 'rozmowa'
    assert wpis['powod'] == 'rozmowa'


def test_loguj_zapytanie_zapisuje_powod_etap2_i_bramki_pominiete():
    dane = {'agent': '', 'powod_odmowy': 'prog_rerank', 'powod_etap2': 'sedzia',
            'bramki_pominiete': ['pokrycie']}
    api.loguj_zapytanie('pl', dane, 0.01, False, 'jakies pytanie', 'kupujacy')
    wpis = json.loads(api.LOG_ANALYTICS.read_text(encoding='utf-8').strip().splitlines()[-1])
    assert wpis['powod_etap2'] == 'sedzia'
    assert wpis['bramki_pominiete'] == ['pokrycie']


# cache_klucz / cache_zdatny / cache_zapisz (N9)


def test_cache_klucz_rozroznia_strona():
    klucz_a = api.cache_klucz('pl', 'jak zmienic haslo', 'kupujacy')
    klucz_b = api.cache_klucz('pl', 'jak zmienic haslo', 'sprzedajacy')
    assert klucz_a != klucz_b


def test_cache_klucz_reaguje_na_corpus_stamp(monkeypatch):
    monkeypatch.setattr(api, 'corpus_stamp', lambda lang: 111)
    klucz_a = api.cache_klucz('pl', 'jak zmienic haslo', 'kupujacy')
    monkeypatch.setattr(api, 'corpus_stamp', lambda lang: 222)
    klucz_b = api.cache_klucz('pl', 'jak zmienic haslo', 'kupujacy')
    assert klucz_a != klucz_b


def test_cache_zdatny_prawda_dla_domyslnego_zadania():
    req = api.ChatRequest(message='jak zmienic haslo')
    assert api.cache_zdatny(req) is True


@pytest.mark.parametrize('pola', [
    {'history': [{'role': 'user', 'content': 'poprzednie pytanie'}]},
    {'agent_poprzedni': 'konto'},
    {'przepisz': True},
    {'bielik_model': 'jakis-model'},
    {'sedzia': False},
])
def test_cache_zdatny_falszywe_dla_kazdego_warunku(pola):
    req = api.ChatRequest(message='jak zmienic haslo', **pola)
    assert api.cache_zdatny(req) is False


def test_cache_zapisz_odrzuca_wynik_bez_agenta_n9():
    klucz = ('pl', 'test', 0, 'kupujacy')
    api.cache_zapisz(klucz, {'agent': '', 'answer': 'brak'})
    assert api.cache_pobierz(klucz) is None


def test_cache_zapisz_akceptuje_wynik_z_agentem():
    klucz = ('pl', 'test', 0, 'kupujacy')
    api.cache_zapisz(klucz, {'agent': 'konto', 'answer': 'tak'})
    assert api.cache_pobierz(klucz) == {'agent': 'konto', 'answer': 'tak'}


def test_cache_zapisz_akceptuje_odmowe_prog_rerank_o7():
    klucz = ('pl', 'test', 0, 'kupujacy')
    wynik = {'agent': '', 'powod_odmowy': 'prog_rerank'}
    api.cache_zapisz(klucz, wynik)
    assert api.cache_pobierz(klucz) == wynik


@pytest.mark.parametrize('powod', ['sedzia', 'pokrycie', 'model_nie_wie', 'brak_generacji'])
def test_cache_zapisz_odrzuca_odmowy_niedeterministyczne_o7(powod):
    klucz = ('pl', f'test-{powod}', 0, 'kupujacy')
    api.cache_zapisz(klucz, {'agent': '', 'powod_odmowy': powod})
    assert api.cache_pobierz(klucz) is None


# /chat/stream


def test_chat_stream_krok_przed_wynikiem_i_kroki_obu_etapow(monkeypatch, atrapa_pipeline, client):
    atrapa_pipeline.ustaw_etap('sprzedajacy', tekst='Odpowiedz z sekcji sprzedazy.')
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)

    odpowiedz = client.post('/chat/stream', json={
        'message': 'jakies pytanie o sprzedaz', 'lang': 'pl', 'strona': 'kupujacy',
        'bez_korekty': True, 'sedzia': False,
    })
    assert odpowiedz.status_code == 200

    zdarzenia = parsuj_sse(odpowiedz.text)
    typy = [z['typ'] for z in zdarzenia]
    assert typy[-1] == 'wynik'
    assert typy.count('wynik') == 1
    assert typy.index('krok') < typy.index('wynik')

    kroki = [z['tekst'] for z in zdarzenia if z['typ'] == 'krok']
    cfg = pipeline.LANG['pl']['kroki']
    nazwy = pipeline.LANG['pl']['nazwy_stron']
    oczekiwane_kupujacy = cfg['wybieram_strone'].format(strona=nazwy['kupujacy'])
    oczekiwane_sprzedajacy = cfg['wybieram_strone'].format(strona=nazwy['sprzedajacy'])
    assert oczekiwane_kupujacy in kroki
    assert oczekiwane_sprzedajacy in kroki
