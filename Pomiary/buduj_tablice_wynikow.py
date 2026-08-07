# Buduje outputs/tablica_rerank.json wg schematu z PLAN_POMIARY_GPU.md: dla kazdego pytania
# i agenta (kupujacy/sprzedaz) top_n kandydatow w kolejnosci RRF (przed dedupem po url), kazdy
# z wlasnym surowym wynikiem rerankera. Kolejnosc RRF nie zalezy od prioru, wiec dowolny wariant
# kwoty k_surowe <= top_n moze wziac prefiks tej listy i odtworzyc dokladnie to, co dzisiaj liczy
# search_reranked_multi() w rankings.py - patrz Pomiary/tablica_rerank.py (F3), ktory to robi.
#
# Uzycie (docelowo na serwerze GPU):
#     python buduj_tablice_wynikow.py --top-n 30 --wsad 128
#
# Lokalny test architektury (Kolejnosc krok 1 z PLAN_POMIARY_GPU.md), bez karty:
#     python buduj_tablice_wynikow.py --n-testowe 50
#
# Bez --n-testowe skrypt wymaga CUDA i przerywa bez niej (Faza 0: zeby nie splacic pelnego
# przebiegu w cenie GPU za obliczenia na CPU).

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import torch
import sentence_transformers
import faiss
from sentence_transformers import SentenceTransformer

import rankings
from rankings import RERANKER_NAME, MODEL_NAME, get_reranker
from lang_config import LANG
from measure import GOLDEN, OOD
from measure_en import golden_en, ood_en
from measure_sprzedaz import golden_sprzedaz

RAG_DIR = ROOT / 'RAG'
OUT_DIR = ROOT / 'outputs'
AGENCI = ('kupujacy', 'sprzedaz')


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


def wczytaj_pytania() -> list[tuple[str, str]]:
    """Zwraca pary (pytanie, lang). Zrodla: pytania_realne.jsonl (PL, PLAN_BAZA_PYTAN.md) oraz
    cztery zestawy golden plus OOD (PLAN_ROUTING_NAPRAWA.md), zeby krok 6 (macierz ramion na
    golden) mial z czego czytac bez ponownego wywolania rerankera."""
    pytania: dict[str, str] = {}

    plik_realne = RAG_DIR / 'pytania_realne.jsonl'
    with open(plik_realne, encoding='utf-8') as f:
        for linia in f:
            w = json.loads(linia)
            pytania[w['pytanie']] = 'pl'

    for g in GOLDEN + golden_sprzedaz('pl') + OOD:
        query = g['query'] if isinstance(g, dict) else g
        pytania[query] = 'pl'
    for g in list(golden_en()) + golden_sprzedaz('en') + list(ood_en()):
        query = g['query'] if isinstance(g, dict) else g
        pytania[query] = 'en'

    return sorted(pytania.items())


def oblicz_wpis(query: str, lang: str, embedery: dict, reranker, top_n: int, wsad: int) -> dict:
    """Jeden wpis tablicy: dla kazdego agenta top_n kandydatow w kolejnosci RRF (NO_dedup),
    kazdy z wlasnym wynikiem rerankera. Wydzielone z main(), zeby Pomiary/weryfikuj_tablice.py
    moglo policzyc te sama rzecz dla garstki pytan bez przechodzenia przez caly plik wejsciowy."""
    emb = embedery[lang].encode([LANG[lang]['query_prefix'] + query]).astype('float32')
    faiss.normalize_L2(emb)

    wpis = {}
    for agent in AGENCI:
        kandydaci = rankings.NO_dedup(query, emb, agent, top_n, lang)
        if not kandydaci:
            wpis[agent] = []
            continue
        pary = [(query, chunk['tekst']) for chunk, _ in kandydaci]
        scores = reranker.predict(pary, batch_size=wsad)
        wpis[agent] = [[chunk['url'], float(s)] for (chunk, _), s in zip(kandydaci, scores)]
    return wpis


def zapisz(sciezka: Path, wyniki: dict, sha_chunkow: dict, sha_faiss: dict, sha_bm25: dict,
           urzadzenie: str, top_n: int) -> None:
    dane = {
        'odcisk': {
            'reranker': RERANKER_NAME,
            'embedder_pl': MODEL_NAME,
            'embedder_en': LANG['en']['embedder'],
            'sha256_chunkow': sha_chunkow,
            'sha256_faiss': sha_faiss,
            'sha256_bm25': sha_bm25,
            'urzadzenie': urzadzenie,
            'torch': torch.__version__,
            'sentence_transformers': sentence_transformers.__version__,
            'top_n': top_n,
            'czas_utc': datetime.now(timezone.utc).isoformat(),
        },
        'wyniki': wyniki,
    }
    OUT_DIR.mkdir(exist_ok=True)
    sciezka.write_text(json.dumps(dane, ensure_ascii=False), encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--top-n', type=int, default=30)
    parser.add_argument('--wsad', type=int, default=128)
    parser.add_argument('--n-testowe', type=int, default=0,
                         help='ogranicza do pierwszych N pytan, do lokalnego testu architektury bez GPU')
    args = parser.parse_args()

    ma_cuda = torch.cuda.is_available()
    print(f'torch.cuda.is_available()={ma_cuda}')
    if not ma_cuda and not args.n_testowe:
        print('BRAK KARTY CUDA i brak --n-testowe: przerywam, zeby nie liczyc pelnej tablicy na CPU.')
        sys.exit(1)

    urzadzenie = f'cuda:{torch.cuda.current_device()}' if ma_cuda else 'cpu'
    print(f'urzadzenie={urzadzenie} torch={torch.__version__} '
          f'sentence_transformers={sentence_transformers.__version__}')
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False

    sha_chunkow, sha_faiss, sha_bm25 = odciski_korpusu()
    pytania = wczytaj_pytania()
    if args.n_testowe:
        pytania = pytania[:args.n_testowe]
    print(f'pytan do policzenia: {len(pytania)}')

    embedery = {
        'pl': SentenceTransformer(MODEL_NAME, device=urzadzenie),
        'en': SentenceTransformer(LANG['en']['embedder'], device=urzadzenie),
    }
    reranker = get_reranker()

    wyniki: dict[str, dict] = {}
    plik_wyjsciowy = OUT_DIR / 'tablica_rerank.json'
    plik_tymczasowy = OUT_DIR / 'tablica_rerank.tmp.json'

    start = time.time()
    for i, (query, lang) in enumerate(pytania, 1):
        wyniki[query] = oblicz_wpis(query, lang, embedery, reranker, args.top_n, args.wsad)

        if i == 100:
            tempo = (time.time() - start) / i
            print(f'po 100 pytaniach: {tempo:.3f} s/pytanie, szacowany calkowity czas: '
                  f'{tempo * len(pytania) / 60:.1f} min')
        if i % 500 == 0:
            zapisz(plik_tymczasowy, wyniki, sha_chunkow, sha_faiss, sha_bm25, urzadzenie, args.top_n)
            print(f'[{i}/{len(pytania)}] zapisano checkpoint', flush=True)

    zapisz(plik_wyjsciowy, wyniki, sha_chunkow, sha_faiss, sha_bm25, urzadzenie, args.top_n)
    if plik_tymczasowy.exists():
        plik_tymczasowy.unlink()
    print(f'zapisano: {plik_wyjsciowy}')


if __name__ == '__main__':
    main()
