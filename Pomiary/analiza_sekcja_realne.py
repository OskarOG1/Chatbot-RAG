import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import math

WYNIK_PLIK = 'Pomiary/WYNIK_SEKCJA_REALNE.json'
RAPORT_PLIK = 'Pomiary/POMIAR_SEKCJA_REALNE.md'
GOLDEN_PLIK = 'Pomiary/WYNIK_ZLA_ZAKLADKA.json'

STRONY = ('kupujacy', 'sprzedajacy')
PROGI_KOLEJNOSC = ['0.0', '0.25', '0.5', '0.75', '1.0', '1.5', '2.0', 'inf']


def przeciwna(strona):
    return [s for s in STRONY if s != strona][0]


def wilson(sukcesy, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = sukcesy / n
    mianownik = 1 + z * z / n
    srodek = (p + z * z / (2 * n)) / mianownik
    margines = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / mianownik
    return (p, max(0.0, srodek - margines), min(1.0, srodek + margines))


def sukces(kategoria, ramie):
    if ramie == 'dobra_zakladka':
        return kategoria == 'zostal'
    return kategoria != 'zostal'


def oba_maja_kandydata(rekord):
    return rekord['liczba_chunkow_kupujacy'] > 0 and rekord['liczba_chunkow_sprzedajacy'] > 0


def zbierz_komorke(rekordy, ramie, etykieta, prog, tylko_oba_kandydata):
    n = 0
    suk = 0
    for r in rekordy:
        if r['etykieta'] != etykieta:
            continue
        if tylko_oba_kandydata and not oba_maja_kandydata(r):
            continue
        wpis = r['ramiona'][ramie]['progi'][prog]
        n += 1
        if sukces(wpis['kategoria'], ramie):
            suk += 1
    return suk, n


def tabela_dla(rekordy, tylko_oba_kandydata):
    wiersze = []
    for prog in PROGI_KOLEJNOSC:
        suk_dk, n_dk = zbierz_komorke(rekordy, 'dobra_zakladka', 'kupujacy', prog, tylko_oba_kandydata)
        suk_ds, n_ds = zbierz_komorke(rekordy, 'dobra_zakladka', 'sprzedajacy', prog, tylko_oba_kandydata)
        suk_zk, n_zk = zbierz_komorke(rekordy, 'zla_zakladka', 'kupujacy', prog, tylko_oba_kandydata)
        suk_zs, n_zs = zbierz_komorke(rekordy, 'zla_zakladka', 'sprzedajacy', prog, tylko_oba_kandydata)

        p_dk, lo_dk, hi_dk = wilson(suk_dk, n_dk)
        p_ds, lo_ds, hi_ds = wilson(suk_ds, n_ds)
        p_zk, lo_zk, hi_zk = wilson(suk_zk, n_zk)
        p_zs, lo_zs, hi_zs = wilson(suk_zs, n_zs)

        suk_razem = suk_dk + suk_ds + suk_zk + suk_zs
        n_razem = n_dk + n_ds + n_zk + n_zs
        p_razem, lo_razem, hi_razem = wilson(suk_razem, n_razem)

        wiersze.append({
            'prog': prog,
            'dobra_kupujacy': {'n': n_dk, 'sukcesy': suk_dk, 'stopa': p_dk, 'ci_low': lo_dk, 'ci_high': hi_dk},
            'dobra_sprzedajacy': {'n': n_ds, 'sukcesy': suk_ds, 'stopa': p_ds, 'ci_low': lo_ds, 'ci_high': hi_ds},
            'zla_kupujacy': {'n': n_zk, 'sukcesy': suk_zk, 'stopa': p_zk, 'ci_low': lo_zk, 'ci_high': hi_zk},
            'zla_sprzedajacy': {'n': n_zs, 'sukcesy': suk_zs, 'stopa': p_zs, 'ci_low': lo_zs, 'ci_high': hi_zs},
            'razem': {'n': n_razem, 'sukcesy': suk_razem, 'stopa': p_razem, 'ci_low': lo_razem, 'ci_high': hi_razem},
        })
    return wiersze


def udzial_brak_kandydata(rekordy):
    licznik = 0
    total = 0
    rozbicie = {'dobra_zakladka': [0, 0], 'zla_zakladka': [0, 0]}
    for r in rekordy:
        for ramie in ('dobra_zakladka', 'zla_zakladka'):
            siedziba = r['ramiona'][ramie]['siedziba']
            klucz = 'liczba_chunkow_' + siedziba
            total += 1
            rozbicie[ramie][1] += 1
            if r[klucz] == 0:
                licznik += 1
                rozbicie[ramie][0] += 1
    return licznik, total, rozbicie


def znajdz_ucieczki_kupujacy(rekordy, prog='0.5', limit=10):
    wyniki = []
    for r in rekordy:
        if r['etykieta'] != 'kupujacy':
            continue
        wpis = r['ramiona']['dobra_zakladka']['progi'][prog]
        if wpis['kategoria'] == 'zostal':
            continue
        wyniki.append({
            'pytanie': r['pytanie'],
            'kategoria': wpis['kategoria'],
            'przewaga': wpis['przewaga'],
            'tytul_wygrywajacy': r['tytul_top1'],
            'najlepsza_ocena_kupujacy': r['najlepsza_ocena_kupujacy'],
            'najlepsza_ocena_sprzedajacy': r['najlepsza_ocena_sprzedajacy'],
        })
    wyniki.sort(key=lambda w: (w['przewaga'] is None, w['przewaga'] if w['przewaga'] is not None else 0))
    return wyniki[:limit]


def przenosiny_przy_progu(rekordy, prog='0.5'):
    przeniesiono = 0
    for r in rekordy:
        wpis = r['ramiona']['dobra_zakladka']['progi'][prog]
        if wpis['kategoria'] != 'zostal':
            przeniesiono += 1
    return przeniesiono, len(rekordy)


def formatuj_procent(p):
    return f'{p * 100:.1f}%'


def formatuj_stopa(komorka):
    return f"{formatuj_procent(komorka['stopa'])} [{formatuj_procent(komorka['ci_low'])}, {formatuj_procent(komorka['ci_high'])}] (n={komorka['n']})"


def wiersze_markdown(wiersze):
    naglowek = '| prog | dobra: kupujacy | dobra: sprzedajacy | zla: kupujacy | zla: sprzedajacy | razem |'
    separator = '|---|---|---|---|---|---|'
    linie = [naglowek, separator]
    for w in wiersze:
        linie.append(
            f"| {w['prog']} | {formatuj_stopa(w['dobra_kupujacy'])} | {formatuj_stopa(w['dobra_sprzedajacy'])} "
            f"| {formatuj_stopa(w['zla_kupujacy'])} | {formatuj_stopa(w['zla_sprzedajacy'])} | {formatuj_stopa(w['razem'])} |"
        )
    return '\n'.join(linie)


def przedzialy_zachodza(a, b):
    return not (a['ci_high'] < b['ci_low'] or b['ci_high'] < a['ci_low'])


def wybierz_najlepszy(wiersze):
    return max(wiersze, key=lambda w: w['razem']['stopa'])


def glowna():
    with open(WYNIK_PLIK, encoding='utf-8') as f:
        dane = json.load(f)
    rekordy = dane['rekordy']

    tabela_wszystkie = tabela_dla(rekordy, tylko_oba_kandydata=False)
    tabela_oba_kandydata = tabela_dla(rekordy, tylko_oba_kandydata=True)

    licznik_brak, total_brak, rozbicie_brak = udzial_brak_kandydata(rekordy)
    ucieczki = znajdz_ucieczki_kupujacy(rekordy, prog='0.5', limit=10)
    przeniesiono_05, n_05 = przenosiny_przy_progu(rekordy, prog='0.5')

    najlepszy = wybierz_najlepszy(tabela_wszystkie)
    wiersz_05 = next(w for w in tabela_wszystkie if w['prog'] == '0.5')
    bije_05 = najlepszy['prog'] != '0.5' and not przedzialy_zachodza(najlepszy['razem'], wiersz_05['razem'])

    golden = None
    if os.path.exists(GOLDEN_PLIK):
        with open(GOLDEN_PLIK, encoding='utf-8') as f:
            golden = json.load(f)

    wynik = {
        'zrodlo_probki': dane.get('liczba_pytan_probki'),
        'ziarno': dane.get('ziarno'),
        'tabela_wszystkie_pytania': tabela_wszystkie,
        'tabela_oba_maja_kandydata': tabela_oba_kandydata,
        'udzial_brak_kandydata': {
            'licznik': licznik_brak,
            'total': total_brak,
            'udzial': licznik_brak / total_brak if total_brak else 0.0,
            'rozbicie_ramiona': {
                'dobra_zakladka': {'licznik': rozbicie_brak['dobra_zakladka'][0], 'total': rozbicie_brak['dobra_zakladka'][1]},
                'zla_zakladka': {'licznik': rozbicie_brak['zla_zakladka'][0], 'total': rozbicie_brak['zla_zakladka'][1]},
            },
        },
        'przeniesiono_przy_05': {'liczba': przeniesiono_05, 'z': n_05},
        'najlepszy_prog': najlepszy['prog'],
        'najlepszy_bije_05_poza_szumem': bije_05,
        'ucieczki_kupujacy_do_sprzedazy_05': ucieczki,
        'golden_porownanie': golden,
    }

    with open('Pomiary/ANALIZA_SEKCJA_REALNE.json', 'w', encoding='utf-8') as f:
        json.dump(wynik, f, ensure_ascii=False, indent=2)

    zbuduj_raport(wynik, golden)
    print('Analiza zapisana: Pomiary/ANALIZA_SEKCJA_REALNE.json oraz ' + RAPORT_PLIK)
    return wynik


def zbuduj_raport(wynik, golden):
    linie = []
    linie.append('# Pomiar rozstrzygania sekcji na realnych pytaniach forum')
    linie.append('')
    linie.append(f"Probka: {wynik['zrodlo_probki']} pytan, ziarno losowania {wynik['ziarno']}, "
                 f"300 na etykiete (kupujacy, sprzedajacy), filtr zrodlo forum, lang pl.")
    linie.append('')
    linie.append('## Tabela progow, wszystkie pytania')
    linie.append('')
    linie.append(wiersze_markdown(wynik['tabela_wszystkie_pytania']))
    linie.append('')
    linie.append('## Tabela progow, tylko pytania gdzie obie strony mialy kandydata (tam gdzie prog faktycznie decyduje)')
    linie.append('')
    linie.append(wiersze_markdown(wynik['tabela_oba_maja_kandydata']))
    linie.append('')

    ub = wynik['udzial_brak_kandydata']
    linie.append('## Udzial kategorii brak_kandydata')
    linie.append('')
    linie.append(f"Ogolem: {ub['licznik']}/{ub['total']} par pytanie plus ramie ({formatuj_procent(ub['udzial'])}), "
                 f"niezaleznie od progu, bo w tych przypadkach ocena_uzytkownika jest None i przeniesienie jest wymuszone.")
    dz = ub['rozbicie_ramiona']['dobra_zakladka']
    zz = ub['rozbicie_ramiona']['zla_zakladka']
    linie.append(f"Ramie dobra_zakladka: {dz['licznik']}/{dz['total']} ({formatuj_procent(dz['licznik'] / dz['total'])}). "
                 f"Ramie zla_zakladka: {zz['licznik']}/{zz['total']} ({formatuj_procent(zz['licznik'] / zz['total'])}).")
    linie.append('')

    pr = wynik['przeniesiono_przy_05']
    linie.append('## Przeniesienia przy progu 0,5')
    linie.append('')
    linie.append(f"W ramieniu dobra_zakladka (uzytkownik siedzi na etykiecie pytania, czyli scenariusz realny): "
                 f"{pr['liczba']}/{pr['z']} pytan zostalo przeniesionych na druga strone ({formatuj_procent(pr['liczba'] / pr['z'])}).")
    linie.append('')

    linie.append('## Najlepszy prog')
    linie.append('')
    linie.append(f"Najwyzsza wartosc razem to prog {wynik['najlepszy_prog']}. "
                 f"Bije 0,5 poza szumem (przedzialy Wilsona sie nie zachodza): {wynik['najlepszy_bije_05_poza_szumem']}.")
    linie.append('')

    linie.append('## Dziesiec ucieczek: etykieta kupujacy, przeniesieni do sprzedazy przy progu 0,5')
    linie.append('')
    if wynik['ucieczki_kupujacy_do_sprzedazy_05']:
        linie.append('| pytanie | kategoria | przewaga | tytul wygrywajacy |')
        linie.append('|---|---|---|---|')
        for u in wynik['ucieczki_kupujacy_do_sprzedazy_05']:
            przewaga_txt = 'brak' if u['przewaga'] is None else f"{u['przewaga']:.4f}"
            pytanie_txt = u['pytanie'].replace('|', '/')
            tytul_txt = (u['tytul_wygrywajacy'] or '').replace('|', '/')
            linie.append(f"| {pytanie_txt} | {u['kategoria']} | {przewaga_txt} | {tytul_txt} |")
    else:
        linie.append('Brak ucieczek w probce przy tym progu.')
    linie.append('')

    if golden:
        linie.append('## Zestawienie z golden (Pomiary/WYNIK_ZLA_ZAKLADKA.json)')
        linie.append('')
        linie.append('Golden byl mierzony na zbiorze golden (70 pytan), a nie na forum, metodologia identyczna '
                     'co do definicji ramion, ale rozna co do zrodla pytan i wielkosci probki.')
        linie.append('')
        linie.append('| prog | golden razem | forum razem (wszystkie) | forum razem (oba maja kandydata) |')
        linie.append('|---|---|---|---|')
        mapa_wszystkie = {w['prog']: w for w in wynik['tabela_wszystkie_pytania']}
        mapa_oba = {w['prog']: w for w in wynik['tabela_oba_maja_kandydata']}
        for wpis in golden['progi']:
            prog_golden = wpis['przewaga_min']
            klucz = str(prog_golden) if prog_golden < 100 else 'inf'
            if klucz not in mapa_wszystkie:
                continue
            forum_w = mapa_wszystkie[klucz]['razem']['stopa']
            forum_o = mapa_oba[klucz]['razem']['stopa']
            linie.append(f"| {klucz} | {formatuj_procent(wpis['razem_recall_5'])} | {formatuj_procent(forum_w)} | {formatuj_procent(forum_o)} |")
        linie.append('')

    with open(RAPORT_PLIK, 'w', encoding='utf-8') as f:
        f.write('\n'.join(linie) + '\n')


if __name__ == '__main__':
    glowna()
