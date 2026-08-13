# Z4 (PLAN_PRZEGLAD_O8_O11_O12.md), krok 4: proba dopisania skrotu tresci do istniejacej
# outputs/tablica_rerank.json bez ponownego wolania rerankera, plus kontrola pozycyjna, ktora
# decyduje, czy taki skrot w ogole wolno zapisac.
#
# Zalozenie: skrot tresci zalezy wylacznie od korpusu, nie od modelu, a kolejnosc wpisow
# w tablicy to kolejnosc kandydaci_rrf() z chwili budowy. Jesli kandydaci_rrf jest odtwarzalny,
# wystarczy policzyc go ponownie na CPU i sparowac pozycyjnie ze scorami z tablicy. Kazda pozycja
# jest sprawdzana po url, a rozjazd przerywa prace i nie zapisuje pliku.
#
# WYNIK POMIARU (2026-08-13): zalozenie NIE TRZYMA miedzy urzadzeniami. Odcisk sha256 korpusu
# (chunki, faiss, bm25) zgadzal sie co do bitu, a mimo to 3046 z 5299 pytan mialo rozjazd url
# wzgledem tablicy zbudowanej na cuda:0. Powod: ranking_faiss szereguje CALY korpus, wiec drobna
# roznica embeddingu GPU kontra CPU przestawia dalekie pozycje, a te wchodza do RRF z niemal
# rownymi wagami 1/(60+pozycja). Kolejnosc kandydatow jest wiec odtwarzalna tylko na tym samym
# urzadzeniu. Tablice zbudowana na GPU trzeba na GPU przebudowac, a nie wzbogacac na CPU.
#
# Skrypt zostaje jako kontrola: jesli ktos podejrzewa, ze tablica rozjechala sie z korpusem
# albo z urzadzeniem, ten przebieg odpowiada w kilka minut i niczego nie psuje.
#
# Uzycie:
#     python Pomiary/wzbogac_tablice_sha.py
#     python Pomiary/wzbogac_tablice_sha.py --limit 50 --wyjscie outputs/tablica_probka.json

import argparse
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
POMIARY = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(POMIARY))

import faiss
from sentence_transformers import SentenceTransformer

import rankings
from lang_config import LANG
from tablica_rerank import SCHEMAT, sha_tresci

AGENCI = ('kupujacy', 'sprzedaz')
WSAD_EMB = 64


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wejscie', default=str(ROOT / 'outputs' / 'tablica_rerank.json'))
    parser.add_argument('--wyjscie', default=None)
    parser.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()

    wejscie = Path(args.wejscie)
    wyjscie = Path(args.wyjscie) if args.wyjscie else wejscie
    tablica = json.loads(wejscie.read_text(encoding='utf-8'))
    odcisk = tablica['odcisk']
    print(f'wczytano {wejscie} ({len(tablica["wyniki"])} pytan, schemat={odcisk.get("schemat")})')

    if odcisk.get('schemat') == SCHEMAT:
        print('tablica ma juz schemat 2, nic do zrobienia')
        return

    klucze = sorted(tablica['wyniki'])
    if args.limit:
        klucze = klucze[:args.limit]
    pary_lang_query = [(k.split('|', 1)[0], k.split('|', 1)[1]) for k in klucze]

    embedery = {}
    for lang in sorted({l for l, _ in pary_lang_query}):
        print(f'laduje embedder {lang}: {LANG[lang]["embedder"]}')
        embedery[lang] = SentenceTransformer(LANG[lang]['embedder'])

    embeddingi = {}
    for lang in embedery:
        pytania = [q for l, q in pary_lang_query if l == lang]
        print(f'embeduje {len(pytania)} pytan {lang}')
        wektory = embedery[lang].encode([LANG[lang]['query_prefix'] + q for q in pytania],
                                         batch_size=WSAD_EMB, show_progress_bar=False).astype('float32')
        faiss.normalize_L2(wektory)
        for q, w in zip(pytania, wektory):
            embeddingi[(lang, q)] = w.reshape(1, -1)

    start = time.time()
    rozjazdy = []
    puste = 0
    for i, (kl, (lang, query)) in enumerate(zip(klucze, pary_lang_query), 1):
        wpis = tablica['wyniki'][kl]
        emb = embeddingi[(lang, query)]

        for agent in AGENCI:
            stare = wpis[agent]
            if not stare:
                puste += 1
                continue
            kandydaci = rankings.kandydaci_rrf(query, emb, agent, len(stare), lang)
            if len(kandydaci) != len(stare):
                rozjazdy.append((kl, agent, f'liczba kandydatow {len(kandydaci)} zamiast {len(stare)}'))
                continue

            nowe = []
            for (chunk, _), pozycja in zip(kandydaci, stare):
                if chunk['url'] != pozycja[0]:
                    rozjazdy.append((kl, agent, f'url {chunk["url"]!r} zamiast {pozycja[0]!r}'))
                    break
                nowe.append([pozycja[0], pozycja[1], sha_tresci(chunk)])
            else:
                wpis[agent] = nowe

        if i % 250 == 0:
            tempo = (time.time() - start) / i
            print(f'[{i}/{len(klucze)}] {tempo:.3f} s/pytanie, zostalo '
                  f'{tempo * (len(klucze) - i) / 60:.1f} min, rozjazdow: {len(rozjazdy)}', flush=True)

    print(f'\nprzetworzono {len(klucze)} pytan w {(time.time() - start) / 60:.1f} min')
    print(f'pustych list agenta: {puste}')
    print(f'rozjazdow url: {len(rozjazdy)}')
    for kl, agent, opis in rozjazdy[:20]:
        print(f'  {kl[:70]} [{agent}] {opis}')

    if rozjazdy:
        print('\nPRZERWANO: kandydaci_rrf nie odtwarza kolejnosci z tablicy, wiec skrotow tresci '
              'nie da sie przypisac pozycyjnie. Tablice trzeba zbudowac od nowa na GPU.')
        sys.exit(1)

    if args.limit:
        print(f'\n--limit {args.limit}: schemat NIE zostaje podbity, bo wiekszosc wpisow nie ma '
              f'skrotow. To przebieg kontrolny, plik wyjsciowy nie nadaje sie do pomiarow.')
        sys.exit(0)

    odcisk['schemat'] = SCHEMAT
    odcisk['sha_dopisany_przez'] = 'wzbogac_tablice_sha.py'
    tymczasowy = wyjscie.with_suffix('.tmp.json')
    tymczasowy.write_text(json.dumps(tablica, ensure_ascii=False), encoding='utf-8')
    tymczasowy.replace(wyjscie)
    print(f'\nzapisano: {wyjscie}')


if __name__ == '__main__':
    main()
