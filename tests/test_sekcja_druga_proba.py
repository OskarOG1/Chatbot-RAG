import time

import pipeline


def slad_zrodel(zdarzenia):
    return [z for z in zdarzenia if z['typ'] == 'token']


def podmien_wolnego_sedziego(monkeypatch, atrapa_pipeline, opoznienie=0.25):
    oryginal = atrapa_pipeline.osadz_sedzia

    def wolny(zapytanie, chunks, bielik_model=None, lang='pl', stan=None):
        time.sleep(opoznienie)
        return oryginal(zapytanie, chunks, bielik_model, lang, stan)

    monkeypatch.setattr(pipeline, 'czy_kontekst_odpowiada', wolny)
    atrapa_pipeline.sedzia_gotowy.set()


def test_druga_sekcja_odpowiada_z_nota_i_etapem_2(monkeypatch, atrapa_pipeline, chunk):
    atrapa_pipeline.ustaw_etap('sprzedajacy', chunki=[chunk('sprzedaz', score=0.0)],
                               tekst='Odpowiedz sprzedazowa.', sedzia=False)
    kupujacy = chunk('kupujacy', score=0.0)
    atrapa_pipeline.ustaw_etap('kupujacy', chunki=[kupujacy],
                               tekst='Limit dla konta firmowego wynosi tyle.', sedzia=True)
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)

    wynik = pipeline.run('jakie limity allegro pay dla konta firmowego', strona='sprzedajacy',
                         bez_korekty=True, sedzia=True, lang='pl', warstwa_ogolna=False)

    assert wynik['answer'] == 'Limit dla konta firmowego wynosi tyle.'
    assert wynik['agent'] == 'kupujacy'
    assert wynik['cechy']['etap'] == 2
    assert wynik['cechy']['strona_wybrana'] == 'kupujacy'
    assert wynik['cechy']['zrodlo_top1'] == kupujacy[0]['url']
    assert wynik['cechy']['rerank_top1'] == 0.0
    assert wynik['nota_sekcji']


def test_brak_chunkow_drugiej_sekcji_zachowanie_bez_zmian(monkeypatch, atrapa_pipeline, chunk):
    atrapa_pipeline.ustaw_etap('sprzedajacy', chunki=[chunk('sprzedaz', score=0.0)],
                               tekst='Odpowiedz sprzedazowa.', sedzia=False)

    zdarzenia = list(pipeline.run_stream('jakie limity allegro pay', strona='sprzedajacy',
                                         bez_korekty=True, sedzia=True, lang='pl',
                                         warstwa_ogolna=False))

    assert not slad_zrodel(zdarzenia)
    assert 'reset' not in [z['typ'] for z in zdarzenia]
    wynik = zdarzenia[-1]['dane']
    assert wynik['powod_odmowy'] == 'sedzia'
    assert wynik['cechy']['etap'] == 1
    assert not wynik.get('nota_sekcji')
    assert atrapa_pipeline.wywolania['sedzia'] == 1


def test_druga_sekcja_ponizej_progu_zachowanie_bez_zmian(monkeypatch, atrapa_pipeline, chunk):
    atrapa_pipeline.ustaw_etap('sprzedajacy', chunki=[chunk('sprzedaz', score=0.0)],
                               tekst='Odpowiedz sprzedazowa.', sedzia=False)
    atrapa_pipeline.ustaw_etap('kupujacy', chunki=[chunk('kupujacy', score=-10.0)],
                               tekst='Odpowiedz kupujacego.', sedzia=True)

    wynik = pipeline.run('jakie limity allegro pay', strona='sprzedajacy',
                         bez_korekty=True, sedzia=True, lang='pl', warstwa_ogolna=False)

    assert wynik['powod_odmowy'] == 'sedzia'
    assert wynik['cechy']['etap'] == 1
    assert wynik['answer'] != 'Odpowiedz kupujacego.'
    assert atrapa_pipeline.wywolania['sedzia'] == 1


def test_sedzia_odrzuca_obie_sekcje_odmowa_jak_dzis(monkeypatch, atrapa_pipeline, chunk):
    atrapa_pipeline.ustaw_etap('sprzedajacy', chunki=[chunk('sprzedaz', score=0.0)],
                               tekst='Odpowiedz sprzedazowa.', sedzia=False)
    atrapa_pipeline.ustaw_etap('kupujacy', chunki=[chunk('kupujacy', score=0.0)],
                               tekst='Odpowiedz kupujacego.', sedzia=False)
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)

    zdarzenia = list(pipeline.run_stream('jakie limity allegro pay', strona='sprzedajacy',
                                         bez_korekty=True, sedzia=True, lang='pl',
                                         warstwa_ogolna=False))

    assert not slad_zrodel(zdarzenia)
    wynik = zdarzenia[-1]['dane']
    assert wynik['powod_odmowy'] == 'sedzia'
    assert wynik['cechy']['etap'] == 1
    assert wynik['answer'] != 'Odpowiedz kupujacego.'
    assert atrapa_pipeline.wywolania['sedzia'] == 2


def test_prog_rerank_nie_uruchamia_drugiej_proby(monkeypatch, atrapa_pipeline, chunk):
    atrapa_pipeline.ustaw_etap('sprzedajacy', chunki=[chunk('sprzedaz', score=-10.0)], sedzia=True)
    atrapa_pipeline.ustaw_etap('kupujacy', chunki=[chunk('kupujacy', score=-10.0)], sedzia=True)

    wynik = pipeline.run('cos zupelnie spoza zakresu', strona='sprzedajacy',
                         bez_korekty=True, sedzia=True, lang='pl', warstwa_ogolna=False)

    assert wynik['powod_odmowy'] == 'prog_rerank'
    assert atrapa_pipeline.wywolania['sedzia'] == 0


def test_druga_proba_idzie_na_sekcje_uzytkownika_a_nie_odrzucona(monkeypatch, atrapa_pipeline, chunk):
    atrapa_pipeline.ustaw_etap('sprzedajacy', chunki=[chunk('sprzedaz', score=2.0)],
                               tekst='Odpowiedz sprzedazowa.', sedzia=False)
    atrapa_pipeline.ustaw_etap('kupujacy', chunki=[chunk('kupujacy', score=0.0)],
                               tekst='Odpowiedz kupujacego.', sedzia=True)
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)

    wynik = pipeline.run('jakie limity allegro pay', strona='kupujacy',
                         bez_korekty=True, sedzia=True, lang='pl', warstwa_ogolna=False)

    assert wynik['answer'] == 'Odpowiedz kupujacego.'
    assert wynik['agent'] == 'kupujacy'
    assert wynik['cechy']['etap'] == 2
    assert wynik['cechy']['strona_wybrana'] == 'kupujacy'
    assert wynik['nota_sekcji'] is None


def test_wylaczony_etap_2_zostawia_odmowe(monkeypatch, atrapa_pipeline, chunk):
    atrapa_pipeline.ustaw_etap('sprzedajacy', chunki=[chunk('sprzedaz', score=0.0)],
                               tekst='Odpowiedz sprzedazowa.', sedzia=False)
    atrapa_pipeline.ustaw_etap('kupujacy', chunki=[chunk('kupujacy', score=0.0)],
                               tekst='Odpowiedz kupujacego.', sedzia=True)
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)

    wynik = pipeline.run('jakie limity allegro pay', strona='sprzedajacy',
                         bez_korekty=True, sedzia=True, lang='pl', warstwa_ogolna=False,
                         etap2=False)

    assert wynik['powod_odmowy'] == 'sedzia'
    assert wynik['cechy']['etap'] == 1
    assert atrapa_pipeline.wywolania['sedzia'] == 1


def test_reset_przed_tokenami_drugiej_proby_po_optymistycznym_wyslaniu(monkeypatch, atrapa_pipeline, chunk):
    monkeypatch.setattr(pipeline, 'SEDZIA_BUFOR_MAX', 2)
    atrapa_pipeline.ustaw_etap('sprzedajacy', chunki=[chunk('sprzedaz', score=0.0)],
                               tekst='Odpowiedz sprzedazowa.', sedzia=False)
    atrapa_pipeline.tokeny['sprzedaz'] = ['a ', 'b ', 'c ', 'd ']
    atrapa_pipeline.ustaw_etap('kupujacy', chunki=[chunk('kupujacy', score=0.0)],
                               tekst='Pelna odpowiedz kupujacego.', sedzia=True)
    atrapa_pipeline.tokeny['kupujacy'] = ['B1 ', 'B2 ']
    podmien_wolnego_sedziego(monkeypatch, atrapa_pipeline)
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)

    zdarzenia = list(pipeline.run_stream('jakie limity allegro pay', strona='sprzedajacy',
                                         bez_korekty=True, sedzia=True, lang='pl',
                                         warstwa_ogolna=False))

    typy = [z['typ'] for z in zdarzenia]
    assert 'reset' in typy
    reset_idx = typy.index('reset')
    przed = [z['tekst'] for i, z in enumerate(zdarzenia) if z['typ'] == 'token' and i < reset_idx]
    po = [z['tekst'] for i, z in enumerate(zdarzenia) if z['typ'] == 'token' and i > reset_idx]
    assert przed == ['a ', 'b ', 'c ', 'd ']
    assert po == ['B1 ', 'B2 ']

    wynik = zdarzenia[-1]['dane']
    assert wynik['answer'] == 'Pelna odpowiedz kupujacego.'
    assert wynik['cechy']['etap'] == 2
    assert wynik['nota_sekcji']


def test_pominiety_sedzia_etapu_2_trafia_do_bramek_pominietych(monkeypatch, atrapa_pipeline, chunk):
    atrapa_pipeline.ustaw_etap('sprzedajacy', chunki=[chunk('sprzedaz', score=0.0)],
                               tekst='Odpowiedz sprzedazowa.', sedzia=False)
    atrapa_pipeline.ustaw_etap('kupujacy', chunki=[chunk('kupujacy', score=0.0)],
                               tekst='Odpowiedz kupujacego.', sedzia=True)
    atrapa_pipeline.sedzia_pominiete.add('kupujacy')
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)

    wynik = pipeline.run('jakie limity allegro pay', strona='sprzedajacy',
                         bez_korekty=True, sedzia=True, lang='pl', warstwa_ogolna=False)

    assert wynik['answer'] == 'Odpowiedz kupujacego.'
    assert wynik['cechy']['etap'] == 2
    assert 'sedzia' in wynik['bramki_pominiete']


def test_odmowa_drugiej_proby_zostawia_slad_w_cechach(monkeypatch, atrapa_pipeline, chunk):
    atrapa_pipeline.ustaw_etap('sprzedajacy', chunki=[chunk('sprzedaz', score=0.0)],
                               tekst='Odpowiedz sprzedazowa.', sedzia=False)
    atrapa_pipeline.ustaw_etap('kupujacy', chunki=[chunk('kupujacy', score=0.0)],
                               tekst='Odpowiedz kupujacego.', sedzia=False)
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)

    wynik = pipeline.run('jakie limity allegro pay', strona='sprzedajacy',
                         bez_korekty=True, sedzia=True, lang='pl', warstwa_ogolna=False)

    assert wynik['powod_odmowy'] == 'sedzia'
    assert wynik['cechy']['etap'] == 1
    assert wynik['cechy']['etap2_powod'] == 'sedzia'
    assert wynik['cechy']['etap2_strona'] == 'kupujacy'
    assert wynik['cechy']['etap2_sedzia_ok'] is False


def test_odmowa_drugiej_proby_ponizej_progu_tez_zostawia_slad(monkeypatch, atrapa_pipeline, chunk):
    atrapa_pipeline.ustaw_etap('sprzedajacy', chunki=[chunk('sprzedaz', score=0.0)],
                               tekst='Odpowiedz sprzedazowa.', sedzia=False)
    atrapa_pipeline.ustaw_etap('kupujacy', chunki=[chunk('kupujacy', score=-10.0)],
                               tekst='Odpowiedz kupujacego.', sedzia=True)

    wynik = pipeline.run('jakie limity allegro pay', strona='sprzedajacy',
                         bez_korekty=True, sedzia=True, lang='pl', warstwa_ogolna=False)

    assert wynik['cechy']['etap2_powod'] == 'druga_sekcja_prog'
    assert wynik['cechy']['etap2_rerank_top1'] == -10.0
