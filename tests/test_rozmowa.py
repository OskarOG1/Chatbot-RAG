import pipeline
import rozmowa


def test_klasa_tury_powitanie_samo():
    klasa, reszta = rozmowa.klasa_tury('cześć', [], None, 'pl')
    assert klasa == 'powitanie'


def test_klasa_tury_powitanie_z_tresciowym_pytaniem_odcina_prefiks():
    klasa, reszta = rozmowa.klasa_tury('cześć, jak zmienić hasło', [], None, 'pl')
    assert klasa is None
    assert reszta == 'jak zmienić hasło'


def test_klasa_tury_powitanie_dluzsze_bez_tresci_zostaje_powitaniem():
    klasa, reszta = rozmowa.klasa_tury('dzień dobry, mam pytanie', [], None, 'pl')
    assert klasa == 'powitanie'


def test_klasa_tury_podziekowanie():
    klasa, reszta = rozmowa.klasa_tury('dziękuję, pomogło', [], None, 'pl')
    assert klasa == 'podziekowanie'


def test_klasa_tury_meta():
    klasa, reszta = rozmowa.klasa_tury('kim jesteś?', [], None, 'pl')
    assert klasa == 'meta'


def test_klasa_tury_fraza_meta_zatopiona_w_dlugim_tekscie_nie_jest_meta():
    query = 'słuchaj no dobra powiedz mi szczerze kim jesteś naprawdę proszę'
    klasa, reszta = rozmowa.klasa_tury(query, [], None, 'pl')
    assert klasa is None


def test_klasa_tury_poza_domena_nie_jest_rozmowa():
    klasa, reszta = rozmowa.klasa_tury('jaka jest stolica Francji', [], None, 'pl')
    assert klasa is None


def test_klasa_tury_kontrola_rag_nie_jest_rozmowa():
    klasa, reszta = rozmowa.klasa_tury('ile mam czasu na zwrot', [], None, 'pl')
    assert klasa is None


HISTORIA = [{'role': 'user', 'content': 'jak zmienić hasło'},
            {'role': 'assistant', 'content': 'x'}]


def test_klasa_tury_sterowanie_wymaga_historii_i_agenta():
    klasa, reszta = rozmowa.klasa_tury('nie rozumiem', [], None, 'pl')
    assert klasa is None
    klasa, reszta = rozmowa.klasa_tury('nie rozumiem', HISTORIA, 'konto', 'pl')
    assert klasa == 'sterowanie'


def test_klasa_tury_sterowanie_potwierdzenie_wymaga_kontekstu():
    klasa, reszta = rozmowa.klasa_tury('tak', [], None, 'pl')
    assert klasa is None
    klasa, reszta = rozmowa.klasa_tury('tak', HISTORIA, 'konto', 'pl')
    assert klasa == 'sterowanie'


def test_podklasa_sterowania():
    assert rozmowa.podklasa_sterowania('rozwiń to', 'pl') == 'rozwin'
    assert rozmowa.podklasa_sterowania('możesz prościej?', 'pl') == 'prosciej'
    assert rozmowa.podklasa_sterowania('tak', 'pl') == 'potwierdzenie'


def test_pipeline_powitanie_daje_szablon_bez_wyszukiwania(monkeypatch):
    def wybuchnij(*a, **k):
        raise AssertionError('wyszukiwanie nie powinno sie odbyc dla powitania')
    monkeypatch.setattr(pipeline, 'search_reranked_multi', wybuchnij)
    monkeypatch.setattr(pipeline, 'embed_query', wybuchnij)

    wynik = pipeline.run('cześć', lang='pl')
    assert wynik['agent'] == ''
    assert wynik['tryb'] == 'rozmowa'
    assert wynik['sources'] == []
    assert wynik['answer'] == pipeline.LANG['pl']['rozmowa']['powitanie']


def test_pipeline_powitanie_z_pytaniem_idzie_do_rag(monkeypatch, atrapa_pipeline):
    atrapa_pipeline.ustaw_etap('kupujacy', tekst='Odpowiedz o hasle [1].')
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)

    wynik = pipeline.run('cześć, jak zmienić hasło', strona='kupujacy',
                         bez_korekty=True, sedzia=False, lang='pl')
    assert wynik.get('powod_odmowy') is None
    assert wynik['agent'] == 'kupujacy'
    assert wynik['tryb'] == 'rag'


def test_pipeline_poza_domena_nadal_odmawia(monkeypatch, atrapa_pipeline):
    for pytanie in ('jaka jest stolica Francji', 'napisz wiersz o jesieni'):
        wynik = pipeline.run(pytanie, strona='kupujacy', bez_korekty=True, sedzia=False, lang='pl')
        assert wynik['powod_odmowy'] == 'prog_rerank'
        assert wynik['agent'] == ''


def test_pipeline_sterowanie_uzywa_poprzedniego_pytania_i_stylu(monkeypatch, atrapa_pipeline):
    atrapa_pipeline.ustaw_etap('kupujacy', tekst='Rozwiniete wyjasnienie licytacji [1].')
    monkeypatch.setattr(pipeline, 'pokrycie_idf', lambda tekst, chunks, lang: 1.0)

    historia = [{'role': 'user', 'content': 'jak działa licytowanie'},
                {'role': 'assistant', 'content': 'Licytowanie polega na...'}]
    wynik = pipeline.run('rozwiń to', history=historia, agent_poprzedni='zakupy',
                         strona='kupujacy', bez_korekty=True, sedzia=False, lang='pl')
    assert wynik.get('powod_odmowy') is None
    assert wynik['agent'] == 'kupujacy'
    assert atrapa_pipeline.wyszukiwania[0]['zapytanie'] == 'jak działa licytowanie'
    assert atrapa_pipeline.generacje[0]['query'] == 'rozwiń to'
    assert atrapa_pipeline.generacje[0]['styl'] == 'rozwin'


def test_pipeline_hi_i_ok_daja_szablon_zamiast_guard_za_krotkie():
    wynik_hi = pipeline.run('hi', lang='en')
    assert wynik_hi['tryb'] == 'rozmowa'
    assert wynik_hi.get('powod_odmowy') is None

    wynik_ok = pipeline.run('ok', lang='pl')
    assert wynik_ok['tryb'] == 'rozmowa'
    assert wynik_ok.get('powod_odmowy') is None


def test_pipeline_ab_nadal_wpada_w_guard_za_krotkie():
    wynik = pipeline.run('ab', lang='pl')
    assert wynik['powod_odmowy'] == 'guard_za_krotkie'
