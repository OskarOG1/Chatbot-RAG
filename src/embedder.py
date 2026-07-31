import argparse
from pathlib import Path
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from lang_config import LANG

BATCH_SIZE = 16
ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / "RAG"

def wczytaj_chunki(sciezka: Path) -> list[dict]:
    with open(sciezka, 'r', encoding='utf-8') as r:
       return json.load(r)

def main(lang: str = 'pl', dopisz: bool = False):
    cfg = LANG[lang]
    suffix = cfg['suffix']

    sciezka_chunks = RAG_DIR / f"chunks{suffix}.json"
    chunki = wczytaj_chunki(sciezka_chunks)
    sciezka_emb = RAG_DIR / f"embeddings{suffix}.npy"

    model = SentenceTransformer(cfg['embedder'])

    if dopisz and sciezka_emb.exists():
        istniejace = np.load(sciezka_emb)
        nowe_chunki = chunki[istniejace.shape[0]:]
        if nowe_chunki:
            teksty = [f"{cfg['passage_prefix']}{c['tytul']}\n{c['tekst']}" for c in nowe_chunki]
            nowe_embeddings = model.encode(teksty, batch_size=BATCH_SIZE, show_progress_bar=True)
            embeddings = np.concatenate([istniejace, nowe_embeddings])
        else:
            embeddings = istniejace
    else:
        teksty = [f"{cfg['passage_prefix']}{c['tytul']}\n{c['tekst']}" for c in chunki]
        embeddings = model.encode(teksty, batch_size=BATCH_SIZE, show_progress_bar=True)

    assert embeddings.shape[0] == len(chunki), \
        f'liczba wierszy embeddingów ({embeddings.shape[0]}) != liczba chunków ({len(chunki)})'

    np.save(sciezka_emb, embeddings)
    print(f'embeddings: {embeddings.shape}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', default='pl', choices=list(LANG))
    parser.add_argument('--dopisz', action='store_true')
    args = parser.parse_args()
    main(args.lang, args.dopisz)
