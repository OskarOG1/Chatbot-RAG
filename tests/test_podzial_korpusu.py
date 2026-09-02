import json

import numpy as np

import strony
import vector


def test_podzial_zgodny_ze_strony_niezaleznie_od_wielkosci_liter_i_spacji(tmp_path, monkeypatch):
    monkeypatch.setattr(vector, 'RAG_DIR', tmp_path)
    chunki = [
        {'agent': 'kupujacy', 'tekst': 'a'},
        {'agent': 'Sprzedaz', 'tekst': 'b'},
        {'agent': ' sprzedaz ', 'tekst': 'c'},
        {'agent': 'konto', 'tekst': 'd'},
        {'agent': 'nieznany_agent', 'tekst': 'e'},
    ]
    with open(tmp_path / 'chunks.json', 'w', encoding='utf-8') as w:
        json.dump(chunki, w, ensure_ascii=False)
    embeddings = np.random.rand(len(chunki), 4).astype('float32')
    np.save(tmp_path / 'embeddings.npy', embeddings)

    vector.main('pl')

    with open(tmp_path / 'chunks_kupujacy.json', encoding='utf-8') as r:
        kupujacy = json.load(r)
    with open(tmp_path / 'chunks_sprzedaz.json', encoding='utf-8') as r:
        sprzedaz = json.load(r)

    assert {c['tekst'] for c in kupujacy} == {'a', 'd', 'e'}
    assert {c['tekst'] for c in sprzedaz} == {'b', 'c'}
    assert (tmp_path / 'kupujacy.faiss').exists()
    assert (tmp_path / 'sprzedaz.faiss').exists()


def test_agenci_wszystkich_stron_zwraca_nazwy_agentow():
    assert strony.agenci_wszystkich_stron() == ['kupujacy', 'sprzedaz']
