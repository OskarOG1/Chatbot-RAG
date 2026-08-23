import pipeline
import strony


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


def test_odmowa_pokrycia_wysyla_reset(monkeypatch, atrapa_pipeline):
    a = atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz A.', sedzia=True)
    atrapa_pipeline.tokeny[a] = ['A1 ', 'A2 ']
    druga = next(s for s in strony.STRONY if s != 'kupujacy')
    b = atrapa_pipeline.ustaw_etap(druga, tekst='Odpowiedz B.', sedzia=True)
    atrapa_pipeline.tokeny[b] = ['B1 ']
    monkeypatch.setattr(pipeline, 'pokrycie_idf',
                         lambda tekst, chunks, lang: 0.0 if tekst == 'Odpowiedz A.' else 1.0)
    zdarzenia = list(pipeline.run_stream('jakies pytanie o konto', strona='kupujacy',
                                          bez_korekty=True, sedzia=True, lang='pl'))
    typy = [z['typ'] for z in zdarzenia]
    assert typy.count('reset') == 1
    indeks = typy.index('reset')
    po_resecie = [z['tekst'] for z in zdarzenia[indeks:] if z['typ'] == 'token']
    assert po_resecie == ['B1 ']


def test_odmowa_obu_sekcji_wysyla_dwa_resety(monkeypatch, atrapa_pipeline):
    a = atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz A.', sedzia=True)
    atrapa_pipeline.tokeny[a] = ['A1 ', 'A2 ']
    druga = next(s for s in strony.STRONY if s != 'kupujacy')
    b = atrapa_pipeline.ustaw_etap(druga, tekst='Odpowiedz B.', sedzia=True)
    atrapa_pipeline.tokeny[b] = ['B1 ']
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 0.0)
    zdarzenia = list(pipeline.run_stream('jakies pytanie o konto', strona='kupujacy',
                                          bez_korekty=True, sedzia=True, lang='pl'))
    typy = [z['typ'] for z in zdarzenia]
    assert typy.count('reset') == 2
    assert zdarzenia[-1]['typ'] == 'wynik'
    assert zdarzenia[-1]['dane']['powod_odmowy']


def test_sukces_bez_resetu(monkeypatch, atrapa_pipeline):
    a = atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz A.', sedzia=True)
    atrapa_pipeline.tokeny[a] = ['A1 ', 'A2 ']
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)
    zdarzenia = list(pipeline.run_stream('jakies pytanie o konto', strona='kupujacy',
                                          bez_korekty=True, sedzia=True, lang='pl'))
    typy = [z['typ'] for z in zdarzenia]
    assert 'reset' not in typy
    teksty = [z['tekst'] for z in zdarzenia if z['typ'] == 'token']
    assert teksty == ['A1 ', 'A2 ']
