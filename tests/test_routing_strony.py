import pipeline
import strony


def test_pytanie_generyczne_bez_priora_pyta_o_strone():
    wynik = pipeline.run('ile mam czasu na zwrot', bez_korekty=True, sedzia=False, lang='pl')
    assert wynik['pyta_strona'] is True
    assert wynik['agent'] == ''
    assert wynik['sources'] == []


def test_pytanie_z_sygnalem_leksykalnym_ma_prior():
    prior, sila = strony.prior_strony('moja paczka nie dotarla', None, 'pl')
    assert prior == 'kupujacy'
    assert sila == 'leksykalna'


def test_pytanie_z_lepkim_agentem_ma_prior():
    prior, sila = strony.prior_strony('ile to bedzie trwac', 'sprzedaz', 'pl')
    assert prior == 'sprzedajacy'
    assert sila == 'lepka'
