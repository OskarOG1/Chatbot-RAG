import strony


def test_wygrywa_sekcja_z_wyzsza_ocena():
    wyniki = [({'agent': 'sprzedaz'}, 8.0), ({'agent': 'zakupy'}, 2.0)]
    strona_wybrana, chunki, przewaga = strony.rozstrzygnij(wyniki, 'kupujacy', 5)
    assert strona_wybrana == 'sprzedajacy'
    assert przewaga == 6.0
    assert all(chunk['agent'] == 'sprzedaz' for chunk, _ in chunki)


def test_remis_rozstrzyga_przelacznik_uzytkownika():
    wyniki = [({'agent': 'zakupy'}, 1.5), ({'agent': 'sprzedaz'}, 1.5)]
    strona_wybrana, chunki, przewaga = strony.rozstrzygnij(wyniki, 'kupujacy', 5)
    assert strona_wybrana == 'kupujacy'
    assert przewaga == 0.0


def test_brak_wynikow_drugiej_strony_daje_przewage_none():
    wyniki = [({'agent': 'zakupy'}, 3.0)]
    strona_wybrana, chunki, przewaga = strony.rozstrzygnij(wyniki, 'kupujacy', 5)
    assert strona_wybrana == 'kupujacy'
    assert przewaga is None
    assert len(chunki) == 1


def test_brak_wynikow_strony_uzytkownika_wybiera_druga():
    wyniki = [({'agent': 'sprzedaz'}, 4.0)]
    strona_wybrana, chunki, przewaga = strony.rozstrzygnij(wyniki, 'kupujacy', 5)
    assert strona_wybrana == 'sprzedajacy'
    assert przewaga is None
    assert len(chunki) == 1


def test_przycina_do_k_i_odrzuca_obca_sekcje():
    wyniki = [({'agent': 'sprzedaz'}, 9.0), ({'agent': 'zakupy'}, 8.0),
              ({'agent': 'sprzedaz'}, 7.0), ({'agent': 'sprzedaz'}, 6.0)]
    strona_wybrana, chunki, przewaga = strony.rozstrzygnij(wyniki, 'kupujacy', 2)
    assert len(chunki) == 2
    assert [ocena for _, ocena in chunki] == [9.0, 7.0]
