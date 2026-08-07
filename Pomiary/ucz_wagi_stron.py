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

import hashlib
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
from measure_routing_strony import prior_markery, MARKERY_R5_CZYSTY_PL

ALFA0 = 500.0
Z_MIN = 1.96
DF_MIN = 20
MAX_WPISOW = 400
PRECYZJA_MIN_MOCNY = 0.85
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
        if df < DF_MIN:
            continue
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
    dodatki, obalone = {}, []
    for lemat, strona in manualne_lematy().items():
        oczekiwany_znak = 1.0 if strona == 'sprzedajacy' else -1.0
        if lemat in z_dane:
            info = z_dane[lemat]
            znak_danych = 1.0 if info['z'] > 0 else -1.0
            if znak_danych != oczekiwany_znak:
                obalone.append({'lemat': lemat, 'strona_manualna': strona,
                                 'z': round(info['z'], 3), 'df': info['df']})
        else:
            dodatki[lemat] = oczekiwany_znak * Z_MIN
    return dodatki, obalone


def zbuduj_tabele(z_dane: dict, dodatki_manualne: dict) -> dict[str, float]:
    tabela = {t: info['z'] for t, info in z_dane.items() if abs(info['z']) >= Z_MIN}
    for lemat, waga in dodatki_manualne.items():
        tabela.setdefault(lemat, waga)
    posortowane = sorted(tabela.items(), key=lambda kv: abs(kv[1]), reverse=True)[:MAX_WPISOW]
    return dict(posortowane)


def suma_wazona(lematy_pytania: set, tabela: dict) -> float:
    return sum(tabela[t] for t in lematy_pytania if t in tabela)


def przewidziana_strona(suma: float) -> str | None:
    if suma > 0:
        return 'sprzedajacy'
    if suma < 0:
        return 'kupujacy'
    return None


def wpisy_do_krzywej(rekordy: list[dict], tabela: dict) -> list[tuple[float, bool]]:
    wpisy = []
    for r in rekordy:
        suma = suma_wazona(r['lematy'], tabela)
        wpisy.append((abs(suma), przewidziana_strona(suma) == r['etykieta']))
    return wpisy


def krzywa_z_wpisow(wpisy: list[tuple[float, bool]]) -> list[dict]:
    progi = sorted({w[0] for w in wpisy if w[0] > 0}, reverse=True)
    n = len(wpisy)
    krzywa = []
    for prog in progi:
        objete = [poprawne for waga, poprawne in wpisy if waga >= prog]
        krzywa.append({
            'prog': round(prog, 4),
            'pokrycie': round(len(objete) / n, 4),
            'precyzja': round(sum(objete) / len(objete), 4) if objete else 0.0,
            'n_objete': len(objete),
        })
    return krzywa


def wybierz_tau_mocny(krzywa: list[dict]) -> float:
    kandydaci = [w for w in krzywa if w['precyzja'] >= PRECYZJA_MIN_MOCNY]
    if not kandydaci:
        return krzywa[0]['prog'] if krzywa else float('inf')
    return min(kandydaci, key=lambda w: w['prog'])['prog']


def trafnosc_dla_progu(rekordy: list[dict], tabela: dict, tau_slaby: float) -> float:
    poprawne = 0
    for r in rekordy:
        suma = suma_wazona(r['lematy'], tabela)
        strona = przewidziana_strona(suma)
        if strona is None or abs(suma) < tau_slaby:
            continue
        if strona == r['etykieta']:
            poprawne += 1
    return poprawne / len(rekordy)


def wybierz_tau_slaby(rekordy: list[dict], tabela: dict, tau_mocny: float) -> tuple[float, float]:
    sumy_abs = {round(abs(suma_wazona(r['lematy'], tabela)), 4) for r in rekordy}
    progi_kandydujace = sorted(p for p in sumy_abs if p <= tau_mocny)
    najlepszy_prog = tau_mocny
    najlepsza_trafnosc = trafnosc_dla_progu(rekordy, tabela, tau_mocny)
    for prog in progi_kandydujace:
        trafnosc = trafnosc_dla_progu(rekordy, tabela, prog)
        if trafnosc > najlepsza_trafnosc:
            najlepsza_trafnosc, najlepszy_prog = trafnosc, prog
    return najlepszy_prog, najlepsza_trafnosc


def trafnosc_r5_czysty(rekordy: list[dict]) -> float:
    poprawne = 0
    for r in rekordy:
        strona, _ = prior_markery(r['pytanie'], None, False, MARKERY_R5_CZYSTY_PL)
        if strona == r['etykieta']:
            poprawne += 1
    return poprawne / len(rekordy)


def zapisz_modul(tabela: dict, tau_mocny: float, tau_slaby: float, n_calosc: int) -> None:
    stempel = datetime.now(timezone.utc).isoformat()
    linie = [
        f"# Wygenerowano przez Pomiary/ucz_wagi_stron.py, {stempel} UTC, na {n_calosc}",
        f"# przykladach z RAG/pytania_realne.jsonl (cala baza). TAU_MOCNY/TAU_SLABY to srednia",
        f"# z 5 foldow walidacji krzyzowej. Patrz Pomiary/PLAN_WAGI_STRON.md,",
        f"# Pomiary/PLAN_POMIARY_GPU.md i Pomiary/POMIAR_WAGI_STRON.md. Nie edytowac recznie,",
        f"# ponowne uruchomienie skryptu nadpisuje ten plik.",
        "",
        "import simplemma",
        "from spell import tokenize_words, MIN_DLUGOSC",
        "",
        f"TAU_MOCNY = {tau_mocny!r}",
        f"TAU_SLABY = {tau_slaby!r}",
        "",
        "WAGI = {",
    ]
    for lemat, waga in sorted(tabela.items(), key=lambda kv: -abs(kv[1])):
        linie.append(f"    {lemat!r}: {waga!r},")
    linie.append("}")
    linie.append("")
    linie.append("")
    linie.append("def prior_wazony(query, agent_poprzedni, lang, czy_followup):")
    linie.append("    if lang == 'pl':")
    linie.append("        tokeny = [t for t in tokenize_words(query) if len(t) >= MIN_DLUGOSC]")
    linie.append("        lematy_pytania = {simplemma.lemmatize(t, lang='pl') for t in tokeny}")
    linie.append("        suma = sum(WAGI[t] for t in lematy_pytania if t in WAGI)")
    linie.append("        if abs(suma) >= TAU_MOCNY:")
    linie.append("            return ('sprzedajacy' if suma > 0 else 'kupujacy'), 'leksykalna'")
    linie.append("        if agent_poprzedni and czy_followup:")
    linie.append("            strona = 'sprzedajacy' if agent_poprzedni == 'sprzedaz' else 'kupujacy'")
    linie.append("            return strona, 'lepka'")
    linie.append("        if abs(suma) >= TAU_SLABY:")
    linie.append("            return ('sprzedajacy' if suma > 0 else 'kupujacy'), 'leksykalna_slaba'")
    linie.append("        return None, None")
    linie.append("    if agent_poprzedni and czy_followup:")
    linie.append("        strona = 'sprzedajacy' if agent_poprzedni == 'sprzedaz' else 'kupujacy'")
    linie.append("        return strona, 'lepka'")
    linie.append("    return None, None")
    linie.append("")

    plik = SRC / 'wagi_stron.py'
    plik.write_text('\n'.join(linie), encoding='utf-8')
    print(f'zapisano: {plik}')


def main() -> None:
    rekordy = wczytaj_wszystkie()
    p_tla = policz_p_tla(rekordy)
    liczebnosc_foldow = Counter(r['fold'] for r in rekordy)
    print(f'rekordow razem: {len(rekordy)}, foldy: {dict(sorted(liczebnosc_foldow.items()))}')

    wpisy_poza_foldem = []
    trafnosci_foldow, tau_mocny_foldow, tau_slaby_foldow = [], [], []

    for test_fold in range(LICZBA_FOLDOW):
        kalibracja_fold = (test_fold + 1) % LICZBA_FOLDOW
        trening = [r for r in rekordy if r['fold'] not in (test_fold, kalibracja_fold)]
        kalibracja = [r for r in rekordy if r['fold'] == kalibracja_fold]
        test = [r for r in rekordy if r['fold'] == test_fold]

        z_dane_fold, _, _ = policz_z(trening, p_tla)
        dodatki_fold, _ = audytuj_manualne(z_dane_fold)
        tabela_fold = zbuduj_tabele(z_dane_fold, dodatki_fold)

        krzywa_kal = krzywa_z_wpisow(wpisy_do_krzywej(kalibracja, tabela_fold))
        tau_mocny = wybierz_tau_mocny(krzywa_kal)
        tau_slaby, _ = wybierz_tau_slaby(kalibracja, tabela_fold, tau_mocny)

        wpisy_test = wpisy_do_krzywej(test, tabela_fold)
        wpisy_poza_foldem.extend(wpisy_test)
        trafnosc_foldu = trafnosc_dla_progu(test, tabela_fold, tau_slaby)

        print(f'fold {test_fold}: trening={len(trening)} kalibracja={len(kalibracja)} '
              f'test={len(test)} tabela={len(tabela_fold)} TAU_MOCNY={tau_mocny:.3f} '
              f'TAU_SLABY={tau_slaby:.3f} trafnosc_out_of_fold={trafnosc_foldu:.4f}')

        trafnosci_foldow.append(trafnosc_foldu)
        tau_mocny_foldow.append(tau_mocny)
        tau_slaby_foldow.append(tau_slaby)

    trafnosc_srednia = statistics.mean(trafnosci_foldow)
    trafnosc_std = statistics.stdev(trafnosci_foldow)
    print(f'\n=== walidacja krzyzowa, {LICZBA_FOLDOW} foldow ===')
    print(f'trafnosc pierwszej tury (r9) per fold: {[round(t, 4) for t in trafnosci_foldow]}')
    print(f'srednia: {trafnosc_srednia:.4f}, odchylenie std.: {trafnosc_std:.4f} '
          f'(bramka: < 0.04, {"PRZESZLA" if trafnosc_std < 0.04 else "NIE PRZESZLA"})')

    trafnosc_r5c = trafnosc_r5_czysty(rekordy)
    print(f'trafnosc pierwszej tury (r5_czysty, cala baza, punkt odniesienia): {trafnosc_r5c:.4f}')
    print(f'przewaga r9 (srednia z foldow) nad r5_czysty: {trafnosc_srednia - trafnosc_r5c:+.4f}')

    krzywa_pelna = krzywa_z_wpisow(wpisy_poza_foldem)

    tau_mocny_prod = statistics.mean(tau_mocny_foldow)
    tau_slaby_prod = statistics.mean(tau_slaby_foldow)
    print(f'\nTAU_MOCNY produkcyjne (srednia z foldow): {tau_mocny_prod:.4f}')
    print(f'TAU_SLABY produkcyjne (srednia z foldow): {tau_slaby_prod:.4f}')

    z_dane_pelne, n_s, n_k = policz_z(rekordy, p_tla)
    print(f'\nn_s (sprzedajacy, cala baza): {n_s}, n_k (kupujacy, cala baza): {n_k}')
    print(f'lematow z df >= {DF_MIN}: {len(z_dane_pelne)}')

    dodatki_manualne, obalone = audytuj_manualne(z_dane_pelne)
    tabela_prod = zbuduj_tabele(z_dane_pelne, dodatki_manualne)
    print(f'tabela produkcyjna: {len(tabela_prod)} wpisow (limit {MAX_WPISOW}), '
          f'w tym {len(dodatki_manualne)} dodatkow manualnych (df < {DF_MIN})')

    posortowane = sorted(tabela_prod.items(), key=lambda kv: kv[1])
    top_kupujacy = posortowane[:TOP_N_RAPORT]
    top_sprzedaz = list(reversed(posortowane[-TOP_N_RAPORT:]))

    print(f'\n=== top {TOP_N_RAPORT} lematow, kupujacy (z ujemne) ===')
    for lemat, z in top_kupujacy:
        print(f'  {lemat:20s} z={z:+.3f}')
    print(f'\n=== top {TOP_N_RAPORT} lematow, sprzedajacy (z dodatnie) ===')
    for lemat, z in top_sprzedaz:
        print(f'  {lemat:20s} z={z:+.3f}')

    print(f'\n=== markery reczne obalone przez dane (df >= {DF_MIN}, przeciwny znak) ===')
    if not obalone:
        print('  brak')
    for wpis in obalone:
        print(f"  {wpis['lemat']:20s} manualnie={wpis['strona_manualna']:12s} "
              f"z_danych={wpis['z']:+.3f} df={wpis['df']}")

    zapisz_modul(tabela_prod, tau_mocny_prod, tau_slaby_prod, len(rekordy))

    OUT_DIR.mkdir(exist_ok=True)
    wynik = {
        'czas_utc': datetime.now(timezone.utc).isoformat(),
        'n_razem': len(rekordy), 'liczba_foldow': LICZBA_FOLDOW,
        'liczebnosc_foldow': {str(k): v for k, v in sorted(liczebnosc_foldow.items())},
        'n_s_calosc': n_s, 'n_k_calosc': n_k,
        'lematow_df_min': len(z_dane_pelne), 'rozmiar_tabeli_produkcyjnej': len(tabela_prod),
        'dodatkow_manualnych': len(dodatki_manualne), 'obalone_markery': obalone,
        'top_kupujacy': [{'lemat': l, 'z': round(z, 3)} for l, z in top_kupujacy],
        'top_sprzedaz': [{'lemat': l, 'z': round(z, 3)} for l, z in top_sprzedaz],
        'trafnosc_foldow_r9': [round(t, 4) for t in trafnosci_foldow],
        'trafnosc_r9_srednia': round(trafnosc_srednia, 4),
        'trafnosc_r9_odchylenie_std': round(trafnosc_std, 4),
        'stabilnosc_bramka_0_04': trafnosc_std < 0.04,
        'trafnosc_r5_czysty_cala_baza': round(trafnosc_r5c, 4),
        'tau_mocny_foldow': [round(t, 4) for t in tau_mocny_foldow],
        'tau_slaby_foldow': [round(t, 4) for t in tau_slaby_foldow],
        'tau_mocny_produkcyjne': round(tau_mocny_prod, 4),
        'tau_slaby_produkcyjne': round(tau_slaby_prod, 4),
        'krzywa_poza_foldem_pelna_baza': krzywa_pelna,
        'z_min': Z_MIN, 'df_min': DF_MIN, 'alfa0': ALFA0,
        'precyzja_min_mocny': PRECYZJA_MIN_MOCNY,
    }
    plik_wynik = OUT_DIR / 'ucz_wagi_stron.json'
    plik_wynik.write_text(json.dumps(wynik, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'zapisano: {plik_wynik}')


if __name__ == '__main__':
    main()
