import math
from pathlib import Path

import strony
import wagi_stron


def test_ocena_pytania_puste_przeciecie():
    assert wagi_stron.ocena_pytania(set(), {'zwrot': -7.0}) == {
        'suma_norm': 0.0, 'dowod': 0.0, 'k': 0}


def test_ocena_pytania_normalizacja_pierwiastkiem():
    tabela = {'zwrot': -6.0, 'sprzedaz': 3.0}
    ocena = wagi_stron.ocena_pytania({'zwrot', 'sprzedaz'}, tabela)
    assert ocena['suma_norm'] == (-6.0 + 3.0) / math.sqrt(2)
    assert ocena['dowod'] == 6.0
    assert ocena['k'] == 2


def test_zdecyduj_r9_lepka_przed_leksykalna_slaba():
    tau_mocny, tau_slaby, z_silny = 10.0, 5.0, 3.5
    strona, sila = wagi_stron.zdecyduj_r9(
        suma_norm=7.0, dowod=4.0, tau_mocny=tau_mocny, tau_slaby=tau_slaby,
        z_silny=z_silny, agent_poprzedni='sprzedaz', czy_followup=True)
    assert (strona, sila) == ('sprzedajacy', 'lepka')


def test_prior_wazony_en_deleguje_do_prior_strony():
    query, agent_poprzedni, czy_followup = 'where is my parcel', None, False
    assert wagi_stron.prior_wazony(query, agent_poprzedni, 'en', czy_followup) == (
        strony.prior_strony(query, agent_poprzedni, 'en', czy_followup))


def test_brak_komentarzy_w_wygenerowanym_module():
    tresc = Path(wagi_stron.__file__).read_text(encoding='utf-8')
    assert '"""' not in tresc
    poza_naglowkiem = tresc.splitlines()[5:]
    assert not [w for w in poza_naglowkiem if w.lstrip().startswith('#')]
