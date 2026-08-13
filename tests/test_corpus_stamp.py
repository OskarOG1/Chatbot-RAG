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
