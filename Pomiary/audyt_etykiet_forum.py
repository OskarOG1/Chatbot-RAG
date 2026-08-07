# Krok 3 z PLAN_KLASYFIKATOR_FORUM.md: audyt szumu etykiet.
#
# Etykieta 'board' mowi, GDZIE uzytkownik napisal, a nie O CZYM pyta. Bez oszacowania
# tego szumu zadnej bramki z kroku 4 nie da sie zinterpretowac: nie wiadomo, czy 0,70
# jest blisko sufitu, czy daleko.
#
# Dwie liczby, obie od czlowieka:
#   klasa_ok        zgodnosc czlowieka z klasa z TAKSONOMIA = sufit mierzalnej trafnosci
#   forum_sensowne  czy link do watku na forum w ogole cos wnosi ponad Centrum Pomocy.
#                   To jest gorne ograniczenie uzytecznosci CALEJ funkcji, niezalezne
#                   od jakosci modelu. Czesc pytan ma jednoznaczna odpowiedz w CP
#                   i forum niczego do nich nie doda.
#
# Skrypt tylko losuje, wypisuje i liczy. Ocenia czlowiek.
#
# Uzycie:
#     python Pomiary/audyt_etykiet_forum.py --wypisz     # generuje plik do wypelnienia
#     (recznie wypelnic pola t/n w outputs/audyt_etykiet_forum.txt)
#     python Pomiary/audyt_etykiet_forum.py --policz     # czyta wypelniony plik

import argparse
import random
import re
from collections import Counter, defaultdict

import dane_forum

WYJSCIE = dane_forum.OUT_DIR / 'audyt_etykiet_forum.txt'
PROBKA = 60
ZIARNO = 42
WYCINEK = 'test'
BRAMKA_SENSOWNOSCI = 0.30

WZORZEC_POZYCJI = re.compile(r'^\[(\d+)\] klasa: (\S+)')
WZORZEC_ODPOWIEDZI = re.compile(r'^\s*(klasa_ok|forum_sensowne) \(t/n\):\s*(\S*)\s*$')


def probka() -> list[dict]:
    """Rozklad po klasach, nie proporcjonalny do licznosci: przy probce 60 klasa
    o 40 rekordach zniknelaby z proporcjonalnego losowania, a to wlasnie na malych
    klasach szum etykiet jest najgrozniejszy."""
    rekordy = [r for r in dane_forum.wczytaj(('forum',))
               if dane_forum.fold(r['pytanie']) == WYCINEK and dane_forum.klasa(r['board'])]

    po_klasie = defaultdict(list)
    for r in rekordy:
        po_klasie[dane_forum.klasa(r['board'])].append(r)

    los = random.Random(ZIARNO)
    for lista in po_klasie.values():
        los.shuffle(lista)

    wybrane = []
    klasy = sorted(po_klasie)
    kolejka = 0
    while len(wybrane) < PROBKA and any(po_klasie[k] for k in klasy):
        k = klasy[kolejka % len(klasy)]
        if po_klasie[k]:
            wybrane.append(po_klasie[k].pop())
        kolejka += 1

    los.shuffle(wybrane)
    return wybrane


def wypisz() -> None:
    wybrane = probka()
    dane_forum.OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(WYJSCIE, 'w', encoding='utf-8') as f:
        f.write(f'# Audyt etykiet forum, wycinek {WYCINEK}, ziarno {ZIARNO}, {len(wybrane)} rekordow.\n')
        f.write('# Wypelnij pola t/n, potem: python Pomiary/audyt_etykiet_forum.py --policz\n')
        f.write('#\n')
        f.write('# klasa_ok:       czy pytanie tematycznie pasuje do podanej klasy\n')
        f.write('# forum_sensowne: czy watek na forum spolecznosci wnosi cos ponad Centrum Pomocy\n')
        f.write('#                 (n dla pytan z jednoznaczna odpowiedzia w CP i dla wpisow,\n')
        f.write('#                  ktore nie sa pytaniem, np. ogloszen Allegro)\n\n')
        for i, r in enumerate(wybrane, 1):
            f.write(f'[{i:03d}] klasa: {dane_forum.klasa(r["board"])}\n')
            f.write(f'      board: {r["board"]}\n')
            f.write(f'      pytanie: {r["pytanie"]}\n')
            f.write(f'      url: {r["url"]}\n')
            f.write('      klasa_ok (t/n):\n')
            f.write('      forum_sensowne (t/n):\n\n')

    rozklad = Counter(dane_forum.klasa(r['board']) for r in wybrane)
    print(f'zapisano {WYJSCIE}: {len(wybrane)} rekordow z wycinka {WYCINEK}')
    print('rozklad po klasach:')
    for k, ile in sorted(rozklad.items()):
        print(f'  {k:24s} {ile}')
    print()
    print('Wypelnij pola t/n recznie, potem uruchom --policz.')


def policz() -> None:
    if not WYJSCIE.exists():
        raise SystemExit(f'brak {WYJSCIE}, najpierw --wypisz')

    pozycje = []
    biezaca = None
    with open(WYJSCIE, encoding='utf-8') as f:
        for linia in f:
            naglowek = WZORZEC_POZYCJI.match(linia)
            if naglowek:
                biezaca = {'numer': int(naglowek.group(1)), 'klasa': naglowek.group(2)}
                pozycje.append(biezaca)
                continue
            odpowiedz = WZORZEC_ODPOWIEDZI.match(linia)
            if odpowiedz and biezaca is not None:
                biezaca[odpowiedz.group(1)] = odpowiedz.group(2).strip().lower()

    if not pozycje:
        raise SystemExit(f'{WYJSCIE} nie zawiera zadnej pozycji')

    def udzial(pole: str) -> tuple[float, int, int]:
        wypelnione = [p for p in pozycje if p.get(pole) in ('t', 'n')]
        tak = sum(1 for p in wypelnione if p[pole] == 't')
        return (tak / len(wypelnione) if wypelnione else 0.0), tak, len(wypelnione)

    zgodnosc, zgodne, ocenione_klasy = udzial('klasa_ok')
    sensownosc, sensowne, ocenione_sens = udzial('forum_sensowne')

    print(f'pozycji w pliku: {len(pozycje)}')
    print()
    print(f'zgodnosc z klasa:        {zgodnosc:.3f}  ({zgodne}/{ocenione_klasy})')
    print('  = SUFIT mierzalnej trafnosci. Model nie moze przebic tej liczby,')
    print('    bo powyzej niej "blad" oznacza juz zla etykiete, nie zla decyzje.')
    print()
    print(f'forum ma sens:           {sensownosc:.3f}  ({sensowne}/{ocenione_sens})')
    print(f'  = gorne ograniczenie uzytecznosci funkcji. Bramka >= {BRAMKA_SENSOWNOSCI}: '
          + ('spelniona' if sensownosc >= BRAMKA_SENSOWNOSCI else 'NIESPELNIONA'))

    if ocenione_klasy < len(pozycje) or ocenione_sens < len(pozycje):
        print()
        print(f'UWAGA: niewypelnione pozycje (klasa_ok {len(pozycje) - ocenione_klasy}, '
              f'forum_sensowne {len(pozycje) - ocenione_sens}). Liczby liczone tylko z wypelnionych.')

    po_klasie = defaultdict(lambda: [0, 0])
    for p in pozycje:
        if p.get('klasa_ok') in ('t', 'n'):
            po_klasie[p['klasa']][1] += 1
            po_klasie[p['klasa']][0] += p['klasa_ok'] == 't'
    if po_klasie:
        print()
        print('zgodnosc w rozbiciu na klasy:')
        for k, (tak, ile) in sorted(po_klasie.items()):
            print(f'  {k:24s} {tak}/{ile}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--wypisz', action='store_true', help='wygeneruj plik do recznego wypelnienia')
    parser.add_argument('--policz', action='store_true', help='policz dwie liczby z wypelnionego pliku')
    args = parser.parse_args()

    if args.wypisz == args.policz:
        raise SystemExit('podaj dokladnie jedno: --wypisz albo --policz')
    if args.wypisz:
        wypisz()
    else:
        policz()


if __name__ == '__main__':
    main()
