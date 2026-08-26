import agents_core
import aliasy

SLUG_ODZYSKANIA = 'jak-odzyskac-dostep-do-konta-gdy-nie-mozesz-sie-zalogowac-0KvwX8YAocP'
SLUG_ODZYSKANIA_SPRZEDAZ = 'jak-odzyskac-dostep-do-konta-gdy-nie-mozesz-sie-zalogowac-AgbzAw2ByF4'


def chunk(url: str, tytul: str = 'Tytuł artykułu', tekst: str = 'Treść artykułu.') -> dict:
    return {'url': url, 'tytul': tytul, 'tekst': tekst, 'naglowek': '', 'agent': 'konto'}


def test_chunk_bez_aliasu_zachowuje_dotychczasowy_format():
    # kontrakt wsteczny: dla artykulow bez aliasu tekst do retrievalu musi byc bit w bit taki
    # jak przed zmiana, inaczej caly korpus dostalby nowe embeddingi i nowy indeks BM25
    c = chunk('https://allegro.pl/pomoc/dla-kupujacych/zakupy/jak-kupowac-ABC123')
    assert aliasy.tekst_do_retrievalu(c) == f"{c['tytul']}\n{c['tekst']}"
    assert aliasy.dla_chunku(c) == ''


def test_artykul_o_odzyskaniu_dostaje_alias_miedzy_tytulem_a_trescia():
    c = chunk(f'https://allegro.pl/pomoc/dla-kupujacych/logowanie-i-haslo/{SLUG_ODZYSKANIA}')
    tekst = aliasy.tekst_do_retrievalu(c)
    assert tekst.startswith(c['tytul'] + '\n')
    assert tekst.endswith('\n' + c['tekst'])
    assert 'włamał' in tekst
    assert 'przejął' in tekst


def test_oba_warianty_artykulu_maja_ten_sam_alias():
    kupujacy = chunk(f'https://allegro.pl/pomoc/dla-kupujacych/logowanie-i-haslo/{SLUG_ODZYSKANIA}')
    sprzedaz = chunk(f'https://help.allegro.com/pl/sell/a/{SLUG_ODZYSKANIA_SPRZEDAZ}')
    assert aliasy.dla_chunku(kupujacy)
    assert aliasy.dla_chunku(kupujacy) == aliasy.dla_chunku(sprzedaz)


def test_alias_nie_trafia_do_promptu_modelu():
    # alias jest pomostem slownikowym dla retrievalu, nie trescia artykulu. Gdyby wszedl do
    # kontekstu, model mialby w prompcie zdania, ktorych nie ma w bazie pomocy.
    c = chunk(f'https://allegro.pl/pomoc/dla-kupujacych/logowanie-i-haslo/{SLUG_ODZYSKANIA}')
    kontekst = agents_core.context([c])
    assert c['tekst'] in kontekst
    assert c['tytul'] in kontekst
    assert 'włamał' not in kontekst
    assert 'Nieautoryzowany dostęp' not in kontekst


def test_brak_pol_nie_wywraca_funkcji():
    assert aliasy.tekst_do_retrievalu({}) == '\n'
    assert aliasy.dla_chunku({'url': None}) == ''
