import pytest
from fastapi import HTTPException

ADRESY = [
    ('jan@poczta.pl', True),
    ('ja n@poczta.pl', False),
    ('jan@poczta.pl cokolwiek', False),
    ('', False),
    ('a' * 244 + '@poczta.pl', True),
]


@pytest.mark.parametrize('adres,oczekiwany', ADRESY)
def test_fullmatch_adresu(adres, oczekiwany):
    import api
    assert bool(api.EMAIL_WZORZEC.fullmatch(adres)) == oczekiwany


def test_wyslij_potwierdzenie_bez_konfiguracji_rzuca(monkeypatch):
    import wysylka
    monkeypatch.delenv('RESEND_API_KEY', raising=False)
    monkeypatch.delenv('RESEND_FROM_EMAIL', raising=False)
    monkeypatch.delenv('DEMO_SPRZEDAWCA_EMAIL', raising=False)
    with pytest.raises(RuntimeError):
        wysylka.wyslij_potwierdzenie('a@b.pl', None, 'Temat', 'Tresc')


def test_sekcja_wysylka_ma_te_same_klucze_pl_en():
    import lang_config
    assert set(lang_config.LANG['pl']['wysylka']) == set(lang_config.LANG['en']['wysylka'])


class FalszywaOdpowiedz:
    status_code = 200

    def raise_for_status(self):
        return None


class FalszywyKlient:
    def __init__(self, *args, **kwargs):
        self.wyslane = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, headers=None, json=None):
        self.wyslane.append(json)
        return FalszywaOdpowiedz()


@pytest.fixture
def resend_env(monkeypatch):
    monkeypatch.setenv('RESEND_API_KEY', 'test_key')
    monkeypatch.setenv('RESEND_FROM_EMAIL', 'demo@ogflow.pl')
    monkeypatch.setenv('DEMO_SPRZEDAWCA_EMAIL', 'sprzedawca@ogflow.pl')


@pytest.mark.parametrize('lang', ['pl', 'en'])
def test_potwierdzenie_w_jezyku_zadania(monkeypatch, resend_env, lang):
    import wysylka
    z_falszywym = FalszywyKlient()
    monkeypatch.setattr(wysylka.httpx, 'Client', lambda *a, **k: z_falszywym)
    wysylka.wyslij_potwierdzenie('klient@example.com', 'zwrot', 'Temat', 'Tresc', lang=lang)
    fraza = wysylka.LANG[lang]['wysylka']['klauzula']
    assert len(z_falszywym.wyslane) == 2
    assert fraza in z_falszywym.wyslane[1]['text']
    assert 'klient@example.com' in z_falszywym.wyslane[0]['text']


def test_cooldown_adresu_blokuje_powtorke_a_potem_puszcza(monkeypatch):
    import api
    api._wysylki_adres.clear()
    zegar = [1000.0]
    monkeypatch.setattr(api.time, 'time', lambda: zegar[0])
    assert api.w_limicie_adresu('Test@Adres.pl') is True
    assert api.w_limicie_adresu('test@adres.pl') is False
    zegar[0] += api.LIMIT_WYSYLKA_ADRES_S + 1
    assert api.w_limicie_adresu('test@adres.pl') is True


def test_sufit_dobowy_wysylki(monkeypatch):
    import api
    api._wysylki.clear()
    zegar = [2000.0]
    monkeypatch.setattr(api.time, 'time', lambda: zegar[0])
    monkeypatch.setattr(api, 'LIMIT_WYSYLKA_DZIEN', 3)
    monkeypatch.setattr(api, 'LIMIT_WYSYLKA_MIN', 100)
    for _ in range(3):
        assert api.w_limicie_wysylki() is True
        zegar[0] += 120
    assert api.w_limicie_wysylki() is False


def test_send_email_endpoint_cooldown_adresu(monkeypatch, resend_env):
    import api
    api._wysylki.clear()
    api._wysylki_adres.clear()
    monkeypatch.setattr(api, 'wyslij_potwierdzenie', lambda *a, **k: 'ABCD1234')
    zadanie = api.WyslijZadanie(email='powtorka@example.com', temat='Temat', tresc='Tresc', kategoria='zwrot')
    odpowiedz = api.send_email(zadanie)
    assert odpowiedz.ticket == 'ABCD1234'
    with pytest.raises(HTTPException) as wyjatek:
        api.send_email(zadanie)
    assert wyjatek.value.status_code == 429


def test_send_email_endpoint_odrzuca_zly_adres(monkeypatch, resend_env):
    import api
    api._wysylki.clear()
    api._wysylki_adres.clear()
    zadanie = api.WyslijZadanie(email='jan@poczta.pl cokolwiek', temat='Temat', tresc='Tresc')
    with pytest.raises(HTTPException) as wyjatek:
        api.send_email(zadanie)
    assert wyjatek.value.status_code == 422


def test_zly_adres_nie_zuzywa_limitu_wysylek(monkeypatch, resend_env):
    import api
    api._wysylki.clear()
    api._wysylki_adres.clear()
    zadanie = api.WyslijZadanie(email='niepoprawny', temat='Temat', tresc='Tresc')
    with pytest.raises(HTTPException):
        api.send_email(zadanie)
    assert len(api._wysylki) == 0


def test_cooldown_adresu_cofniety_po_nieudanej_wysylce(monkeypatch, resend_env):
    import api
    api._wysylki.clear()
    api._wysylki_adres.clear()

    def rzuca(*a, **k):
        raise RuntimeError('wysylka niedostepna')

    monkeypatch.setattr(api, 'wyslij_potwierdzenie', rzuca)
    zadanie = api.WyslijZadanie(email='powtorka2@example.com', temat='Temat', tresc='Tresc')
    with pytest.raises(HTTPException) as wyjatek:
        api.send_email(zadanie)
    assert wyjatek.value.status_code == 503
    assert 'powtorka2@example.com' not in api._wysylki_adres


def test_czesciowa_wysylka_zachowuje_ticket_sprzedawcy(monkeypatch, resend_env):
    import httpx
    import api
    import wysylka
    api._wysylki.clear()
    api._wysylki_adres.clear()

    class KlientCzesciowy:
        def __init__(self, *a, **k):
            self.wywolanie = 0

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, headers=None, json=None):
            self.wywolanie += 1
            if self.wywolanie == 1:
                return FalszywaOdpowiedz()
            raise httpx.HTTPError('blad wysylki do klienta')

    monkeypatch.setattr(wysylka.httpx, 'Client', lambda *a, **k: KlientCzesciowy())
    zadanie = api.WyslijZadanie(email='klient@example.com', temat='Temat', tresc='Tresc')
    with pytest.raises(HTTPException) as wyjatek:
        api.send_email(zadanie)
    assert wyjatek.value.status_code == 502
    assert 'klient@example.com' in api._wysylki_adres
