import pipeline
import strony


def test_pytanie_generyczne_bez_priora_pyta_o_strone():
    wynik = pipeline.run('ile mam czasu na zwrot', bez_korekty=True, sedzia=False, lang='pl')
    assert wynik['pyta_strona'] is True
    assert wynik['agent'] == ''
    assert wynik['sources'] == []


def test_pytanie_bez_priora_z_jasnym_zwyciezca_nie_pyta():
    wynik = pipeline.run('jak zmienić hasło', bez_korekty=True, sedzia=False, lang='pl')
    assert not wynik.get('pyta_strona')
    assert wynik['agent'] != ''
    assert wynik['sources'] != []


def test_pytanie_z_sygnalem_leksykalnym_ma_prior():
    prior, sila = strony.prior_strony('moja paczka nie dotarla', None, 'pl')
    assert prior == 'kupujacy'
    assert sila == 'leksykalna'


def test_pytanie_z_lepkim_agentem_ma_prior_tylko_przy_followupie():
    prior, sila = strony.prior_strony('ile to bedzie trwac', 'sprzedaz', 'pl', czy_followup=True)
    assert prior == 'sprzedajacy'
    assert sila == 'lepka'


def test_pytanie_bez_followupu_ignoruje_lepki_agent():
    prior, sila = strony.prior_strony('ile to bedzie trwac', 'sprzedaz', 'pl', czy_followup=False)
    assert prior is None
    assert sila is None
