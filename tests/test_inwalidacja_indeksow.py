import json
import os
import time

import rankings


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
