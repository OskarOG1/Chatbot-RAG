import sys
import threading
import time
from collections import Counter
from itertools import count
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

KORPUS_DOSTEPNY = (SRC.parent / 'RAG' / 'chunks_kupujacy.json').exists()
wymaga_korpusu = pytest.mark.skipif(
    not KORPUS_DOSTEPNY,
    reason='wymaga pelnego korpusu RAG (chunks_kupujacy.json), niedostepnego w CI'
)


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'wymaga_korpusu: test wymaga pelnego korpusu RAG, pomijany bez niego')


@pytest.fixture(autouse=True)
def maly_slownik(monkeypatch):
    import spell
    monkeypatch.setattr(spell, 'SLOWNIK_CACHE',
                        Counter({'konto': 100, 'haslo': 40, 'dom': 50, 'zwrot': 30}))


@pytest.fixture
def chunk():
    licznik = count(1)

    def zbuduj(agent, score=0.0, url=None, tekst='Treść przykładowego artykułu pomocy.',
               tytul='Artykuł pomocy'):
        n = next(licznik)
        return ({'agent': agent, 'url': url or f'https://allegro.pl/pomoc/artykul-{agent}-{n}',
                 'tytul': tytul, 'tekst': tekst, 'naglowek': None}, score)
    return zbuduj


class AtrapaPipeline:

    def __init__(self, monkeypatch, chunk):
        self.monkeypatch = monkeypatch
        self.chunk = chunk
        self.sekcje = {}
        self.odpowiedzi = {}
        self.sedzia_wyniki = {}
        self.sedzia_pominiete = set()
        self.tokeny = {}
        self.przerwane = []
        self.sedzia_gotowy = threading.Event()
        self.kategoria_maila = None
        self.mail_szkic = {'tekst': 'Szkic maila.'}
        self.przepisane_zapytanie = None
        self.wywolania = Counter()
        self.wyszukiwania = []
        self.generacje = []
        self.historie_odpowiedzi = []
        self.style_odpowiedzi = []
        self.ogolna_tekst = None
        self.tokeny_ogolne = []

        import pipeline
        monkeypatch.setattr(pipeline, 'embed_query', lambda lang, tekst: None)
        monkeypatch.setattr(pipeline, 'search_reranked_multi', self.wyszukaj)
        monkeypatch.setattr(pipeline, 'answer_stream', self.generuj)
        monkeypatch.setattr(pipeline, 'czy_kontekst_odpowiada', self.osadz_sedzia)
        monkeypatch.setattr(pipeline, 'sedzia_kategoria_mail', self.kategoria)
        monkeypatch.setattr(pipeline, 'napisz_email', self.mail)
        monkeypatch.setattr(pipeline, 'przepisz_zapytanie', self.przepisz)
        monkeypatch.setattr(pipeline, 'answer_ogolna_stream', self.generuj_ogolna)

    def ustaw_etap(self, strona, chunki=None, tekst=None, cytaty=None, sedzia=True):
        import strony
        agent = strony.STRONA_DO_AGENTA[strona]
        self.sekcje[agent] = chunki if chunki is not None else [self.chunk(agent)]
        self.sedzia_wyniki[agent] = sedzia
        if tekst is not None:
            self.odpowiedzi[agent] = {'tekst': tekst, 'cytaty': cytaty or []}
        return agent

    def wyszukaj(self, zapytanie, emb, agenci, k, k_surowe, lang='pl'):
        agent = agenci[0]
        self.wywolania['search'] += 1
        self.wywolania[f'search:{agent}'] += 1
        self.wyszukiwania.append({'zapytanie': zapytanie, 'agent': agent})
        return list(self.sekcje.get(agent, []))

    def generuj(self, query, agent, chunks, bielik_model, history, lang, styl=None):
        self.wywolania['answer'] += 1
        self.wywolania[f'answer:{agent}'] += 1
        self.generacje.append({'query': query, 'agent': agent, 'styl': styl, 'history': history})
        self.historie_odpowiedzi.append(history)
        self.style_odpowiedzi.append(styl)
        odp = self.odpowiedzi.get(agent)
        tokeny = self.tokeny.get(agent) or []
        try:
            if tokeny:
                self.sedzia_gotowy.wait(timeout=2.0)
                time.sleep(0.02)
            for tekst in tokeny:
                yield {'typ': 'token', 'tekst': tekst}
            if odp is not None:
                yield {'typ': 'koniec', 'dane': odp}
        except GeneratorExit:
            self.przerwane.append(agent)
            raise

    def osadz_sedzia(self, zapytanie, chunks, bielik_model=None, lang='pl', stan=None):
        agent = chunks[0][0]['agent'] if chunks else None
        self.wywolania['sedzia'] += 1
        self.wywolania[f'sedzia:{agent}'] += 1
        if stan is not None and agent in self.sedzia_pominiete:
            stan['sedzia_pominiety'] = True
        try:
            return self.sedzia_wyniki.get(agent, True)
        finally:
            self.sedzia_gotowy.set()

    def kategoria(self, history, chunks, lang):
        self.wywolania['kategoria'] += 1
        return self.kategoria_maila

    def mail(self, history, chunks, lang, kategoria):
        self.wywolania['mail'] += 1
        return self.mail_szkic

    def przepisz(self, query, history, bielik_model, lang):
        return self.przepisane_zapytanie if self.przepisane_zapytanie is not None else query

    def generuj_ogolna(self, query, history=None, bielik_model=None, lang='pl'):
        self.wywolania['ogolna'] += 1
        for tekst in self.tokeny_ogolne:
            yield {'typ': 'token', 'tekst': tekst}
        if self.ogolna_tekst is not None:
            yield {'typ': 'koniec', 'dane': self.ogolna_tekst}


@pytest.fixture
def atrapa_pipeline(monkeypatch, chunk, tmp_path):
    import pipeline
    monkeypatch.setattr(pipeline, 'LOG_TRUDNE', tmp_path / 'trudne_test.jsonl')
    idf = {'konto': 1.0, 'haslo': 2.0, 'zwrot': 1.5}
    monkeypatch.setitem(pipeline.IDF_DANE, 'pl', (idf, 3.0, True))
    return AtrapaPipeline(monkeypatch, chunk)
