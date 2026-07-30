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
    assert pipeline._jawna_prosba_o_mail('napisz mi maila do sprzedawcy') is True


def test_jawna_prosba_wymaga_czasownika_i_obiektu():
    assert pipeline._jawna_prosba_o_mail('sprzedawca nie odpowiada') is False


def test_kategoria_z_oferty_reklamacja():
    oferta = pipeline.LANG['pl']['mail_kategorie']['reklamacja']['oferta']
    assert pipeline._kategoria_z_oferty(oferta) == 'reklamacja'


def test_kategoria_z_oferty_zwrot():
    oferta = pipeline.LANG['pl']['mail_kategorie']['zwrot']['oferta']
    assert pipeline._kategoria_z_oferty(oferta) == 'zwrot'


def test_kategoria_z_oferty_brak_dopasowania():
    assert pipeline._kategoria_z_oferty('cos zupelnie innego') is None
