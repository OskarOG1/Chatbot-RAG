import threading
import time
from concurrent.futures import ThreadPoolExecutor

import ogolna
import pipeline


def test_odmowa_sedziego_nie_wypuszcza_tokenow(atrapa_pipeline):
    agent = atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz.', sedzia=False)
    atrapa_pipeline.tokeny[agent] = ['Aby ', 'zalozyc ', 'konto ', 'wejdz ', 'na ']
    zdarzenia = list(pipeline.run_stream('jakies pytanie o konto', strona='kupujacy',
                                          bez_korekty=True, sedzia=True, lang='pl'))
    assert not any(z['typ'] == 'token' for z in zdarzenia)
    assert zdarzenia[-1]['typ'] == 'wynik'
    assert zdarzenia[-1]['dane']['powod_odmowy'] == 'sedzia'
    assert agent in atrapa_pipeline.przerwane


def test_przerwanie_zostawia_slad_w_cechach(atrapa_pipeline):
    agent = atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz.', sedzia=False)
    atrapa_pipeline.tokeny[agent] = ['Aby ', 'zalozyc ', 'konto ', 'wejdz ', 'na ']
    wynik = pipeline.run('jakies pytanie o konto', strona='kupujacy',
                         bez_korekty=True, sedzia=True, lang='pl')
    assert wynik['powod_odmowy'] == 'sedzia'
    assert wynik['cechy']['generacja_przerwana'] is True
    assert wynik['cechy']['tokeny_stracone'] >= 1


def test_zgoda_sedziego_przepuszcza_wszystkie_tokeny(monkeypatch, atrapa_pipeline):
    agent = atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz.', sedzia=True)
    atrapa_pipeline.tokeny[agent] = ['raz ', 'dwa ', 'trzy ']
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)
    zdarzenia = list(pipeline.run_stream('jakies pytanie o konto', strona='kupujacy',
                                          bez_korekty=True, sedzia=True, lang='pl'))
    teksty = [z['tekst'] for z in zdarzenia if z['typ'] == 'token']
    assert teksty == ['raz ', 'dwa ', 'trzy ']
    assert atrapa_pipeline.przerwane == []


def test_odmowa_pokrycia_wysyla_reset(monkeypatch, atrapa_pipeline):
    a = atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz A.', sedzia=True)
    atrapa_pipeline.tokeny[a] = ['A1 ', 'A2 ']
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 0.0)
    zdarzenia = list(pipeline.run_stream('jakies pytanie o konto', strona='kupujacy',
                                          bez_korekty=True, sedzia=True, lang='pl',
                                          warstwa_ogolna=False))
    typy = [z['typ'] for z in zdarzenia]
    assert typy.count('reset') == 1
    indeks = typy.index('reset')
    assert not any(z['typ'] == 'token' for z in zdarzenia[indeks:])
    assert zdarzenia[-1]['typ'] == 'wynik'
    assert zdarzenia[-1]['dane']['powod_odmowy'] == 'pokrycie'


def test_reset_pochodzi_z_warstwy_ogolnej_gdy_sekcja_nie_wyslala_tokenow(monkeypatch, atrapa_pipeline, chunk):
    atrapa_pipeline.ustaw_etap('kupujacy', chunki=[chunk('kupujacy', score=-10.0)])
    atrapa_pipeline.tokeny_ogolne = ['C1 ']
    atrapa_pipeline.ogolna_tekst = 'Odpowiedz ogolna.'
    monkeypatch.setattr(ogolna, 'temat_zablokowany', lambda query, lang='pl': None)
    monkeypatch.setattr(ogolna, 'pytanie_o_allegro', lambda query, lang='pl': False)
    monkeypatch.setattr(ogolna, 'sprawdz_odpowiedz', lambda surowa, lang='pl':
                         {'tekst': surowa, 'konkrety': None, 'powod': 'ogolna_temat'})
    zdarzenia = list(pipeline.run_stream('jakies pytanie o konto', strona='kupujacy',
                                          bez_korekty=True, sedzia=True, lang='pl'))
    typy = [z['typ'] for z in zdarzenia]
    assert typy.count('reset') == 1
    assert zdarzenia[-1]['typ'] == 'wynik'
    assert zdarzenia[-1]['dane']['powod_odmowy'] == 'prog_rerank'
    assert zdarzenia[-1]['dane']['powod_ogolna'] == 'ogolna_temat'


def test_sukces_bez_resetu(monkeypatch, atrapa_pipeline):
    a = atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz A.', sedzia=True)
    atrapa_pipeline.tokeny[a] = ['A1 ', 'A2 ']
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)
    zdarzenia = list(pipeline.run_stream('jakies pytanie o konto', strona='kupujacy',
                                          bez_korekty=True, sedzia=True, lang='pl'))
    typy = [z['typ'] for z in zdarzenia]
    assert 'reset' not in typy
    teksty = [z['tekst'] for z in zdarzenia if z['typ'] == 'token']
    assert teksty == ['A1 ', 'A2 ']


def podmien_wolnego_sedziego(monkeypatch, atrapa_pipeline, opoznienie=0.15):
    oryginal = atrapa_pipeline.osadz_sedzia

    def wolny(zapytanie, chunks, bielik_model=None, lang='pl', stan=None):
        time.sleep(opoznienie)
        return oryginal(zapytanie, chunks, bielik_model, lang, stan)

    monkeypatch.setattr(pipeline, 'czy_kontekst_odpowiada', wolny)
    atrapa_pipeline.sedzia_gotowy.set()


def test_przekroczony_bufor_puszcza_tokeny(monkeypatch, atrapa_pipeline):
    monkeypatch.setattr(pipeline, 'SEDZIA_BUFOR_MAX', 2)
    atrapa_pipeline.ustaw_etap('kupujacy')

    def generuj_bez_oczekiwania(query, agent, chunks, bielik_model, history, lang, styl=None):
        for tekst in ['a ', 'b ', 'c ', 'd ']:
            yield {'typ': 'token', 'tekst': tekst}
        yield {'typ': 'koniec', 'dane': {'tekst': 'Odpowiedz.', 'cytaty': []}}

    monkeypatch.setattr(pipeline, 'answer_stream', generuj_bez_oczekiwania)

    class OpakowanyEgzekutor:
        def __init__(self, wewnetrzny):
            self.wewnetrzny = wewnetrzny
            self.ostatni = None

        def submit(self, *args, **kwargs):
            self.ostatni = self.wewnetrzny.submit(*args, **kwargs)
            return self.ostatni

    prawdziwy = ThreadPoolExecutor(max_workers=1)
    opakowany = OpakowanyEgzekutor(prawdziwy)
    monkeypatch.setattr(pipeline, 'EGZEKUTOR_SEDZIEGO', opakowany)

    blokada = threading.Event()

    def sedzia_zablokowany(zapytanie, chunks, bielik_model=None, lang='pl', stan=None):
        blokada.wait(timeout=2.0)
        return True

    monkeypatch.setattr(pipeline, 'czy_kontekst_odpowiada', sedzia_zablokowany)
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)

    zdarzenia = pipeline.run_stream('jakies pytanie o konto', strona='kupujacy',
                                     bez_korekty=True, sedzia=True, lang='pl')
    teksty = []
    try:
        for z in zdarzenia:
            if z['typ'] == 'token':
                teksty.append(z['tekst'])
                if len(teksty) == 2:
                    break
        assert teksty == ['a ', 'b ']
        assert opakowany.ostatni is not None and not opakowany.ostatni.done()
    finally:
        blokada.set()
        teksty += [z['tekst'] for z in zdarzenia if z['typ'] == 'token']

    assert teksty == ['a ', 'b ', 'c ', 'd ']


def test_odmowa_po_optymistycznym_wyslaniu(monkeypatch, atrapa_pipeline):
    monkeypatch.setattr(pipeline, 'SEDZIA_BUFOR_MAX', 2)
    agent = atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz.', sedzia=False)
    atrapa_pipeline.tokeny[agent] = ['a ', 'b ', 'c ', 'd ']
    podmien_wolnego_sedziego(monkeypatch, atrapa_pipeline)
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)
    zdarzenia = list(pipeline.run_stream('jakies pytanie o konto', strona='kupujacy',
                                          bez_korekty=True, sedzia=True, lang='pl'))
    typy = [z['typ'] for z in zdarzenia]
    teksty = [z['tekst'] for z in zdarzenia if z['typ'] == 'token']
    assert teksty == ['a ', 'b ', 'c ', 'd ']
    assert typy.count('reset') == 1
    assert typy.index('reset') > typy.index('token')
    assert zdarzenia[-1]['typ'] == 'wynik'
    assert zdarzenia[-1]['dane']['powod_odmowy'] == 'sedzia'
    cechy = zdarzenia[-1]['dane']['cechy']
    assert cechy['sedzia_ok'] is False
    assert not cechy.get('generacja_przerwana')
    assert cechy['tokeny_stracone'] == len(teksty)


def test_werdykt_niezdazony_w_krotkim_limicie_przepuszcza(monkeypatch, atrapa_pipeline):
    monkeypatch.setattr(pipeline, 'SEDZIA_BUFOR_MAX', 2)
    monkeypatch.setattr(pipeline, 'SEDZIA_CZEKANIE_KONCOWE', 0.01)
    agent = atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz.', sedzia=True)
    atrapa_pipeline.tokeny[agent] = ['a ', 'b ', 'c ', 'd ']
    podmien_wolnego_sedziego(monkeypatch, atrapa_pipeline, opoznienie=1.0)
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)
    zdarzenia = list(pipeline.run_stream('jakies pytanie o konto', strona='kupujacy',
                                          bez_korekty=True, sedzia=True, lang='pl'))
    typy = [z['typ'] for z in zdarzenia]
    teksty = [z['tekst'] for z in zdarzenia if z['typ'] == 'token']
    assert teksty == ['a ', 'b ', 'c ', 'd ']
    assert 'reset' not in typy
    assert zdarzenia[-1]['typ'] == 'wynik'
    assert not zdarzenia[-1]['dane'].get('powod_odmowy')
    assert 'sedzia' in zdarzenia[-1]['dane']['bramki_pominiete']


def test_anulowanie_sedziego_po_porzuceniu(monkeypatch, atrapa_pipeline):
    class OpakowanyEgzekutor:
        def __init__(self, wewnetrzny):
            self.wewnetrzny = wewnetrzny
            self.ostatni = None

        def submit(self, *args, **kwargs):
            self.ostatni = self.wewnetrzny.submit(*args, **kwargs)
            return self.ostatni

    prawdziwy = ThreadPoolExecutor(max_workers=1)
    opakowany = OpakowanyEgzekutor(prawdziwy)
    monkeypatch.setattr(pipeline, 'EGZEKUTOR_SEDZIEGO', opakowany)
    blokada = threading.Event()
    prawdziwy.submit(blokada.wait)
    try:
        atrapa_pipeline.ustaw_etap('kupujacy', sedzia=True)
        gen = pipeline.run_stream('jakies pytanie o konto', strona='kupujacy',
                                   bez_korekty=True, sedzia=True, lang='pl')
        for _ in range(20):
            next(gen)
            if opakowany.ostatni is not None:
                break
        else:
            raise AssertionError('sedzia nie zostal zlecony w rozsadnej liczbie zdarzen')
        gen.close()
        assert opakowany.ostatni.cancelled()
    finally:
        blokada.set()
        prawdziwy.shutdown(wait=True)
