def test_efektywny_jezyk_jawny_wybor_ma_priorytet():
    import api
    assert api.efektywny_jezyk('Allegro Smart konto', 'en') == 'en'


def test_efektywny_jezyk_bez_jawnego_wyboru_uzywa_heurystyki():
    import api
    assert api.efektywny_jezyk('jak zmienic haslo', None) == 'pl'


def test_lepki_prior_wymaga_historii(monkeypatch):
    import pipeline
    import strony

    monkeypatch.setattr(pipeline, 'embed_query', lambda lang, tekst: None)
    monkeypatch.setattr(pipeline, 'search_reranked_multi', lambda *a, **k: [])

    wywolania = []
    oryginalny = strony.prior_strony

    def szpieg(query, agent_poprzedni, lang='pl', czy_followup=False):
        wywolania.append(czy_followup)
        return oryginalny(query, agent_poprzedni, lang, czy_followup)

    monkeypatch.setattr(strony, 'prior_strony', szpieg)
    pipeline.run('a ile to bedzie kosztowac', agent_poprzedni='sprzedaz', history=[],
                 bez_korekty=True, sedzia=False, lang='pl')
    assert wywolania == [False]


def test_lepki_prior_dziala_gdy_jest_historia(monkeypatch):
    import pipeline
    import strony

    monkeypatch.setattr(pipeline, 'embed_query', lambda lang, tekst: None)
    monkeypatch.setattr(pipeline, 'search_reranked_multi', lambda *a, **k: [])
    monkeypatch.setattr(pipeline, 'przepisz_zapytanie', lambda query, history, bielik_model, lang: query)

    wywolania = []
    oryginalny = strony.prior_strony

    def szpieg(query, agent_poprzedni, lang='pl', czy_followup=False):
        wywolania.append(czy_followup)
        return oryginalny(query, agent_poprzedni, lang, czy_followup)

    monkeypatch.setattr(strony, 'prior_strony', szpieg)
    historia = [{'role': 'user', 'content': 'jak wystawic przedmiot na sprzedaz'},
                {'role': 'assistant', 'content': 'odpowiedz'}]
    pipeline.run('a ile to bedzie kosztowac', agent_poprzedni='sprzedaz', history=historia,
                 bez_korekty=True, sedzia=False, lang='pl')
    assert wywolania == [True]


def test_ranking_faiss_odrzuca_indeksy_minus_jeden(monkeypatch):
    import numpy as np
    import rankings

    class FalszywyIndeks:
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
        return ({}, 1.0)

    monkeypatch.setattr(pipeline, 'zaladuj_idf', falszywy_zaladuj_idf)
    swiezy = pipeline.IdfLeniwe()
    assert zaladowane == []
    swiezy['pl']
    assert zaladowane == ['pl']
