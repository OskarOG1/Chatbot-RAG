import pipeline


def test_sygnal_reklamacja():
    assert pipeline.sygnal_maila('sluchawki przyszly uszkodzone') is True


def test_sygnal_zwrot():
    assert pipeline.sygnal_maila('chce zwrocic te buty') is True


def test_sygnal_faktura():
    assert pipeline.sygnal_maila('prosze o fakture za zakup') is True


def test_sygnal_eskalacja():
    assert pipeline.sygnal_maila('sprzedawca nie odpowiada od tygodnia') is True


def test_pytanie_faktyczne_bez_slow_kluczowych():
    assert pipeline.sygnal_maila('jak sprawdzic gdzie jest moja przesylka') is False


def test_jawna_prosba_o_mail_wykryta():
    assert pipeline.jawna_prosba_o_mail('napisz mi maila do sprzedawcy') is True


def test_jawna_prosba_wymaga_czasownika_i_obiektu():
    assert pipeline.jawna_prosba_o_mail('sprzedawca nie odpowiada') is False


def test_kategoria_z_oferty_reklamacja():
    oferta = pipeline.LANG['pl']['mail_kategorie']['reklamacja']['oferta']
    assert pipeline.kategoria_z_oferty(oferta) == 'reklamacja'


def test_kategoria_z_oferty_zwrot():
    oferta = pipeline.LANG['pl']['mail_kategorie']['zwrot']['oferta']
    assert pipeline.kategoria_z_oferty(oferta) == 'zwrot'


def test_kategoria_z_oferty_brak_dopasowania():
    assert pipeline.kategoria_z_oferty('cos zupelnie innego') is None


def test_jawna_prosba_bez_ogonkow():
    assert pipeline.jawna_prosba_o_mail('chce napisac mail') is True


def test_jawna_prosba_z_ogonkami():
    assert pipeline.jawna_prosba_o_mail('chcę napisać mail') is True


def test_jawna_prosba_ogonki_dają_ten_sam_wynik():
    bez = pipeline.jawna_prosba_o_mail('chce napisac mail')
    z = pipeline.jawna_prosba_o_mail('chcę napisać mail')
    assert bez == z is True


def test_jawna_prosba_wielkie_litery():
    assert pipeline.jawna_prosba_o_mail('CHCE NAPISAC MAIL') is True


def test_pozycja_16_z_przebiegu_ocen():
    assert pipeline.jawna_prosba_o_mail('Chce napisac mail bo produkt jest uszkodzony') is True


def test_listy_maila_normalizowane_raz():
    pierwsze = pipeline.listy_maila('pl')
    drugie = pipeline.listy_maila('pl')
    assert pierwsze is drugie


def test_brak_nowych_falszywych_trafien_na_neutralnych_pytaniach():
    neutralne = (
        'jak sprawdzic status przesylki',
        'ile kosztuje dostawa kurierem',
        'jak zalogowac sie na konto',
        'gdzie znajde regulamin allegro',
        'czy moge zmienic adres dostawy',
    )
    for pytanie in neutralne:
        assert pipeline.jawna_prosba_o_mail(pytanie) is False


def test_kategoria_z_oferty_ma_pierwszenstwo_przed_lista(monkeypatch):
    neutralna_oferta = 'zupelnie neutralne zdanie bez sygnalow maila'
    monkeypatch.setitem(
        pipeline.LANG['pl']['mail_kategorie']['reklamacja'], 'oferta', neutralna_oferta)
    assert pipeline.jawna_prosba_o_mail(neutralna_oferta) is True


def test_en_jawna_prosba_pozytyw_niezmieniona():
    assert pipeline.jawna_prosba_o_mail('please write me an email', lang='en') is True


def test_en_jawna_prosba_negatyw_niezmieniona():
    assert pipeline.jawna_prosba_o_mail('the seller is not responding', lang='en') is False
