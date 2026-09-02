import pytest
from pipeline import redaguj, skazone_tokeny


PRZYPADKI_MASKOWAC = [
    'Nazywam sie Jan Kowalski i chce zlozyc reklamacje.',
    'Nazywam sie Anna Nowak, mam problem ze zwrotem.',
    'Moj sprzedawca to Piotr Zielinski, nie odpowiada na wiadomosci.',
    'My name is John Smith and I have an issue with my order.',
    'My name is Sarah Connor, I never received the package.',
    'This is Michael Brown writing about a late delivery.',
    'Mieszkam przy ulicy Kwiatowej 12 w Warszawie i paczka nie dotarla.',
    'Adres dostawy to ulica Dluga 5, Krakow, prosze poprawic.',
    'My address is 221 Baker Street, London, please update it.',
    'Jestem Marek Kowalczyk, zamowienie numer 123456789 nie doszlo.',
]

PRZYPADKI_NIE_MASKOWAC = [
    'Does Allegro Pay cost anything',
    'Is Allegro Pay safe',
    'How do I enable Allegro Pay',
    'What is Allegro Pay',
    'How do I return an item bought with Allegro Smart!',
    'What does Allegro Smart! give',
    'Jak dziala Allegro Lokalnie przy odbiorze osobistym',
    'Gdzie znajde Strefa Okazji na stronie glownej',
    'Jak sprawdzic zamowienia w Moje Allegro',
    'How does Allegro Pay work exactly',
]


@pytest.mark.parametrize('tekst', PRZYPADKI_MASKOWAC)
def test_redaguj_maskuje_dane_osobowe(tekst):
    assert '[ukryte]' in redaguj(tekst)


@pytest.mark.parametrize('tekst', PRZYPADKI_NIE_MASKOWAC)
def test_redaguj_nie_rusza_nazw_wlasnych(tekst):
    assert redaguj(tekst) == tekst


def test_redaguj_maskuje_email():
    assert redaguj('Mozna do mnie pisac na jan.kowalski@przyklad.pl') == \
        'Mozna do mnie pisac na [ukryte]'


def test_redaguj_maskuje_numer_telefonu():
    assert '[ukryte]' in redaguj('Mozna do mnie dzwonic pod numerem 123456789')


def test_redaguj_maskuje_url():
    assert '[ukryte]' in redaguj('Wiecej informacji na https://allegro.pl/pomoc/artykul')


def test_redaguj_maskuje_numer_zamowienia():
    assert '[ukryte]' in redaguj('Numer zamowienia to A1B2C3D4')


def test_skazone_tokeny_nie_usuwa_literowki():
    nieznane = ['zwroit', 'jan', 'kowalski']
    skazone = skazone_tokeny('Nazywam sie Jan Kowalski, chyba zwroit paczke')
    pozostale = sorted({t.lower() for t in nieznane} - skazone)
    assert 'zwroit' in pozostale
