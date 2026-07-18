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

        fragmenty = r.read().split('---', 2)
        metadane = yaml.safe_load(fragmenty[1])

        tresc = fragmenty[2].strip()
        return metadane, tresc


def podziel_na_chunki(tekst: str, size: int, overlap: int) -> list[str]:

    tokeny = encoder.encode(tekst)
    chunki = []
    i = 0

    while i < len(tokeny):
        okno = tokeny[i:i + size]
        chunki.append(encoder.decode(okno))
        i += max(1, size - overlap)

    return chunki


def podziel_na_sekcje(tresc: str) -> list[tuple[str | None, str]]:

    linie = tresc.split('\n')
    i = 0
    while i < len(linie) and not linie[i].strip():
        i += 1
    start = i
    while i < len(linie) and linie[i].strip():
        i += 1

    kandydat = [l.strip() for l in linie[start:i] if l.strip()]
    reszta = linie[i:]
    zbior = {l.strip() for l in reszta if l.strip()}

    if not (len(kandydat) >= 2 and all(naglowek in zbior for naglowek in kandydat)):
        return [(None, tresc)]

    granice = []
    szukany = 0
    for idx, linia in enumerate(reszta):
        if szukany < len(kandydat) and linia.strip() == kandydat[szukany]:
            granice.append((idx, kandydat[szukany]))
            szukany += 1

    sekcje = []
    intro = '\n'.join(reszta[:granice[0][0]]).strip()
    if intro:
        sekcje.append((None, intro))
    for j, (idx, naglowek) in enumerate(granice):
        koniec = granice[j + 1][0] if j + 1 < len(granice) else len(reszta)
        sekcje.append((naglowek, '\n'.join(reszta[idx + 1:koniec]).strip()))
    return sekcje


def chunk_document(sciezka: Path) -> list[dict]:

    metadane, tresc = wczytaj_dokument(sciezka)

    chunki = []
    for naglowek, tekst_sekcji in podziel_na_sekcje(tresc):
        if not tekst_sekcji:
            continue
        prefiks = f'{naglowek}\n' if naglowek else ''
        rezerwa = len(encoder.encode(prefiks))
        size = max(CHUNK_OVERLAP + 1, CHUNK_SIZE - rezerwa)
        for kawalek in podziel_na_chunki(tekst_sekcji, size, CHUNK_OVERLAP):
            chunki.append({'tekst': prefiks + kawalek, 'naglowek': naglowek or '', **metadane})
    return chunki


if __name__ == '__main__':

    docs_dir = RAG_DIR / 'docs'
    wszystkie_chunki = []
    pliki = 0

    for plik_md in docs_dir.rglob('*.md'):
        try:

            wszystkie_chunki.extend(chunk_document(plik_md))
            pliki += 1

        except Exception as e:
            print(f'Pominięto {plik_md.name}: {e}')

    print(f'plików: {pliki} chunków łącznie: {len(wszystkie_chunki)}')

    licznik = Counter(c['agent'] for c in wszystkie_chunki)
    sciezka_json = RAG_DIR / 'chunks.json'

    with open(sciezka_json, 'w', encoding='utf-8') as w:
        json.dump(wszystkie_chunki, w, ensure_ascii=False, indent=2)

    print(licznik)
