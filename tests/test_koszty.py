import contextvars
import json
import threading

import api
import koszty


class Usage:
    def __init__(self, we, wy):
        self.prompt_tokens = we
        self.completion_tokens = wy


class Odpowiedz:
    def __init__(self, we, wy):
        self.usage = Usage(we, wy)


def test_podsumowanie_bez_zacznij_zwraca_zera():
    koszty.ZUZYCIE.set(None)
    podsumowanie = koszty.podsumowanie()
    assert podsumowanie == {'tokeny_we': 0, 'tokeny_wy': 0, 'koszt_usd': 0.0,
                             'wywolania': 0, 'szacowane': False}


def test_dodaj_bez_zacznij_nie_wybucha():
    koszty.ZUZYCIE.set(None)
    koszty.dodaj('x', 100, 50)
    assert koszty.ZUZYCIE.get() is None


def test_dodaj_po_zacznij():
    koszty.zacznij()
    koszty.dodaj('x', 100, 50)
    podsumowanie = koszty.podsumowanie()
    assert podsumowanie['tokeny_we'] == 100
    assert podsumowanie['tokeny_wy'] == 50
    assert podsumowanie['wywolania'] == 1


def test_dwa_wywolania_sumuja_sie():
    koszty.zacznij()
    koszty.dodaj('x', 10, 5)
    koszty.dodaj('x', 20, 7)
    podsumowanie = koszty.podsumowanie()
    assert podsumowanie['tokeny_we'] == 30
    assert podsumowanie['tokeny_wy'] == 12
    assert podsumowanie['wywolania'] == 2


def test_zacznij_drugi_raz_zeruje_licznik():
    koszty.zacznij()
    koszty.dodaj('x', 100, 50)
    koszty.zacznij()
    podsumowanie = koszty.podsumowanie()
    assert podsumowanie['tokeny_we'] == 0
    assert podsumowanie['tokeny_wy'] == 0
    assert podsumowanie['wywolania'] == 0


def test_koszt_liczony_z_cennika(monkeypatch):
    monkeypatch.setitem(koszty.CENNIK, 'test', (2.0, 6.0))
    koszty.zacznij()
    koszty.dodaj('test', 1_000_000, 1_000_000)
    podsumowanie = koszty.podsumowanie()
    assert podsumowanie['koszt_usd'] == 8.0


def test_model_spoza_cennika_dostaje_domyslna_stawke():
    koszty.zacznij()
    koszty.dodaj('nieznany-model-xyz', 1_000_000, 1_000_000)
    podsumowanie = koszty.podsumowanie()
    assert podsumowanie['koszt_usd'] == 0.0
    assert podsumowanie['tokeny_we'] == 1_000_000
    assert podsumowanie['tokeny_wy'] == 1_000_000


def test_oszacuj_granice():
    assert koszty.oszacuj('') == 0
    assert koszty.oszacuj('a') == 1
    assert koszty.oszacuj('a' * 360) == 100


def test_dodaj_z_odpowiedzi_bierze_liczby_z_usage():
    koszty.zacznij()
    koszty.dodaj_z_odpowiedzi('m', Odpowiedz(11, 7), [{'content': 'x'}], 'y')
    podsumowanie = koszty.podsumowanie()
    assert podsumowanie['tokeny_we'] == 11
    assert podsumowanie['tokeny_wy'] == 7
    assert podsumowanie['szacowane'] is False


def test_dodaj_z_odpowiedzi_szacuje_po_znakach():
    koszty.zacznij()
    koszty.dodaj_z_odpowiedzi('m', None, [{'content': 'ab' * 100}], 'cd' * 50)
    podsumowanie = koszty.podsumowanie()
    assert podsumowanie['szacowane'] is True
    assert podsumowanie['tokeny_we'] > 0
    assert podsumowanie['tokeny_wy'] > 0


def test_dodaj_z_odpowiedzi_usage_niekompletne_spada_na_szacowanie():
    koszty.zacznij()
    odp = Odpowiedz(None, None)
    odp.usage.prompt_tokens = None
    koszty.dodaj_z_odpowiedzi('m', odp, [{'content': 'abc'}], 'def')
    podsumowanie = koszty.podsumowanie()
    assert podsumowanie['szacowane'] is True


def test_jedno_szacowane_wywolanie_ustawia_szacowane_na_cale_podsumowanie():
    koszty.zacznij()
    koszty.dodaj_z_odpowiedzi('m', Odpowiedz(11, 7), [{'content': 'x'}], 'y')
    koszty.dodaj_z_odpowiedzi('m', None, [{'content': 'abc'}], 'def')
    podsumowanie = koszty.podsumowanie()
    assert podsumowanie['szacowane'] is True


def w_watku(funkcja, *argumenty):
    kontekst = contextvars.copy_context()
    wynik = []
    watek = threading.Thread(target=lambda: wynik.append(kontekst.run(funkcja, *argumenty)))
    watek.start()
    watek.join()
    return wynik[0] if wynik else None


def test_licznik_widoczny_w_innym_watku():
    koszty.zacznij()
    w_watku(koszty.dodaj, 'm', 10, 5)
    w_watku(koszty.dodaj, 'm', 20, 7)
    podsumowanie = koszty.podsumowanie()
    assert podsumowanie['tokeny_we'] == 30
    assert podsumowanie['tokeny_wy'] == 12


def test_zacznij_w_watku_nie_wycieka():
    koszty.zacznij()
    koszty.dodaj('m', 1, 1)
    w_watku(koszty.zacznij)
    podsumowanie = koszty.podsumowanie()
    assert podsumowanie['tokeny_we'] == 1
    assert podsumowanie['tokeny_wy'] == 1


def ostatni_wpis_logu(sciezka):
    linie = sciezka.read_text(encoding='utf-8').strip().splitlines()
    return json.loads(linie[-1])


def test_loguj_zapytanie_zapisuje_liczbe_wywolan_dla_trafienia_w_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(api, 'LOG_ANALYTICS', tmp_path / 'log_analytics_test.jsonl')
    api.loguj_zapytanie('pl', {'agent': 'konto', 'answer': 'x'}, 0.01, True,
                        'jakies pytanie', 'kupujacy', None)
    wpis = ostatni_wpis_logu(api.LOG_ANALYTICS)
    assert wpis['wywolania'] == 0


def test_loguj_zapytanie_zapisuje_liczbe_wywolan_dla_zadania_policzonego(tmp_path, monkeypatch):
    monkeypatch.setattr(api, 'LOG_ANALYTICS', tmp_path / 'log_analytics_test.jsonl')
    koszty.zacznij()
    koszty.dodaj('m', 10, 5)
    koszty.dodaj('m', 10, 5)
    api.loguj_zapytanie('pl', {'agent': 'konto', 'answer': 'x'}, 0.01, False,
                        'jakies pytanie', 'kupujacy', koszty.podsumowanie())
    wpis = ostatni_wpis_logu(api.LOG_ANALYTICS)
    assert wpis['wywolania'] == 2
