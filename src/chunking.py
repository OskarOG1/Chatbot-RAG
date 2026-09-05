import argparse
import re
from pathlib import Path
import tiktoken
import json
import yaml
from collections import Counter
from lang_config import LANG

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'

encoder = tiktoken.get_encoding('cl100k_base')

SKROTY = {'np', 'tzn', 'm.in', 'ul', 'art', 'zl', 'zł', 'godz', 'tj', 'itd', 'itp', 'pkt', 'nr', 'str'}


def wczytaj_dokument(sciezka: Path) -> tuple[dict, str]:
    with open(sciezka, 'r', encoding='utf-8') as r:

        fragmenty = r.read().split('---', 2)
        metadane = yaml.safe_load(fragmenty[1])

        tresc = fragmenty[2].strip()
        return metadane, tresc


def dlugosc_tokenow(tekst: str) -> int:
    return len(encoder.encode(tekst))


SEP_DLUGOSC = {'': 0, ' ': dlugosc_tokenow(' '), '\n\n': dlugosc_tokenow('\n\n')}


def podziel_na_bloki(tekst: str) -> list[str]:
    return [blok.strip() for blok in re.split(r'\n\s*\n', tekst.strip()) if blok.strip()]


def podziel_na_zdania(tekst: str) -> list[str]:
    znormalizowany = ' '.join(tekst.split())
    if not znormalizowany:
        return []

    granice = []
    for match in re.finditer(r'[.!?]+[\'"\)\]]*', znormalizowany):
        poczatek, koniec = match.start(), match.end()

        przed = znormalizowany[:poczatek].rsplit(' ', 1)[-1]
        slowo = przed.strip('.!?\'"()[]').lower()

        reszta = znormalizowany[koniec:].lstrip()
        pierwszy_znak = reszta[0] if reszta else ''

        czy_skrot = slowo in SKROTY or slowo.isdigit()
        if czy_skrot:
            continue

        czy_koniec = not reszta
        czy_nowe_zdanie = pierwszy_znak.isupper() or pierwszy_znak.isdigit()
        if czy_koniec or czy_nowe_zdanie:
            granice.append(koniec)

    zdania = []
    start = 0
    for koniec in granice:
        kawalek = znormalizowany[start:koniec].strip()
        if kawalek:
            zdania.append(kawalek)
        start = koniec
    ogon = znormalizowany[start:].strip()
    if ogon:
        zdania.append(ogon)

    return zdania


def rozbij_sekcje(tekst: str, budget: int) -> list[dict]:
    fragmenty = []

    def dodaj(sep, tresc):
        fragmenty.append({'sep': sep, 'tekst': tresc, 'dl': dlugosc_tokenow(tresc)})

    for i, blok in enumerate(podziel_na_bloki(tekst)):
        sep_bloku = '' if i == 0 else '\n\n'
        if dlugosc_tokenow(blok) <= budget:
            dodaj(sep_bloku, blok)
            continue

        for j, zdanie in enumerate(podziel_na_zdania(blok)):
            sep_zdania = sep_bloku if j == 0 else ' '
            if dlugosc_tokenow(zdanie) <= budget:
                dodaj(sep_zdania, zdanie)
                continue

            kawalek = ''
            sep_kawalka = sep_zdania
            for slowo in zdanie.split(' '):
                probka = f'{kawalek} {slowo}' if kawalek else slowo
                if kawalek and dlugosc_tokenow(probka) > budget:
                    dodaj(sep_kawalka, kawalek)
                    kawalek = slowo
                    sep_kawalka = ' '
                else:
                    kawalek = probka
            if kawalek:
                dodaj(sep_kawalka, kawalek)

    return fragmenty


def zloz_fragmenty(fragmenty: list[dict]) -> str:
    return ''.join(f['sep'] + f['tekst'] for f in fragmenty)


def wybierz_zakladke(poprzedni: list[dict], nastepny: dict, overlap: int, size: int) -> tuple[list[dict], int]:
    wybrane = []
    dlugosc = 0
    for f in reversed(poprzedni):
        sep_dl = SEP_DLUGOSC[wybrane[0]['sep']] if wybrane else 0
        nowa_dlugosc = dlugosc + sep_dl + f['dl']
        if wybrane and nowa_dlugosc > overlap:
            break
        if nowa_dlugosc + SEP_DLUGOSC[nastepny['sep']] + nastepny['dl'] > size:
            break
        wybrane.insert(0, f)
        dlugosc = nowa_dlugosc
    if wybrane:
        wybrane[0] = {**wybrane[0], 'sep': ''}
    return wybrane, dlugosc


def podziel_na_chunki(tekst: str, size: int, overlap: int) -> list[str]:

    fragmenty = rozbij_sekcje(tekst, size)
    if not fragmenty:
        return []

    chunki = []
    biezacy: list[dict] = []
    dlugosc_biezacego = 0

    i = 0
    while i < len(fragmenty):
        frag = fragmenty[i]
        sep_dl = SEP_DLUGOSC[frag['sep']] if biezacy else 0

        if not biezacy or dlugosc_biezacego + sep_dl + frag['dl'] <= size:
            biezacy.append(frag if biezacy else {**frag, 'sep': ''})
            dlugosc_biezacego += sep_dl + frag['dl']
            i += 1
            continue

        chunki.append(zloz_fragmenty(biezacy))
        biezacy, dlugosc_biezacego = wybierz_zakladke(biezacy, frag, overlap, size)

    if biezacy:
        chunki.append(zloz_fragmenty(biezacy))

    return chunki


def podziel_na_sekcje(tresc: str) -> list[tuple[str | None, str]]:

    linie = tresc.split('\n')
    i = 0
    while i < len(linie) and not linie[i].strip():
        i += 1
    start = i
    while i < len(linie) and linie[i].strip():
        i += 1

    kandydat = [linia.strip() for linia in linie[start:i] if linia.strip()]
    reszta = linie[i:]
    zbior = {linia.strip() for linia in reszta if linia.strip()}

    if not (len(kandydat) >= 2 and all(naglowek in zbior for naglowek in kandydat)):
        return [(None, tresc)]

    granice = []
    szukany = 0
    for idx, linia in enumerate(reszta):
        if szukany < len(kandydat) and linia.strip() == kandydat[szukany]:
            granice.append((idx, kandydat[szukany]))
            szukany += 1

    sekcje = []
    intro = '\n'.join(reszta[:granice[0][0]]).strip()
    if intro:
        sekcje.append((None, intro))
    for j, (idx, naglowek) in enumerate(granice):
        koniec = granice[j + 1][0] if j + 1 < len(granice) else len(reszta)
        sekcje.append((naglowek, '\n'.join(reszta[idx + 1:koniec]).strip()))
    return sekcje


def chunk_document(sciezka: Path) -> list[dict]:

    metadane, tresc = wczytaj_dokument(sciezka)

    chunki = []
    for naglowek, tekst_sekcji in podziel_na_sekcje(tresc):
        if not tekst_sekcji:
            continue
        prefiks = f'{naglowek}\n' if naglowek else ''
        rezerwa = len(encoder.encode(prefiks))
        size = max(CHUNK_OVERLAP + 1, CHUNK_SIZE - rezerwa)
        for kawalek in podziel_na_chunki(tekst_sekcji, size, CHUNK_OVERLAP):
            chunki.append({'tekst': prefiks + kawalek, 'naglowek': naglowek or '', **metadane})
    return chunki


def main(lang: str = 'pl', docs_dir: Path | None = None, out: Path | None = None):

    suffix = LANG[lang]['suffix']
    docs_dir = docs_dir or RAG_DIR / f'docs{suffix}'
    wszystkie_chunki = []
    pliki = 0

    for plik_md in docs_dir.rglob('*.md'):
        try:

            wszystkie_chunki.extend(chunk_document(plik_md))
            pliki += 1

        except Exception as e:
            print(f'Pominięto {plik_md.name}: {e}')

    print(f'plików: {pliki} chunków łącznie: {len(wszystkie_chunki)}')

    licznik = Counter(c['agent'] for c in wszystkie_chunki)
    sciezka_json = out or RAG_DIR / f'chunks{suffix}.json'

    with open(sciezka_json, 'w', encoding='utf-8') as w:
        json.dump(wszystkie_chunki, w, ensure_ascii=False, indent=2)

    print(licznik)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', default='pl', choices=list(LANG))
    parser.add_argument('--docs-dir', type=Path, default=None)
    parser.add_argument('--out', type=Path, default=None)
    args = parser.parse_args()
    main(args.lang, args.docs_dir, args.out)
