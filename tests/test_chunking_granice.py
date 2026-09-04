import chunking


def test_zdania_scalaja_linie_polamane_przez_linki():
    tekst = 'potrzebujesz\naktywnego\nkonta. Nastepne zdanie.'
    assert chunking.podziel_na_zdania(tekst) == ['potrzebujesz aktywnego konta.', 'Nastepne zdanie.']


def test_skrot_z_kropka_nie_konczy_zdania():
    tekst = 'Sprawdz np. w zakladce Moje zakupy. Potem kliknij.'
    assert chunking.podziel_na_zdania(tekst) == [
        'Sprawdz np. w zakladce Moje zakupy.',
        'Potem kliknij.',
    ]


def test_skrot_m_in_nie_jest_rozbijany():
    tekst = 'Kupujesz m.in. telefony i tablety. Sprzedajesz tez akcesoria.'
    assert chunking.podziel_na_zdania(tekst) == [
        'Kupujesz m.in. telefony i tablety.',
        'Sprzedajesz tez akcesoria.',
    ]


def test_bloki_dziela_sie_po_pustej_linii():
    tekst = 'Pierwszy blok.\nDalej ten sam blok.\n\nDrugi blok.\n\n\nTrzeci blok.'
    assert chunking.podziel_na_bloki(tekst) == [
        'Pierwszy blok.\nDalej ten sam blok.',
        'Drugi blok.',
        'Trzeci blok.',
    ]


def test_zaden_chunk_nie_jest_dluzszy_niz_budzet():
    zdanie = ' '.join(f'slowo{i}' for i in range(400))
    tekst = f'{zdanie}. Drugie zdanie tego samego bloku ma tez sporo slow tutaj wpisanych.'
    for chunk in chunking.podziel_na_chunki(tekst, size=50, overlap=10):
        assert chunking.dlugosc_tokenow(chunk) <= 50


def test_zaden_chunk_nie_jest_w_calosci_zawarty_w_poprzednim():
    zdania = [f'To jest zdanie numer {i} w tekscie testowym.' for i in range(60)]
    tekst = ' '.join(zdania)
    chunki = chunking.podziel_na_chunki(tekst, size=50, overlap=15)
    for i in range(1, len(chunki)):
        assert chunki[i] not in chunki[i - 1]


def test_ciecie_nigdy_nie_wypada_w_srodku_slowa():
    slowa = [f'slowoxyz{i}' for i in range(300)]
    tekst = ' '.join(slowa)
    for chunk in chunking.podziel_na_chunki(tekst, size=30, overlap=5):
        for fragment in chunk.split(' '):
            assert fragment == '' or fragment in slowa


def test_wielki_blok_pokrywa_cala_swoja_tresc_bez_luki():
    blok = ' '.join(f'akapit{i} tresci' for i in range(200)) + '.'
    fragmenty = chunking.rozbij_sekcje(blok, budget=40)
    zlozone = chunking.zloz_fragmenty(fragmenty)
    assert ' '.join(zlozone.split()) == ' '.join(blok.split())


def test_chunk_document_naglowek_prefiks_w_kazdym_chunku(tmp_path):
    naglowki = ['Pierwsza sekcja', 'Druga sekcja']
    tresc = (
        'Pierwsza sekcja\nDruga sekcja\n\n'
        'Pierwsza sekcja\nTresc pierwszej sekcji, wystarczajaco dluga na test.\n\n'
        'Druga sekcja\nTresc drugiej sekcji, rowniez wystarczajaco dluga na test.'
    )
    plik = tmp_path / 'artykul.md'
    plik.write_text(
        '---\nurl: https://allegro.pl/pomoc/test\n---\n' + tresc,
        encoding='utf-8',
    )
    chunki = chunking.chunk_document(plik)
    assert chunki
    for c in chunki:
        assert c['naglowek'] in naglowki
        assert c['tekst'].startswith(c['naglowek'] + '\n')
        assert chunking.dlugosc_tokenow(c['tekst']) <= chunking.CHUNK_SIZE
        rdzen = c['tekst'][len(c['naglowek']) + 1:]
        assert rdzen.strip()
