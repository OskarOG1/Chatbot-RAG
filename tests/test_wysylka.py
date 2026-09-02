import pytest
from fastapi import HTTPException
from starlette.requests import Request


@pytest.fixture(autouse=True)
def izoluj_log_analytics(monkeypatch, tmp_path):
    import api
    monkeypatch.setattr(api, 'LOG_ANALYTICS', tmp_path / 'log_analytics_test.jsonl')


def zrob_request(client_host: str = '10.0.0.9') -> Request:
    scope = {'type': 'http', 'headers': [], 'client': (client_host, 12345)}
    return Request(scope)


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


FORMY_JEDNEGO_ODBIORCY = [
    'ofiara@example.com',
    'Ofiara<ofiara@example.com>',
    'a<ofiara@example.com>',
    'bb<ofiara@example.com>',
    'Jan Kowalski <ofiara@example.com>',
    '  ofiara@example.com  ',
    'OFIARA@Example.COM',
]


@pytest.mark.parametrize('forma', FORMY_JEDNEGO_ODBIORCY)
def test_zwykly_adres_sprowadza_formy_do_jednego_klucza(forma):
    import api
    assert api.zwykly_adres(forma) == 'ofiara@example.com'


ADRESY_ODRZUCONE = [
    '',
    '   ',
    'ja n@poczta.pl',
    'jan@poczta.pl cokolwiek',
    'bez-malpy.pl',
    'Jan Kowalski <bez-malpy.pl>',
    'Jan Kowalski <>',
    'a@b@c.pl',
]


@pytest.mark.parametrize('adres', ADRESY_ODRZUCONE)
def test_zwykly_adres_odrzuca_smieci(adres):
    import api
    assert api.zwykly_adres(adres) is None


def test_limit_adresu_nie_daje_sie_obejsc_nawiasem_katowym(monkeypatch):
    import api
    monkeypatch.setattr(api, '_wysylki_adres', api.OrderedDict())
    pierwszy = api.zwykly_adres('ofiara@example.com')
    assert api.w_limicie_adresu(pierwszy) is True
    for forma in FORMY_JEDNEGO_ODBIORCY:
        klucz = api.zwykly_adres(forma)
        assert klucz is not None
        assert api.w_limicie_adresu(klucz) is False


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
    api._wysylki_ip.clear()
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
    api._wysylki_ip.clear()
    api._wysylki_adres.clear()
    monkeypatch.setattr(api, 'wyslij_potwierdzenie', lambda *a, **k: 'ABCD1234')
    zadanie = api.WyslijZadanie(email='powtorka@example.com', temat='Temat', tresc='Tresc', kategoria='zwrot')
    odpowiedz = api.send_email(zadanie, zrob_request())
    assert odpowiedz.ticket == 'ABCD1234'
    with pytest.raises(HTTPException) as wyjatek:
        api.send_email(zadanie, zrob_request())
    assert wyjatek.value.status_code == 429


def test_send_email_endpoint_kategoria_za_dluga_zwraca_422():
    from fastapi.testclient import TestClient
    import api
    klient = TestClient(api.app)
    odpowiedz = klient.post('/send-email', json={
        'email': 'osoba@example.com',
        'temat': 'Temat',
        'tresc': 'Tresc',
        'kategoria': 'x' * 201,
    })
    assert odpowiedz.status_code == 422


def test_send_email_endpoint_odrzuca_zly_adres(monkeypatch, resend_env):
    import api
    api._wysylki.clear()
    api._wysylki_ip.clear()
    api._wysylki_adres.clear()
    zadanie = api.WyslijZadanie(email='jan@poczta.pl cokolwiek', temat='Temat', tresc='Tresc')
    with pytest.raises(HTTPException) as wyjatek:
        api.send_email(zadanie, zrob_request())
    assert wyjatek.value.status_code == 422


def test_zly_adres_nie_zuzywa_limitu_wysylek(monkeypatch, resend_env):
    import api
    api._wysylki.clear()
    api._wysylki_ip.clear()
    api._wysylki_adres.clear()
    zadanie = api.WyslijZadanie(email='niepoprawny', temat='Temat', tresc='Tresc')
    with pytest.raises(HTTPException):
        api.send_email(zadanie, zrob_request())
    assert len(api._wysylki) == 0


def test_cooldown_adresu_cofniety_po_nieudanej_wysylce(monkeypatch, resend_env):
    import api
    api._wysylki.clear()
    api._wysylki_ip.clear()
    api._wysylki_adres.clear()

    def rzuca(*a, **k):
        raise RuntimeError('wysylka niedostepna')

    monkeypatch.setattr(api, 'wyslij_potwierdzenie', rzuca)
    zadanie = api.WyslijZadanie(email='powtorka2@example.com', temat='Temat', tresc='Tresc')
    with pytest.raises(HTTPException) as wyjatek:
        api.send_email(zadanie, zrob_request())
    assert wyjatek.value.status_code == 503
    assert 'powtorka2@example.com' not in api._wysylki_adres


def test_korekta_uzywa_podanego_ticketu_i_pomija_temat_bez_korekty(monkeypatch, resend_env):
    import wysylka
    z_falszywym = FalszywyKlient()
    monkeypatch.setattr(wysylka.httpx, 'Client', lambda *a, **k: z_falszywym)
    ticket = wysylka.wyslij_potwierdzenie('klient@example.com', 'zwrot', 'Temat', 'Tresc', ticket='ABCD1234')
    assert ticket == 'ABCD1234'
    assert 'ABCD1234' in z_falszywym.wyslane[0]['subject']
    assert 'korekta' in z_falszywym.wyslane[0]['subject'].lower()


def test_korekta_omija_cooldown_adresu_raz_a_drugi_raz_dostaje_429(monkeypatch, resend_env):
    import api
    api._wysylki.clear()
    api._wysylki_ip.clear()
    api._wysylki_adres.clear()
    api._tickety.clear()
    api.zarejestruj_ticket('ABCD1234', 'powtorka3@example.com')
    monkeypatch.setattr(api, 'wyslij_potwierdzenie', lambda *a, **k: k['ticket'])
    api.w_limicie_adresu('powtorka3@example.com')
    zadanie = api.WyslijZadanie(email='powtorka3@example.com', temat='Temat', tresc='Tresc', ticket='ABCD1234')
    odpowiedz = api.send_email(zadanie, zrob_request())
    assert odpowiedz.ticket == 'ABCD1234'
    with pytest.raises(HTTPException) as wyjatek:
        api.send_email(zadanie, zrob_request())
    assert wyjatek.value.status_code == 429


def test_zadanie_bez_ticketu_nadal_podlega_cooldownowi_adresu(monkeypatch, resend_env):
    import api
    api._wysylki.clear()
    api._wysylki_ip.clear()
    api._wysylki_adres.clear()
    api._tickety.clear()
    api.zarejestruj_ticket('ABCD1234', 'powtorka4@example.com')
    monkeypatch.setattr(api, 'wyslij_potwierdzenie', lambda *a, **k: k['ticket'])
    api.send_email(api.WyslijZadanie(email='powtorka4@example.com', temat='Temat', tresc='Tresc', ticket='ABCD1234'), zrob_request())
    zadanie_bez_ticketu = api.WyslijZadanie(email='powtorka4@example.com', temat='Temat', tresc='Tresc')
    with pytest.raises(HTTPException) as wyjatek:
        api.send_email(zadanie_bez_ticketu, zrob_request())
    assert wyjatek.value.status_code == 429


def test_ticket_niewystawiony_odrzucony(monkeypatch, resend_env):
    import api
    api._wysylki.clear()
    api._wysylki_ip.clear()
    api._wysylki_adres.clear()
    api._tickety.clear()
    monkeypatch.setattr(api, 'wyslij_potwierdzenie', lambda *a, **k: k['ticket'])
    zadanie = api.WyslijZadanie(email='ofiara@example.com', temat='Temat', tresc='Tresc', ticket='DEADBEEF')
    with pytest.raises(HTTPException) as wyjatek:
        api.send_email(zadanie, zrob_request())
    assert wyjatek.value.status_code == 429


def test_ticket_zarejestrowany_na_inny_adres_odrzucony(monkeypatch, resend_env):
    import api
    api._wysylki.clear()
    api._wysylki_ip.clear()
    api._wysylki_adres.clear()
    api._tickety.clear()
    api.zarejestruj_ticket('ABCD1234', 'wlasciciel@example.com')
    monkeypatch.setattr(api, 'wyslij_potwierdzenie', lambda *a, **k: k['ticket'])
    zadanie = api.WyslijZadanie(email='ofiara@example.com', temat='Temat', tresc='Tresc', ticket='ABCD1234')
    with pytest.raises(HTTPException) as wyjatek:
        api.send_email(zadanie, zrob_request())
    assert wyjatek.value.status_code == 429


def test_czesciowa_wysylka_korekty_nie_zuzywa_ticketu_na_stale(monkeypatch, resend_env):
    import httpx
    import api
    import wysylka
    api._wysylki.clear()
    api._wysylki_ip.clear()
    api._wysylki_adres.clear()
    api._tickety.clear()
    api.zarejestruj_ticket('ABCD1234', 'klient@example.com')

    class KlientCzesciowy:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, headers=None, json=None):
            if json.get('to') == 'sprzedawca@ogflow.pl':
                return FalszywaOdpowiedz()
            raise httpx.HTTPError('blad wysylki do klienta')

    monkeypatch.setattr(wysylka.httpx, 'Client', lambda *a, **k: KlientCzesciowy())
    zadanie = api.WyslijZadanie(email='klient@example.com', temat='Temat', tresc='Tresc', ticket='ABCD1234')
    with pytest.raises(HTTPException) as wyjatek:
        api.send_email(zadanie, zrob_request())
    assert wyjatek.value.status_code == 502
    with pytest.raises(HTTPException) as wyjatek2:
        api.send_email(zadanie, zrob_request())
    assert wyjatek2.value.status_code == 502


def test_czesciowa_wysylka_zachowuje_ticket_sprzedawcy(monkeypatch, resend_env):
    import httpx
    import api
    import wysylka
    api._wysylki.clear()
    api._wysylki_ip.clear()
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
        api.send_email(zadanie, zrob_request())
    assert wyjatek.value.status_code == 502
    assert 'klient@example.com' in api._wysylki_adres


# Przy odmowie Resend raise_for_status gubi tresc odpowiedzi, wiec operator panelu widzial
# tylko ogolne "wysylka sie nie powiodla" i nie mial jak odroznic niezweryfikowanej domeny
# od zlego adresu. Powod ma trafic do logu serwera, ale bez adresu odbiorcy, bo adresy
# zgloszen podlegaja retencji i nie moga wyciekac do logu kontenera na stale.
def test_odmowa_resend_trafia_do_logu_bez_adresu_odbiorcy(monkeypatch, resend_env, capsys):
    import httpx
    import wysylka

    class OdmowaResend:
        status_code = 403

        def json(self):
            return {'statusCode': 403, 'name': 'validation_error',
                    'message': 'The ogflow.pl domain is not verified.'}

        def raise_for_status(self):
            raise httpx.HTTPStatusError('403', request=None, response=self)

    class KlientOdmawiajacy:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, headers=None, json=None):
            return OdmowaResend()

    monkeypatch.setattr(wysylka.httpx, 'Client', lambda *a, **k: KlientOdmawiajacy())

    with pytest.raises(httpx.HTTPStatusError):
        wysylka.wyslij_odpowiedz_operatora('pytajacy@example.com', 'pytanie', 'odpowiedz',
                                           '2E248855')

    log = capsys.readouterr().err
    assert 'validation_error' in log
    assert 'domain is not verified' in log
    assert '2E248855' in log
    assert 'pytajacy@example.com' not in log


def test_powod_resend_znosi_odpowiedz_bez_json():
    import wysylka

    class BezJson:
        status_code = 502
        text = 'Bad gateway' * 100

        def json(self):
            raise ValueError('to nie jest json')

    powod = wysylka.powod_resend(BezJson())
    assert powod.startswith('Bad gateway')
    assert len(powod) <= 200
