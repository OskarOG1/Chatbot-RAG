import json
from collections import OrderedDict, deque

import pytest
from fastapi.testclient import TestClient

import api
import pipeline
import spell


@pytest.fixture(autouse=True)
def reset_stan(monkeypatch, tmp_path):
    monkeypatch.setattr(api, '_zapytania', deque())
    monkeypatch.setattr(api, '_zapytania_ip', OrderedDict())
    monkeypatch.setattr(api, '_cache', OrderedDict())
    monkeypatch.setattr(api, '_wysylki', deque())
    monkeypatch.setattr(api, '_wysylki_adres', OrderedDict())
    monkeypatch.setattr(api, '_tickety', OrderedDict())
    monkeypatch.setattr(api, 'LOG_ANALYTICS', tmp_path / 'log.jsonl')
    monkeypatch.setattr(pipeline, 'LOG_TRUDNE', tmp_path / 'trudne.jsonl')
    monkeypatch.setattr(spell, 'FOLDED_CACHE', None)


@pytest.fixture
def client():
    return TestClient(api.app)


def test_cache_ignoruje_bez_korekty(monkeypatch, atrapa_pipeline, client):
    atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz o koncie.')
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda t, c, lang: 1.0)
    monkeypatch.setattr(api, 'corpus_stamp', lambda lang: 1)

    baza = {'message': 'jak zmienic hasllo', 'lang': 'pl', 'sedzia': False, 'strona': 'kupujacy'}

    a = client.post('/chat', json={**baza, 'bez_korekty': False}).json()
    szukania_po_a = len(atrapa_pipeline.wyszukiwania)
    b = client.post('/chat', json={**baza, 'bez_korekty': True}).json()
    szukania_po_b = len(atrapa_pipeline.wyszukiwania)

    print('A (bez_korekty=False) doprecyzowanie =', repr(a.get('doprecyzowanie')))
    print('B (bez_korekty=True)  doprecyzowanie =', repr(b.get('doprecyzowanie')))
    print('zapytanie retrievalowe A =', atrapa_pipeline.wyszukiwania[0]['zapytanie'])
    print('liczba wyszukiwan po A =', szukania_po_a, ', po B =', szukania_po_b)
    wpisy = [json.loads(l) for l in api.LOG_ANALYTICS.read_text(encoding='utf-8').splitlines()]
    print('cache_hit w logu:', [w['cache_hit'] for w in wpisy])


def test_cache_pobierz_wyscig(monkeypatch, client):
    class Zlosliwy(OrderedDict):
        def get(self, k, d=None):
            v = OrderedDict.get(self, k, d)
            OrderedDict.pop(self, k, None)
            return v

    c = Zlosliwy()
    c[('pl', 'x', 1, 'kupujacy')] = {'agent': 'kupujacy', 'answer': 'a'}
    monkeypatch.setattr(api, '_cache', c)
    try:
        api.cache_pobierz(('pl', 'x', 1, 'kupujacy'))
        print('brak wyjatku')
    except Exception as e:
        print('cache_pobierz podnosi:', type(e).__name__, e)


def test_wysylka_zly_ticket_zjada_limit_globalny(monkeypatch, client):
    monkeypatch.setattr(api, 'LIMIT_WYSYLKA_DZIEN', 3)
    monkeypatch.setattr(api, 'LIMIT_WYSYLKA_MIN', 100)
    wywolania = []
    monkeypatch.setattr(api, 'wyslij_potwierdzenie',
                        lambda *a, **k: (wywolania.append(1), 'ABCD1234')[1])

    kody = []
    for _ in range(3):
        r = client.post('/send-email', json={'email': 'a@b.pl', 'temat': 't', 'tresc': 'x',
                                             'ticket': 'DEADBEEF'})
        kody.append(r.status_code)
    r = client.post('/send-email', json={'email': 'realny@b.pl', 'temat': 't', 'tresc': 'x'})
    kody.append(r.status_code)
    print('kody:', kody, 'realnych wysylek:', len(wywolania))
    print('stan _wysylki (globalny licznik):', len(api._wysylki))


def test_stream_vs_chat_pola(monkeypatch, atrapa_pipeline, client):
    atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz o koncie.')
    atrapa_pipeline.sedzia_pominiete.add('kupujacy')
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda t, c, lang: 1.0)
    monkeypatch.setattr(api, 'corpus_stamp', lambda lang: 1)
    baza = {'message': 'jak zmienic konto', 'lang': 'pl', 'bez_korekty': True, 'strona': 'kupujacy'}

    a = client.post('/chat', json=baza).json()
    monkeypatch.setattr(api, '_cache', OrderedDict())
    tekst = client.post('/chat/stream', json=baza).text
    ostatnie = [json.loads(l[6:]) for l in tekst.splitlines() if l.startswith('data: ')][-1]
    print('/chat klucze       :', sorted(a.keys()))
    print('/chat/stream klucze:', sorted(ostatnie['dane'].keys()))
