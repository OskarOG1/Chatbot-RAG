import pytest
import pipeline


@pytest.fixture(autouse=True)
def maly_idf(monkeypatch):
    idf = {'konto': 1.0, 'haslo': 2.0, 'zwrot': 1.5}
    idf_max = 3.0
    monkeypatch.setitem(pipeline.IDF_DANE, 'pl', (idf, idf_max, True))


def chunk(tekst):
    return ({'url': 'u', 'tekst': tekst, 'tytul': 't'}, 0.9)


def test_pusty_tekst_zero():
    assert pipeline.pokrycie_idf('', [chunk('konto haslo')]) == 0.0


def test_pelne_pokrycie_wysokie():
    wynik = pipeline.pokrycie_idf('konto haslo', [chunk('konto haslo zwrot')])
    assert wynik == pytest.approx(1.0)


def test_brak_wspolnych_lematow_niski():
    wynik = pipeline.pokrycie_idf('zwrot', [chunk('konto haslo')])
    assert wynik == 0.0


def test_nieznany_lemat_dostaje_idf_max():
    wynik = pipeline.pokrycie_idf('niecodwiadomy', [chunk('niecodwiadomy inny tekst')])
    assert wynik == pytest.approx(1.0)
