from pathlib import Path
import tiktoken
import json
import yaml
from collections import Counter

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'

encoder = tiktoken.get_encoding('cl100k_base')

def wczytaj_dokument(sciezka: Path) -> tuple[dict, str]:
    with open(sciezka, 'r', encoding='utf-8') as r:
       
        fragmenty = r.read().split('---')
        metadane = yaml.safe_load(fragmenty[1])
       
        tresc = fragmenty[2].strip()
        return metadane, tresc
  

def podziel_na_chunki(tekst:str, size:int, overlap:int) -> list[str]:
  
    tokeny = encoder.encode(tekst)
    chunki = []
    i = 0

    while i < len(tokeny):
        okno = tokeny[i:i+size]
        chunki.append(encoder.decode(okno))
        i += size - overlap

    return chunki

def chunk_document(sciezka:Path) -> list[dict]:
    
    metadane, tresc = wczytaj_dokument(sciezka)
    
    kawalki = podziel_na_chunki(tresc, CHUNK_SIZE, CHUNK_OVERLAP)
    return [
        {'tekst': k, **metadane}
        for k in kawalki]

if __name__ == '__main__':

    docs_dir = RAG_DIR / 'Fundaments' / 'docs' 
    wszystkie_chunki = []

    for plik_md in docs_dir.rglob('*.md'):
        chunki = chunk_document(plik_md)
        wszystkie_chunki.extend(chunki)

    print(f'plików:~141, chunków łącznie: {len(wszystkie_chunki)}' )
    
    licznik = Counter(c['agent'] for c in wszystkie_chunki)
    sciezka_json = RAG_DIR /'chunks.json'

    with open(sciezka_json, 'w', encoding='utf-8') as w:
        json.dump(wszystkie_chunki, w, ensure_ascii=False, indent=2)

    print(licznik)
