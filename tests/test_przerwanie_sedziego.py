import pipeline


def test_odmowa_sedziego_nie_wypuszcza_tokenow(atrapa_pipeline):
    agent = atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz.', sedzia=False)
    atrapa_pipeline.tokeny[agent] = ['Aby ', 'zalozyc ', 'konto ', 'wejdz ', 'na ']
    zdarzenia = list(pipeline.run_stream('jakies pytanie o konto', strona='kupujacy',
                                          bez_korekty=True, sedzia=True, lang='pl'))
    assert not any(z['typ'] == 'token' for z in zdarzenia)
    assert zdarzenia[-1]['typ'] == 'wynik'
    assert zdarzenia[-1]['dane']['powod_odmowy'] == 'sedzia'
    assert agent in atrapa_pipeline.przerwane


def test_przerwanie_zostawia_slad_w_cechach(atrapa_pipeline):
    agent = atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz.', sedzia=False)
    atrapa_pipeline.tokeny[agent] = ['Aby ', 'zalozyc ', 'konto ', 'wejdz ', 'na ']
    wynik = pipeline.run('jakies pytanie o konto', strona='kupujacy',
                         bez_korekty=True, sedzia=True, lang='pl')
    assert wynik['powod_odmowy'] == 'sedzia'
    assert wynik['powod_etap2'] == 'prog_rerank'
    assert wynik['cechy']['generacja_przerwana'] is True
    assert wynik['cechy']['tokeny_stracone'] >= 1


def test_zgoda_sedziego_przepuszcza_wszystkie_tokeny(monkeypatch, atrapa_pipeline):
    agent = atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz.', sedzia=True)
    atrapa_pipeline.tokeny[agent] = ['raz ', 'dwa ', 'trzy ']
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)
    zdarzenia = list(pipeline.run_stream('jakies pytanie o konto', strona='kupujacy',
                                          bez_korekty=True, sedzia=True, lang='pl'))
    teksty = [z['tekst'] for z in zdarzenia if z['typ'] == 'token']
    assert teksty == ['raz ', 'dwa ', 'trzy ']
    assert atrapa_pipeline.przerwane == []
