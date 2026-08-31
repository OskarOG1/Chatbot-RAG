import argparse
from pathlib import Path
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from lang_config import LANG
import aliasy

BATCH_SIZE = 16
LIMIT_NOWYCH = 40
ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / "RAG"

def wczytaj_chunki(sciezka: Path) -> list[dict]:
    with open(sciezka, 'r', encoding='utf-8') as r:
       return json.load(r)

def indeksy_do_przeliczenia(chunki: list[dict], slugi: list[str]) -> list[int]:
    return [i for i, c in enumerate(chunki)
            if aliasy.dla_chunku(c) or any(s in (c.get('url') or '') for s in slugi)]


def tekst_dla_modelu(chunk: dict, cfg: dict) -> str:
    return cfg['passage_prefix'] + aliasy.tekst_do_retrievalu(chunk)


def zloz_ze_starego(chunki: list[dict], stare_chunki: list[dict], stare_emb: np.ndarray,
                    cfg: dict, daj_model, limit_nowych: int) -> np.ndarray:
    if stare_emb.shape[0] != len(stare_chunki):
        raise SystemExit(f'stary korpus niespojny: {stare_emb.shape[0]} wierszy embeddingow '
                         f'i {len(stare_chunki)} chunkow')

    stary_indeks: dict[str, int] = {}
    for i, c in enumerate(stare_chunki):
        stary_indeks.setdefault(tekst_dla_modelu(c, cfg), i)

    embeddings = np.zeros((len(chunki), stare_emb.shape[1]), dtype=stare_emb.dtype)
    nieznane: list[int] = []
    z_aliasem: list[int] = []
    for j, c in enumerate(chunki):
        stary = stary_indeks.get(tekst_dla_modelu(c, cfg))
        if stary is None:
            nieznane.append(j)
        elif aliasy.dla_chunku(c):
            z_aliasem.append(j)
        else:
            embeddings[j] = stare_emb[stary]

    do_kodowania = sorted(nieznane + z_aliasem)
    print(f'chunkow: {len(chunki)}, wierszy przepisanych ze starego korpusu: '
          f'{len(chunki) - len(do_kodowania)}, do policzenia: {len(do_kodowania)} '
          f'({len(nieznane)} o nowym tekscie, {len(z_aliasem)} z aliasem)')
    for url in sorted({chunki[j].get('url') for j in nieznane}):
        print(f'  nowy tekst: {url}')

    if len(nieznane) > limit_nowych:
        raise SystemExit(f'chunkow o nowym tekscie jest {len(nieznane)}, limit to '
                         f'{limit_nowych}. Zmienilo sie wiecej niz dociagniete artykuly: '
                         f'sprawdz, czy stary korpus jest tym wlasciwym, albo podnies '
                         f'--limit-nowych swiadomie')

    if do_kodowania:
        teksty = [tekst_dla_modelu(chunki[j], cfg) for j in do_kodowania]
        policzone = daj_model().encode(teksty, batch_size=BATCH_SIZE, show_progress_bar=True)
        for j, wektor in zip(do_kodowania, policzone):
            embeddings[j] = wektor

    return embeddings


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
         slugi: list[str] | None = None, stary: str | None = None,
         limit_nowych: int = LIMIT_NOWYCH):
    cfg = LANG[lang]
    suffix = cfg['suffix']

    sciezka_chunks = RAG_DIR / f"chunks{suffix}.json"
    chunki = wczytaj_chunki(sciezka_chunks)
    sciezka_emb = RAG_DIR / f"embeddings{suffix}.npy"

    zaladowany = []

    def daj_model():
        if not zaladowany:
            zaladowany.append(SentenceTransformer(cfg['embedder']))
        return zaladowany[0]

    if stary:
        katalog = Path(stary)
        stare_chunki_sciezka = katalog / f"chunks{suffix}.json"
        stare_emb_sciezka = katalog / f"embeddings{suffix}.npy"
        for sciezka in (stare_chunki_sciezka, stare_emb_sciezka):
            if not sciezka.exists():
                raise SystemExit(f'brak {sciezka}, wskaz katalog ze starym korpusem tego jezyka')
        embeddings = zloz_ze_starego(chunki, wczytaj_chunki(stare_chunki_sciezka),
                                     np.load(stare_emb_sciezka), cfg, daj_model, limit_nowych)
    elif przelicz:
        if not sciezka_emb.exists():
            raise SystemExit(f'brak {sciezka_emb}, nie ma czego podmieniać')
        embeddings = przelicz_wybrane(chunki, np.load(sciezka_emb), daj_model(), cfg, slugi or [])
    elif dopisz and sciezka_emb.exists():
        istniejace = np.load(sciezka_emb)
        nowe_chunki = chunki[istniejace.shape[0]:]
        if nowe_chunki:
            teksty = [tekst_dla_modelu(c, cfg) for c in nowe_chunki]
            nowe_embeddings = daj_model().encode(teksty, batch_size=BATCH_SIZE, show_progress_bar=True)
            embeddings = np.concatenate([istniejace, nowe_embeddings])
        else:
            embeddings = istniejace
    else:
        teksty = [tekst_dla_modelu(c, cfg) for c in chunki]
        embeddings = daj_model().encode(teksty, batch_size=BATCH_SIZE, show_progress_bar=True)

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
    parser.add_argument('--stary', default=None,
                        help='katalog ze starym korpusem (chunks*.json i embeddings*.npy) '
                             'sprzed przebudowy: wiersze chunkow o niezmienionym tekscie '
                             'sa przepisywane, liczone sa tylko teksty nowe')
    parser.add_argument('--limit-nowych', type=int, default=LIMIT_NOWYCH, dest='limit_nowych',
                        help=f'ile chunkow wolno policzyc przy --stary, zanim skrypt uzna, '
                             f'ze zmienilo sie za duzo i przerwie (domyslnie {LIMIT_NOWYCH})')
    args = parser.parse_args()
    main(args.lang, args.dopisz, args.przelicz, args.slugi, args.stary, args.limit_nowych)
