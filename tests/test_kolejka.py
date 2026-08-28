import json
from datetime import datetime, timedelta, timezone

import pytest

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
