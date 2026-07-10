from pathlib import Path
import json
import numpy as np 
from sentence_transformers import SentenceTransformer

MODEL_NAME = 'sdadas/mmlw-retrieval-roberta-base'
BATCH_SIZE = 16
ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / "RAG"

def wczytaj_chunki(sciezka: Path) -> list[dict]:
    with open(sciezka, 'r', encoding='utf-8') as r:
       return json.load(r)
    
def main():
     
    sciezka_chunks = RAG_DIR / 'chunks.json'
    chunki = wczytaj_chunki(sciezka_chunks)
    teksty = [f"{c['tytul']} \n {c['tekst']}" for c in chunki]
    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(teksty, batch_size=BATCH_SIZE, show_progress_bar=True)
    sciezka_emb = RAG_DIR / 'embeddings.npy'
    
    np.save(sciezka_emb, embeddings)
    print(f'embeddings: {embeddings.shape}') 

if __name__ == '__main__':
    main()