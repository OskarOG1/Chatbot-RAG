import ogolna
import pipeline


# Grupa A: temat_zablokowany


def test_temat_zablokowany_dawka_leku_to_zdrowie():
    assert ogolna.temat_zablokowany('Jaka jest bezpieczna dawka tego leku?', 'pl') == 'zdrowie'


def test_temat_zablokowany_krzywda_to_kryzys_nie_zdrowie():
    # zdanie zawiera slowo z listy 'zdrowie' (lekow) i fraze z listy 'kryzys' (zrobic sobie
    # krzywde), a kryzys jest w LANG wpisany przed zdrowiem; test pilnuje tej kolejnosci.
    query = 'Biorę za dużo leków i chcę zrobić sobie krzywdę.'
    assert ogolna.temat_zablokowany(query, 'pl') == 'kryzys'


def test_temat_zablokowany_zwykle_pytanie_o_zwrot_butow_to_none():
    assert ogolna.temat_zablokowany('Jak zwrócić buty, które nie pasują?', 'pl') is None


# Grupa B: konkrety


def test_konkrety_termin_w_dniach_niepuste():
    assert ogolna.konkrety('Na zwrot masz 14 dni.') != []


def test_konkrety_bez_liczb_puste():
    assert ogolna.konkrety('Zwrot zgłaszasz w swoim koncie.') == []


def test_konkrety_kwota_niepuste():
    assert ogolna.konkrety('Koszt przesyłki to 9,99 zł.') != []


def test_konkrety_link_niepuste():
    assert ogolna.konkrety('Sprawdź szczegóły na http://example.com') != []


# Grupa C: oczysc, skroc_do_zdan


def test_oczysc_kasuje_cytat_naglowek_i_znacznik_czatu():
    tekst = '# Ważne\nTreść odpowiedzi [1] z cytatem.<|im_end|>'
    oczyszczony = ogolna.oczysc(tekst)
    assert '[1]' not in oczyszczony
    assert '#' not in oczyszczony
    assert '<|im_end|>' not in oczyszczony
    assert 'Ważne' in oczyszczony
    assert 'Treść odpowiedzi' in oczyszczony


def test_skroc_do_zdan_obcina_do_limitu():
    tekst = 'Zdanie pierwsze. Zdanie drugie. Zdanie trzecie. Zdanie czwarte.'
    wynik = ogolna.skroc_do_zdan(tekst, 3)
    assert wynik == 'Zdanie pierwsze. Zdanie drugie. Zdanie trzecie.'
    assert 'Zdanie czwarte' not in wynik


# Grupa D: sprawdz_odpowiedz, z_odeslaniem


def test_sprawdz_odpowiedz_za_krotka_daje_ogolna_pusta():
    wynik = ogolna.sprawdz_odpowiedz('Krótko.', 'pl')
    assert wynik['powod'] == 'ogolna_pusta'


def test_z_odeslaniem_dokleja_odeslanie_z_konfiguracji():
    wynik = ogolna.z_odeslaniem('Tekst odpowiedzi.', 'pl')
    assert wynik.startswith('Tekst odpowiedzi.')
    assert pipeline.LANG['pl']['ogolna']['odeslanie'] in wynik


# Grupa E: integracja przez pipeline.run, obie sekcje RAG odmawiaja przez prog_rerank
# (atrapa_pipeline nie ma ustawionej zadnej sekcji), wiec kaskada zawsze schodzi do
# trzeciego szczebla drabiny.


def test_ogolna_czysta_odpowiedz_wygrywa_jako_wynik(atrapa_pipeline):
    atrapa_pipeline.ogolna_tekst = ('Sklepy internetowe zwykle stosują podobne zasady '
                                     'obsługi klienta i wsparcia technicznego.')
    wynik = pipeline.run('jakies pytanie poza domena', strona='kupujacy',
                         bez_korekty=True, sedzia=False, lang='pl')
    assert wynik['tryb'] == 'ogolna'
    assert wynik['sources'] == []
    assert wynik['citations'] == []
    assert wynik['nota_sekcji']
    assert wynik['answer'].endswith(pipeline.LANG['pl']['ogolna']['odeslanie'])
    assert wynik['powod_rag'] == 'prog_rerank'


def test_ogolna_odpowiedz_z_konkretem_wraca_do_brak_wiedzy(atrapa_pipeline):
    atrapa_pipeline.ogolna_tekst = 'Na zwrot masz 30 dni od odbioru przesyłki.'
    wynik = pipeline.run('jakies pytanie poza domena', strona='kupujacy',
                         bez_korekty=True, sedzia=False, lang='pl')
    assert wynik['answer'] == pipeline.LANG['pl']['brak_wiedzy']
    assert wynik['powod_odmowy'] == 'prog_rerank'
    assert wynik['powod_ogolna'] == 'ogolna_konkrety'


def test_ogolna_temat_zablokowany_nie_wywoluje_modelu(atrapa_pipeline):
    wynik = pipeline.run('Jaka jest bezpieczna dawka tego leku?', strona='kupujacy',
                         bez_korekty=True, sedzia=False, lang='pl')
    komunikat = pipeline.LANG['pl']['ogolna']['tematy_zablokowane']['zdrowie']['komunikat']
    assert wynik['answer'] == komunikat
    assert wynik['powod_ogolna'] == 'ogolna_temat'
    assert atrapa_pipeline.wywolania['ogolna'] == 0


def test_warstwa_ogolna_wylaczona_zostawia_brak_wiedzy(atrapa_pipeline):
    wynik = pipeline.run('jakies pytanie poza domena', strona='kupujacy',
                         bez_korekty=True, sedzia=False, lang='pl', warstwa_ogolna=False)
    assert wynik['answer'] == pipeline.LANG['pl']['brak_wiedzy']
    assert atrapa_pipeline.wywolania['ogolna'] == 0


def test_sukces_pierwszej_sekcji_nie_uruchamia_warstwy_ogolnej(monkeypatch, atrapa_pipeline):
    atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz o koncie.')
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)
    wynik = pipeline.run('jakies pytanie o konto', strona='kupujacy',
                         bez_korekty=True, sedzia=False, lang='pl')
    assert wynik.get('powod_odmowy') is None
    assert atrapa_pipeline.wywolania['ogolna'] == 0


def test_etap_trzy_dopiero_gdy_warstwa_ogolna_odpowiedziala(atrapa_pipeline, chunk):
    atrapa_pipeline.ustaw_etap('kupujacy', chunki=[chunk('kupujacy', score=-10.0)])
    atrapa_pipeline.ogolna_tekst = ('Sklepy internetowe zwykle stosują podobne zasady '
                                     'obsługi klienta i wsparcia technicznego.')
    wynik = pipeline.run('jakies pytanie poza domena', strona='kupujacy',
                         bez_korekty=True, sedzia=False, lang='pl')
    assert wynik['tryb'] == 'ogolna'
    assert wynik['cechy']['etap'] == 3


def test_etap_zostaje_przy_sekcji_gdy_warstwa_ogolna_odmawia(atrapa_pipeline, chunk):
    atrapa_pipeline.ustaw_etap('kupujacy', chunki=[chunk('kupujacy', score=-10.0)])
    atrapa_pipeline.ogolna_tekst = 'Na zwrot masz 30 dni od odbioru przesyłki.'
    wynik = pipeline.run('jakies pytanie poza domena', strona='kupujacy',
                         bez_korekty=True, sedzia=False, lang='pl')
    assert wynik['powod_ogolna'] == 'ogolna_konkrety'
    assert wynik['cechy']['etap'] == 1


def test_strumien_resetuje_po_tokenach_warstwy_ogolnej(atrapa_pipeline):
    atrapa_pipeline.tokeny_ogolne = ['a', 'b']
    atrapa_pipeline.ogolna_tekst = 'Na zwrot masz 30 dni od odbioru przesyłki.'
    zdarzenia = list(pipeline.run_stream('jakies pytanie poza domena', strona='kupujacy',
                                          bez_korekty=True, sedzia=False, lang='pl'))
    typy = [z['typ'] for z in zdarzenia]
    assert typy[-1] == 'wynik'
    indeks_resetu = len(typy) - 1 - typy[::-1].index('reset')
    ostatni_token = max(i for i, t in enumerate(typy) if t == 'token')
    assert indeks_resetu > ostatni_token
    assert indeks_resetu < len(typy) - 1
