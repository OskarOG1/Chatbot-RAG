# Krok 6 z PLAN_POMIARY_GPU.md: macierz ramion (brak x 3 slowniki, r5/r7/r5_czysty/r9 x
# poprawna/bledna) na pelnej bazie realnej poza foldem, plus ten sam komplet na czterech
# zestawach golden. Zero wywolan modelu: rankings.search_reranked_multi podmieniony na odczyt
# z outputs/tablica_rerank.json (F3), wiec embed() tez nie jest wolane (query_emb w tablicy
# nieuzywany). r9 na bazie realnej liczy sie na piecu tabelach fold-specyficznych (ten sam
# podzial co ucz_wagi_stron.py), bo kazde pytanie wchodzilo do treningu tabeli produkcyjnej;
# golden nie wchodzi do treningu, wiec liczy sie na jednej tabeli produkcyjnej (src/wagi_stron.py,
# przez prior_wariant). McNemar (r9 wobec r5, r9 wobec r5_czysty) liczony na stanie brak (to jest
# metryka decyzyjna z PLAN_WAGI_STRON.md, "trafienie strony w pierwszej turze"), parami po tych
# samych pytaniach. Przedzial Wilsona 95% dla kazdego raportowanego odsetka.
#
# Uzycie:
#     python macierz_ramion.py

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
OUT_DIR = ROOT / 'outputs'
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from measure import GOLDEN, OOD
from measure_en import golden_en, ood_en
from measure_sprzedaz import golden_sprzedaz
import rankings
import strony

import tablica_rerank
import ucz_wagi_stron as uws
import measure_routing_strony as mrs

Z_WILSON = 1.96
BRAMKA_TRAFNOSC_SPRZEDAZ = 0.70
BRAMKA_TRAFNOSC_KUPUJACY = 0.75
TRAFNOSC_SPRZEDAZ_DZIS = 0.420
TRAFNOSC_KUPUJACY_DZIS = 0.653
BRAMKA_ZLA_CICHA_SPRZEDAZ = 0.20
ZLA_CICHA_SPRZEDAZ_DZIS = 0.427
BRAMKA_PRECYZJA_MOCNY = 0.85
BRAMKA_ODSETEK_ZBYTYCH = 0.15
BRAMKA_PRZEWAGA_NAD_RECZNA = 0.05

WARIANTY = ('r5', 'r7', 'r5_czysty', 'r9')


def wczytaj_tablice_z_odciskiem() -> dict:
    return tablica_rerank.wczytaj_tablice()


def podmien_search(tablica: dict) -> None:
    def search_z_tablicy(query, query_emb, agenci, k=3, k_surowe=20, lang='pl'):
        return tablica_rerank.search_reranked_multi_z_tablicy(
            tablica, query, agenci, k=k, k_surowe=k_surowe)
    rankings.search_reranked_multi = search_z_tablicy


def wilson(k: int, n: int, z: float = Z_WILSON) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    phat = k / n
    denom = 1 + z * z / n
    center = phat + z * z / (2 * n)
    margines = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))
    return (round((center - margines) / denom, 4), round((center + margines) / denom, 4))


def mcnemar(b: int, c: int) -> dict:
    n = b + c
    if n == 0:
        return {'b': b, 'c': c, 'n': n, 'p': 1.0, 'metoda': 'brak_par_niezgodnych'}
    if n <= 200:
        k = min(b, c)
        p_le_k = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
        p = min(1.0, 2 * p_le_k)
        metoda = 'dwumianowy_dokladny'
    else:
        chi2 = (abs(b - c) - 1) ** 2 / n
        p = math.erfc(math.sqrt(chi2 / 2))
        metoda = 'chi_kwadrat_z_korekta'
    return {'b': b, 'c': c, 'n': n, 'p': round(p, 6), 'metoda': metoda}


def buduj_tabele_foldow(rekordy: list[dict], p_tla: dict[str, float]) -> dict[int, dict]:
    tabele = {}
    for test_fold in range(uws.LICZBA_FOLDOW):
        kalibracja_fold = (test_fold + 1) % uws.LICZBA_FOLDOW
        trening = [r for r in rekordy if r['fold'] not in (test_fold, kalibracja_fold)]
        kalibracja = [r for r in rekordy if r['fold'] == kalibracja_fold]
        z_dane, _, _ = uws.policz_z(trening, p_tla)
        dodatki, _ = uws.audytuj_manualne(z_dane)
        tabela = uws.zbuduj_tabele(z_dane, dodatki)
        krzywa_kal = uws.krzywa_z_wpisow(uws.wpisy_do_krzywej(kalibracja, tabela))
        tau_mocny = uws.wybierz_tau_mocny(krzywa_kal)
        tau_slaby, _ = uws.wybierz_tau_slaby(kalibracja, tabela, tau_mocny)
        tabele[test_fold] = {'tabela': tabela, 'tau_mocny': tau_mocny, 'tau_slaby': tau_slaby}
    return tabele


def prior_r9_poza_foldem(rekord: dict, agent_poprzedni: str | None, czy_followup: bool,
                          tabele_foldow: dict) -> tuple[str | None, str | None]:
    info = tabele_foldow[rekord['fold']]
    suma = uws.suma_wazona(rekord['lematy'], info['tabela'])
    if abs(suma) >= info['tau_mocny']:
        return uws.przewidziana_strona(suma), 'leksykalna'
    if agent_poprzedni and czy_followup:
        strona = 'sprzedajacy' if agent_poprzedni == 'sprzedaz' else 'kupujacy'
        return strona, 'lepka'
    if abs(suma) >= info['tau_slaby']:
        return uws.przewidziana_strona(suma), 'leksykalna_slaba'
    return None, None


def prior_dla_realny(rekord: dict, agent_poprzedni: str | None, czy_followup: bool,
                      wariant: str, tabele_foldow: dict) -> tuple[str | None, str | None]:
    if wariant == 'r9':
        return prior_r9_poza_foldem(rekord, agent_poprzedni, czy_followup, tabele_foldow)
    return mrs.prior_wariant(rekord['pytanie'], agent_poprzedni, 'pl', czy_followup, wariant)


def ramie_realny(rekordy: list[dict], oczekiwana: str, agent_poprzedni: str | None,
                  czy_followup: bool, wariant: str, tabele_foldow: dict) -> dict:
    poprawne_lista = []
    sila_mocny_poprawne = sila_mocny_n = 0
    zbyte = 0
    for r in rekordy:
        prior, sila = prior_dla_realny(r, agent_poprzedni, czy_followup, wariant, tabele_foldow)
        kwoty = strony.przydzial_kandydatow(prior, sila)
        chunks_szerokie = rankings.search_reranked_multi(
            r['pytanie'], None, list(kwoty), k=10, k_surowe=kwoty, lang='pl')
        zwyciezca, _, czy_pytac = strony.rozstrzygnij(chunks_szerokie, prior, sila, k=5)
        if czy_pytac:
            zbyte += 1
            poprawne_lista.append(False)
            continue
        poprawne = zwyciezca == oczekiwana
        poprawne_lista.append(poprawne)
        if sila == 'leksykalna':
            sila_mocny_n += 1
            sila_mocny_poprawne += poprawne

    n = len(rekordy)
    k = sum(poprawne_lista)
    return {
        'n': n, 'poprawne': k, 'trafnosc': round(k / n, 4), 'wilson_trafnosc': wilson(k, n),
        'zbyte': zbyte, 'odsetek_zbytych': round(zbyte / n, 4),
        'zla_cicha': round((n - k - zbyte) / n, 4),
        'precyzja_leksykalna_mocny': round(sila_mocny_poprawne / sila_mocny_n, 4) if sila_mocny_n else None,
        'n_leksykalna_mocny': sila_mocny_n,
        'poprawne_lista': poprawne_lista,
    }


def ramie_golden(golden: list[dict], lang: str, oczekiwana: str, agent_poprzedni: str | None,
                  czy_followup: bool, wariant: str) -> dict:
    dane = []
    for g in golden:
        prior, sila = mrs.prior_wariant(g['query'], agent_poprzedni, lang, czy_followup, wariant)
        kwoty = strony.przydzial_kandydatow(prior, sila)
        chunks_szerokie = rankings.search_reranked_multi(
            g['query'], None, list(kwoty), k=10, k_surowe=kwoty, lang=lang)
        dane.append({'query': g['query'], 'prior': prior, 'sila': sila,
                     'chunks_szerokie': chunks_szerokie, 'zrodlo': mrs.zrodla_jako_lista(g)})
    w = mrs.hit_z_przygotowanych(dane, oczekiwana)
    w['wilson_hit5'] = wilson(round(w['hit5'] * w['n']), w['n'])
    del w['braki_top5']
    return w


def macierz_realny(rekordy_wszystkie: list[dict], tabele_foldow: dict) -> dict:
    zestawy = {
        'kupujacy_pl': ([r for r in rekordy_wszystkie if r['etykieta'] == 'kupujacy'], 'kupujacy'),
        'sprzedaz_pl': ([r for r in rekordy_wszystkie if r['etykieta'] == 'sprzedajacy'], 'sprzedajacy'),
    }
    wynik = {}
    for nazwa, (rekordy, oczekiwana) in zestawy.items():
        print(f'  [{nazwa}] {len(rekordy)} pytan poza foldem', flush=True)
        agent_wlasny = strony.STRONA_DO_AGENTA[oczekiwana]
        agent_obcy = next(a for s, a in strony.STRONA_DO_AGENTA.items() if s != oczekiwana)

        ramiona = {
            'brak_markery_stron': ramie_realny(rekordy, oczekiwana, None, False, 'r5', tabele_foldow),
            'brak_r5_czysty': ramie_realny(rekordy, oczekiwana, None, False, 'r5_czysty', tabele_foldow),
            'brak_r9': ramie_realny(rekordy, oczekiwana, None, False, 'r9', tabele_foldow),
        }
        for wariant in WARIANTY:
            print(f'    [{nazwa}][{wariant}] poprawna/bledna', flush=True)
            ramiona[f'{wariant}_poprawna'] = ramie_realny(
                rekordy, oczekiwana, agent_wlasny, True, wariant, tabele_foldow)
            ramiona[f'{wariant}_bledna'] = ramie_realny(
                rekordy, oczekiwana, agent_obcy, True, wariant, tabele_foldow)

        for klucz, w in ramiona.items():
            print(f'    [{nazwa}][{klucz}] trafnosc={w["trafnosc"]:.4f} '
                  f'zbyte={w["odsetek_zbytych"]:.4f} zla_cicha={w["zla_cicha"]:.4f}')

        wynik[nazwa] = ramiona
    return wynik


def macierz_golden(tabele_foldow: dict) -> dict:
    zestawy = {
        'kupujacy_pl': (GOLDEN, 'pl', 'kupujacy'),
        'sprzedaz_pl': (golden_sprzedaz('pl'), 'pl', 'sprzedajacy'),
        'kupujacy_en': (golden_en(), 'en', 'kupujacy'),
        'sprzedaz_en': (golden_sprzedaz('en'), 'en', 'sprzedajacy'),
    }
    wynik = {}
    for nazwa, (golden, lang, oczekiwana) in zestawy.items():
        print(f'  [{nazwa}] {len(golden)} pytan golden', flush=True)
        agent_wlasny = strony.STRONA_DO_AGENTA[oczekiwana]
        agent_obcy = next(a for s, a in strony.STRONA_DO_AGENTA.items() if s != oczekiwana)

        ramiona = {
            'brak_markery_stron': ramie_golden(golden, lang, oczekiwana, None, False, 'r5'),
            'brak_r5_czysty': ramie_golden(golden, lang, oczekiwana, None, False, 'r5_czysty'),
            'brak_r9': ramie_golden(golden, lang, oczekiwana, None, False, 'r9'),
        }
        for wariant in WARIANTY:
            ramiona[f'{wariant}_poprawna'] = ramie_golden(golden, lang, oczekiwana, agent_wlasny, True, wariant)
            ramiona[f'{wariant}_bledna'] = ramie_golden(golden, lang, oczekiwana, agent_obcy, True, wariant)

        for klucz, w in ramiona.items():
            print(f'    [{nazwa}][{klucz}] hit5={w["hit5"]:.3f} zbyte={w["odsetek_zbytych"]:.3f} '
                  f'zla_strona_po={w["zla_strona_po_chunkow"]}')

        wynik[nazwa] = ramiona
    return wynik


def testy_statystyczne(macierz_r: dict) -> dict:
    wyniki = {}
    for nazwa, ramiona in macierz_r.items():
        lista_r9 = ramiona['brak_r9']['poprawne_lista']
        lista_r5 = ramiona['brak_markery_stron']['poprawne_lista']
        lista_r5c = ramiona['brak_r5_czysty']['poprawne_lista']

        def pary(lista_a, lista_b):
            b = sum(1 for a, x in zip(lista_a, lista_b) if a and not x)
            c = sum(1 for a, x in zip(lista_a, lista_b) if not a and x)
            return b, c

        b, c = pary(lista_r9, lista_r5)
        wyniki[f'{nazwa}_r9_wobec_r5'] = mcnemar(b, c)
        b, c = pary(lista_r9, lista_r5c)
        wyniki[f'{nazwa}_r9_wobec_r5_czysty'] = mcnemar(b, c)
    return wyniki


def przygotuj_ood(pytania: list, lang: str, wariant: str) -> dict:
    from lang_config import LANG
    prog = LANG[lang]['prog_rerank']
    zlapane = 0
    for p in pytania:
        query = p['query'] if isinstance(p, dict) else p
        prior, sila = mrs.prior_wariant(query, None, lang, False, wariant)
        kwoty = strony.przydzial_kandydatow(prior, sila)
        chunks_szerokie = rankings.search_reranked_multi(
            query, None, list(kwoty), k=10, k_surowe=kwoty, lang=lang)
        zwyciezca, chunks, czy_pytac = strony.rozstrzygnij(chunks_szerokie, prior, sila, k=1)
        if czy_pytac or not chunks or chunks[0][1] < prog:
            zlapane += 1
    n = len(pytania)
    return {'n': n, 'zlapane': zlapane}


def sprawdz_bramki(macierz_r: dict, macierz_g: dict, testy: dict, ood_dzis: dict, ood_r9: dict) -> list[str]:
    problemy = []

    trafnosc_sprzedaz_r9 = macierz_r['sprzedaz_pl']['brak_r9']['trafnosc']
    if trafnosc_sprzedaz_r9 < BRAMKA_TRAFNOSC_SPRZEDAZ:
        problemy.append(f'[bramka 1] trafnosc sprzedaz_pl brak_r9: {trafnosc_sprzedaz_r9:.4f} '
                         f'< {BRAMKA_TRAFNOSC_SPRZEDAZ} (dzis {TRAFNOSC_SPRZEDAZ_DZIS})')

    trafnosc_kupujacy_r9 = macierz_r['kupujacy_pl']['brak_r9']['trafnosc']
    if trafnosc_kupujacy_r9 < BRAMKA_TRAFNOSC_KUPUJACY:
        problemy.append(f'[bramka 2] trafnosc kupujacy_pl brak_r9: {trafnosc_kupujacy_r9:.4f} '
                         f'< {BRAMKA_TRAFNOSC_KUPUJACY} (dzis {TRAFNOSC_KUPUJACY_DZIS})')

    zla_cicha_sprzedaz_r9 = macierz_r['sprzedaz_pl']['brak_r9']['zla_cicha']
    if zla_cicha_sprzedaz_r9 >= BRAMKA_ZLA_CICHA_SPRZEDAZ:
        problemy.append(f'[bramka 3] zla_cicha sprzedaz_pl brak_r9: {zla_cicha_sprzedaz_r9:.4f} '
                         f'>= {BRAMKA_ZLA_CICHA_SPRZEDAZ} (dzis {ZLA_CICHA_SPRZEDAZ_DZIS})')

    for nazwa in ('kupujacy_pl', 'sprzedaz_pl'):
        precyzja = macierz_r[nazwa]['brak_r9']['precyzja_leksykalna_mocny']
        if precyzja is not None and precyzja < BRAMKA_PRECYZJA_MOCNY:
            problemy.append(f'[bramka 4] precyzja leksykalna_mocny {nazwa}: {precyzja:.4f} '
                             f'< {BRAMKA_PRECYZJA_MOCNY}')

    for nazwa in ('kupujacy_pl', 'sprzedaz_pl'):
        odsetek = macierz_r[nazwa]['brak_r9']['odsetek_zbytych']
        if odsetek >= BRAMKA_ODSETEK_ZBYTYCH:
            problemy.append(f'[bramka 5] odsetek_zbytych {nazwa} brak_r9: {odsetek:.4f} '
                             f'>= {BRAMKA_ODSETEK_ZBYTYCH}')

    for nazwa, ramiona in macierz_g.items():
        for stan in ('poprawna', 'bledna'):
            hit5_r9 = ramiona[f'r9_{stan}']['hit5']
            hit5_r5 = ramiona[f'r5_{stan}']['hit5']
            if hit5_r9 < hit5_r5 - 1e-9:
                problemy.append(f'[bramka 6] golden {nazwa} {stan}: hit5 r9={hit5_r9:.4f} '
                                 f'< r5(dzis)={hit5_r5:.4f}')
            zbyte_r9 = ramiona[f'r9_{stan}']['odsetek_zbytych']
            zbyte_r5 = ramiona[f'r5_{stan}']['odsetek_zbytych']
            if zbyte_r9 > zbyte_r5 + 1e-9:
                problemy.append(f'[bramka 6] golden {nazwa} {stan}: odsetek_zbytych r9={zbyte_r9:.4f} '
                                 f'> r5(dzis)={zbyte_r5:.4f}')

    for nazwa in ('kupujacy_pl', 'sprzedaz_pl'):
        przewaga = macierz_r[nazwa]['brak_r9']['trafnosc'] - macierz_r[nazwa]['brak_r5_czysty']['trafnosc']
        if przewaga < BRAMKA_PRZEWAGA_NAD_RECZNA:
            problemy.append(f'[bramka 7] przewaga r9 nad r5_czysty {nazwa}: {przewaga:+.4f} '
                             f'< {BRAMKA_PRZEWAGA_NAD_RECZNA}')

    for lang in ('pl', 'en'):
        if ood_r9[lang]['zlapane'] < ood_dzis[lang]['zlapane']:
            problemy.append(f'[bramka 8] odmowy OOD {lang}: r9={ood_r9[lang]["zlapane"]} '
                             f'< dzis(r5)={ood_dzis[lang]["zlapane"]}')

    return problemy


def main() -> None:
    print('=== Wczytywanie tablicy rerankera ===')
    tablica = wczytaj_tablice_z_odciskiem()
    print(f"odcisk zgodny, {len(tablica['wyniki'])} pytan w tablicy, "
          f"urzadzenie={tablica['odcisk']['urzadzenie']}")
    podmien_search(tablica)

    print('\n=== Budowa piesciu tabel fold-specyficznych (r9, poza foldem) ===')
    rekordy_wszystkie = uws.wczytaj_wszystkie()
    p_tla = uws.policz_p_tla(rekordy_wszystkie)
    tabele_foldow = buduj_tabele_foldow(rekordy_wszystkie, p_tla)
    for fold, info in tabele_foldow.items():
        print(f'  fold {fold}: tabela={len(info["tabela"])} TAU_MOCNY={info["tau_mocny"]:.3f} '
              f'TAU_SLABY={info["tau_slaby"]:.3f}')

    print('\n=== Macierz ramion, baza realna, poza foldem ===')
    macierz_r = macierz_realny(rekordy_wszystkie, tabele_foldow)

    print('\n=== Macierz ramion, cztery zestawy golden ===')
    macierz_g = macierz_golden(tabele_foldow)

    print('\n=== McNemar, stan brak (metryka decyzyjna) ===')
    testy = testy_statystyczne(macierz_r)
    for nazwa, w in testy.items():
        print(f'  [{nazwa}] b={w["b"]} c={w["c"]} p={w["p"]} ({w["metoda"]})')

    print('\n=== Odmowy OOD, r5(dzis) wobec r9 ===')
    ood_dzis = {'pl': przygotuj_ood(OOD, 'pl', 'r5'), 'en': przygotuj_ood(list(ood_en()), 'en', 'r5')}
    ood_r9 = {'pl': przygotuj_ood(OOD, 'pl', 'r9'), 'en': przygotuj_ood(list(ood_en()), 'en', 'r9')}
    for lang in ('pl', 'en'):
        print(f'  [{lang}] dzis(r5)={ood_dzis[lang]["zlapane"]}/{ood_dzis[lang]["n"]} '
              f'r9={ood_r9[lang]["zlapane"]}/{ood_r9[lang]["n"]}')

    print('\n=== Bramki PLAN_WAGI_STRON.md / PLAN_POMIARY_GPU.md ===')
    problemy = sprawdz_bramki(macierz_r, macierz_g, testy, ood_dzis, ood_r9)
    if problemy:
        print('BRAMKI NIE PRZESZLY:')
        for p in problemy:
            print(f'  - {p}')
    else:
        print('wszystkie bramki (1-8, bez 9: latencja, odlozona do Kroku 7) przeszly')
    print('Bramka 9 (czas prior_strony < 1ms) nie jest tu liczona: PLAN_POMIARY_GPU.md Faza 4 '
          'trzyma latencje poza tablica, na sprzecie klasy produkcyjnej. Sprawdzana w Kroku 7.')

    for ramiona in list(macierz_r.values()) + list(macierz_g.values()):
        for w in ramiona.values():
            w.pop('poprawne_lista', None)

    OUT_DIR.mkdir(exist_ok=True)
    wynik = {
        'tabele_foldow_meta': {str(f): {'rozmiar_tabeli': len(info['tabela']),
                                         'tau_mocny': round(info['tau_mocny'], 4),
                                         'tau_slaby': round(info['tau_slaby'], 4)}
                                for f, info in tabele_foldow.items()},
        'macierz_realny': macierz_r,
        'macierz_golden': macierz_g,
        'mcnemar_brak': testy,
        'ood_dzis': ood_dzis, 'ood_r9': ood_r9,
        'problemy_bramek': problemy,
        'wszystkie_bramki_przeszly': not problemy,
    }
    plik = OUT_DIR / 'macierz_ramion.json'
    plik.write_text(json.dumps(wynik, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    print(f'\nzapisano: {plik}')


if __name__ == '__main__':
    main()
