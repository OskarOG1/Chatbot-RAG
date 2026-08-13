import pytest

import rankings


# O11 (Pomiary/PLAN_ODMOWY.md): korpus ma grupy artykulow o identycznej tresci pod roznymi URL,
# wiec dedup po samym URL przepuszczal duplikaty i marnowal miejsca w oknie k. Ten plik pilnuje
# dedupu po tresci bez korpusu i bez modelu: kandydaci i reranker sa podmienione atrapami.


def chunk(url, tytul, tekst, agent='kupujacy'):
    return {'agent': agent, 'url': url, 'tytul': tytul, 'tekst': tekst, 'naglowek': None}


TRESC_A = ('Jak wystawiac oferty', 'Ofertę wystawisz w zakładce Sprzedaj.')
TRESC_B = ('Jak zwrocic towar', 'Zwrot zgłaszasz w zakładce Moje zakupy.')
TRESC_C = ('Jak zmienic haslo', 'Hasło zmienisz w ustawieniach konta.')
TRESC_D = ('Jak platic', 'Płatność wybierasz w koszyku.')

# Dwie grupy duplikatow (A pod trzema URL, B pod dwoma) plus dwa unikaty. Wyniki rerankera sa
# tak dobrane, zeby najlepszy egzemplarz kazdej grupy nie byl tym pierwszym na liscie.
KANDYDACI = [
    (chunk('https://allegro.pl/pomoc/a-1', *TRESC_A), 0.10),
    (chunk('https://allegro.pl/pomoc/b-1', *TRESC_B), 0.09),
    (chunk('https://allegro.pl/pomoc/a-2', *TRESC_A), 0.08),
    (chunk('https://allegro.pl/pomoc/c-1', *TRESC_C), 0.07),
    (chunk('https://allegro.pl/pomoc/b-2', *TRESC_B), 0.06),
    (chunk('https://allegro.pl/pomoc/a-3', *TRESC_A), 0.05),
    (chunk('https://allegro.pl/pomoc/d-1', *TRESC_D), 0.04),
]
WYNIKI_RERANKERA = [1.0, 2.0, 5.0, 4.0, 6.0, 3.0, 0.5]

NAJLEPSZY_A = 'https://allegro.pl/pomoc/a-2'
NAJLEPSZY_B = 'https://allegro.pl/pomoc/b-2'


class AtrapaRerankera:

    def __init__(self, wyniki):
        self.wyniki = wyniki
        self.wywolania = []

    def predict(self, pary, batch_size=None):
        self.wywolania.append(list(pary))
        return list(self.wyniki)


@pytest.fixture
def atrapa_retrievalu(monkeypatch):
    reranker = AtrapaRerankera(WYNIKI_RERANKERA)
    monkeypatch.setattr(rankings, 'kandydaci_rrf',
                        lambda query, query_emb, agent, k_surowe, lang='pl': list(KANDYDACI))
    monkeypatch.setattr(rankings, 'get_reranker', lambda: reranker)
    return reranker


def szukaj(k):
    return rankings.search_reranked_multi('pytanie', None, ['kupujacy'], k=k, k_surowe=20, lang='pl')


def test_z_grupy_duplikatow_zostaje_wpis_o_najwyzszym_wyniku(atrapa_retrievalu):
    wyniki = szukaj(k=7)
    urle = [c['url'] for c, _ in wyniki]

    assert urle.count(NAJLEPSZY_B) == 1
    assert urle.count(NAJLEPSZY_A) == 1
    assert 'https://allegro.pl/pomoc/a-1' not in urle
    assert 'https://allegro.pl/pomoc/a-3' not in urle
    assert 'https://allegro.pl/pomoc/b-1' not in urle


def test_zwolnione_miejsce_w_oknie_zajmuje_kolejny_rozny_chunk(atrapa_retrievalu):
    wyniki = szukaj(k=4)
    urle = [c['url'] for c, _ in wyniki]

    assert len(urle) == 4
    assert len(set(urle)) == 4
    assert urle == [NAJLEPSZY_B, NAJLEPSZY_A, 'https://allegro.pl/pomoc/c-1',
                    'https://allegro.pl/pomoc/d-1']

    tresci = [(c['tytul'], c['tekst']) for c, _ in wyniki]
    assert len(set(tresci)) == 4


def test_kolejnosc_wynikow_jest_nierosnaca(atrapa_retrievalu):
    wyniki = szukaj(k=7)
    oceny = [s for _, s in wyniki]

    assert oceny == sorted(oceny, reverse=True)
    assert oceny == [6.0, 5.0, 4.0, 0.5]
