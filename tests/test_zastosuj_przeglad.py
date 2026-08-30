import json

import pytest

import zastosuj_przeglad

URL_ART = 'https://allegro.pl/pomoc/dla-kupujacych/historia-zakupow/gdzie-widac-zakupy-ab12CD'
URL_ALIAS = 'https://allegro.pl/pomoc/dla-kupujacych/konto/jak-odzyskac-dostep-xy99ZZ'


def wpis(decyzja=None, url=None, agent='zakupy', lang='pl', pytanie='pytanie testowe', zgl='AA11BB22'):
    return {
        'zgloszenie': zgl, 'pytanie': pytanie, 'lang': lang, 'agent': agent,
        'etykieta': 'luka_w_bazie', 'odpowiedz_operatora': 'odpowiedz',
        'propozycja_url': None, 'rerank_top1': None, 'decyzja': decyzja, 'url': url,
    }


def pobieracz_notujacy():
    wywolania = []

    def fn(url, agent, lang, rag_dir=None):
        wywolania.append((url, agent, lang))
        return 0

    fn.wywolania = wywolania
    return fn


def test_decyzja_artykul_wola_dociagniecie(tmp_path):
    fn = pobieracz_notujacy()
    wynik = zastosuj_przeglad.zastosuj(
        [wpis('artykul', URL_ART, agent='zakupy', lang='pl')], rag_dir=tmp_path, dociagnij_fn=fn)

    assert fn.wywolania == [(URL_ART, 'zakupy', 'pl')]
    assert wynik['licz']['artykul'] == 1
    assert wynik['licz']['blad'] == 0


def test_decyzja_alias_dokleja_wiersz_do_golden_kolejka(tmp_path):
    wynik = zastosuj_przeglad.zastosuj(
        [wpis('alias', URL_ALIAS, agent='konto', pytanie='ktos wszedl na moje konto')],
        rag_dir=tmp_path, dociagnij_fn=pobieracz_notujacy())

    golden = json.loads((tmp_path / 'golden_kolejka.json').read_text(encoding='utf-8'))
    assert golden == [{
        'query': 'ktos wszedl na moje konto',
        'agent': 'konto',
        'zrodlo_url': 'jak-odzyskac-dostep-xy99ZZ',
    }]
    assert wynik['aliasy'][0]['slug'] == 'jak-odzyskac-dostep-xy99ZZ'


def test_alias_dwa_razy_nie_dubluje_wiersza(tmp_path):
    dane = [wpis('alias', URL_ALIAS, agent='konto', pytanie='to samo pytanie')]
    zastosuj_przeglad.zastosuj(dane, rag_dir=tmp_path, dociagnij_fn=pobieracz_notujacy())
    zastosuj_przeglad.zastosuj(dane, rag_dir=tmp_path, dociagnij_fn=pobieracz_notujacy())

    golden = json.loads((tmp_path / 'golden_kolejka.json').read_text(encoding='utf-8'))
    assert len(golden) == 1


def test_pomijamy_i_pusta_decyzja_licza_sie_osobno_i_nic_nie_robia(tmp_path):
    fn = pobieracz_notujacy()
    wynik = zastosuj_przeglad.zastosuj(
        [wpis('pomijamy', URL_ART), wpis(None, URL_ART), wpis('pomijamy')],
        rag_dir=tmp_path, dociagnij_fn=fn)

    assert wynik['licz']['pomijamy'] == 2
    assert wynik['licz']['nieprzejrzane'] == 1
    assert fn.wywolania == []
    assert not (tmp_path / 'golden_kolejka.json').exists()


def test_decyzja_dzialania_bez_url_to_blad_ale_batch_leci_dalej(tmp_path):
    fn = pobieracz_notujacy()
    wynik = zastosuj_przeglad.zastosuj(
        [wpis('artykul', None, zgl='BRAK01'), wpis('artykul', URL_ART, zgl='OK02')],
        rag_dir=tmp_path, dociagnij_fn=fn)

    assert wynik['licz']['blad'] == 1
    assert wynik['licz']['artykul'] == 1
    assert fn.wywolania == [(URL_ART, 'zakupy', 'pl')]
    assert 'BRAK01' in wynik['bledy'][0]


def test_nieudane_dociagniecie_nie_przerywa_pozostalych(tmp_path):
    def fn(url, agent, lang, rag_dir=None):
        if url == URL_ART:
            raise SystemExit('blad sieci')
        return 0

    wynik = zastosuj_przeglad.zastosuj(
        [wpis('artykul', URL_ART, zgl='ZLE01'),
         wpis('artykul', 'https://allegro.pl/pomoc/dla-kupujacych/konto/inny-artykul-zz00', zgl='DOB02')],
        rag_dir=tmp_path, dociagnij_fn=fn)

    assert wynik['licz']['artykul'] == 1
    assert wynik['licz']['blad'] == 1
    assert 'ZLE01' in wynik['bledy'][0]


def test_na_sucho_nie_pobiera_i_nie_zapisuje(tmp_path):
    fn = pobieracz_notujacy()
    wynik = zastosuj_przeglad.zastosuj(
        [wpis('artykul', URL_ART), wpis('alias', URL_ALIAS, agent='konto')],
        rag_dir=tmp_path, na_sucho=True, dociagnij_fn=fn)

    assert fn.wywolania == []
    assert not (tmp_path / 'golden_kolejka.json').exists()
    assert wynik['licz']['artykul'] == 1
    assert wynik['licz']['alias'] == 1


def test_identyfikator_artykulu_bierze_ostatni_czlon():
    assert zastosuj_przeglad.identyfikator_artykulu(URL_ALIAS) == 'jak-odzyskac-dostep-xy99ZZ'
    assert zastosuj_przeglad.identyfikator_artykulu(URL_ALIAS + '/') == 'jak-odzyskac-dostep-xy99ZZ'


def test_main_bez_pliku_konczy_sie_bledem(tmp_path):
    with pytest.raises(SystemExit) as wy:
        zastosuj_przeglad.main(['--plik', str(tmp_path / 'niema.json')])
    assert wy.value.code


def test_main_na_prawdziwym_pliku_liczy_i_zwraca_kod(tmp_path, monkeypatch):
    plik = tmp_path / 'do_przegladu.json'
    plik.write_text(json.dumps([
        wpis('alias', URL_ALIAS, agent='konto', pytanie='ktos przejal konto'),
        wpis('pomijamy'),
    ], ensure_ascii=False), encoding='utf-8')

    kod = zastosuj_przeglad.main(['--plik', str(plik), '--rag', str(tmp_path)])

    assert kod == 0
    golden = json.loads((tmp_path / 'golden_kolejka.json').read_text(encoding='utf-8'))
    assert golden[0]['zrodlo_url'] == 'jak-odzyskac-dostep-xy99ZZ'
