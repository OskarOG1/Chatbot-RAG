import pytest

import rankings


def chunk(url, tytul, tekst, naglowek='', agent='kupujacy'):
    return {'agent': agent, 'url': url, 'tytul': tytul, 'tekst': tekst, 'naglowek': naglowek}


ARTYKUL = 'https://allegro.pl/pomoc/logowanie'

KORPUS_LOGOWANIE = [
    chunk(ARTYKUL, 'Logowanie', 'Wstep bez naglowka.', naglowek=''),
    chunk(ARTYKUL, 'Logowanie', 'Wpisz haslo w polu logowania.', naglowek='Jak sie logowac haslem'),
    chunk(ARTYKUL, 'Logowanie', 'Klucz dostepu, nie musisz tworzyc osobnego hasla.',
          naglowek='Jak sie logowac kluczem dostepu'),
    chunk(ARTYKUL, 'Logowanie', 'Drugi akapit o kluczu dostepu.',
          naglowek='Jak sie logowac kluczem dostepu'),
    chunk(ARTYKUL, 'Logowanie', 'Trzeci akapit o kluczu dostepu.',
          naglowek='Jak sie logowac kluczem dostepu'),
    chunk(ARTYKUL, 'Logowanie', 'Google, Facebook lub Apple, krok pierwszy.',
          naglowek='Jak sie logowac kontem Google, Facebook lub Apple'),
    chunk(ARTYKUL, 'Logowanie', 'Google, Facebook lub Apple, krok drugi.',
          naglowek='Jak sie logowac kontem Google, Facebook lub Apple'),
]

INNY_ARTYKUL = 'https://allegro.pl/pomoc/platnosci'


class AtrapaRerankera:
    def __init__(self, wyniki):
        self.wyniki = wyniki

    def predict(self, pary, batch_size=None):
        return list(self.wyniki)


@pytest.fixture
def flaga_wlaczona(monkeypatch):
    monkeypatch.setattr(rankings, 'DOSZYCIE_SASIADOW_ON', True)


@pytest.fixture
def korpus_logowanie(monkeypatch):
    monkeypatch.setattr(rankings, 'wczytaj_chunki',
                        lambda agent, lang='pl': list(KORPUS_LOGOWANIE))


def test_flaga_wylaczona_domyslnie():
    assert rankings.DOSZYCIE_SASIADOW_ON is False


def test_domyslny_limit_sasiadow():
    assert rankings.K_SASIEDZI_SEKCJI == 5


def test_dopasowanie_po_parze_adres_tekst_a_nie_po_naglowku(korpus_logowanie):
    zwyciezca = KORPUS_LOGOWANIE[2]

    sasiedzi = rankings.sasiedzi_artykulu(zwyciezca, limit=3)

    teksty = [c['tekst'] for c in sasiedzi]
    assert teksty == [
        'Wpisz haslo w polu logowania.',
        'Klucz dostepu, nie musisz tworzyc osobnego hasla.',
        'Drugi akapit o kluczu dostepu.',
    ]


def test_trzy_chunki_o_identycznym_naglowku_daja_rozne_sasiedztwa(korpus_logowanie):
    identyczny_naglowek = [c for c in KORPUS_LOGOWANIE
                           if c['naglowek'] == 'Jak sie logowac kluczem dostepu']
    assert len(identyczny_naglowek) == 3

    zestawy = [tuple(s['tekst'] for s in rankings.sasiedzi_artykulu(c, limit=3))
              for c in identyczny_naglowek]

    assert len(set(zestawy)) == 3


def test_artykul_krotszy_niz_limit_wchodzi_w_calosci(monkeypatch):
    krotki = [chunk(INNY_ARTYKUL, 'Platnosci', 'Akapit jeden.'),
              chunk(INNY_ARTYKUL, 'Platnosci', 'Akapit dwa.')]
    monkeypatch.setattr(rankings, 'wczytaj_chunki', lambda agent, lang='pl': krotki)

    sasiedzi = rankings.sasiedzi_artykulu(krotki[0], limit=5)

    assert [c['tekst'] for c in sasiedzi] == ['Akapit jeden.', 'Akapit dwa.']


def test_obcy_chunk_wstawiony_miedzy_blok_nie_wchodzi_do_sasiedztwa(monkeypatch):
    obcy = chunk('https://allegro.pl/pomoc/obcy', 'Obcy', 'Tekst obcego artykulu.')
    tablica = [KORPUS_LOGOWANIE[0], KORPUS_LOGOWANIE[1], obcy,
              KORPUS_LOGOWANIE[2], KORPUS_LOGOWANIE[3]]
    monkeypatch.setattr(rankings, 'wczytaj_chunki', lambda agent, lang='pl': tablica)

    sasiedzi = rankings.sasiedzi_artykulu(KORPUS_LOGOWANIE[2], limit=3)

    assert all(c['url'] == ARTYKUL for c in sasiedzi)
    assert obcy not in sasiedzi


def test_rozszerzany_jest_tylko_czolowy_wpis_kazdej_strony(monkeypatch, flaga_wlaczona,
                                                            korpus_logowanie):
    monkeypatch.setattr(rankings, 'K_SASIEDZI_SEKCJI', 3)
    platnosci_url = 'https://allegro.pl/pomoc/platnosci-kupujacy'
    sprzedaz_url = 'https://allegro.pl/pomoc/sprzedaz-lepsza'

    kandydaci = {
        'kupujacy': [(chunk(ARTYKUL, 'Logowanie', KORPUS_LOGOWANIE[2]['tekst'],
                            naglowek='Jak sie logowac kluczem dostepu'), 1.0),
                    (chunk(platnosci_url, 'Platnosci', 'Inny artykul kupujacego.'), 0.5)],
        'sprzedaz': [(chunk(sprzedaz_url, 'Sprzedaz', 'Wygrywajacy artykul sprzedazy.',
                            agent='sprzedaz'), 3.0)],
    }
    monkeypatch.setattr(rankings, 'kandydaci_rrf',
                        lambda query, query_emb, agent, k_surowe, lang='pl': list(kandydaci[agent]))
    monkeypatch.setattr(rankings, 'get_reranker',
                        lambda: AtrapaRerankera([s for para in kandydaci.values() for _, s in para]))

    wyniki = rankings.search_reranked_multi('pytanie', None, ['kupujacy', 'sprzedaz'],
                                             k=None, k_surowe=20, lang='pl')

    zwyciezca_strony = [c for c, s in wyniki if c['url'] == ARTYKUL]
    assert len(zwyciezca_strony) == 3

    przegrany_kupujacego = [c for c, s in wyniki if c['url'] == platnosci_url]
    assert len(przegrany_kupujacego) == 1

    sprzedaz_chunki = [c for c, s in wyniki if c['url'] == sprzedaz_url]
    assert len(sprzedaz_chunki) == 1


def test_dedup_po_tresci_nie_skleja_doszytych_sasiadow(monkeypatch, flaga_wlaczona,
                                                        korpus_logowanie):
    monkeypatch.setattr(rankings, 'K_SASIEDZI_SEKCJI', 3)
    monkeypatch.setattr(rankings, 'kandydaci_rrf',
                        lambda query, query_emb, agent, k_surowe, lang='pl':
                        [(KORPUS_LOGOWANIE[2], 1.0)])
    monkeypatch.setattr(rankings, 'get_reranker', lambda: AtrapaRerankera([1.0]))

    wyniki = rankings.search_reranked_multi('pytanie', None, ['kupujacy'],
                                             k=None, k_surowe=20, lang='pl')

    assert len(wyniki) == 3


def test_kolejnosc_sasiadow_odpowiada_kolejnosci_czytania(monkeypatch, flaga_wlaczona,
                                                           korpus_logowanie):
    monkeypatch.setattr(rankings, 'K_SASIEDZI_SEKCJI', 3)
    monkeypatch.setattr(rankings, 'kandydaci_rrf',
                        lambda query, query_emb, agent, k_surowe, lang='pl':
                        [(KORPUS_LOGOWANIE[2], 1.0)])
    monkeypatch.setattr(rankings, 'get_reranker', lambda: AtrapaRerankera([1.0]))

    wyniki = rankings.search_reranked_multi('pytanie', None, ['kupujacy'],
                                             k=None, k_surowe=20, lang='pl')

    teksty = [c['tekst'] for c, _ in wyniki]
    assert teksty == [
        'Wpisz haslo w polu logowania.',
        'Klucz dostepu, nie musisz tworzyc osobnego hasla.',
        'Drugi akapit o kluczu dostepu.',
    ]


def test_flaga_wylaczona_nie_rozszerza(monkeypatch, korpus_logowanie):
    monkeypatch.setattr(rankings, 'kandydaci_rrf',
                        lambda query, query_emb, agent, k_surowe, lang='pl':
                        [(KORPUS_LOGOWANIE[2], 1.0)])
    monkeypatch.setattr(rankings, 'get_reranker', lambda: AtrapaRerankera([1.0]))

    wyniki = rankings.search_reranked_multi('pytanie', None, ['kupujacy'],
                                             k=None, k_surowe=20, lang='pl')

    assert len(wyniki) == 1
