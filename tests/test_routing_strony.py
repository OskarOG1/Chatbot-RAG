import pipeline


def test_kaskada_odpowiada_z_drugiej_sekcji_z_nota(monkeypatch, atrapa_pipeline):
    atrapa_pipeline.ustaw_etap('sprzedajacy', tekst='Odpowiedz z sekcji sprzedających [1].')
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)

    wynik = pipeline.run('jakies pytanie o sprzedaz', strona='kupujacy',
                         bez_korekty=True, sedzia=False, lang='pl')
    assert wynik.get('powod_odmowy') is None
    assert wynik['agent'] == 'sprzedaz'
    assert wynik['nota_sekcji'] == pipeline.LANG['pl']['nota_sekcji']['sprzedajacy']


def test_kaskada_odmawia_dla_pytania_poza_domena_mimo_dwoch_etapow(monkeypatch, atrapa_pipeline):
    wynik = pipeline.run('jak ugotowac makaron', strona='kupujacy',
                         bez_korekty=True, sedzia=False, lang='pl')
    assert wynik['powod_odmowy'] == 'prog_rerank'
    assert wynik['agent'] == ''
    assert wynik['sources'] == []
