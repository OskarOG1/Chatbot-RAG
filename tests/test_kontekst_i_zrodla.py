import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from agents_core import (usun_liste_zrodel_bez_naglowka, usun_sekcje_zrodel, verify_answer,
                         zwin_powtorzone_cytaty)
from pipeline import przytnij_kontekst


def chunk(url, tytul='Tytul'):
    return {'url': url, 'tytul': tytul, 'tekst': 'tresc', 'agent': 'sprzedaz'}


def test_lista_zrodel_bez_naglowka_znika():
    tekst = ('1. Wejdz w ustawienia konta.\n'
             '[[1]](https://help.allegro.com/pl/a/jeden-AAA) - Pierwszy artykul Zdanie z kontekstu.\n'
             '[[2]](https://help.allegro.com/pl/a/dwa-BBB) - Drugi artykul To samo zdanie z kontekstu.')
    assert usun_liste_zrodel_bez_naglowka(tekst) == '1. Wejdz w ustawienia konta.'


def test_lista_zrodel_w_pojedynczych_nawiasach_tez_znika():
    tekst = ('Haslo zmienisz w ustawieniach.\n'
             '[1] - Jak zmienic haslo Opis pierwszy.\n'
             '[2] - Dane konta Opis drugi.')
    assert usun_liste_zrodel_bez_naglowka(tekst) == 'Haslo zmienisz w ustawieniach.'


def test_krok_instrukcji_z_odsylaczem_na_koncu_zostaje():
    # Przypadek graniczny: ostatni wiersz to zwykly krok, ktory KONCZY sie odsylaczem,
    # a nie zaczyna. Gdyby wzorzec lapal takie wiersze, zjadalby tresc odpowiedzi.
    tekst = ('1. Wejdz w ustawienia [1].\n'
             '2. Kliknij Zmien haslo [2].\n'
             '3. Zapisz zmiany [2].')
    assert usun_liste_zrodel_bez_naglowka(tekst) == tekst


def test_pojedynczy_wiersz_zrodla_nie_wystarcza():
    # Jeden wiersz moze byc trescia odpowiedzi, wiec listy nie usuwamy ponizej dwoch wpisow.
    tekst = ('Zwrot zglosisz w zakladce Moje zakupy.\n'
             '[[1]](https://help.allegro.com/pl/a/jeden-AAA) - Jak zwrocic zakup Opis.')
    assert usun_liste_zrodel_bez_naglowka(tekst) == tekst


def test_sama_lista_bez_tresci_zostaje_nietknieta():
    # Gdyby po usunieciu nie zostalo nic, odpowiedz bylaby pusta. Wtedy lepiej nie ruszac.
    tekst = ('[[1]](https://help.allegro.com/pl/a/jeden-AAA) - Pierwszy Opis.\n'
             '[[2]](https://help.allegro.com/pl/a/dwa-BBB) - Drugi Opis.')
    assert usun_liste_zrodel_bez_naglowka(tekst) == tekst


def test_naglowek_zrodel_dalej_dziala():
    tekst = 'Odpowiedz [1].\n\nZrodla:\n[1]\n[2]'
    assert usun_sekcje_zrodel(tekst) == 'Odpowiedz [1].'


def test_verify_answer_czysci_dopisana_liste_i_nie_zostawia_ogryzka():
    tekst = ('Nazwe produktu zmienisz przez formularz zgloszenia bledu [1].\n'
             '[[1]](https://help.allegro.com/pl/sell/a/jeden-AAA) - Pierwszy artykul Opis.\n'
             '[[2]](https://help.allegro.com/pl/sell/a/dwa-BBB) - Drugi artykul Opis.')
    wynik = verify_answer(tekst, [(chunk('https://help.allegro.com/pl/sell/a/jeden-AAA'), -1.0),
                                  (chunk('https://help.allegro.com/pl/sell/a/dwa-BBB'), -2.0)])
    assert '[[' not in wynik['tekst']
    assert 'Pierwszy artykul' not in wynik['tekst']
    assert wynik['tekst'].startswith('Nazwe produktu zmienisz')
    assert [c['n'] for c in wynik['cytaty']] == [1]


def test_przyciecie_kontekstu_odrzuca_slabe_chunki():
    chunks = [(chunk('a'), -1.0), (chunk('b'), -2.5), (chunk('c'), -4.9), (chunk('d'), -6.2)]
    assert [c['url'] for c, _ in przytnij_kontekst(chunks, 4.0, minimum=3)] == ['a', 'b', 'c']


def test_przyciecie_zostawia_podloge_dla_sedziego():
    # Sedzia dostaje SEDZIA_CHUNKOW pierwszych chunkow, wiec przyciecie nie moze zejsc ponizej
    # tej liczby, inaczej bramka sedziego ocenia kontekst uboszszy niz dotad.
    chunks = [(chunk('a'), -1.0), (chunk('b'), -9.0), (chunk('c'), -9.5), (chunk('d'), -9.9)]
    assert [c['url'] for c, _ in przytnij_kontekst(chunks, 4.0, minimum=3)] == ['a', 'b', 'c']


def test_przyciecie_nie_dosypuje_gdy_chunkow_jest_mniej_niz_podloga():
    chunks = [(chunk('a'), -1.0), (chunk('b'), -9.0)]
    assert len(przytnij_kontekst(chunks, 4.0, minimum=3)) == 2


def test_margines_zero_wylacza_przyciecie():
    chunks = [(chunk('a'), -1.0), (chunk('b'), -9.0)]
    assert len(przytnij_kontekst(chunks, 0, minimum=3)) == 2


def test_przyciecie_pustej_listy():
    assert przytnij_kontekst([], 4.0) == []


def test_lista_zrodel_w_srodku_odpowiedzi_znika():
    # Tak wygladala odpowiedz z produkcji: kroki, potem osiem wierszy zrodel,
    # potem jeszcze akapit. Blok nie siedzi na koncu, a i tak ma zniknac.
    tekst = ('1. Przejdz do zakladki Moje oferty [5].\n'
             '2. Kliknij Zmien obok nazwy produktu [5].\n'
             '[[1]](https://help.allegro.com/pl/sell/a/jeden-AAA) - Pierwszy Katalog Nazw produktow.\n'
             '[[2]](https://help.allegro.com/pl/sell/a/dwa-BBB) - Drugi Katalog Nazw produktow.\n'
             '[[3]](https://help.allegro.com/pl/sell/a/trzy-CCC) - Trzeci Katalog Nazw produktow.\n'
             'Jesli nazwa nie spelnia wymogow, mozemy ja odrzucic [2].')
    wynik = usun_liste_zrodel_bez_naglowka(tekst)
    assert 'Katalog Nazw' not in wynik
    assert wynik.startswith('1. Przejdz do zakladki Moje oferty [5].')
    assert wynik.endswith('mozemy ja odrzucic [2].')


def test_numery_z_usunietego_bloku_nie_udaja_cytatow():
    # Interfejs pokazuje wylacznie zrodla zacytowane w tresci. Numery z dopisanej listy
    # nie moga trafic do cytatow, bo inaczej na liscie zrodel laduje cale okno kontekstu.
    urle = [f'https://help.allegro.com/pl/sell/a/art{i}-X{i}X' for i in range(1, 4)]
    tekst = ('Nazwe zmienisz przez formularz zgloszenia bledu [2].\n'
             f'[[1]]({urle[0]}) - Pierwszy Opis.\n'
             f'[[2]]({urle[1]}) - Drugi Opis.\n'
             f'[[3]]({urle[2]}) - Trzeci Opis.\n'
             'Nazwa musi byc zgodna z parametrami [2].')
    wynik = verify_answer(tekst, [(chunk(u), -1.0) for u in urle])
    assert [c['n'] for c in wynik['cytaty']] == [2]


def test_ten_sam_numer_w_podpunktach_zostaje_raz_na_koncu():
    # Tak wygladala odpowiedz z produkcji: kazdy podpunkt jednego kroku konczyl sie tym samym [1].
    tekst = ('1. Na stronie ogloszenia: a. Kliknij zglos naruszenie [1]. b. Wybierz powod [1]. '
             'c. Kliknij wyslij [1].')
    assert zwin_powtorzone_cytaty(tekst) == (
        '1. Na stronie ogloszenia: a. Kliknij zglos naruszenie. b. Wybierz powod. '
        'c. Kliknij wyslij [1].')


def test_kolejne_kroki_z_jednego_zrodla_maja_jeden_numer():
    tekst = '1. Wejdz w ustawienia [1].\n2. Kliknij Zmien [1].\n3. Zapisz [1].'
    assert zwin_powtorzone_cytaty(tekst) == '1. Wejdz w ustawienia.\n2. Kliknij Zmien.\n3. Zapisz [1].'


def test_zmiana_zrodla_przerywa_ciag():
    # Przypadek graniczny: [1] wraca po [2], wiec kazdy z trzech numerow zamyka wlasny ciag
    # i zaden nie moze zniknac, inaczej krok 3 wygladalby na wziety z [2].
    tekst = '1. Krok A [1].\n2. Krok B [2].\n3. Krok C [1].'
    assert zwin_powtorzone_cytaty(tekst) == tekst


def test_pusta_linia_przerywa_ciag():
    tekst = 'Pierwszy akapit [1].\n\nDrugi akapit [1].'
    assert zwin_powtorzone_cytaty(tekst) == tekst


def test_zwiniecie_nie_zmienia_listy_zrodel():
    urle = [f'https://help.allegro.com/pl/a/art{i}-X{i}X' for i in range(1, 3)]
    tekst = ('Zgloszenie wyslesz na dwa sposoby.\n'
             '1. Kliknij zglos naruszenie [1]. Wybierz powod [1].\n'
             '2. Uzyj formularza [2]. Opisz naruszenie [2].')
    wynik = verify_answer(tekst, [(chunk(u), -1.0) for u in urle])
    assert [c['n'] for c in wynik['cytaty']] == [1, 2]
    assert wynik['tekst'].count('[1]') == 1
    assert wynik['tekst'].count('[2]') == 1
    assert '1. Kliknij zglos naruszenie. Wybierz powod [1].' in wynik['tekst']


def test_cytat_z_kilkoma_numerami_zostaje_cytatem():
    # Wczesniej [2, 3] tracilo nawiasy jak adnotacja [Note: ...], w tekscie zostawalo gole
    # "2, 3", a zrodla 2 i 3 wypadaly z listy linkow pod odpowiedzia.
    urle = [f'https://help.allegro.com/pl/a/art{i}-X{i}X' for i in range(1, 4)]
    wynik = verify_answer('Wybierz szablon cennika [2, 3]. Zapisz zmiany [1].',
                          [(chunk(u), -1.0) for u in urle])
    assert wynik['tekst'] == 'Wybierz szablon cennika [2] [3]. Zapisz zmiany [1].'
    assert [c['n'] for c in wynik['cytaty']] == [2, 3, 1]


def test_adnotacja_w_nawiasie_dalej_traci_nawiasy():
    # Przypadek graniczny: rozbijanie dotyczy tylko samych liczb z przecinkami. Tekst
    # w nawiasie z liczba i slowem to nie cytat i ma dalej stracic nawiasy.
    urle = ['https://help.allegro.com/pl/a/art1-X1X']
    wynik = verify_answer('Oplata [2 zl, 3 zl] zalezy od kategorii [1].', [(chunk(u), -1.0) for u in urle])
    assert wynik['tekst'] == 'Oplata 2 zl, 3 zl zalezy od kategorii [1].'
