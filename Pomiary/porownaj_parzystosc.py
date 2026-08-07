# Faza 2 z PLAN_POMIARY_GPU.md: kontrola parzystosci GPU wobec CPU. Porownuje dwie tablice
# (te same pytania, raz liczone na karcie, raz z CUDA_VISIBLE_DEVICES=) - maksymalna
# bezwzgledna roznica wyniku rerankera, odsetek pytan ze zmiana kolejnosci w pierwszej
# dziesiatce, i zgodnosc decyzji strony (rozstrzygnij) miedzy dwiema tablicami na wariancie r5.
#
# Uzycie (na serwerze GPU, po zbudowaniu obu tablic):
#     python porownaj_parzystosc.py outputs/tablica_rerank_gpu.json outputs/tablica_rerank_cpu.json

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import strony
import tablica_rerank


def main() -> None:
    plik_a, plik_b = sys.argv[1], sys.argv[2]
    with open(plik_a, encoding='utf-8') as f:
        tab_a = json.load(f)
    with open(plik_b, encoding='utf-8') as f:
        tab_b = json.load(f)

    pytania = sorted(set(tab_a['wyniki']) & set(tab_b['wyniki']))
    print(f'wspolne pytania: {len(pytania)}')

    max_roznica = 0.0
    zmiana_kolejnosci_top10 = 0
    for query in pytania:
        for agent in ('kupujacy', 'sprzedaz'):
            a = tab_a['wyniki'][query].get(agent, [])
            b = tab_b['wyniki'][query].get(agent, [])
            skory_a = {url: s for url, s in a}
            skory_b = {url: s for url, s in b}
            for url in set(skory_a) & set(skory_b):
                roznica = abs(skory_a[url] - skory_b[url])
                max_roznica = max(max_roznica, roznica)

            top10_a = [url for url, _ in sorted(a, key=lambda p: p[1], reverse=True)[:10]]
            top10_b = [url for url, _ in sorted(b, key=lambda p: p[1], reverse=True)[:10]]
            if top10_a != top10_b:
                zmiana_kolejnosci_top10 += 1

    print(f'max bezwzgledna roznica score: {max_roznica:.6f}')
    print(f'zmiana kolejnosci top10 (pytanie x agent): {zmiana_kolejnosci_top10}/{len(pytania) * 2}')

    zgodne = 0
    for query in pytania:
        prior, sila = strony.prior_strony(query, None, 'pl', False)
        kwoty = strony.przydzial_kandydatow(prior, sila)

        chunks_a = tablica_rerank.search_reranked_multi_z_tablicy(tab_a, query, list(kwoty), k=10, k_surowe=kwoty)
        zwyciezca_a, _, pytac_a = strony.rozstrzygnij(chunks_a, prior, sila, k=5)

        chunks_b = tablica_rerank.search_reranked_multi_z_tablicy(tab_b, query, list(kwoty), k=10, k_surowe=kwoty)
        zwyciezca_b, _, pytac_b = strony.rozstrzygnij(chunks_b, prior, sila, k=5)

        if (zwyciezca_a, pytac_a) == (zwyciezca_b, pytac_b):
            zgodne += 1

    zgodnosc = zgodne / len(pytania)
    print(f'zgodnosc decyzji strony (rozstrzygnij, r5): {zgodne}/{len(pytania)} = {zgodnosc:.4f}')
    print('BRAMKA (>=0.99): ' + ('PRZESZLA' if zgodnosc >= 0.99 else 'NIE PRZESZLA'))


if __name__ == '__main__':
    main()
