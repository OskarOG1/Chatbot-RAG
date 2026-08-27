import pytest

import podpowiedzi

ARTYKUL_ZWROTY = 'https://allegro.pl/pomoc/zwroty'
ARTYKUL_REKLAMACJE = 'https://allegro.pl/pomoc/reklamacje'

KORPUS = [
    {'url': ARTYKUL_ZWROTY, 'agent': 'zakupy', 'tytul': 'Zwrot produktu', 'naglowek': '',
     'tekst': 'Wstep bez pytania.\n'
              'Kto ponosi koszty odeslania produktu\n'
              'Ile masz czasu na zwrot produktu\n'
              'Zwrot mozesz zglosic w zakladce Moje zakupy.\n'},
    {'url': ARTYKUL_ZWROTY, 'agent': 'zakupy', 'tytul': 'Zwrot produktu', 'naglowek': '',
     'tekst': 'Kiedy sprzedajacy moze odmowic zwrotu\n'
              'Kto ponosi koszty odeslania produktu\n'},
    {'url': ARTYKUL_REKLAMACJE, 'agent': 'zakupy', 'tytul': 'Reklamacja', 'naglowek': '',
     'tekst': 'Co napisac w reklamacji produktu\n'
              'Jak dziala licytacja krok po kroku\n'},
]


@pytest.fixture(autouse=True)
def czysty_indeks():
    podpowiedzi.INDEKS_CACHE.clear()
    yield
    podpowiedzi.INDEKS_CACHE.clear()


@pytest.fixture
def korpus(monkeypatch):
    monkeypatch.setattr(podpowiedzi, 'wczytaj_chunki', lambda agent, lang='pl': KORPUS)


def chunki(*urle):
    return [({'url': url, 'agent': 'zakupy', 'tytul': 'Zwrot produktu',
              'tekst': '', 'naglowek': ''}, 0.0) for url in urle]


def test_bierze_srodtytuly_calego_artykulu_a_nie_tylko_chunka(korpus):
    wynik = podpowiedzi.zbuduj(chunki(ARTYKUL_ZWROTY), 'gdzie zglosic zwrot')
    assert 'Kiedy sprzedajacy moze odmowic zwrotu?' in wynik


def test_dopisuje_znak_zapytania_i_pomija_zdania(korpus):
    wynik = podpowiedzi.zbuduj(chunki(ARTYKUL_ZWROTY), 'gdzie zglosic zwrot')
    assert all(p.endswith('?') for p in wynik)
    assert not any('Zwrot mozesz zglosic' in p for p in wynik)


def test_nie_powtarza_pytania_uzytkownika(korpus):
    wynik = podpowiedzi.zbuduj(chunki(ARTYKUL_ZWROTY), 'kto ponosi koszty odeslania produktu')
    assert 'Kto ponosi koszty odeslania produktu?' not in wynik


def test_nie_duplikuje_tego_samego_srodtytulu(korpus):
    wynik = podpowiedzi.zbuduj(chunki(ARTYKUL_ZWROTY), 'gdzie zglosic zwrot')
    assert len(wynik) == len(set(wynik))


def test_dalszy_artykul_wymaga_wspolnego_lematu(korpus):
    wynik = podpowiedzi.zbuduj(chunki(ARTYKUL_ZWROTY, ARTYKUL_REKLAMACJE),
                                'gdzie zglosic zwrot', ile=4)
    assert 'Co napisac w reklamacji produktu?' in wynik
    assert 'Jak dziala licytacja krok po kroku?' not in wynik


def test_bez_korpusu_zwraca_pusta_liste(monkeypatch):
    def brak(agent, lang='pl'):
        raise FileNotFoundError('chunks.json')

    monkeypatch.setattr(podpowiedzi, 'wczytaj_chunki', brak)
    assert podpowiedzi.zbuduj(chunki(ARTYKUL_ZWROTY), 'gdzie zglosic zwrot') == []


def test_bez_chunkow_zwraca_pusta_liste(korpus):
    assert podpowiedzi.zbuduj([], 'gdzie zglosic zwrot') == []
