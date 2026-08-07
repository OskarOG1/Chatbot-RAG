# Analiza pomocnicza do decyzji R7 vs R8 (PLAN_ROUTING_NAPRAWA.md krok 6).
# Pokazuje pojedyncze pytania z ramienia sprzedaz_pl/poprawna, gdzie r5 (dzisiejsza
# produkcja) trafia strone poprawnie, a r7 (marker przed lepkoscia) juz nie -
# zeby zobaczyc, jaki marker przechwytuje pytanie i czy to false positive.
#
# Uzycie:
#     python analiza_r7_sprzedaz.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lang_config import LANG
from spell import tokenize_words
import strony

from measure_routing_strony import wczytaj_realny, prior_wariant, przygotuj_realny

zapytania = wczytaj_realny('sprzedaz', 150, 42)
agent_wlasny = 'sprzedaz'

dane_r5 = przygotuj_realny(zapytania, 'pl', agent_wlasny, True, 'r5')
dane_r7 = przygotuj_realny(zapytania, 'pl', agent_wlasny, True, 'r7')

cfg = LANG['pl']

roznice = []
for query, d5, d7 in zip(zapytania, dane_r5, dane_r7):
    zw5, _, pytaj5 = strony.rozstrzygnij(d5['chunks_szerokie'], d5['prior'], d5['sila'], k=5)
    zw7, _, pytaj7 = strony.rozstrzygnij(d7['chunks_szerokie'], d7['prior'], d7['sila'], k=5)
    ok5 = (not pytaj5) and zw5 == 'sprzedajacy'
    ok7 = (not pytaj7) and zw7 == 'sprzedajacy'
    if ok5 and not ok7:
        low = query.lower()
        tokeny = set(tokenize_words(low))
        markery_trafione = {}
        for strona_nazwa, markery in cfg['markery_stron'].items():
            trafienia_slow = tokeny & markery['slowa']
            trafienia_fraz = [f for f in markery['frazy'] if f in low]
            if trafienia_slow or trafienia_fraz:
                markery_trafione[strona_nazwa] = {'slowa': trafienia_slow, 'frazy': trafienia_fraz}
        roznice.append({
            'query': query, 'r7_prior': d7['prior'], 'r7_sila': d7['sila'],
            'r7_zwyciezca': zw7, 'r7_pytaj': pytaj7, 'markery': markery_trafione,
        })

print(f'sprzedaz_pl/poprawna: {len(roznice)} pytan gdzie r5 trafia, r7 nie ({len(roznice)}/{len(zapytania)})\n')
for r in roznice:
    print(f'- "{r["query"]}"')
    print(f'    r7: prior={r["r7_prior"]!r} sila={r["r7_sila"]!r} zwyciezca={r["r7_zwyciezca"]!r} pytaj={r["r7_pytaj"]}')
    print(f'    markery trafione: {r["markery"]}')
