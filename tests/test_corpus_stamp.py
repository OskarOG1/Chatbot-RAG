import os

import pipeline


def test_corpus_stamp_reaguje_na_dotkniecie_pliku_sekcji(tmp_path, monkeypatch):
    rag_dir = tmp_path
    kupujacy = rag_dir / 'chunks_kupujacy.json'
    sprzedaz = rag_dir / 'chunks_sprzedaz.json'
    kupujacy.write_text('[]', encoding='utf-8')
    sprzedaz.write_text('[]', encoding='utf-8')

    monkeypatch.setattr(pipeline, 'sekcje_chunks_paths', lambda lang: [kupujacy, sprzedaz])

    przed = pipeline.corpus_stamp('pl')
    os.utime(kupujacy, (przed + 1000, przed + 1000))
    po = pipeline.corpus_stamp('pl')

    assert po != przed


# B5 (Pomiary/PLAN_PRZEGLAD_PR44_PR45.md): idf.pkl stemplowal sie po chunks.json, a cache
# odpowiedzi po plikach sekcji, wiec przebudowa samych sekcji zostawiala IDF stare bez zadnego
# sygnalu. zaladuj_idf ma teraz jedno pojecie swiezosci, corpus_stamp, tak jak cache_klucz.


def test_zaladuj_idf_reaguje_na_dotkniecie_pliku_sekcji_bez_ruszania_chunks_json(tmp_path, monkeypatch):
    rag_dir = tmp_path
    chunks_json = rag_dir / 'chunks.json'
    kupujacy = rag_dir / 'chunks_kupujacy.json'
    sprzedaz = rag_dir / 'chunks_sprzedaz.json'
    chunks_json.write_text(
        '[{"tekst": "hasło do konta"}]', encoding='utf-8')
    kupujacy.write_text('[]', encoding='utf-8')
    sprzedaz.write_text('[]', encoding='utf-8')

    monkeypatch.setattr(pipeline, 'chunks_path', lambda lang: chunks_json)
    monkeypatch.setattr(pipeline, 'sekcje_chunks_paths', lambda lang: [kupujacy, sprzedaz])

    _, _, _ = pipeline.zaladuj_idf('pl')
    stamp_przed = pipeline.corpus_stamp('pl')
    idf_cache = chunks_json.parent / 'idf.pkl'
    assert idf_cache.exists()

    os.utime(kupujacy, (stamp_przed + 1000, stamp_przed + 1000))

    import pickle
    with open(idf_cache, 'rb') as plik:
        zapis = pickle.load(plik)
    assert zapis['stamp'] != pipeline.corpus_stamp('pl')
