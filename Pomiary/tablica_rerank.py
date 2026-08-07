# F3 (PLAN_POMIARY_GPU.md): wczytuje outputs/tablica_rerank.json zbudowana przez
# buduj_tablice_wynikow.py, sprawdza odcisk palca korpusu (sha256 chunkow/faiss/bm25) i
# odtwarza dokladnie to, co dzisiaj liczy rankings.search_reranked_multi(), czytajac wyniki
# rerankera z tablicy zamiast wolac model. Uzywane wylacznie w trybie pomiaru.
#
# Wlasnosc, na ktorej to sie opiera: NO_dedup() zwraca zagniezdzone prefiksy tego samego
# rankingu RRF niezaleznie od k_surowe, wiec branie pierwszych k_surowe wpisow z listy
# top_n=30 zapisanej w tablicy jest tozsame z policzeniem NO_dedup od nowa z mniejszym k_surowe.
#
# search_reranked_multi_z_tablicy czyta wpis[agent] wprost, bez .get(agent, []): oblicz_wpis
# (buduj_tablice_wynikow.py) zawsze zapisuje klucz dla kazdego agenta z AGENCI, wiec brak klucza
# tutaj moze oznaczac wylacznie literowke w nazwie agenta, a nie pusty wynik.

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'
OUT_DIR = ROOT / 'outputs'


class NiezgodnyOdcisk(Exception):
    pass


def klucz(lang: str, query: str) -> str:
    """P8: klucz tablicy nosi jezyk, nie sam tekst pytania, zeby identyczny string w dwoch
    jezykach (albo pomylka lang przy odczycie) nie trafial cicho w wpis drugiego jezyka."""
    return f'{lang}|{query}'


def sha256_pliku(sciezka: Path) -> str:
    h = hashlib.sha256()
    with open(sciezka, 'rb') as f:
        for kawalek in iter(lambda: f.read(1 << 20), b''):
            h.update(kawalek)
    return h.hexdigest()


def odciski_korpusu() -> tuple[dict, dict, dict]:
    sha_chunkow = {p.name: sha256_pliku(p) for p in sorted(RAG_DIR.glob('chunks*.json'))}
    sha_faiss = {p.name: sha256_pliku(p) for p in sorted(RAG_DIR.glob('*.faiss'))}
    sha_bm25 = {p.name: sha256_pliku(p) for p in sorted(RAG_DIR.glob('*.bm25'))}
    return sha_chunkow, sha_faiss, sha_bm25


def wczytaj_tablice(sciezka: Path | None = None) -> dict:
    sciezka = sciezka or OUT_DIR / 'tablica_rerank.json'
    with open(sciezka, encoding='utf-8') as f:
        tablica = json.load(f)

    odcisk = tablica['odcisk']
    sha_chunkow, sha_faiss, sha_bm25 = odciski_korpusu()
    if odcisk['sha256_chunkow'] != sha_chunkow:
        raise NiezgodnyOdcisk(f'sha256_chunkow niezgodny miedzy tablica a stanem RAG/: '
                               f'tablica={odcisk["sha256_chunkow"]!r} obecny={sha_chunkow!r}')
    if odcisk['sha256_faiss'] != sha_faiss:
        raise NiezgodnyOdcisk(f'sha256_faiss niezgodny miedzy tablica a stanem RAG/: '
                               f'tablica={odcisk["sha256_faiss"]!r} obecny={sha_faiss!r}')
    if odcisk['sha256_bm25'] != sha_bm25:
        raise NiezgodnyOdcisk(f'sha256_bm25 niezgodny miedzy tablica a stanem RAG/: '
                               f'tablica={odcisk["sha256_bm25"]!r} obecny={sha_bm25!r}')

    return tablica


def search_reranked_multi_z_tablicy(tablica: dict, query: str, agenci: list[str], k: int = 3,
                                     k_surowe: dict | int = 20, lang: str = 'pl') -> list[tuple[dict, float]]:
    top_n = tablica['odcisk']['top_n']
    wpis = tablica['wyniki'].get(klucz(lang, query))
    if wpis is None:
        raise KeyError(f'pytanie nie ma wpisu w tablicy dla lang={lang!r}: {query!r}')

    linki = []
    for agent in agenci:
        k_surowe_agenta = k_surowe[agent] if isinstance(k_surowe, dict) else k_surowe
        if k_surowe_agenta > top_n:
            raise ValueError(f'k_surowe={k_surowe_agenta} przekracza top_n={top_n} zapisane w tablicy')
        for url, score in wpis[agent][:k_surowe_agenta]:
            linki.append(({'agent': agent, 'url': url}, score))

    if not linki:
        return []

    najlepszy = {}
    for chunk, s in linki:
        url = chunk['url']
        if url not in najlepszy or s > najlepszy[url][0]:
            najlepszy[url] = (s, chunk)

    posortowane = sorted(najlepszy.values(), key=lambda p: p[0], reverse=True)
    return [(chunk, score) for score, chunk in posortowane][:k]
