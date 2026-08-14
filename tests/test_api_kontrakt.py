import json
import threading
from collections import OrderedDict, deque

import pytest
from fastapi.testclient import TestClient

import api
import pipeline

POWODY = (
    'prog_rerank', 'sedzia', 'brak_generacji', 'pokrycie', 'model_nie_wie',
    'jawna_odmowa', 'nie_zrozumialem', 'mail_doprecyzuj',
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
    monkeypatch.setattr(api, '_bramki_pominiete_historia', deque(maxlen=api.SYGNAL_POMINIETE_OKNO))
    monkeypatch.setattr(api, '_sygnal_bramki_pominiete_aktywny', False)


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
    {'bez_korekty': True},
])
def test_cache_zdatny_falszywe_dla_kazdego_warunku(pola):
    req = api.ChatRequest(message='jak zmienic haslo', **pola)
    assert api.cache_zdatny(req) is False


def test_cache_pobierz_trzyma_zamek_do_konca_wiec_rownolegly_zapis_czeka(monkeypatch):
    klucz = ('pl', 'test', 0, 'kupujacy')

    wszedl_do_srodka = threading.Event()
    moze_zwrocic = threading.Event()

    class Powolny(OrderedDict):
        def get(self, k, d=None):
            wynik = OrderedDict.get(self, k, d)
            wszedl_do_srodka.set()
            moze_zwrocic.wait(timeout=2)
            return wynik

    cache = Powolny()
    cache[klucz] = {'agent': 'konto', 'answer': 'a'}
    monkeypatch.setattr(api, '_cache', cache)

    wynik_pobierz = {}

    def watek_pobierz():
        wynik_pobierz['wynik'] = api.cache_pobierz(klucz)

    watek1 = threading.Thread(target=watek_pobierz)
    watek1.start()
    assert wszedl_do_srodka.wait(timeout=2)

    zapis_zakonczony = threading.Event()

    def watek_zapis():
        api.cache_zapisz(klucz, {'agent': 'konto', 'answer': 'b'})
        zapis_zakonczony.set()

    watek2 = threading.Thread(target=watek_zapis)
    watek2.start()

    zapis_gotowy_przedwczesnie = zapis_zakonczony.wait(timeout=0.2)
    moze_zwrocic.set()

    watek1.join(timeout=2)
    watek2.join(timeout=2)

    assert zapis_gotowy_przedwczesnie is False
    assert wynik_pobierz['wynik'] == {'agent': 'konto', 'answer': 'a'}
    assert cache[klucz]['answer'] == 'b'


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


@pytest.mark.parametrize('powod',
                         ['sedzia', 'pokrycie', 'model_nie_wie', 'jawna_odmowa', 'brak_generacji'])
def test_cache_zapisz_odrzuca_odmowy_niedeterministyczne_o7(powod):
    klucz = ('pl', f'test-{powod}', 0, 'kupujacy')
    api.cache_zapisz(klucz, {'agent': '', 'powod_odmowy': powod})
    assert api.cache_pobierz(klucz) is None


# sygnal bramki_pominiete (A7)


def test_sygnal_bramki_pominiete_zapala_sie_i_gasnie(monkeypatch):
    monkeypatch.setattr(api, 'SYGNAL_POMINIETE_OKNO', 5)
    monkeypatch.setattr(api, '_bramki_pominiete_historia', deque(maxlen=5))
    monkeypatch.setattr(api, '_sygnal_bramki_pominiete_aktywny', False)

    for _ in range(5):
        api.zglos_bramki_pominiete(['sedzia'])
    assert api.sygnal_bramki_pominiete_aktywny() is True

    for _ in range(5):
        api.zglos_bramki_pominiete([])
    assert api.sygnal_bramki_pominiete_aktywny() is False


def test_sygnal_bramki_pominiete_ignoruje_trafienia_w_cache(monkeypatch):
    monkeypatch.setattr(api, 'SYGNAL_POMINIETE_OKNO', 5)
    monkeypatch.setattr(api, '_bramki_pominiete_historia', deque(maxlen=5))
    monkeypatch.setattr(api, '_sygnal_bramki_pominiete_aktywny', False)

    for _ in range(5):
        api.zglos_bramki_pominiete(['sedzia'], cache_hit=True)
    assert api.sygnal_bramki_pominiete_aktywny() is False
    assert len(api._bramki_pominiete_historia) == 0

    for _ in range(5):
        api.zglos_bramki_pominiete(['sedzia'], cache_hit=False)
    assert api.sygnal_bramki_pominiete_aktywny() is True


def test_loguj_zapytanie_z_cache_hit_nie_karmi_sygnalu(monkeypatch):
    monkeypatch.setattr(api, 'SYGNAL_POMINIETE_OKNO', 5)
    monkeypatch.setattr(api, '_bramki_pominiete_historia', deque(maxlen=5))
    monkeypatch.setattr(api, '_sygnal_bramki_pominiete_aktywny', False)

    dane = {'agent': 'konto', 'answer': 'x', 'bramki_pominiete': ['sedzia']}
    for _ in range(6):
        api.loguj_zapytanie('pl', dane, 0.01, True, 'jakies pytanie', 'kupujacy')
    assert api.sygnal_bramki_pominiete_aktywny() is False


# limit wysylki: zly ticket nie moze zjadac globalnego budzetu dnia


def test_zly_ticket_nie_zuzywa_globalnego_limitu_wysylki(monkeypatch, client):
    monkeypatch.setattr(api, '_wysylki', deque())
    monkeypatch.setattr(api, '_tickety', OrderedDict())
    monkeypatch.setattr(api, 'LIMIT_WYSYLKA_DZIEN', 3)
    monkeypatch.setattr(api, 'LIMIT_WYSYLKA_MIN', 100)
    wyslane = []
    monkeypatch.setattr(api, 'wyslij_potwierdzenie',
                        lambda *a, **k: (wyslane.append(1), 'ABCD1234')[1])

    for _ in range(3):
        odrzucone = client.post('/send-email', json={'email': 'atakujacy@b.pl', 'temat': 't',
                                                     'tresc': 'x', 'ticket': 'DEADBEEF'})
        assert odrzucone.status_code == 429

    assert len(api._wysylki) == 0
    assert wyslane == []

    prawdziwa = client.post('/send-email', json={'email': 'realny@b.pl', 'temat': 't', 'tresc': 'x'})
    assert prawdziwa.status_code == 200
    assert len(wyslane) == 1


def test_odrzucenie_na_limicie_globalnym_zwalnia_limit_adresu(monkeypatch, client):
    monkeypatch.setattr(api, '_wysylki', deque())
    monkeypatch.setattr(api, '_wysylki_adres', OrderedDict())
    monkeypatch.setattr(api, 'LIMIT_WYSYLKA_DZIEN', 0)

    odrzucone = client.post('/send-email', json={'email': 'ktos@b.pl', 'temat': 't', 'tresc': 'x'})
    assert odrzucone.status_code == 429
    assert api.w_limicie_adresu('ktos@b.pl') is True


# guard_za_dlugie (A5)


def test_guard_za_dlugie_osiagalny_zamiast_422(monkeypatch, client):
    monkeypatch.setattr(api, 'corpus_stamp', lambda lang: 1)
    odpowiedz = client.post('/chat', json={'message': 'a' * (api.MAX_ZNAKI + 1), 'lang': 'pl'})
    assert odpowiedz.status_code == 200
    dane = odpowiedz.json()
    assert dane['powod_odmowy'] == 'guard_za_dlugie'
    assert dane['answer'] == api.LANG['pl']['guardy']['za_dlugie']


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
