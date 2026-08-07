# Krok 5 z PLAN_POMIARY_GPU.md (nadrzedny wobec pojedynczego podzialu z Kroku 3
# PLAN_WAGI_STRON.md: "pomiar idzie na pelna baze z pieciokrotna walidacja krzyzowa zamiast
# na jeden wycinek testowy"). Piec foldow, sha1(guards.normalizuj(pytanie)) mod 100 // 20.
# W kazdym foldzie: tabela wag uczona na pozostalych 3 foldach (log-odds z informacyjnym
# priorem Dirichleta, Monroe/Colaresi/Quinn 2008: dla lematu t, y_s/y_k obecnosc w pytaniach
# danej strony, n_s/n_k licznosci klas, alfa_t = ALFA0 * p_tla(t), p_tla liczone na calej
# bazie), TAU_MOCNY/TAU_SLABY kalibrowane na czwartym foldzie (krzywa pokrycia wobec
# precyzji), ocena na piatym, dotad nie widzianym foldzie. Trafnosc pierwszej tury i
# stabilnosc (odchylenie std. po 5 foldach) licza sie z tych wylacznie out-of-fold
# przewidywan, krzywa w raporcie to pula wszystkich 3896 out-of-fold wpisow. Produkcyjny
# src/wagi_stron.py uczony na calej bazie, progi to srednia z 5 foldow. Liczy tez wariant
# "reczna poprawka list" (r5_czysty) jako punkt odniesienia, ten sam dla kazdego foldu bo
# nie jest uczony z danych.
#
# Uzycie:
#     python ucz_wagi_stron.py

import ast
import hashlib
import inspect
import json
import math
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
OUT_DIR = ROOT / 'outputs'
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import simplemma
from spell import tokenize_words, MIN_DLUGOSC
from lang_config import LANG
from guards import normalizuj
from strony import prior_strony
from measure_routing_strony import prior_markery, MARKERY_R5_CZYSTY_PL

ALFA0 = 500.0
Z_MIN = 1.96
DF_MIN = 20
MAX_WPISOW = 400
PRECYZJA_MIN_MOCNY = 0.85
BRAMKA_ODSETEK_ZBYTYCH = 0.15
# P4: zadna wartosc z SIATKA_Z_SILNY nie spelnila ograniczen (outputs/przemiatanie_z_silny.json,
# wszyscy_dopuszczalni pusty). 3.5 wygralo remis na liczbie naruszen z 4.0 i 4.5 kolejnoscia w
# siatce, nie jakoscia. Zostaje, bo caly Krok 8 i POMIAR_WAGI_STRON.md policzono przy tej wartosci.
Z_SILNY_PRODUKCYJNY = 3.5
TOP_N_RAPORT = 40
LICZBA_FOLDOW = 5

STRONA_JSONL_DO_ETYKIETY = {'sprzedaz': 'sprzedajacy', 'kupujacy': 'kupujacy'}


def piaty_fold(pytanie: str) -> int:
    cyfra = int(hashlib.sha1(normalizuj(pytanie).encode('utf-8')).hexdigest(), 16) % 100
    return cyfra // 20


def lematy(tekst: str) -> set:
    return {simplemma.lemmatize(t, lang='pl')
            for t in tokenize_words(tekst) if len(t) >= MIN_DLUGOSC}


def wczytaj_wszystkie() -> list[dict]:
    plik = ROOT / 'RAG' / 'pytania_realne.jsonl'
    rekordy = []
    with open(plik, encoding='utf-8') as f:
        for linia in f:
            w = json.loads(linia)
            if w['strona'] not in STRONA_JSONL_DO_ETYKIETY:
                continue
            rekordy.append({
                'pytanie': w['pytanie'],
                'etykieta': STRONA_JSONL_DO_ETYKIETY[w['strona']],
                'fold': piaty_fold(w['pytanie']),
                'lematy': lematy(w['pytanie']),
            })
    return rekordy


def policz_p_tla(rekordy: list[dict]) -> dict[str, float]:
    n = len(rekordy)
    df = Counter()
    for r in rekordy:
        df.update(r['lematy'])
    return {t: c / n for t, c in df.items()}


def policz_z(rekordy_uczenie: list[dict], p_tla: dict[str, float]) -> tuple[dict, int, int]:
    """P0.7: p_tla liczone przez wywolujacego na samym zbiorze uczacym (foldu), nie na calej
    bazie, zeby czestosci tla nie widzialy foldu testowego. P7: brak filtra po DF_MIN tutaj,
    kazdy lemat z co najmniej jednym wystapieniem dostaje realny z-score z danych (filtr po
    DF_MIN przenosi sie do zbuduj_tabele, gdzie decyduje o wejsciu automatycznym, nie tutaj)."""
    y_s, y_k, df_all = Counter(), Counter(), Counter()
    n_s = sum(1 for r in rekordy_uczenie if r['etykieta'] == 'sprzedajacy')
    n_k = sum(1 for r in rekordy_uczenie if r['etykieta'] == 'kupujacy')
    for r in rekordy_uczenie:
        for t in r['lematy']:
            df_all[t] += 1
            if r['etykieta'] == 'sprzedajacy':
                y_s[t] += 1
            else:
                y_k[t] += 1

    wyniki = {}
    for t, df in df_all.items():
        alfa = ALFA0 * p_tla.get(t, 0.0)
        ys, yk = y_s[t], y_k[t]
        delta = (math.log((ys + alfa) / (n_s + ALFA0 - ys - alfa))
                 - math.log((yk + alfa) / (n_k + ALFA0 - yk - alfa)))
        wariancja = 1 / (ys + alfa) + 1 / (yk + alfa)
        z = delta / math.sqrt(wariancja)
        wyniki[t] = {'z': z, 'df': df, 'y_s': ys, 'y_k': yk}
    return wyniki, n_s, n_k


def manualne_lematy() -> dict[str, str]:
    cfg = LANG['pl']['markery_stron']
    wynik = {}
    for strona in ('kupujacy', 'sprzedajacy'):
        for slowo in cfg[strona]['slowa']:
            wynik[simplemma.lemmatize(slowo, lang='pl')] = strona
    return wynik


def audytuj_manualne(z_dane: dict) -> tuple[dict, list]:
    """P7: bez danych (lemat nieobecny, df=0) dostaje wprost oczekiwany_znak * Z_MIN, to jedyny
    prawdziwy przypadek zero-danych. Gdy dane sa, ale ponizej DF_MIN, wchodzi realny z-score z
    danych (male df, wiec sam wariancja/mianownik formuly Monroe go i tak scisnie), zamiast
    pelnej sily Z_MIN bez pokrycia w danych."""
    dodatki, obalone = {}, []
    for lemat, strona in manualne_lematy().items():
        oczekiwany_znak = 1.0 if strona == 'sprzedajacy' else -1.0
        if lemat in z_dane:
            info = z_dane[lemat]
            znak_danych = 1.0 if info['z'] > 0 else -1.0
            if znak_danych != oczekiwany_znak:
                obalone.append({'lemat': lemat, 'strona_manualna': strona,
                                 'z': round(info['z'], 3), 'df': info['df']})
            elif info['df'] < DF_MIN:
                dodatki[lemat] = info['z']
        else:
            dodatki[lemat] = oczekiwany_znak * Z_MIN
    return dodatki, obalone


def zbuduj_tabele(z_dane: dict, dodatki_manualne: dict) -> dict[str, float]:
    tabela = {t: info['z'] for t, info in z_dane.items()
              if info['df'] >= DF_MIN and abs(info['z']) >= Z_MIN}
    for lemat, waga in dodatki_manualne.items():
        tabela.setdefault(lemat, waga)
    posortowane = sorted(tabela.items(), key=lambda kv: (-abs(kv[1]), kv[0]))[:MAX_WPISOW]
    return dict(posortowane)


# P3: suma znormalizowana przez sqrt(k), k = liczba dopasowanych lematow, zeby dlugie
# pytanie nie przekraczalo progu samym nazbieraniem slabych wag. P2: dowod to |z| pojedynczego
# najmocniejszego dopasowanego lematu, osobno od sumy, bo suma wybiera strone, a dowod
# rozstrzyga, czy w ogole wolno miec zdanie.
def ocena_pytania(lematy_pytania: set, tabela: dict) -> dict:
    dopasowane = [tabela[t] for t in lematy_pytania if t in tabela]
    if not dopasowane:
        return {'suma_norm': 0.0, 'dowod': 0.0, 'k': 0}
    suma = sum(dopasowane)
    return {'suma_norm': suma / math.sqrt(len(dopasowane)),
            'dowod': max(abs(w) for w in dopasowane), 'k': len(dopasowane)}


def przewidziana_strona(suma_norm: float) -> str | None:
    if suma_norm > 0:
        return 'sprzedajacy'
    if suma_norm < 0:
        return 'kupujacy'
    return None


def zdecyduj_r9(suma_norm: float, dowod: float, tau_mocny: float, tau_slaby: float,
                 z_silny: float, agent_poprzedni: str | None,
                 czy_followup: bool) -> tuple[str | None, str | None]:
    strona = przewidziana_strona(suma_norm)
    ma_dowod = strona is not None and dowod >= z_silny
    if ma_dowod and abs(suma_norm) >= tau_mocny:
        return strona, 'leksykalna'
    if agent_poprzedni and czy_followup:
        return ('sprzedajacy' if agent_poprzedni == 'sprzedaz' else 'kupujacy'), 'lepka'
    if ma_dowod and abs(suma_norm) >= tau_slaby:
        return strona, 'leksykalna_slaba'
    return None, None


def wpisy_do_krzywej(rekordy: list[dict], tabela: dict, z_silny: float) -> list[tuple[float, bool]]:
    wpisy = []
    for r in rekordy:
        ocena = ocena_pytania(r['lematy'], tabela)
        if ocena['dowod'] < z_silny:
            wpisy.append((0.0, False))
            continue
        wpisy.append((abs(ocena['suma_norm']), przewidziana_strona(ocena['suma_norm']) == r['etykieta']))
    return wpisy


def wilson_dolna(k: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 0.0
    phat = k / n
    denom = 1 + z * z / n
    center = phat + z * z / (2 * n)
    margines = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))
    return (center - margines) / denom


def krzywa_z_wpisow(wpisy: list[tuple[float, bool]]) -> list[dict]:
    progi = sorted({w[0] for w in wpisy if w[0] > 0}, reverse=True)
    n = len(wpisy)
    krzywa = []
    for prog in progi:
        objete = [poprawne for waga, poprawne in wpisy if waga >= prog]
        trafne = sum(objete)
        krzywa.append({
            'prog': round(prog, 4),
            'pokrycie': round(len(objete) / n, 4),
            'precyzja': round(trafne / len(objete), 4) if objete else 0.0,
            'precyzja_dolna_wilson': round(wilson_dolna(trafne, len(objete)), 4),
            'n_objete': len(objete),
        })
    return krzywa


def wybierz_tau_mocny(krzywa: list[dict]) -> float:
    """P0.6: dolna granica Wilsona zamiast punktowej precyzji, zeby prog nie osiadal na
    przypadkowym szczycie krzywej wspartym garstka przykladow (D4/D6)."""
    kandydaci = [w for w in krzywa if w['precyzja_dolna_wilson'] >= PRECYZJA_MIN_MOCNY]
    if not kandydaci:
        return krzywa[0]['prog'] if krzywa else float('inf')
    return min(kandydaci, key=lambda w: w['prog'])['prog']


def wynik_dla_progu(rekordy: list[dict], tabela: dict, tau_slaby: float, z_silny: float) -> dict:
    n = len(rekordy)
    poprawne = zle = 0
    for r in rekordy:
        ocena = ocena_pytania(r['lematy'], tabela)
        if ocena['dowod'] < z_silny:
            continue
        strona = przewidziana_strona(ocena['suma_norm'])
        if strona is None or abs(ocena['suma_norm']) < tau_slaby:
            continue
        if strona == r['etykieta']:
            poprawne += 1
        else:
            zle += 1
    return {'trafnosc': poprawne / n, 'zla_cicha': zle / n,
            'odsetek_zbytych': (n - poprawne - zle) / n,
            'poprawne': poprawne, 'zle': zle, 'n': n}


def trafnosc_dla_progu(rekordy: list[dict], tabela: dict, tau_slaby: float, z_silny: float) -> float:
    return wynik_dla_progu(rekordy, tabela, tau_slaby, z_silny)['trafnosc']


def wybierz_tau_slaby(rekordy: list[dict], tabela: dict, tau_mocny: float,
                       z_silny: float) -> tuple[float, float]:
    """P0.5: metryka karzaca blad (zla_cicha), nie trafnosc/N_stale: ta druga jest niemalejaca
    przy obnizaniu progu (D5), wiec petla ponizej zawsze zwracala minimum. Pierwsza wersja tej
    funkcji dodatkowo odrzucala kazdego kandydata z odsetek_zbytych >= 0.15 w petli wewnetrznej,
    ale ten cel z P4 jest wlasnoscia calej konfiguracji (sprawdzana przez przemiatanie_z_silny),
    nie pojedynczego foldu kalibracji: przy malej tabeli wiekszosc pytan nie dopasowuje zadnego
    lematu, wiec podloga odsetek_zbytych z samej bramki dowodu bywa powyzej 15% niezaleznie od
    progu, i twardy filtr tutaj zapadal zawsze na tau_mocny (TAU_SLABY == TAU_MOCNY dla kazdego
    Z_SILNY, zmierzone w przemiatanie_z_silny.py). Zamiast tego: schodzimy od tau_mocny w dol,
    najnizszy prog przy ktorym zla_cicha nie rosnie ponad minimum osiagniete po drodze."""
    sumy_abs = set()
    for r in rekordy:
        ocena = ocena_pytania(r['lematy'], tabela)
        if ocena['dowod'] >= z_silny:
            sumy_abs.add(round(abs(ocena['suma_norm']), 4))
    progi_kandydujace = sorted((p for p in sumy_abs if p <= tau_mocny), reverse=True)
    najlepszy_prog = tau_mocny
    najlepsza_zla_cicha = wynik_dla_progu(rekordy, tabela, tau_mocny, z_silny)['zla_cicha']
    for prog in progi_kandydujace:
        zla_cicha = wynik_dla_progu(rekordy, tabela, prog, z_silny)['zla_cicha']
        if zla_cicha <= najlepsza_zla_cicha:
            najlepsza_zla_cicha, najlepszy_prog = zla_cicha, prog
    return najlepszy_prog, najlepsza_zla_cicha


def trafnosc_r5_czysty(rekordy: list[dict]) -> float:
    poprawne = 0
    for r in rekordy:
        strona, _ = prior_markery(r['pytanie'], None, False, MARKERY_R5_CZYSTY_PL)
        if strona == r['etykieta']:
            poprawne += 1
    return poprawne / len(rekordy)


def zrodlo_bez_docstringa(funkcja) -> str:
    zrodlo = inspect.getsource(funkcja)
    wezel = ast.parse(zrodlo).body[0]
    pierwszy = wezel.body[0] if wezel.body else None
    if (isinstance(pierwszy, ast.Expr) and isinstance(pierwszy.value, ast.Constant)
            and isinstance(pierwszy.value.value, str)):
        linie = zrodlo.splitlines()
        del linie[pierwszy.lineno - 1:pierwszy.end_lineno]
        return '\n'.join(linie).rstrip()
    return zrodlo.rstrip()


def zapisz_modul(tabela: dict, tau_mocny: float, tau_slaby: float, z_silny: float, n_calosc: int) -> None:
    stempel = datetime.now(timezone.utc).isoformat()
    linie = [
        f"# Wygenerowano przez Pomiary/ucz_wagi_stron.py, {stempel} UTC, na {n_calosc}",
        "# przykladach z RAG/pytania_realne.jsonl (cala baza). TAU_MOCNY i TAU_SLABY to srednia z 5",
        "# foldow walidacji krzyzowej, Z_SILNY to stala wejsciowa wybrana w P4 (przemiatanie_z_silny.py).",
        "# Patrz Pomiary/PLAN_WAGI_STRON.md, Pomiary/PLAN_KALIBRACJA_R9.md i Pomiary/POMIAR_WAGI_STRON.md.",
        "# Nie edytowac recznie, ponowne uruchomienie skryptu nadpisuje ten plik.",
        "",
        "import math",
        "import simplemma",
        "from spell import tokenize_words, MIN_DLUGOSC",
        "from strony import prior_strony",
        "",
        f"TAU_MOCNY = {tau_mocny!r}",
        f"TAU_SLABY = {tau_slaby!r}",
        f"Z_SILNY = {z_silny!r}",
        "",
        "WAGI = {",
    ]
    for lemat, waga in sorted(tabela.items(), key=lambda kv: (-abs(kv[1]), kv[0])):
        linie.append(f"    {lemat!r}: {waga!r},")
    linie.append("}")
    linie.append("")
    linie.append("")
    linie.append(zrodlo_bez_docstringa(ocena_pytania))
    linie.append("")
    linie.append("")
    linie.append(zrodlo_bez_docstringa(przewidziana_strona))
    linie.append("")
    linie.append("")
    linie.append(zrodlo_bez_docstringa(zdecyduj_r9))
    linie.append("")
    linie.append("")
    linie.append("def prior_wazony(query, agent_poprzedni, lang, czy_followup):")
    linie.append("    if lang != 'pl':")
    linie.append("        return prior_strony(query, agent_poprzedni, lang, czy_followup)")
    linie.append("    tokeny = [t for t in tokenize_words(query) if len(t) >= MIN_DLUGOSC]")
    linie.append("    lematy_pytania = {simplemma.lemmatize(t, lang='pl') for t in tokeny}")
    linie.append("    ocena = ocena_pytania(lematy_pytania, WAGI)")
    linie.append("    return zdecyduj_r9(ocena['suma_norm'], ocena['dowod'], TAU_MOCNY, TAU_SLABY, "
                  "Z_SILNY, agent_poprzedni, czy_followup)")
    linie.append("")

    plik = SRC / 'wagi_stron.py'
    plik.write_text('\n'.join(linie), encoding='utf-8')
    print(f'zapisano: {plik}')


def przebieg(rekordy: list[dict], z_silny: float, cichy: bool = False) -> dict:
    """Piec foldow walidacji krzyzowej dla ustalonego Z_SILNY. P0.7: p_tla liczone osobno na
    zbiorze uczacym kazdego foldu (trening), nie raz na calej bazie, zeby fold testowy nie
    wplywal na prior Dirichleta modelu, ktory ma go nie widziec. Uzywane zarowno przez main()
    (pojedynczy przebieg produkcyjny) jak i przez przemiatanie_z_silny.py (P4, siatka po
    Z_SILNY)."""
    def wypisz(tekst: str) -> None:
        if not cichy:
            print(tekst)

    liczebnosc_foldow = Counter(r['fold'] for r in rekordy)
    wypisz(f'rekordow razem: {len(rekordy)}, foldy: {dict(sorted(liczebnosc_foldow.items()))}')

    wpisy_poza_foldem = []
    trafnosci_foldow, tau_mocny_foldow, tau_slaby_foldow = [], [], []
    poprawne_total = zle_total = n_total = 0

    for test_fold in range(LICZBA_FOLDOW):
        kalibracja_fold = (test_fold + 1) % LICZBA_FOLDOW
        trening = [r for r in rekordy if r['fold'] not in (test_fold, kalibracja_fold)]
        kalibracja = [r for r in rekordy if r['fold'] == kalibracja_fold]
        test = [r for r in rekordy if r['fold'] == test_fold]

        p_tla_fold = policz_p_tla(trening)
        z_dane_fold, _, _ = policz_z(trening, p_tla_fold)
        dodatki_fold, _ = audytuj_manualne(z_dane_fold)
        tabela_fold = zbuduj_tabele(z_dane_fold, dodatki_fold)

        krzywa_kal = krzywa_z_wpisow(wpisy_do_krzywej(kalibracja, tabela_fold, z_silny))
        tau_mocny = wybierz_tau_mocny(krzywa_kal)
        tau_slaby, _ = wybierz_tau_slaby(kalibracja, tabela_fold, tau_mocny, z_silny)

        wpisy_test = wpisy_do_krzywej(test, tabela_fold, z_silny)
        wpisy_poza_foldem.extend(wpisy_test)
        wynik_testu = wynik_dla_progu(test, tabela_fold, tau_slaby, z_silny)

        wypisz(f'fold {test_fold}: trening={len(trening)} kalibracja={len(kalibracja)} '
               f'test={len(test)} tabela={len(tabela_fold)} TAU_MOCNY={tau_mocny:.3f} '
               f'TAU_SLABY={tau_slaby:.3f} trafnosc_out_of_fold={wynik_testu["trafnosc"]:.4f} '
               f'zla_cicha_out_of_fold={wynik_testu["zla_cicha"]:.4f}')

        trafnosci_foldow.append(wynik_testu['trafnosc'])
        tau_mocny_foldow.append(tau_mocny)
        tau_slaby_foldow.append(tau_slaby)
        poprawne_total += wynik_testu['poprawne']
        zle_total += wynik_testu['zle']
        n_total += wynik_testu['n']

    trafnosc_srednia = statistics.mean(trafnosci_foldow)
    trafnosc_std = statistics.stdev(trafnosci_foldow)
    wypisz(f'\n=== walidacja krzyzowa, {LICZBA_FOLDOW} foldow, Z_SILNY={z_silny} ===')
    wypisz(f'trafnosc pierwszej tury (r9) per fold: {[round(t, 4) for t in trafnosci_foldow]}')
    wypisz(f'srednia: {trafnosc_srednia:.4f}, odchylenie std.: {trafnosc_std:.4f} '
           f'(bramka: < 0.04, {"PRZESZLA" if trafnosc_std < 0.04 else "NIE PRZESZLA"})')

    trafnosc_r5c = trafnosc_r5_czysty(rekordy)
    wypisz(f'trafnosc pierwszej tury (r5_czysty, cala baza, punkt odniesienia): {trafnosc_r5c:.4f}')
    wypisz(f'przewaga r9 (srednia z foldow) nad r5_czysty: {trafnosc_srednia - trafnosc_r5c:+.4f}')

    krzywa_pelna = krzywa_z_wpisow(wpisy_poza_foldem)
    zla_cicha_pelna = round(zle_total / n_total, 4)
    zbyte_pelna = round((n_total - poprawne_total - zle_total) / n_total, 4)

    tau_mocny_prod = statistics.mean(tau_mocny_foldow)
    tau_slaby_prod = statistics.mean(tau_slaby_foldow)
    wypisz(f'\nTAU_MOCNY produkcyjne (srednia z foldow): {tau_mocny_prod:.4f}')
    wypisz(f'TAU_SLABY produkcyjne (srednia z foldow): {tau_slaby_prod:.4f}')

    p_tla_pelne = policz_p_tla(rekordy)
    z_dane_pelne, n_s, n_k = policz_z(rekordy, p_tla_pelne)
    lematow_df_min = sum(1 for info in z_dane_pelne.values() if info['df'] >= DF_MIN)
    wypisz(f'\nn_s (sprzedajacy, cala baza): {n_s}, n_k (kupujacy, cala baza): {n_k}')
    wypisz(f'lematow z df >= {DF_MIN}: {lematow_df_min} (widzianych lacznie: {len(z_dane_pelne)})')

    dodatki_manualne, obalone = audytuj_manualne(z_dane_pelne)
    tabela_prod = zbuduj_tabele(z_dane_pelne, dodatki_manualne)
    wypisz(f'tabela produkcyjna: {len(tabela_prod)} wpisow (limit {MAX_WPISOW}), '
           f'w tym {len(dodatki_manualne)} dodatkow manualnych (df < {DF_MIN})')

    posortowane = sorted(tabela_prod.items(), key=lambda kv: kv[1])
    top_kupujacy = posortowane[:TOP_N_RAPORT]
    top_sprzedaz = list(reversed(posortowane[-TOP_N_RAPORT:]))

    if not cichy:
        print(f'\n=== top {TOP_N_RAPORT} lematow, kupujacy (z ujemne) ===')
        for lemat, z in top_kupujacy:
            print(f'  {lemat:20s} z={z:+.3f}')
        print(f'\n=== top {TOP_N_RAPORT} lematow, sprzedajacy (z dodatnie) ===')
        for lemat, z in top_sprzedaz:
            print(f'  {lemat:20s} z={z:+.3f}')

        print(f'\n=== markery reczne obalone przez dane (przeciwny znak) ===')
        if not obalone:
            print('  brak')
        for wpis in obalone:
            print(f"  {wpis['lemat']:20s} manualnie={wpis['strona_manualna']:12s} "
                  f"z_danych={wpis['z']:+.3f} df={wpis['df']}")

    return {
        'z_silny': z_silny, 'n_razem': len(rekordy), 'liczba_foldow': LICZBA_FOLDOW,
        'liczebnosc_foldow': {str(k): v for k, v in sorted(liczebnosc_foldow.items())},
        'n_s_calosc': n_s, 'n_k_calosc': n_k,
        'lematow_df_min': lematow_df_min, 'rozmiar_tabeli_produkcyjnej': len(tabela_prod),
        'dodatkow_manualnych': len(dodatki_manualne), 'obalone_markery': obalone,
        'top_kupujacy': [{'lemat': l, 'z': round(z, 3)} for l, z in top_kupujacy],
        'top_sprzedaz': [{'lemat': l, 'z': round(z, 3)} for l, z in top_sprzedaz],
        'trafnosc_foldow_r9': [round(t, 4) for t in trafnosci_foldow],
        'trafnosc_r9_srednia': round(trafnosc_srednia, 4),
        'trafnosc_r9_odchylenie_std': round(trafnosc_std, 4),
        'stabilnosc_bramka_0_04': trafnosc_std < 0.04,
        'zla_cicha_poza_foldem': zla_cicha_pelna, 'odsetek_zbytych_poza_foldem': zbyte_pelna,
        'trafnosc_r5_czysty_cala_baza': round(trafnosc_r5c, 4),
        'tau_mocny_foldow': [round(t, 4) for t in tau_mocny_foldow],
        'tau_slaby_foldow': [round(t, 4) for t in tau_slaby_foldow],
        'tau_mocny_produkcyjne': round(tau_mocny_prod, 4),
        'tau_slaby_produkcyjne': round(tau_slaby_prod, 4),
        'krzywa_poza_foldem_pelna_baza': krzywa_pelna,
        'tabela_prod': tabela_prod,
    }


def main(z_silny: float = Z_SILNY_PRODUKCYJNY) -> dict:
    rekordy = wczytaj_wszystkie()
    wynik = przebieg(rekordy, z_silny)

    zapisz_modul(wynik['tabela_prod'], wynik['tau_mocny_produkcyjne'], wynik['tau_slaby_produkcyjne'],
                 z_silny, wynik['n_razem'])

    OUT_DIR.mkdir(exist_ok=True)
    do_zapisu = {k: v for k, v in wynik.items() if k != 'tabela_prod'}
    do_zapisu['czas_utc'] = datetime.now(timezone.utc).isoformat()
    do_zapisu['z_min'] = Z_MIN
    do_zapisu['df_min'] = DF_MIN
    do_zapisu['alfa0'] = ALFA0
    do_zapisu['precyzja_min_mocny'] = PRECYZJA_MIN_MOCNY
    do_zapisu['bramka_odsetek_zbytych'] = BRAMKA_ODSETEK_ZBYTYCH
    plik_wynik = OUT_DIR / 'ucz_wagi_stron.json'
    plik_wynik.write_text(json.dumps(do_zapisu, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'zapisano: {plik_wynik}')
    return wynik


if __name__ == '__main__':
    main()
