from collections import OrderedDict

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
