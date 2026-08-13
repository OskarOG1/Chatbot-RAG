from prior_strony import prior_strony


def test_pytanie_z_sygnalem_leksykalnym_ma_prior():
    prior, sila = prior_strony('moja paczka nie dotarla', None, 'pl')
    assert prior == 'kupujacy'
    assert sila == 'leksykalna'


def test_pytanie_z_lepkim_agentem_ma_prior_tylko_przy_followupie():
    prior, sila = prior_strony('ile to bedzie trwac', 'sprzedaz', 'pl', czy_followup=True)
    assert prior == 'sprzedajacy'
    assert sila == 'lepka'


def test_pytanie_bez_wlasnego_sygnalu_dziedziczy_lepki_agent_bez_followupu():
    prior, sila = prior_strony('ile to bedzie trwac', 'sprzedaz', 'pl', czy_followup=False)
    assert prior == 'sprzedajacy'
    assert sila == 'lepka'


def test_pytanie_bez_agenta_poprzedniego_i_bez_sygnalu_nie_ma_priora():
    prior, sila = prior_strony('ile to bedzie trwac', None, 'pl', czy_followup=False)
    assert prior is None
    assert sila is None
