import json
from datetime import datetime, timedelta, timezone

import pytest

import statystyki


def wpis(**pola):
    baza = {'czas': datetime.now(timezone.utc).isoformat(), 'lang': 'pl',
            'sekcja': 'konto', 'wynik': 'odpowiedz', 'latencja_s': 5.0,
            'cache_hit': False, 'pytanie': 'jak zmienic haslo'}
    baza.update(pola)
    return baza


@pytest.fixture
def log(tmp_path):
    def zapisz(wpisy):
        sciezka = tmp_path / 'log.jsonl'
        with open(sciezka, 'w', encoding='utf-8') as w:
            for x in wpisy:
                w.write(json.dumps(x, ensure_ascii=False) + '\n')
        return sciezka
    return zapisz


def test_wczytaj_pomija_puste_i_niedekodowalne(log):
    sciezka = log([])
    with open(sciezka, 'a', encoding='utf-8') as w:
        w.write('\n')
        w.write('to nie jest json\n')
        w.write(json.dumps(wpis()) + '\n')
    wpisy = statystyki.wczytaj(sciezka)
    assert len(wpisy) == 1


def test_wczytaj_brak_pliku_zwraca_pusta_liste(tmp_path):
    assert statystyki.wczytaj(tmp_path / 'brak.jsonl') == []


def test_filtruj_dni_odrzuca_stare_wpisy():
    teraz = datetime.now(timezone.utc)
    stary = wpis(czas=(teraz - timedelta(days=3)).isoformat())
    dzisiejszy = wpis(czas=teraz.isoformat())
    wynik = statystyki.filtruj([stary, dzisiejszy], dni=1)
    assert wynik == [dzisiejszy]


def test_filtruj_strona_odrzuca_wpisy_bez_pola():
    z_polem = wpis(strona='kupujacy')
    bez_pola = wpis()
    wynik = statystyki.filtruj([z_polem, bez_pola], strona='kupujacy')
    assert wynik == [z_polem]


def test_normalizuj_strone():
    assert statystyki.normalizuj_strone(None) == 'nieznana'
    assert statystyki.normalizuj_strone('auto') == 'nieznana'
    assert statystyki.normalizuj_strone('kupujacy') == 'kupujacy'


def test_trafnosc_ignoruje_rozmowy():
    wpisy = ([wpis(wynik='odpowiedz') for _ in range(8)]
             + [wpis(wynik='odmowa') for _ in range(2)]
             + [wpis(wynik='rozmowa') for _ in range(5)])
    wynik = statystyki.statystyki(wpisy)
    assert wynik['ogolem']['trafnosc'] == 0.8


def test_trafnosc_brak_danych_daje_none():
    wynik = statystyki.statystyki([wpis(wynik='rozmowa')])
    assert wynik['ogolem']['trafnosc'] is None


def test_powod_bez_pola_trafia_do_brak_danych():
    wynik = statystyki.statystyki([wpis(wynik='odmowa')])
    powody = {p['powod']: p['ile'] for p in wynik['powody']}
    assert powody == {'brak_danych': 1}


def test_sekcje_liczy_tylko_odpowiedzi():
    wpisy = [wpis(wynik='odpowiedz', sekcja='zakupy'),
             wpis(wynik='odmowa', sekcja='zakupy')]
    wynik = statystyki.statystyki(wpisy)
    sekcje = {s['sekcja']: s['ile'] for s in wynik['sekcje']}
    assert sekcje == {'zakupy': 1}


def test_kwantyl():
    assert statystyki.kwantyl([1, 2, 3, 4, 5], 0.5) == 3.0
    assert statystyki.kwantyl([], 0.5) == 0.0


def test_histogram_latencji():
    wynik = statystyki.histogram_latencji([1.0, 3.0, 7.0, 15.0, 30.0])
    assert [k['ile'] for k in wynik] == [1, 1, 1, 1, 1]


def test_dzienne_uzupelnia_luki_zerami():
    teraz = datetime.now(timezone.utc)
    dzien1 = teraz - timedelta(days=2)
    dzien3 = teraz
    wpisy = [wpis(czas=dzien1.isoformat()), wpis(czas=dzien3.isoformat())]
    wynik = statystyki.statystyki(wpisy)
    dni = [d['dzien'] for d in wynik['dzienne']]
    assert dni == sorted(dni)
    assert len(dni) == 3
    assert wynik['dzienne'][1]['zapytan'] == 0


def test_top_pytania_sklejane_case_i_bialymi_znakami():
    wpisy = [wpis(pytanie='Jak zmienić hasło'), wpis(pytanie='jak zmienić hasło ')]
    wynik = statystyki.statystyki(wpisy)
    assert wynik['top_pytania'][0]['ile'] == 2


def test_wysylka_i_ocena_nie_liczone_jako_zapytania():
    wpisy = [wpis(), {'typ': 'wysylka', 'czas': datetime.now(timezone.utc).isoformat()},
             {'typ': 'ocena', 'czas': datetime.now(timezone.utc).isoformat()}]
    wynik = statystyki.statystyki(wpisy)
    assert wynik['ogolem']['zapytan'] == 1


def test_liczba_odrzuca_bool():
    assert statystyki.liczba(True) is False
    assert statystyki.liczba(False) is False
    assert statystyki.liczba(1.5) is True
