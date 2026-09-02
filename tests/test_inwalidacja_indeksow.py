import json
import os
import time

import numpy as np
import pytest

import rankings


class FaiszAtrapa:
    def __init__(self, ntotal, wyniki):
        self.ntotal = ntotal
        self.wyniki = wyniki

    def search(self, query_emb, k):
        idx = np.array([self.wyniki[:k]])
        odl = np.zeros_like(idx, dtype='float32')
        return odl, idx


def test_niezgodna_para_konczy_sie_wyjatkiem_z_obiema_liczbami(monkeypatch):
    monkeypatch.setattr(rankings, 'get_faiss', lambda agent, lang='pl': FaiszAtrapa(3, [0, 1, 2]))
    chunki = [{'tekst': f'{i}'} for i in range(4)]

    with pytest.raises(AssertionError) as blad:
        rankings.ranking_faiss(np.zeros((1, 8), dtype='float32'), 'kupujacy', chunki, 'pl')

    assert '3' in str(blad.value)
    assert '4' in str(blad.value)


def test_zgodna_para_dziala_jak_dotad(monkeypatch):
    monkeypatch.setattr(rankings, 'get_faiss', lambda agent, lang='pl': FaiszAtrapa(3, [2, 0, 1]))
    chunki = [{'tekst': f'{i}'} for i in range(3)]

    wynik = rankings.ranking_faiss(np.zeros((1, 8), dtype='float32'), 'kupujacy', chunki, 'pl')

    assert wynik == [2, 0, 1]


def test_drugie_wywolanie_bez_zmiany_pliku_nie_czyta_go_ponownie(tmp_path, monkeypatch):
    monkeypatch.setattr(rankings, 'RAG_DIR', tmp_path)
    rankings.CHUNKI_CACHE.clear()
    sciezka = tmp_path / 'chunks_kupujacy.json'
    with open(sciezka, 'w', encoding='utf-8') as plik:
        json.dump([{'tekst': 'pierwszy'}], plik)

    pierwsze = rankings.wczytaj_chunki('kupujacy', 'pl')
    drugie = rankings.wczytaj_chunki('kupujacy', 'pl')

    assert pierwsze is drugie

    rankings.CHUNKI_CACHE.clear()


def test_podmiana_pliku_uniewaznia_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(rankings, 'RAG_DIR', tmp_path)
    rankings.CHUNKI_CACHE.clear()
    sciezka = tmp_path / 'chunks_kupujacy.json'
    with open(sciezka, 'w', encoding='utf-8') as plik:
        json.dump([{'tekst': 'pierwszy'}], plik)

    rankings.wczytaj_chunki('kupujacy', 'pl')

    with open(sciezka, 'w', encoding='utf-8') as plik:
        json.dump([{'tekst': 'drugi'}], plik)
    czas = time.time()
    os.utime(sciezka, (czas + 10, czas + 10))

    wynik = rankings.wczytaj_chunki('kupujacy', 'pl')

    assert wynik == [{'tekst': 'drugi'}]

    rankings.CHUNKI_CACHE.clear()
