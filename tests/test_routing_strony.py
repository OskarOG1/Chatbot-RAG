import pipeline
import strony


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


def test_pytanie_z_sygnalem_leksykalnym_ma_prior():
    prior, sila = strony.prior_strony('moja paczka nie dotarla', None, 'pl')
    assert prior == 'kupujacy'
    assert sila == 'leksykalna'


def test_pytanie_z_lepkim_agentem_ma_prior_tylko_przy_followupie():
    prior, sila = strony.prior_strony('ile to bedzie trwac', 'sprzedaz', 'pl', czy_followup=True)
    assert prior == 'sprzedajacy'
    assert sila == 'lepka'


def test_pytanie_bez_wlasnego_sygnalu_dziedziczy_lepki_agent_bez_followupu():
    prior, sila = strony.prior_strony('ile to bedzie trwac', 'sprzedaz', 'pl', czy_followup=False)
    assert prior == 'sprzedajacy'
    assert sila == 'lepka'


def test_pytanie_bez_agenta_poprzedniego_i_bez_sygnalu_nie_ma_priora():
    prior, sila = strony.prior_strony('ile to bedzie trwac', None, 'pl', czy_followup=False)
    assert prior is None
    assert sila is None
