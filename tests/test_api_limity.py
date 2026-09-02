import threading
import time
from collections import OrderedDict, deque

import pytest
from fastapi import HTTPException
from starlette.requests import Request

import api


def zrob_request(naglowki: list, client_host: str = '10.0.0.5') -> Request:
    scope = {
        'type': 'http',
        'headers': [(k.lower().encode(), v.encode()) for k, v in naglowki],
        'client': (client_host, 12345),
    }
    return Request(scope)


def test_adres_klienta_ostatni_wpis_z_naglowka():
    request = zrob_request([('X-Forwarded-For', '1.2.3.4, 5.6.7.8, 9.10.11.12')])
    assert api.adres_klienta(request) == '9.10.11.12'


def test_adres_klienta_odrzuca_podrobiony_pierwszy_wpis():
    request = zrob_request([('X-Forwarded-For', '6.6.6.6, 203.0.113.7')])
    assert api.adres_klienta(request) == '203.0.113.7'
    assert api.adres_klienta(request) != '6.6.6.6'


def test_adres_klienta_brak_naglowka_uzywa_client_host():
    request = zrob_request([], client_host='192.168.1.1')
    assert api.adres_klienta(request) == '192.168.1.1'


def test_w_limicie_ip_blokuje_po_przekroczeniu_minuty(monkeypatch):
    monkeypatch.setattr(api, '_zapytania_ip', OrderedDict())
    monkeypatch.setattr(api, 'LIMIT_IP_MIN', 3)
    monkeypatch.setattr(api, 'LIMIT_IP_DZIEN', 100)
    for _ in range(3):
        assert api.w_limicie_ip('1.1.1.1') is True
    assert api.w_limicie_ip('1.1.1.1') is False


def test_w_limicie_ip_kubelki_niezalezne_dla_roznych_adresow(monkeypatch):
    monkeypatch.setattr(api, '_zapytania_ip', OrderedDict())
    monkeypatch.setattr(api, 'LIMIT_IP_MIN', 1)
    monkeypatch.setattr(api, 'LIMIT_IP_DZIEN', 100)
    assert api.w_limicie_ip('1.1.1.1') is True
    assert api.w_limicie_ip('1.1.1.1') is False
    assert api.w_limicie_ip('2.2.2.2') is True


def test_zapis_do_logu_nie_czeka_na_trzymana_blokade_licznikow(tmp_path, monkeypatch):
    monkeypatch.setattr(api, '_zapytania_ip', OrderedDict())
    monkeypatch.setattr(api, 'LOG_ANALYTICS', tmp_path / 'log_analytics_test.jsonl')

    wchodzi_w_srodek = threading.Event()
    moze_zwolnic = threading.Event()

    def watek_trzymajacy_zamek():
        with api._zamek:
            wchodzi_w_srodek.set()
            moze_zwolnic.wait(timeout=2)

    watek = threading.Thread(target=watek_trzymajacy_zamek)
    watek.start()
    assert wchodzi_w_srodek.wait(timeout=2)

    start = time.monotonic()
    api.dopisz_do_logu({'test': 'wpis'})
    trwanie = time.monotonic() - start

    moze_zwolnic.set()
    watek.join(timeout=2)

    assert trwanie < 0.5


def test_zgloszenie_wyczerpany_limit_zwraca_429_i_nie_przeszukuje_logu(monkeypatch):
    monkeypatch.setattr(api, '_zgloszenia_ip', OrderedDict())
    monkeypatch.setattr(api, '_zgloszenia', deque())
    monkeypatch.setattr(api, 'LIMIT_ZGLOSZEN_MIN', 0)

    def wpisy_logu_nie_powinno_byc_wolane():
        raise AssertionError('wpisy_logu nie powinno zostac wywolane przy wyczerpanym limicie')

    monkeypatch.setattr(api, 'wpisy_logu', wpisy_logu_nie_powinno_byc_wolane)

    request = zrob_request([], client_host='1.1.1.1')
    zadanie = api.ZgloszenieZadanie(id_zapytania='0' * 16, email='osoba@example.com')

    with pytest.raises(HTTPException) as blad:
        api.zgloszenie(zadanie, request)

    assert blad.value.status_code == 429


def test_zgloszenie_zly_email_zwraca_422_i_nie_zuzywa_limitu(monkeypatch):
    monkeypatch.setattr(api, '_zgloszenia_ip', OrderedDict())
    monkeypatch.setattr(api, '_zgloszenia', deque())
    monkeypatch.setattr(api, 'LIMIT_ZGLOSZEN_MIN', 1)
    monkeypatch.setattr(api, 'LIMIT_ZGLOSZEN_IP_MIN', 1)

    request = zrob_request([], client_host='2.2.2.2')
    zadanie = api.ZgloszenieZadanie(id_zapytania='0' * 16, email='to-nie-jest-email')

    with pytest.raises(HTTPException) as blad:
        api.zgloszenie(zadanie, request)

    assert blad.value.status_code == 422
    assert len(api._zgloszenia) == 0
    assert not api._zgloszenia_ip


def test_send_email_limit_per_adres_klienta_niezalezny_dla_dwoch_klientow(monkeypatch):
    monkeypatch.setattr(api, '_wysylki_ip', OrderedDict())
    monkeypatch.setattr(api, '_wysylki_adres', OrderedDict())
    monkeypatch.setattr(api, '_wysylki', deque())
    monkeypatch.setattr(api, 'LIMIT_WYSYLKA_IP_MIN', 1)
    monkeypatch.setattr(api, 'LIMIT_WYSYLKA_IP_DZIEN', 1)
    monkeypatch.setattr(api, 'wyslij_potwierdzenie', lambda *a, **k: 'ABCD1234')

    zadanie_pierwszy = api.WyslijZadanie(email='pierwszy@example.com', temat='Temat', tresc='Tresc')
    api.send_email(zadanie_pierwszy, zrob_request([], client_host='3.3.3.3'))
    zadanie_powtorka = api.WyslijZadanie(email='pierwszy2@example.com', temat='Temat', tresc='Tresc')
    with pytest.raises(HTTPException) as blad:
        api.send_email(zadanie_powtorka, zrob_request([], client_host='3.3.3.3'))
    assert blad.value.status_code == 429

    zadanie_drugi_klient = api.WyslijZadanie(email='drugi@example.com', temat='Temat', tresc='Tresc')
    odpowiedz = api.send_email(zadanie_drugi_klient, zrob_request([], client_host='4.4.4.4'))
    assert odpowiedz.ticket == 'ABCD1234'


def test_send_email_limit_klienta_zwalniany_po_nieudanej_wysylce(monkeypatch):
    monkeypatch.setattr(api, '_wysylki_ip', OrderedDict())
    monkeypatch.setattr(api, '_wysylki_adres', OrderedDict())
    monkeypatch.setattr(api, '_wysylki', deque())
    monkeypatch.setattr(api, 'LIMIT_WYSYLKA_IP_MIN', 1)
    monkeypatch.setattr(api, 'LIMIT_WYSYLKA_IP_DZIEN', 5)

    def rzuca(*a, **k):
        raise RuntimeError('wysylka niedostepna')

    monkeypatch.setattr(api, 'wyslij_potwierdzenie', rzuca)
    zadanie = api.WyslijZadanie(email='awaria@example.com', temat='Temat', tresc='Tresc')
    with pytest.raises(HTTPException) as blad:
        api.send_email(zadanie, zrob_request([], client_host='5.5.5.5'))
    assert blad.value.status_code == 503

    monkeypatch.setattr(api, 'wyslij_potwierdzenie', lambda *a, **k: 'ABCD1234')
    zadanie_powtorka = api.WyslijZadanie(email='awaria@example.com', temat='Temat', tresc='Tresc')
    odpowiedz = api.send_email(zadanie_powtorka, zrob_request([], client_host='5.5.5.5'))
    assert odpowiedz.ticket == 'ABCD1234'
