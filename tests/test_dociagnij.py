import json

import pytest

import dociagnij

WZOR_URL = 'https://allegro.pl/pomoc/dla-kupujacych/historia-zakupow/lista-zakupow-ab12CD'


def artykul_atrapa(url=WZOR_URL, agent='zakupy'):
    return {
        'url': url,
        'tytul': 'Lista zakupow w zakladce Moje zakupy',
        'tresc': 'Tresc artykulu pomocy wystarczajaco dluga, zeby cos w niej bylo.',
        'agent': agent,
        'podslug': 'historia-zakupow',
    }


def pobieracz_zwraca(artykul):
    wywolania = []

    def pobierz(url, agent):
        wywolania.append((url, agent))
        if artykul is None:
            return None
        dane = dict(artykul)
        dane['url'] = url
        dane['agent'] = agent
        return dane

    pobierz.wywolania = wywolania
    return pobierz


@pytest.mark.parametrize('zly_url', [
    'https://allegro.pl/pomoc/dla-kupujacych/tylko-kategoria',
    'https://allegro.pl/pomoc/dla-kupujacych/historia-zakupow/artykul/nadmiarowy-czlon',
    'https://allegro.pl/pomoc/dla-kupujacych/historia-zakupow/',
    'https://example.com/pomoc/dla-kupujacych/historia-zakupow/artykul-ab12',
    'http://allegro.pl/pomoc/dla-kupujacych/historia-zakupow/artykul-ab12',
    'https://allegro.pl/pomoc/historia-zakupow/artykul-ab12',
    '',
])
def test_adres_spoza_wzorca_konczy_sie_bledem_i_nic_nie_zapisuje(tmp_path, zly_url):
    licznik_pobran = []

    def pobierz(url, agent):
        licznik_pobran.append(url)
        return artykul_atrapa()

    with pytest.raises(SystemExit) as wyjscie:
        dociagnij.wykonaj(zly_url, 'zakupy', 'pl', rag_dir=tmp_path, pobieracz=pobierz)

    assert wyjscie.value.code
    assert not licznik_pobran
    assert not (tmp_path / 'links.json').exists()
    assert not list(tmp_path.glob('docs*/**/*.md'))


def test_pobranie_nieudane_konczy_sie_bledem_bez_pliku_i_bez_linku(tmp_path):
    pobierz = pobieracz_zwraca(None)

    with pytest.raises(SystemExit) as wyjscie:
        dociagnij.wykonaj(WZOR_URL, 'zakupy', 'pl', rag_dir=tmp_path, pobieracz=pobierz)

    assert wyjscie.value.code
    assert pobierz.wywolania == [(WZOR_URL, 'zakupy')]
    assert not (tmp_path / 'links.json').exists()
    assert not list(tmp_path.glob('docs*/**/*.md'))


def test_sciezka_udana_zapisuje_md_i_dopisuje_link(tmp_path):
    pobierz = pobieracz_zwraca(artykul_atrapa())

    kod = dociagnij.wykonaj(WZOR_URL, 'zakupy', 'pl', rag_dir=tmp_path, pobieracz=pobierz)

    assert kod == 0
    plik_md = tmp_path / 'docs' / 'zakupy' / 'lista-zakupow-ab12CD.md'
    assert plik_md.exists()
    tresc = plik_md.read_text(encoding='utf-8')
    assert 'Tresc artykulu pomocy' in tresc
    assert WZOR_URL in tresc

    links = json.loads((tmp_path / 'links.json').read_text(encoding='utf-8'))
    assert links == {'zakupy': [WZOR_URL]}


def test_agent_sprzedaz_i_lang_en_trafia_do_wlasciwego_katalogu(tmp_path):
    url = 'https://help.allegro.com/en/sell/a/jak-wystawic-oferte-xy99ZZ'
    pobierz = pobieracz_zwraca(artykul_atrapa(url=url, agent='sprzedaz'))

    dociagnij.wykonaj(url, 'sprzedaz', 'en', rag_dir=tmp_path, pobieracz=pobierz)

    assert (tmp_path / 'docs_sprzedaz_en' / 'sprzedaz' / 'jak-wystawic-oferte-xy99ZZ.md').exists()
    links = json.loads((tmp_path / 'links_sprzedaz_en.json').read_text(encoding='utf-8'))
    assert links == {'sprzedaz': [url]}


def test_adres_help_allegro_sell_jest_akceptowany_i_trafia_do_links_sprzedaz(tmp_path):
    url = 'https://help.allegro.com/pl/sell/a/jak-zlozyc-polecenie-zaplaty-AbC123'
    pobierz = pobieracz_zwraca(artykul_atrapa(url=url, agent='sprzedaz'))

    kod = dociagnij.wykonaj(url, 'sprzedaz', 'pl', rag_dir=tmp_path, pobieracz=pobierz)

    assert kod == 0
    assert (tmp_path / 'docs_sprzedaz' / 'sprzedaz' / 'jak-zlozyc-polecenie-zaplaty-AbC123.md').exists()
    links = json.loads((tmp_path / 'links_sprzedaz_pl.json').read_text(encoding='utf-8'))
    assert links == {'sprzedaz': [url]}


@pytest.mark.parametrize('zly_url', [
    'https://help.allegro.com/pl/sell/c/kategoria-nie-artykul',
    'https://help.allegro.com/pl/buy/a/to-kupujacy-nie-sprzedaz',
    'https://help.allegro.com/de/sell/a/zly-jezyk-AbC1',
    'https://help.allegro.com/pl/sell/a/artykul/nadmiar',
])
def test_zle_odmiany_help_allegro_sa_odrzucane(tmp_path, zly_url):
    with pytest.raises(SystemExit):
        dociagnij.wykonaj(zly_url, 'sprzedaz', 'pl', rag_dir=tmp_path,
                          pobieracz=pobieracz_zwraca(artykul_atrapa()))


def test_powtorne_uruchomienie_nie_dubluje_linku_i_zglasza_nadpisanie(tmp_path, capsys):
    pobierz = pobieracz_zwraca(artykul_atrapa())

    dociagnij.wykonaj(WZOR_URL, 'zakupy', 'pl', rag_dir=tmp_path, pobieracz=pobierz)
    capsys.readouterr()
    dociagnij.wykonaj(WZOR_URL, 'zakupy', 'pl', rag_dir=tmp_path, pobieracz=pobierz)
    wyjscie = capsys.readouterr().out

    assert 'Nadpisuje istniejacy artykul' in wyjscie
    assert 'pomijam dopisanie' in wyjscie
    links = json.loads((tmp_path / 'links.json').read_text(encoding='utf-8'))
    assert links == {'zakupy': [WZOR_URL]}


def test_istniejacy_link_nie_zmienia_kolejnosci_pozostalych(tmp_path):
    sciezka_links = tmp_path / 'links.json'
    zawartosc_przed = {
        'konto': [
            'https://allegro.pl/pomoc/dla-kupujacych/konto/pierwszy-aa11',
            'https://allegro.pl/pomoc/dla-kupujacych/konto/drugi-bb22',
        ],
        'zakupy': [WZOR_URL],
    }
    sciezka_links.write_text(
        json.dumps(zawartosc_przed, ensure_ascii=False, indent=2), encoding='utf-8')
    tekst_przed = sciezka_links.read_text(encoding='utf-8')

    dopisano = dociagnij.dopisz_link(sciezka_links, 'zakupy', WZOR_URL)

    assert dopisano is False
    assert sciezka_links.read_text(encoding='utf-8') == tekst_przed


def test_nowy_link_ladnie_dokleja_sie_na_koncu_listy_agenta(tmp_path):
    sciezka_links = tmp_path / 'links.json'
    sciezka_links.write_text(
        json.dumps({'zakupy': ['https://allegro.pl/pomoc/dla-kupujacych/konto/stary-aa11']},
                   ensure_ascii=False, indent=2),
        encoding='utf-8')

    dopisano = dociagnij.dopisz_link(sciezka_links, 'zakupy', WZOR_URL)

    assert dopisano is True
    links = json.loads(sciezka_links.read_text(encoding='utf-8'))
    assert links['zakupy'] == [
        'https://allegro.pl/pomoc/dla-kupujacych/konto/stary-aa11',
        WZOR_URL,
    ]


def test_polski_adres_z_lang_en_nie_zapisuje_nic(tmp_path):
    pobierz = pobieracz_zwraca(artykul_atrapa())

    with pytest.raises(SystemExit) as wyjscie:
        dociagnij.wykonaj(WZOR_URL, 'zakupy', 'en', rag_dir=tmp_path, pobieracz=pobierz)

    assert wyjscie.value.code
    assert pobierz.wywolania == []
    assert not list(tmp_path.glob('docs*/**/*.md'))


def test_adres_sprzedazowy_w_innym_jezyku_niz_lang_jest_odrzucany(tmp_path):
    url = 'https://help.allegro.com/pl/sell/a/jak-wystawic-oferte-xy99ZZ'
    pobierz = pobieracz_zwraca(artykul_atrapa(url=url, agent='sprzedaz'))

    with pytest.raises(SystemExit):
        dociagnij.wykonaj(url, 'sprzedaz', 'en', rag_dir=tmp_path, pobieracz=pobierz)

    assert pobierz.wywolania == []


def test_pusta_tresc_nie_zapisuje_pliku_ani_linku(tmp_path):
    pusty = artykul_atrapa()
    pusty['tresc'] = '\n  \n'
    pobierz = pobieracz_zwraca(pusty)

    with pytest.raises(SystemExit) as wyjscie:
        dociagnij.wykonaj(WZOR_URL, 'zakupy', 'pl', rag_dir=tmp_path, pobieracz=pobierz)

    assert wyjscie.value.code
    assert not (tmp_path / 'links.json').exists()
    assert not list(tmp_path.glob('docs*/**/*.md'))
