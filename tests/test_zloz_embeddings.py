import json

import numpy as np
import pytest

import aliasy
import embedder
from lang_config import LANG

CFG = LANG['pl']


class AtrapaModelu:
    def __init__(self):
        self.wywolania = 0
        self.teksty = []

    def encode(self, teksty, batch_size=None, show_progress_bar=None):
        self.wywolania += 1
        self.teksty.extend(teksty)
        return np.array([[float(len(t)), -1.0, -1.0] for t in teksty], dtype='float32')


def daj_atrape(model):
    def daj():
        model.wywolania_pobrania = getattr(model, 'wywolania_pobrania', 0) + 1
        return model
    return daj


def chunk(nr: int, url: str | None = None) -> dict:
    return {'tytul': f'tytul {nr}', 'tekst': f'tresc chunku {nr}',
            'url': url or f'https://allegro.pl/pomoc/artykul-{nr}'}


def wiersz(nr: int) -> list[float]:
    return [float(nr), float(nr) * 2, float(nr) * 3]


# --dopisz liczy wektory tylko za koncem macierzy i dokleja je na koncu, wiec chunk
# wstawiony w srodek przesuwa cala reszte i rozjezdza wektory z chunkami po cichu.
# Skladanie po tekscie musi trafic kazdy stary wiersz na jego nowa pozycje.
def test_przepisuje_wiersze_gdy_nowy_chunk_wchodzi_w_srodek():
    stare = [chunk(1), chunk(2), chunk(3)]
    stare_emb = np.array([wiersz(1), wiersz(2), wiersz(3)], dtype='float32')
    nowe = [chunk(1), chunk(9), chunk(2), chunk(3)]

    model = AtrapaModelu()
    wynik = embedder.zloz_ze_starego(nowe, stare, stare_emb, CFG, daj_atrape(model), 40)

    assert wynik.shape == (4, 3)
    assert np.array_equal(wynik[0], stare_emb[0])
    assert np.array_equal(wynik[2], stare_emb[1])
    assert np.array_equal(wynik[3], stare_emb[2])
    assert model.wywolania == 1
    assert model.teksty == [embedder.tekst_dla_modelu(chunk(9), CFG)]
    assert not np.array_equal(wynik[1], np.zeros(3, dtype='float32'))


def test_nie_dotyka_modelu_gdy_korpus_sie_nie_zmienil():
    stare = [chunk(1), chunk(2)]
    stare_emb = np.array([wiersz(1), wiersz(2)], dtype='float32')

    model = AtrapaModelu()
    daj = daj_atrape(model)
    wynik = embedder.zloz_ze_starego(list(stare), stare, stare_emb, CFG, daj, 40)

    assert np.array_equal(wynik, stare_emb)
    assert model.wywolania == 0
    assert getattr(model, 'wywolania_pobrania', 0) == 0


def test_przerywa_gdy_do_policzenia_wchodzi_wiecej_niz_limit():
    stare = [chunk(1)]
    stare_emb = np.array([wiersz(1)], dtype='float32')
    nowe = [chunk(1)] + [chunk(100 + i) for i in range(5)]

    model = AtrapaModelu()
    with pytest.raises(SystemExit) as blad:
        embedder.zloz_ze_starego(nowe, stare, stare_emb, CFG, daj_atrape(model), 3)

    assert '5' in str(blad.value)
    assert model.wywolania == 0


def test_odrzuca_stary_korpus_o_niezgodnej_liczbie_wierszy():
    stare = [chunk(1), chunk(2)]
    stare_emb = np.array([wiersz(1)], dtype='float32')

    with pytest.raises(SystemExit):
        embedder.zloz_ze_starego([chunk(1)], stare, stare_emb, CFG,
                                 daj_atrape(AtrapaModelu()), 40)


# Klucz liczony jest biezacym slownikiem aliasow po obu stronach, wiec chunk, ktoremu
# wlasnie dodano alias, ma po obu stronach ten sam tekst i wygladal by na niezmieniony.
# Stary wiersz pochodzi jednak sprzed dodania aliasu i alias nie mialby zadnego wplywu.
# Dlatego kazdy chunk z aliasem jest liczony od nowa, niezaleznie od dopasowania tekstu.
def test_chunk_ze_swiezym_aliasem_jest_liczony_od_nowa(monkeypatch):
    z_aliasem = chunk(1, url='https://allegro.pl/pomoc/allegro-pay-limit')
    stare = [z_aliasem, chunk(2)]
    stare_emb = np.array([wiersz(1), wiersz(2)], dtype='float32')

    monkeypatch.setitem(aliasy.ALIASY, 'allegro-pay-limit', 'limit kwotowy raty')

    model = AtrapaModelu()
    wynik = embedder.zloz_ze_starego([z_aliasem, chunk(2)], stare, stare_emb, CFG,
                                     daj_atrape(model), 40)

    assert model.wywolania == 1
    assert 'limit kwotowy raty' in model.teksty[0]
    assert not np.array_equal(wynik[0], stare_emb[0])
    assert np.array_equal(wynik[1], stare_emb[1])


# Limit pilnuje tego, czego nie planowalismy: tekstow, ktorych w starym korpusie nie ma.
# Chunki z aliasem sa zbiorem znanym i celowym, wiec ich liczba nie moze przewracac
# skladania, inaczej kazdy nowy alias podnosilby prog dla wykrywania niespodzianek.
def test_chunki_z_aliasem_nie_licza_sie_do_limitu_nowych(monkeypatch):
    monkeypatch.setitem(aliasy.ALIASY, 'artykul-1', 'alias pierwszy')
    monkeypatch.setitem(aliasy.ALIASY, 'artykul-2', 'alias drugi')
    monkeypatch.setitem(aliasy.ALIASY, 'artykul-3', 'alias trzeci')

    stare = [chunk(1), chunk(2), chunk(3)]
    stare_emb = np.array([wiersz(1), wiersz(2), wiersz(3)], dtype='float32')

    model = AtrapaModelu()
    wynik = embedder.zloz_ze_starego(list(stare), stare, stare_emb, CFG,
                                     daj_atrape(model), 1)

    assert wynik.shape == (3, 3)
    assert len(model.teksty) == 3


def test_main_sklada_z_katalogu_i_zapisuje_obok_chunkow(tmp_path, monkeypatch):
    stary_katalog = tmp_path / 'przed'
    stary_katalog.mkdir()
    rag = tmp_path / 'RAG'
    rag.mkdir()

    stare = [chunk(1), chunk(2)]
    stare_emb = np.array([wiersz(1), wiersz(2)], dtype='float32')
    (stary_katalog / 'chunks.json').write_text(json.dumps(stare), encoding='utf-8')
    np.save(stary_katalog / 'embeddings.npy', stare_emb)

    nowe = [chunk(1), chunk(7), chunk(2)]
    (rag / 'chunks.json').write_text(json.dumps(nowe), encoding='utf-8')

    monkeypatch.setattr(embedder, 'RAG_DIR', rag)
    model = AtrapaModelu()
    monkeypatch.setattr(embedder, 'SentenceTransformer', lambda nazwa: model)

    embedder.main('pl', stary=str(stary_katalog))

    zapisane = np.load(rag / 'embeddings.npy')
    assert zapisane.shape == (3, 3)
    assert np.array_equal(zapisane[0], stare_emb[0])
    assert np.array_equal(zapisane[2], stare_emb[1])
    assert model.wywolania == 1


def test_main_mowi_wprost_ze_brakuje_starego_korpusu(tmp_path, monkeypatch):
    rag = tmp_path / 'RAG'
    rag.mkdir()
    (rag / 'chunks.json').write_text(json.dumps([chunk(1)]), encoding='utf-8')
    monkeypatch.setattr(embedder, 'RAG_DIR', rag)

    with pytest.raises(SystemExit) as blad:
        embedder.main('pl', stary=str(tmp_path / 'nie-ma-takiego'))

    assert 'chunks.json' in str(blad.value)
