import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

import aliasy

SLUG_TERMIN = 'jak-zwrocic-zakup-i-odeslac-produkt-do-sprzedajacego-GDeq5VeKRHD'


def test_alias_z_kotwica_omija_chunk_bez_kotwicy():
    z_kotwica = {'url': f'https://x/{SLUG_TERMIN}', 'tekst': 'masz maksymalnie 14 dni na odeslanie'}
    bez_kotwicy = {'url': f'https://x/{SLUG_TERMIN}', 'tekst': 'jak zapakowac przesylke zwrotna'}
    assert aliasy.dla_chunku(z_kotwica)
    assert aliasy.dla_chunku(bez_kotwicy) == ''


def test_alias_bez_kotwicy_dziala_na_calym_artykule():
    chunk = {'url': 'https://x/jak-odzyskac-dostep-do-konta-gdy-nie-mozesz-sie-zalogowac-0KvwX8YAocP',
             'tekst': 'dowolny tekst bez zadnej kotwicy'}
    assert aliasy.dla_chunku(chunk)


def test_alias_terminu_siedzi_tylko_na_chunkach_z_terminem():
    chunki = json.loads((Path(__file__).resolve().parent.parent / 'RAG' / 'chunks.json')
                        .read_text(encoding='utf-8'))
    artykul = [c for c in chunki if SLUG_TERMIN in (c.get('url') or '')]
    assert artykul, 'artykul o zwrocie zniknal z korpusu'
    z_aliasem = [c for c in artykul if aliasy.dla_chunku(c)]
    assert 0 < len(z_aliasem) < len(artykul), (
        'alias ma pokrywac czesc chunkow artykulu, nie zero i nie wszystkie: '
        f'{len(z_aliasem)} z {len(artykul)}')
