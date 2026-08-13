# Kroki 4 i 6 z PLAN_KLASYFIKATOR_FORUM.md: model liniowy rozpoznajacy sekcje forum,
# kalibracja progow oferty, dwa punkty odniesienia, kontrola OOD i weto rozkladowe.
# Generuje Pomiary/wagi_forum.py. Zaden plik w src/ go nie importuje (patrz
# PLAN_DLUG_SRC.md pozycja 9), czytaja go wylacznie skrypty pomiarowe w tym katalogu.
#
# ESTYMATOR. Ten sam co w PLAN_WAGI_STRON.md, rozszerzony na wiele klas przez jeden
# przeciw reszcie. Dla klasy c i lematu t, na wycinku uczacym:
#   delta_c(t)     = log((y_c + a) / (n_c + ALFA0 - y_c - a)) - log((y_r + a) / (n_r + ALFA0 - y_r - a))
#   wariancja_c(t) = 1/(y_c + a) + 1/(y_r + a)
#   z_c(t)         = delta_c(t) / sqrt(wariancja_c(t))
# gdzie a = ALFA0 * df(t)/N. Wygladzanie proporcjonalne do czestosci tla, wiec slowo
# pospolite musi sie mocniej wychylic, zeby dostac te sama wage co rzadkie.
#
# Dlaczego nie sklearn: nie jest zaleznoscia tego projektu, dokladalby wagi do obrazu
# i wymuszal wersjonowanie artefaktu modelu przy deployu. Przy ~3600 krotkich przykladach
# z zaszumionymi etykietami roznica miesci sie w szumie. Regresja logistyczna zostaje
# jako sciezka odwrotu, gdyby bramki nie przeszly.
#
# DWA PROGI, nie jeden. Sam margines nie wystarcza: pytanie o wszystkich wynikach ujemnych
# moze miec duzy margines i zerowa tresc.
#
# PEWNOSC SKALARNA. Do metryki "precyzja przy pokryciu 0,30" potrzebny jest jeden porzadek,
# a regula decyzyjna jest dwuwymiarowa. Uzywamy min z dwoch rang percentylowych liczonych
# na wycinku KALIBRACYJNYM. Odciecie tej pewnosci na poziomie q to dokladnie regula
# dwuprogowa przy progach z percentyla q, wiec nie jest to inna metoda, tylko inny sposob
# jej zapisania.
#
# Uzycie:
#     python Pomiary/ucz_klasyfikator_forum.py

import argparse
import json
import math
import subprocess
import sys
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import dane_forum

WYJSCIE = dane_forum.OUT_DIR / 'klasyfikator_forum.json'
MODUL = dane_forum.ROOT / 'Pomiary' / 'wagi_forum.py'
SKRYPT_CZASU = Path(__file__).resolve().parent / 'czas_klasyfikacji_forum.py'

ALFA0 = 500
DF_MIN = 20
MAX_NA_KLASE = 200
K_SASIADOW = 10

SIATKA_PERCENTYLI = [10 + 5 * i for i in range(17)]
BRAMKA_PRECYZJI = 0.70
POKRYCIE_DECYZYJNE = 0.30
BRAMKA_PRZEWAGI_STRONA = 0.15
BRAMKA_PRZEWAGI_KNN = 0.05
BRAMKA_OOD = 0.10
BRAMKA_GOLDEN = 0.15
NAJMOCNIEJSZYCH_DO_RAPORTU = 40


def z_lematu(y_c: float, n_c: int, y_r: float, n_r: int, alfa: float) -> float:
    a = y_c + alfa
    b = max(n_c + ALFA0 - y_c - alfa, 1e-9)
    c = y_r + alfa
    d = max(n_r + ALFA0 - y_r - alfa, 1e-9)
    delta = math.log(a / b) - math.log(c / d)
    wariancja = 1.0 / a + 1.0 / c
    return delta / math.sqrt(wariancja)


def tablice_wag(lematy_uczenia: list[set], klasy_uczenia: list[str]) -> dict[str, dict[str, float]]:
    """Jedna tablica na klase, kazda przycieta do MAX_NA_KLASE wpisow po |z|.
    Odciecie df >= DF_MIN idzie PRZED liczeniem z: lemat widziany 5 razy w calej bazie
    dostalby wysokie |z| z samego przypadku."""
    n = len(lematy_uczenia)
    df = Counter()
    for zbior in lematy_uczenia:
        df.update(zbior)

    df_w_klasie: dict[str, Counter] = defaultdict(Counter)
    licznosci = Counter(klasy_uczenia)
    for zbior, k in zip(lematy_uczenia, klasy_uczenia):
        df_w_klasie[k].update(zbior)

    kandydaci = [t for t, ile in df.items() if ile >= DF_MIN]

    tablice = {}
    for klasa in sorted(licznosci):
        n_c = licznosci[klasa]
        n_r = n - n_c
        wpisy = []
        for t in kandydaci:
            alfa = ALFA0 * df[t] / n
            y_c = df_w_klasie[klasa][t]
            y_r = df[t] - y_c
            wpisy.append((z_lematu(y_c, n_c, y_r, n_r, alfa), t))
        wpisy.sort(key=lambda para: -abs(para[0]))
        tablice[klasa] = {t: round(z, 4) for z, t in wpisy[:MAX_NA_KLASE]}
    return tablice


def decyzja(tokeny: set, tablice: dict) -> tuple[str | None, float, float]:
    wyniki = sorted(
        ((sum(tablica[t] for t in tokeny if t in tablica), klasa)
         for klasa, tablica in tablice.items()),
        reverse=True,
    )
    if not wyniki:
        return None, 0.0, 0.0
    najlepszy, klasa = wyniki[0]
    drugi = wyniki[1][0] if len(wyniki) > 1 else 0.0
    return klasa, najlepszy, najlepszy - drugi


def kwantyl(posortowane: list[float], q: float) -> float:
    if not posortowane:
        return 0.0
    return posortowane[min(len(posortowane) - 1, max(0, int(round(q * (len(posortowane) - 1)))))]


def ranga(posortowane: list[float], x: float) -> float:
    """Ranga percentylowa x wzgledem rozkladu kalibracyjnego, z zakresu 0 do 1."""
    if not posortowane:
        return 0.0
    return bisect_right(posortowane, x) / len(posortowane)


def punkt_siatki(punkty: list[dict], tau_w: float, tau_m: float) -> dict:
    pokryte = [p for p in punkty if p['wynik'] >= tau_w and p['margines'] >= tau_m]
    trafione = sum(1 for p in pokryte if p['pred'] == p['prawda'])
    return {
        'tau_wynik': round(tau_w, 4),
        'tau_margines': round(tau_m, 4),
        'pokrycie': round(len(pokryte) / len(punkty), 4) if punkty else 0.0,
        'precyzja': round(trafione / len(pokryte), 4) if pokryte else 0.0,
        'pokrytych': len(pokryte),
    }


def siatka(punkty: list[dict], wyniki_sort: list[float], marginesy_sort: list[float]) -> list[dict]:
    krzywa = []
    for pw in SIATKA_PERCENTYLI:
        for pm in SIATKA_PERCENTYLI:
            tau_w = kwantyl(wyniki_sort, pw / 100)
            tau_m = kwantyl(marginesy_sort, pm / 100)
            wpis = punkt_siatki(punkty, tau_w, tau_m)
            wpis['percentyl_wynik'] = pw
            wpis['percentyl_margines'] = pm
            krzywa.append(wpis)
    return krzywa


def obwiednia(krzywa: list[dict]) -> list[dict]:
    """Najwyzsza precyzja osiagalna przy danym pokryciu lub wyzszym. Bez tego surowa
    siatka wyglada jak chmura i nie widac kompromisu."""
    posortowane = sorted(krzywa, key=lambda w: -w['pokrycie'])
    najlepsza = -1.0
    wynik = []
    for w in posortowane:
        if w['precyzja'] > najlepsza:
            najlepsza = w['precyzja']
            wynik.append({'pokrycie': w['pokrycie'], 'precyzja': w['precyzja'],
                          'percentyl_wynik': w['percentyl_wynik'],
                          'percentyl_margines': w['percentyl_margines']})
    return wynik


def precyzja_przy_pokryciu(punkty: list[dict], pokrycie: float) -> dict:
    """Sortuje po pewnosci malejaco i bierze gorne `pokrycie` czesci zbioru.
    Dziala tak samo dla modelu liniowego i dla kNN, wiec obie liczby sa porownywalne."""
    ile = max(1, int(round(pokrycie * len(punkty))))
    posortowane = sorted(punkty, key=lambda p: -p['pewnosc'])[:ile]
    trafione = sum(1 for p in posortowane if p['pred'] == p['prawda'])
    return {
        'pokrycie': round(len(posortowane) / len(punkty), 4),
        'precyzja': round(trafione / len(posortowane), 4),
        'pokrytych': len(posortowane),
        'trafionych': trafione,
    }


def zbuduj_punkty(rekordy, tablice, wyniki_sort, marginesy_sort) -> list[dict]:
    punkty = []
    for r in rekordy:
        tokeny = dane_forum.lematy_pytania(r['pytanie'])
        pred, wynik, margines = decyzja(tokeny, tablice)
        punkty.append({
            'pytanie': r['pytanie'],
            'prawda': dane_forum.klasa(r['board']),
            'pred': pred,
            'wynik': wynik,
            'margines': margines,
            'pewnosc': min(ranga(wyniki_sort, wynik), ranga(marginesy_sort, margines)),
        })
    return punkty


def odniesienie_strona(rekordy, klasy_uczenia, boardy_uczenia) -> list[dict]:
    """Zawsze najliczniejsza klasa tej strony, ktora wybieral dawny routing
    (prior_strony, czysto leksykalny), zachowany tu jako historyczna linia
    odniesienia. Brak prioru to globalna wiekszosc."""
    import strony
    from prior_strony import prior_strony

    najliczniejsza_globalnie = Counter(klasy_uczenia).most_common(1)[0][0]
    po_stronie = defaultdict(Counter)
    for k, b in zip(klasy_uczenia, boardy_uczenia):
        po_stronie[dane_forum.strona(b)][k] += 1
    wybor = {s: c.most_common(1)[0][0] for s, c in po_stronie.items() if c}

    punkty = []
    for r in rekordy:
        prior, _sila = prior_strony(r['pytanie'], None, 'pl', False)
        agent = strony.STRONA_DO_AGENTA.get(prior) if prior else None
        punkty.append({
            'prawda': dane_forum.klasa(r['board']),
            'pred': wybor.get(agent, najliczniejsza_globalnie),
            'prior': agent,
        })
    return punkty


def odniesienie_knn(rekordy_wszystkie, wektory, foldy, wycinek, populacja=None) -> list[dict]:
    """Klasa wiekszosciowa z K_SASIADOW sasiadow, bez uczenia czegokolwiek. Pewnosc to
    udzial klasy zwycieskiej wsrod sasiadow, wiec kNN da sie odciac na tym samym
    pokryciu co model liniowy.

    populacja=None to definicja z planu: wszystko spoza foldu, czyli dla wycinka
    testowego uczenie plus kalibracja (85% bazy). Model liniowy widzial tylko uczenie
    (71%), wiec ta wersja daje kNN lekka przewage. Dlatego liczymy tez wariant
    populacja='uczenie', dopasowany do tego, co widzial model."""
    import numpy as np

    if populacja is None:
        sasiedzi = dane_forum.sasiedzi_spoza_foldu(wektory, foldy, K_SASIADOW)
    else:
        maska = np.array([f == populacja for f in foldy])
        indeks, mapowanie = dane_forum.indeks_podzbioru(wektory, maska)
        pozycje = np.flatnonzero(np.array([f == wycinek for f in foldy]))
        _wyniki, trafienia = indeks.search(np.ascontiguousarray(wektory[pozycje]), K_SASIADOW)
        sasiedzi = [[] for _ in foldy]
        for wiersz, poz in enumerate(pozycje):
            sasiedzi[poz] = [int(mapowanie[j]) for j in trafienia[wiersz] if j >= 0]

    punkty = []
    for i, r in enumerate(rekordy_wszystkie):
        if foldy[i] != wycinek:
            continue
        glosy = Counter(dane_forum.klasa(rekordy_wszystkie[j]['board']) for j in sasiedzi[i])
        glosy.pop(None, None)
        if not glosy:
            punkty.append({'prawda': dane_forum.klasa(r['board']), 'pred': None, 'pewnosc': 0.0})
            continue
        klasa, ile = glosy.most_common(1)[0]
        punkty.append({
            'prawda': dane_forum.klasa(r['board']),
            'pred': klasa,
            'pewnosc': ile / sum(glosy.values()),
        })
    return punkty


def rozklad(wartosci: list[float]) -> dict:
    posortowane = sorted(wartosci)
    return {
        'n': len(posortowane),
        'p10': round(kwantyl(posortowane, 0.10), 3),
        'mediana': round(kwantyl(posortowane, 0.50), 3),
        'p90': round(kwantyl(posortowane, 0.90), 3),
    }


def kalibracja_golden(tablice: dict, tau_w: float, tau_m: float) -> dict:
    """Krok 6, weto rozkladowe. Baza to TYTULY watkow ("Anulowanie przesylki allegro dhl"),
    a produkcja dostaje ZDANIA w pierwszej osobie ("jak anulowac przesylke, ktora
    wyslalem"). Golden nie ma etykiety sekcji forum, wiec nie mierzymy trafnosci, tylko
    kalibracje: czy model na zdaniach w ogole przekracza progi.
    Jesli prawie nigdy nie przekracza, oferta na produkcji nie pojawi sie NIGDY i cala
    praca jest bezuzyteczna, niezaleznie od wynikow kroku 4."""
    from measure import GOLDEN
    from measure_sprzedaz import golden_sprzedaz

    pytania = [g['query'] if isinstance(g, dict) else g for g in list(GOLDEN) + list(golden_sprzedaz('pl'))]
    wyniki, marginesy, przekroczyly = [], [], 0
    for p in pytania:
        _pred, wynik, margines = decyzja(dane_forum.lematy_pytania(p), tablice)
        wyniki.append(wynik)
        marginesy.append(margines)
        przekroczyly += wynik >= tau_w and margines >= tau_m

    udzial = przekroczyly / len(pytania) if pytania else 0.0
    return {
        'n': len(pytania),
        'wynik': rozklad(wyniki),
        'margines': rozklad(marginesy),
        'przekroczylo_progi': round(udzial, 4),
        'bramka': BRAMKA_GOLDEN,
        'weto': udzial < BRAMKA_GOLDEN,
    }


def kontrola_ood(tablice: dict, tau_w: float, tau_m: float) -> dict:
    rekordy = dane_forum.wczytaj(('ood',))
    if not rekordy:
        return {'n': 0, 'uwaga': 'brak rekordow zrodlo=ood, uruchom Pomiary/zbierz_ood_forum.py'}
    wyniki, marginesy, przekroczyly = [], [], 0
    for r in rekordy:
        _pred, wynik, margines = decyzja(dane_forum.lematy_pytania(r['pytanie']), tablice)
        wyniki.append(wynik)
        marginesy.append(margines)
        przekroczyly += wynik >= tau_w and margines >= tau_m
    udzial = przekroczyly / len(rekordy)
    return {
        'n': len(rekordy),
        'boardy': dict(Counter(r['board'] for r in rekordy)),
        'wynik': rozklad(wyniki),
        'margines': rozklad(marginesy),
        'przekroczylo_progi': round(udzial, 4),
        'bramka': BRAMKA_OOD,
        'spelniona': udzial < BRAMKA_OOD,
    }


def surowe_punkty(pytania: list[str], tablice: dict) -> list[tuple[float, float]]:
    return [decyzja(dane_forum.lematy_pytania(p), tablice)[1:] for p in pytania]


def przemiataj_bramki(punkty_kal, punkty_test, wyniki_sort, marginesy_sort,
                      ood_punkty, golden_punkty) -> dict:
    """Czy ISTNIEJE para progow spelniajaca naraz bramke precyzji, bramke OOD i weto
    rozkladowe. Dwa punkty pracy, ktore sobie przecza, to jeszcze nie dowod, ze sie nie da.

    WYBOR liczony jest na wycinku KALIBRACYJNYM, nie testowym. OOD i golden to osobne
    zbiory, wiec wolno ich uzyc jako ograniczen; test zostaje nietkniety i sluzy tylko
    do zaraportowania, co wybrany punkt daje na danych, ktorych nie widzial."""
    wszystkie = []
    for pw in SIATKA_PERCENTYLI:
        for pm in SIATKA_PERCENTYLI:
            tau_w = kwantyl(wyniki_sort, pw / 100)
            tau_m = kwantyl(marginesy_sort, pm / 100)

            def przechodzi(pary):
                return sum(1 for w, m in pary if w >= tau_w and m >= tau_m)

            ood_udzial = przechodzi(ood_punkty) / len(ood_punkty) if ood_punkty else 0.0
            golden_udzial = przechodzi(golden_punkty) / len(golden_punkty) if golden_punkty else 0.0
            wpis = punkt_siatki(punkty_kal, tau_w, tau_m)
            wpis.update({
                'percentyl_wynik': pw, 'percentyl_margines': pm,
                'test': punkt_siatki(punkty_test, tau_w, tau_m),
                'ood': round(ood_udzial, 4), 'golden': round(golden_udzial, 4),
                'ood_ok': ood_udzial < BRAMKA_OOD,
                'golden_ok': golden_udzial >= BRAMKA_GOLDEN,
                'precyzja_ok': wpis['precyzja'] >= BRAMKA_PRECYZJI,
            })
            wszystkie.append(wpis)

    obie = [w for w in wszystkie if w['ood_ok'] and w['golden_ok']]
    wszystkie_trzy = [w for w in obie if w['precyzja_ok'] and w['pokrytych'] >= 20]
    dopuszczalne = sorted(wszystkie_trzy, key=lambda w: (-w['pokrycie'], -w['precyzja']))
    return {
        'punktow_siatki': len(wszystkie),
        'spelnia_ood_i_golden': len(obie),
        'spelnia_ood_golden_i_precyzje': len(wszystkie_trzy),
        'najlepszy_kompromis': max(wszystkie, key=lambda w: (w['golden'] - w['ood'])),
        'wybrany': dopuszczalne[0] if dopuszczalne else None,
        'punkty_spelniajace': dopuszczalne[:10],
        'siatka': wszystkie,
    }


def zapisz_modul(tablice: dict, tau_w: float, tau_m: float, n_uczenia: int) -> None:
    data = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    linie = [
        f'# Wygenerowane przez Pomiary/ucz_klasyfikator_forum.py, przebieg {data}, '
        f'{n_uczenia} przykladow,',
        '# wycinek uczenia z RAG/pytania_realne.jsonl. Nie edytowac recznie.',
        '',
        'WAGI = {',
    ]
    for klasa in sorted(tablice):
        wpisy = sorted(tablice[klasa].items(), key=lambda para: -abs(para[1]))
        linie.append(f'    {klasa!r}: {{')
        for t, z in wpisy:
            linie.append(f'        {t!r}: {z},')
        linie.append('    },')
    linie.append('}')
    linie.append('')
    linie.append('KLASA_DO_URL = {')
    for klasa in sorted(tablice):
        linie.append(f'    {klasa!r}: {dane_forum.KLASA_DO_URL[klasa]!r},')
    linie.append('}')
    linie.append('')
    linie.append(f'TAU_WYNIK = {round(tau_w, 4)}')
    linie.append(f'TAU_MARGINES = {round(tau_m, 4)}')
    linie.append(f"PRZEBIEG = {{'data': {data!r}, 'przykladow': {n_uczenia}, "
                 f"'klas': {len(tablice)}, 'alfa0': {ALFA0}, 'df_min': {DF_MIN}, "
                 f"'max_na_klase': {MAX_NA_KLASE}}}")
    linie.append('')
    MODUL.write_text('\n'.join(linie), encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--bez-czasu', action='store_true', help='pomin pomiar czasu w osobnym procesie')
    args = parser.parse_args()

    rekordy = [r for r in dane_forum.wczytaj(('forum',)) if dane_forum.klasa(r['board'])]
    foldy = [dane_forum.fold(r['pytanie']) for r in rekordy]
    wektory = dane_forum.embeddingi([r['pytanie'] for r in rekordy])

    uczenie = [r for r, f in zip(rekordy, foldy) if f == 'uczenie']
    kalibracja = [r for r, f in zip(rekordy, foldy) if f == 'kalibracja']
    test = [r for r, f in zip(rekordy, foldy) if f == 'test']
    print(f'uczenie {len(uczenie)}, kalibracja {len(kalibracja)}, test {len(test)}, '
          f'klas {len(set(dane_forum.klasa(r["board"]) for r in rekordy))}')

    lematy_uczenia = [dane_forum.lematy_pytania(r['pytanie']) for r in uczenie]
    klasy_uczenia = [dane_forum.klasa(r['board']) for r in uczenie]
    tablice = tablice_wag(lematy_uczenia, klasy_uczenia)
    print(f'tablica: {len(tablice)} klas, {sum(len(t) for t in tablice.values())} wpisow razem')

    surowe_kal = [decyzja(dane_forum.lematy_pytania(r['pytanie']), tablice) for r in kalibracja]
    wyniki_sort = sorted(w for _p, w, _m in surowe_kal)
    marginesy_sort = sorted(m for _p, _w, m in surowe_kal)

    punkty_kal = zbuduj_punkty(kalibracja, tablice, wyniki_sort, marginesy_sort)
    punkty_test = zbuduj_punkty(test, tablice, wyniki_sort, marginesy_sort)

    krzywa_kal = siatka(punkty_kal, wyniki_sort, marginesy_sort)

    from measure import GOLDEN
    from measure_sprzedaz import golden_sprzedaz
    golden_pytania = [g['query'] if isinstance(g, dict) else g
                      for g in list(GOLDEN) + list(golden_sprzedaz('pl'))]
    przemiat = przemiataj_bramki(
        punkty_kal, punkty_test, wyniki_sort, marginesy_sort,
        surowe_punkty([r['pytanie'] for r in dane_forum.wczytaj(('ood',))], tablice),
        surowe_punkty(golden_pytania, tablice),
    )

    # Punkt pracy wybierany pod WSZYSTKIE trzy ograniczenia naraz, nie pod jedno.
    # Wybor pod sama precyzje daje progi luzne (pokrycie 0,54), ktore przepuszczaja
    # 28% OOD; wybor pod samo pokrycie 0,30 daje progi ciasne, przy ktorych golden
    # przekracza je w 4%, czyli oferta na produkcji nie pojawilaby sie prawie nigdy.
    # Dopiero przemiat pokazuje, ze pas spelniajacy komplet ograniczen istnieje.
    if przemiat['wybrany'] is not None:
        wybrany = przemiat['wybrany']
    else:
        dopuszczalne = [w for w in krzywa_kal
                        if w['precyzja'] >= BRAMKA_PRECYZJI and w['pokrytych'] >= 20]
        wybrany = (max(dopuszczalne, key=lambda w: (w['pokrycie'], w['precyzja']))
                   if dopuszczalne else max(krzywa_kal, key=lambda w: (w['precyzja'], w['pokrycie'])))
        print('UWAGA: zaden punkt siatki nie spelnia kompletu bramek, '
              'wybrany punkt tylko pod precyzje')

    tau_w, tau_m = wybrany['tau_wynik'], wybrany['tau_margines']
    print(f'punkt pracy: TAU_WYNIK={tau_w} TAU_MARGINES={tau_m}')
    print(f'  kalibracja: pokrycie {wybrany["pokrycie"]} precyzja {wybrany["precyzja"]}')
    print(f'  OOD {wybrany.get("ood")} golden {wybrany.get("golden")}')

    test_w_punkcie = punkt_siatki(punkty_test, tau_w, tau_m)
    test_30 = precyzja_przy_pokryciu(punkty_test, POKRYCIE_DECYZYJNE)

    # Dwa punkty skrajne, zachowane do raportu, zeby bylo widac caly kompromis.
    skrajny_precyzja = max(
        [w for w in krzywa_kal if w['precyzja'] >= BRAMKA_PRECYZJI and w['pokrytych'] >= 20]
        or krzywa_kal, key=lambda w: (w['pokrycie'], w['precyzja']))
    wybrany_30 = min(krzywa_kal, key=lambda w: (abs(w['pokrycie'] - POKRYCIE_DECYZYJNE),
                                                -w['precyzja']))
    tau_w30, tau_m30 = wybrany_30['tau_wynik'], wybrany_30['tau_margines']

    knn_test = odniesienie_knn(rekordy, wektory, foldy, 'test')
    knn_30 = precyzja_przy_pokryciu(knn_test, POKRYCIE_DECYZYJNE)
    knn_pelne = round(sum(1 for p in knn_test if p['pred'] == p['prawda']) / len(knn_test), 4)

    knn_uczenie = odniesienie_knn(rekordy, wektory, foldy, 'test', populacja='uczenie')
    knn_uczenie_30 = precyzja_przy_pokryciu(knn_uczenie, POKRYCIE_DECYZYJNE)
    knn_uczenie_pelne = round(
        sum(1 for p in knn_uczenie if p['pred'] == p['prawda']) / len(knn_uczenie), 4)

    strona_test = odniesienie_strona(test, klasy_uczenia, [r['board'] for r in uczenie])
    strona_pelne = round(sum(1 for p in strona_test if p['pred'] == p['prawda']) / len(strona_test), 4)
    # Ta sama podproba, ktora bierze model przy pokryciu 0,30: inaczej porownywalibysmy
    # trafnosc na latwych pytaniach z trafnoscia na wszystkich.
    ile = max(1, int(round(POKRYCIE_DECYZYJNE * len(punkty_test))))
    kolejnosc = sorted(range(len(punkty_test)), key=lambda i: -punkty_test[i]['pewnosc'])[:ile]
    strona_na_podprobie = round(
        sum(1 for i in kolejnosc if strona_test[i]['pred'] == strona_test[i]['prawda']) / len(kolejnosc), 4)

    przewaga_strona = round(test_30['precyzja'] - strona_na_podprobie, 4)
    przewaga_knn = round(test_30['precyzja'] - knn_30['precyzja'], 4)

    ood = kontrola_ood(tablice, tau_w, tau_m)
    golden = kalibracja_golden(tablice, tau_w, tau_m)
    ood_30 = kontrola_ood(tablice, tau_w30, tau_m30)
    golden_30 = kalibracja_golden(tablice, tau_w30, tau_m30)
    ood_luzny = kontrola_ood(tablice, skrajny_precyzja['tau_wynik'], skrajny_precyzja['tau_margines'])
    golden_luzny = kalibracja_golden(tablice, skrajny_precyzja['tau_wynik'],
                                     skrajny_precyzja['tau_margines'])

    najmocniejsze = {
        klasa: [[t, z] for t, z in sorted(tablice[klasa].items(), key=lambda p: -p[1])[:NAJMOCNIEJSZYCH_DO_RAPORTU]]
        for klasa in sorted(tablice)
    }

    zapisz_modul(tablice, tau_w, tau_m, len(uczenie))
    print(f'zapisano {MODUL}')

    czas = {}
    if not args.bez_czasu:
        proces = subprocess.run([sys.executable, str(SKRYPT_CZASU)], capture_output=True, text=True)
        czas = {'stdout': proces.stdout.strip(), 'kod': proces.returncode}
        print(proces.stdout.strip() or proces.stderr.strip()[-800:])

    wynik = {
        'przebieg': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'parametry': {'alfa0': ALFA0, 'df_min': DF_MIN, 'max_na_klase': MAX_NA_KLASE,
                      'k_sasiadow': K_SASIADOW},
        'wycinki': {'uczenie': len(uczenie), 'kalibracja': len(kalibracja), 'test': len(test)},
        'klasy': dict(Counter(klasy_uczenia).most_common()),
        'tablica': {'klas': len(tablice), 'wpisow': sum(len(t) for t in tablice.values())},
        'punkt_pracy': {'tau_wynik': tau_w, 'tau_margines': tau_m,
                        'kalibracja': wybrany, 'test': test_w_punkcie},
        'punkty_skrajne': {
            'tylko_precyzja': {
                'tau_wynik': skrajny_precyzja['tau_wynik'],
                'tau_margines': skrajny_precyzja['tau_margines'],
                'kalibracja': skrajny_precyzja,
                'ood': ood_luzny['przekroczylo_progi'],
                'golden': golden_luzny['przekroczylo_progi'],
            },
            'pokrycie_030': {
                'tau_wynik': tau_w30, 'tau_margines': tau_m30,
                'kalibracja': wybrany_30,
                'test': punkt_siatki(punkty_test, tau_w30, tau_m30),
                'ood': ood_30['przekroczylo_progi'],
                'golden': golden_30['przekroczylo_progi'],
            },
        },
        'krzywa_kalibracja': krzywa_kal,
        'obwiednia_kalibracja': obwiednia(krzywa_kal),
        'obwiednia_test': obwiednia(siatka(punkty_test, wyniki_sort, marginesy_sort)),
        'metryka_decyzyjna': {
            'pokrycie': POKRYCIE_DECYZYJNE,
            'model_liniowy': test_30,
            'knn': knn_30,
            'knn_tylko_uczenie': knn_uczenie_30,
            'wiekszosc_w_stronie_na_tej_samej_podprobie': strona_na_podprobie,
            'przewaga_nad_strona': przewaga_strona,
            'przewaga_nad_knn': przewaga_knn,
            'przewaga_nad_knn_tylko_uczenie': round(
                test_30['precyzja'] - knn_uczenie_30['precyzja'], 4),
            'bramki': {
                'precyzja': test_30['precyzja'] >= BRAMKA_PRECYZJI,
                'przewaga_strona': przewaga_strona >= BRAMKA_PRZEWAGI_STRONA,
                'przewaga_knn': przewaga_knn >= BRAMKA_PRZEWAGI_KNN,
            },
        },
        'odniesienia_pelne_pokrycie': {
            'wiekszosc_w_stronie': strona_pelne,
            'knn': knn_pelne,
            'knn_tylko_uczenie': knn_uczenie_pelne,
            'model_liniowy': round(
                sum(1 for p in punkty_test if p['pred'] == p['prawda']) / len(punkty_test), 4),
        },
        'ood': ood,
        'golden': golden,
        'przemiat_bramek': przemiat,
        'czas': czas,
        'najmocniejsze_lematy': najmocniejsze,
    }

    dane_forum.OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(WYJSCIE, 'w', encoding='utf-8') as f:
        json.dump(wynik, f, ensure_ascii=False, indent=1)

    print()
    print(f'--- wycinek testowy, pokrycie {POKRYCIE_DECYZYJNE} ---')
    print(f'model liniowy:            precyzja {test_30["precyzja"]:.3f} '
          f'({test_30["trafionych"]}/{test_30["pokrytych"]})')
    print(f'kNN (10 sasiadow):        precyzja {knn_30["precyzja"]:.3f} '
          f'({knn_30["trafionych"]}/{knn_30["pokrytych"]})')
    print(f'kNN tylko na uczeniu:     precyzja {knn_uczenie_30["precyzja"]:.3f} '
          f'({knn_uczenie_30["trafionych"]}/{knn_uczenie_30["pokrytych"]}) '
          '- ta sama populacja co model liniowy')
    print(f'wiekszosc w stronie:      precyzja {strona_na_podprobie:.3f} (ta sama podproba)')
    print(f'przewaga nad strona: {przewaga_strona:+.3f} (bramka >= {BRAMKA_PRZEWAGI_STRONA})')
    print(f'przewaga nad kNN:    {przewaga_knn:+.3f} (bramka >= {BRAMKA_PRZEWAGI_KNN})')
    print()
    print('--- pelne pokrycie (bez progow) ---')
    print(f'model liniowy {wynik["odniesienia_pelne_pokrycie"]["model_liniowy"]:.3f}, '
          f'kNN {knn_pelne:.3f}, wiekszosc w stronie {strona_pelne:.3f}')
    print()
    print('--- kompromis progow, trzy punkty ---')
    print(f'{"punkt":34s} {"pokrycie":>9s} {"precyzja":>9s} {"OOD":>7s} {"golden":>7s}')
    print(f'{"tylko precyzja (luzny)":34s} {skrajny_precyzja["pokrycie"]:9.3f} '
          f'{skrajny_precyzja["precyzja"]:9.3f} {ood_luzny["przekroczylo_progi"]:7.3f} '
          f'{golden_luzny["przekroczylo_progi"]:7.3f}')
    print(f'{"WYBRANY (komplet bramek)":34s} {wybrany["pokrycie"]:9.3f} '
          f'{wybrany["precyzja"]:9.3f} {wybrany.get("ood", 0):7.3f} {wybrany.get("golden", 0):7.3f}')
    print(f'{"pokrycie 0,30 (ciasny)":34s} {wybrany_30["pokrycie"]:9.3f} '
          f'{wybrany_30["precyzja"]:9.3f} {ood_30["przekroczylo_progi"]:7.3f} '
          f'{golden_30["przekroczylo_progi"]:7.3f}')
    print(f'bramki: OOD < {BRAMKA_OOD}, golden >= {BRAMKA_GOLDEN}, precyzja >= {BRAMKA_PRECYZJI}')
    print()
    print(f'wybrany punkt na WYCINKU TESTOWYM: pokrycie {test_w_punkcie["pokrycie"]} '
          f'precyzja {test_w_punkcie["precyzja"]} ({test_w_punkcie["pokrytych"]} pytan)')
    print()
    print('--- czy ISTNIEJE para progow spelniajaca bramke OOD i weto naraz ---')
    print(f'punktow siatki: {przemiat["punktow_siatki"]}')
    print(f'  spelnia OOD < {BRAMKA_OOD} oraz golden >= {BRAMKA_GOLDEN}: '
          f'{przemiat["spelnia_ood_i_golden"]}')
    print(f'  spelnia dodatkowo precyzje >= {BRAMKA_PRECYZJI} na tescie: '
          f'{przemiat["spelnia_ood_golden_i_precyzje"]}')
    naj = przemiat['najlepszy_kompromis']
    print(f'  najlepszy kompromis (golden minus OOD): golden {naj["golden"]}, ood {naj["ood"]}, '
          f'pokrycie {naj["pokrycie"]}, precyzja {naj["precyzja"]}')
    for w in przemiat['punkty_spelniajace'][:5]:
        print(f'    pokrycie {w["pokrycie"]} precyzja {w["precyzja"]} '
              f'ood {w["ood"]} golden {w["golden"]}')
    print()
    print(f'zapisano {WYJSCIE}')


if __name__ == '__main__':
    main()
