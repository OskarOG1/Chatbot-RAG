def test_efektywny_jezyk_jawny_wybor_ma_priorytet():
    import api
    assert api.efektywny_jezyk('Allegro Smart konto', 'en') == 'en'


def test_efektywny_jezyk_bez_jawnego_wyboru_uzywa_heurystyki():
    import api
    assert api.efektywny_jezyk('jak zmienic haslo', None) == 'pl'


def test_ranking_faiss_odrzuca_indeksy_minus_jeden(monkeypatch):
    import numpy as np
    import rankings

    class FalszywyIndeks:
        ntotal = 3

        def search(self, query_emb, k):
            idx = np.array([[2, -1, 0, -1, 1]])
            dist = np.zeros((1, k))
            return dist, idx

    monkeypatch.setattr(rankings, 'get_faiss', lambda agent, lang='pl': FalszywyIndeks())
    wynik = rankings.ranking_faiss(None, 'kupujacy', [{}, {}, {}])
    assert -1 not in wynik
    assert wynik == [2, 0, 1]


def test_modele_leniwe_nie_laduje_wszystkich_jezykow(monkeypatch):
    import pipeline

    zaladowane = []

    class FalszywyModel:
        def __init__(self, nazwa):
            zaladowane.append(nazwa)

    monkeypatch.setattr(pipeline, 'SentenceTransformer', FalszywyModel)
    swiezy = pipeline.ModeleLeniwe()
    assert zaladowane == []
    swiezy['pl']
    assert zaladowane == [pipeline.LANG['pl']['embedder']]
    swiezy['pl']
    assert zaladowane == [pipeline.LANG['pl']['embedder']]


def test_idf_leniwe_nie_laduje_wszystkich_jezykow(monkeypatch):
    import pipeline

    zaladowane = []

    def falszywy_zaladuj_idf(lang):
        zaladowane.append(lang)
        return ({}, 1.0, True)

    monkeypatch.setattr(pipeline, 'zaladuj_idf', falszywy_zaladuj_idf)
    swiezy = pipeline.IdfLeniwe()
    assert zaladowane == []
    swiezy['pl']
    assert zaladowane == ['pl']
