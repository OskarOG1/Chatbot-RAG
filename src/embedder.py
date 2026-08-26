import argparse
from pathlib import Path
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from lang_config import LANG
import aliasy

BATCH_SIZE = 16
ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / "RAG"

def wczytaj_chunki(sciezka: Path) -> list[dict]:
    with open(sciezka, 'r', encoding='utf-8') as r:
       return json.load(r)

def indeksy_do_przeliczenia(chunki: list[dict], slugi: list[str]) -> list[int]:
    return [i for i, c in enumerate(chunki)
            if aliasy.dla_chunku(c) or any(s in (c.get('url') or '') for s in slugi)]


def przelicz_wybrane(chunki: list[dict], istniejace: np.ndarray, model, cfg: dict,
                     slugi: list[str]) -> np.ndarray:
    if istniejace.shape[0] != len(chunki):
        raise SystemExit(f'embeddings ma {istniejace.shape[0]} wierszy, a chunków jest '
                         f'{len(chunki)}: przelicz całość zamiast podmieniać wiersze')

    indeksy = indeksy_do_przeliczenia(chunki, slugi)
    if not indeksy:
        print('nie ma chunków do przeliczenia')
        return istniejace

    teksty = [cfg['passage_prefix'] + aliasy.tekst_do_retrievalu(chunki[i]) for i in indeksy]
    nowe = model.encode(teksty, batch_size=BATCH_SIZE, show_progress_bar=True)
    embeddings = istniejace.copy()
    embeddings[indeksy] = nowe
    print(f'przeliczono {len(indeksy)} z {len(chunki)} chunków')
    return embeddings


def main(lang: str = 'pl', dopisz: bool = False, przelicz: bool = False,
         slugi: list[str] | None = None):
    cfg = LANG[lang]
    suffix = cfg['suffix']

    sciezka_chunks = RAG_DIR / f"chunks{suffix}.json"
    chunki = wczytaj_chunki(sciezka_chunks)
    sciezka_emb = RAG_DIR / f"embeddings{suffix}.npy"

    model = SentenceTransformer(cfg['embedder'])

    if przelicz:
        if not sciezka_emb.exists():
            raise SystemExit(f'brak {sciezka_emb}, nie ma czego podmieniać')
        embeddings = przelicz_wybrane(chunki, np.load(sciezka_emb), model, cfg, slugi or [])
    elif dopisz and sciezka_emb.exists():
        istniejace = np.load(sciezka_emb)
        nowe_chunki = chunki[istniejace.shape[0]:]
        if nowe_chunki:
            teksty = [cfg['passage_prefix'] + aliasy.tekst_do_retrievalu(c) for c in nowe_chunki]
            nowe_embeddings = model.encode(teksty, batch_size=BATCH_SIZE, show_progress_bar=True)
            embeddings = np.concatenate([istniejace, nowe_embeddings])
        else:
            embeddings = istniejace
    else:
        teksty = [cfg['passage_prefix'] + aliasy.tekst_do_retrievalu(c) for c in chunki]
        embeddings = model.encode(teksty, batch_size=BATCH_SIZE, show_progress_bar=True)

    assert embeddings.shape[0] == len(chunki), \
        f'liczba wierszy embeddingów ({embeddings.shape[0]}) != liczba chunków ({len(chunki)})'

    np.save(sciezka_emb, embeddings)
    print(f'embeddings: {embeddings.shape}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', default='pl', choices=list(LANG))
    parser.add_argument('--dopisz', action='store_true')
    parser.add_argument('--przelicz-aliasy', action='store_true', dest='przelicz',
                        help='przelicza tylko chunki z aliasem i podmienia ich wiersze '
                             'w istniejacym pliku, zamiast liczyc caly korpus od nowa')
    parser.add_argument('--slug', action='append', default=[], dest='slugi',
                        help='dodatkowy slug artykulu do przeliczenia, do uzycia razem '
                             'z --przelicz-aliasy po usunieciu aliasu z aliasy.py')
    args = parser.parse_args()
    main(args.lang, args.dopisz, args.przelicz, args.slugi)
