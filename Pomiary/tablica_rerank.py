# F3 (PLAN_POMIARY_GPU.md): wczytuje outputs/tablica_rerank.json zbudowana przez
# buduj_tablice_wynikow.py, sprawdza odcisk palca korpusu (sha256 chunkow/faiss/bm25) i
# odtwarza dokladnie to, co dzisiaj liczy rankings.search_reranked_multi(), czytajac wyniki
# rerankera z tablicy zamiast wolac model. Uzywane wylacznie w trybie pomiaru.
#
# Wlasnosc, na ktorej to sie opiera: kandydaci_rrf() zwraca zagniezdzone prefiksy tego samego
# rankingu RRF niezaleznie od k_surowe, wiec branie pierwszych k_surowe wpisow z listy
# top_n=30 zapisanej w tablicy jest tozsame z policzeniem kandydaci_rrf od nowa z mniejszym k_surowe.
#
# search_reranked_multi_z_tablicy czyta wpis[agent] wprost, bez .get(agent, []): oblicz_wpis
# (buduj_tablice_wynikow.py) zawsze zapisuje klucz dla kazdego agenta z AGENCI, wiec brak klucza
# tutaj moze oznaczac wylacznie literowke w nazwie agenta, a nie pusty wynik.
#
# Z4 (PLAN_PRZEGLAD_O8_O11_O12.md): po O11 produkcja dedupuje dwa razy, po url i po tresci,
# a replay dedupowal tylko po url, wiec kazdy pomiar puszczony przez tablice dostawal ranking
# sprzed O11 i twierdzil, ze to produkcja. Wpis tablicy nosi teraz skrot tresci obok url i score
# (SCHEMAT=2), a sam dedup jest wolany z rankings.dedup_najlepszy, czyli z tej samej funkcji,
# ktorej uzywa produkcja. Rozjazd moze juz wyniknac tylko ze zmiany kluczy, nie z kopii regulki.
#
# Bramka schematu stoi w search_reranked_multi_z_tablicy, a nie we wczytaj_tablice, i to jest
# swiadome zawezenie. Stary schemat klamie wylacznie o RANKINGU, bo tylko ranking przechodzi
# przez dedup. Konsument czytajacy z wpisu surowe wyniki rerankera (measure_mc1_top1.py bierze
# lista[0][1], czyli top1 per sekcja) nie dotyka dedupu w ogole, wiec O11 go nie zmienia
# i blokowanie go byloby falszywym alarmem. Odcisk korpusu zostaje we wczytaj_tablice, bo ten
# dotyczy kazdego odczytu.

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'
OUT_DIR = ROOT / 'outputs'
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

SCHEMAT = 2


class NiezgodnyOdcisk(Exception):
    pass


def sha_tresci(chunk: dict) -> str:
    return hashlib.sha1(f'{chunk["tytul"]}\n{chunk["tekst"]}'.encode('utf-8')).hexdigest()


def klucz_sha(chunk: dict) -> str:
    return chunk['sha']


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
    import rankings

    odcisk = tablica['odcisk']
    if odcisk.get('schemat') != SCHEMAT:
        raise NiezgodnyOdcisk(
            f'schemat tablicy {odcisk.get("schemat")!r} zamiast {SCHEMAT}: tablica pochodzi sprzed '
            f'dedupu tresci (O11) i odtworzylaby ranking sprzed tej zmiany. Przebuduj ja przez '
            f'Pomiary/buduj_tablice_wynikow.py na tym samym urzadzeniu, na ktorym powstala '
            f'(odcisk["urzadzenie"]={odcisk.get("urzadzenie")!r}): kolejnosc kandydatow RRF nie '
            f'jest odtwarzalna miedzy GPU a CPU, patrz naglowek Pomiary/wzbogac_tablice_sha.py')

    top_n = odcisk['top_n']
    wpis = tablica['wyniki'].get(klucz(lang, query))
    if wpis is None:
        raise KeyError(f'pytanie nie ma wpisu w tablicy dla lang={lang!r}: {query!r}')

    ocenione = []
    for agent in agenci:
        k_surowe_agenta = k_surowe[agent] if isinstance(k_surowe, dict) else k_surowe
        if k_surowe_agenta > top_n:
            raise ValueError(f'k_surowe={k_surowe_agenta} przekracza top_n={top_n} zapisane w tablicy')
        for url, score, sha in wpis[agent][:k_surowe_agenta]:
            ocenione.append(({'agent': agent, 'url': url, 'sha': sha}, score))

    if not ocenione:
        return []

    unikalne = rankings.dedup_najlepszy(ocenione, rankings.klucz_url)
    unikalne = rankings.dedup_najlepszy(unikalne, klucz_sha)

    return sorted(unikalne, key=lambda p: p[1], reverse=True)[:k]
