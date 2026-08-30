import random
from pathlib import Path

import numpy as np
import pytest

import aliasy
from lang_config import LANG

RAG_DIR = Path(__file__).resolve().parent.parent / 'RAG'
CHUNKS = RAG_DIR / 'chunks.json'
EMBEDDINGS = RAG_DIR / 'embeddings.npy'

if not CHUNKS.exists() or not EMBEDDINGS.exists():
    pytest.skip('brak RAG/chunks.json albo RAG/embeddings.npy, test wymaga zbudowanego korpusu',
                allow_module_level=True)


def kosinus(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype('float64')
    b = b.astype('float64')
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


# embedder.py --dopisz liczy wektory tylko dla chunkow za koncem macierzy i dokleja je na
# koncu. Gdy nowy chunk kupujacego wejdzie w srodek chunks.json, sprzedaz przesuwa sie o
# kilka pozycji, a asercja w embedder.py porownuje tylko liczbe wierszy, wiec przechodzi.
# Wektory rozjezdzaja sie z chunkami po cichu. Ten test liczy wektor na probce pozycji tym
# samym modelem i prefiksem co embedder.py i sprawdza, ze siedzi na swoim wierszu.
def test_wektory_siedza_na_swoich_chunkach():
    import json

    chunki = json.loads(CHUNKS.read_text(encoding='utf-8'))
    macierz = np.load(EMBEDDINGS)

    assert macierz.shape[0] == len(chunki), (
        f'embeddings.npy ma {macierz.shape[0]} wierszy, a chunks.json {len(chunki)} chunkow')

    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(LANG['pl']['embedder'])
    except Exception as blad:
        pytest.skip(f'model embeddingow niedostepny offline: {blad}')

    prefiks = LANG['pl']['passage_prefix']
    losowy = random.Random(20260830)
    probka = losowy.sample(range(len(chunki)), k=min(6, len(chunki)))

    teksty = [prefiks + aliasy.tekst_do_retrievalu(chunki[i]) for i in probka]
    swieze = model.encode(teksty, batch_size=8)

    for pozycja, wektor in zip(probka, swieze):
        na_swoim = kosinus(wektor, macierz[pozycja])
        assert na_swoim > 0.97, (
            f'chunk {pozycja} ma na swoim wierszu podobienstwo {na_swoim:.3f}, '
            f'wektor nie odpowiada temu chunkowi')

        inne = [p for p in probka if p != pozycja]
        if inne:
            najlepszy_obcy = max(kosinus(wektor, macierz[p]) for p in inne)
            assert na_swoim > najlepszy_obcy, (
                f'chunk {pozycja} pasuje do cudzego wiersza lepiej niz do swojego '
                f'({na_swoim:.3f} <= {najlepszy_obcy:.3f})')
