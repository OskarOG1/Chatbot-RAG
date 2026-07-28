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

def main(lang: str = 'pl'):
    cfg = LANG[lang]
    suffix = cfg['suffix']

    sciezka_chunks = RAG_DIR / f"chunks{suffix}.json"
    chunki = wczytaj_chunki(sciezka_chunks)
    teksty = [f"{cfg['passage_prefix']}{c['tytul']}\n{c['tekst']}" for c in chunki]

    model = SentenceTransformer(cfg['embedder'])
    embeddings = model.encode(teksty, batch_size=BATCH_SIZE, show_progress_bar=True)
    sciezka_emb = RAG_DIR / f"embeddings{suffix}.npy"

    np.save(sciezka_emb, embeddings)
    print(f'embeddings: {embeddings.shape}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', default='pl', choices=list(LANG))
    args = parser.parse_args()
    main(args.lang)
