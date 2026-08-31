import argparse
import json
from pathlib import Path

import dociagnij
from petla import KATALOG_WYJSCIA, NAZWA_DO_PRZEGLADU

ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'
NAZWA_GOLDEN_KOLEJKA = 'golden_kolejka.json'
DECYZJE_DZIALANIA = ('artykul', 'alias')


def identyfikator_artykulu(url: str) -> str:
    return url.rstrip('/').split('/')[-1]


def wczytaj_przeglad(sciezka: Path) -> list[dict]:
    with open(sciezka, encoding='utf-8') as r:
        dane = json.load(r)
    if not isinstance(dane, list):
        raise SystemExit(f'Plik {sciezka} nie zawiera listy wpisow.')
    return dane


def dopisz_golden(sciezka_golden: Path, query: str, agent: str, zrodlo_url: str) -> bool:
    if sciezka_golden.exists():
        with open(sciezka_golden, encoding='utf-8') as r:
            wiersze = json.load(r)
    else:
        wiersze = []

    for w in wiersze:
        if w.get('query') == query and w.get('zrodlo_url') == zrodlo_url:
            return False

    wiersze.append({'query': query, 'agent': agent, 'zrodlo_url': zrodlo_url})
    with open(sciezka_golden, 'w', encoding='utf-8') as w:
        json.dump(wiersze, w, ensure_ascii=False, indent=2)
    return True


def zastosuj(wpisy: list[dict], rag_dir: Path = RAG_DIR, na_sucho: bool = False,
             dociagnij_fn=dociagnij.wykonaj) -> dict:
    golden = rag_dir / NAZWA_GOLDEN_KOLEJKA
    licz = {'artykul': 0, 'alias': 0, 'pomijamy': 0, 'nieprzejrzane': 0, 'blad': 0}
    dociagniete: list[dict] = []
    aliasy: list[dict] = []
    bledy: list[str] = []

    for wpis in wpisy:
        decyzja = wpis.get('decyzja')
        if decyzja not in DECYZJE_DZIALANIA:
            licz['pomijamy' if decyzja == 'pomijamy' else 'nieprzejrzane'] += 1
            continue

        url = wpis.get('url')
        agent = wpis.get('agent')
        lang = wpis.get('lang') or 'pl'
        zgl = wpis.get('zgloszenie')
        if not url or not agent:
            licz['blad'] += 1
            bledy.append(f'zgloszenie {zgl}: decyzja {decyzja} bez pola url albo agent, pomijam')
            continue

        if decyzja == 'artykul':
            korpus = {'url': url, 'agent': agent, 'lang': lang,
                      'rodzina': dociagnij.rodzina_agenta(agent)}
            if na_sucho:
                licz['artykul'] += 1
                dociagniete.append(korpus)
                continue
            try:
                dociagnij_fn(url, agent, lang, rag_dir=rag_dir)
                licz['artykul'] += 1
                dociagniete.append(korpus)
            except SystemExit as blad:
                licz['blad'] += 1
                bledy.append(f'zgloszenie {zgl}: dociagniecie {url} nieudane: {blad.code}')
            continue

        slug = identyfikator_artykulu(url)
        pytanie = wpis.get('pytanie') or ''
        dodano = False if na_sucho else dopisz_golden(golden, pytanie, agent, slug)
        licz['alias'] += 1
        aliasy.append({'slug': slug, 'pytanie': pytanie, 'agent': agent,
                       'lang': lang, 'golden_dodany': dodano})

    return {'licz': licz, 'dociagniete': dociagniete, 'aliasy': aliasy, 'bledy': bledy}


def komenda_chunkingu(rodzina: str, lang: str) -> str:
    suffix = '' if lang == 'pl' else f'_{lang}'
    czlon = 'docs' if rodzina == 'kupujacy' else 'docs_sprzedaz'
    baza = 'chunks_kupujacy' if rodzina == 'kupujacy' else 'chunks_sprzedaz'
    return (f'  python chunking.py --lang {lang} --docs-dir ../RAG/{czlon}{suffix} '
            f'--out ../RAG/{baza}{suffix}.json')


def wypisz_nastepne_kroki(wynik: dict) -> None:
    if wynik['dociagniete']:
        korpusy = sorted({(d['rodzina'], d['lang']) for d in wynik['dociagniete']})
        print()
        print('Dociagniete artykuly wymagaja pelnej przebudowy korpusu, bez przelacznika --dopisz:')
        for rodzina, lang in korpusy:
            print(komenda_chunkingu(rodzina, lang))
        for lang in sorted({lang for _, lang in korpusy}):
            print(f'  python scal_korpus.py --lang {lang} && python embedder.py --lang {lang} '
                  f'&& python vector.py --lang {lang}')
    if wynik['aliasy']:
        print()
        print('Aliasy: wpisz slownictwo z pytania uzytkownika, nie z odpowiedzi operatora, '
              'do slownika ALIASY w src/aliasy.py:')
        for a in wynik['aliasy']:
            print(f"    {a['slug']!r}: (")
            print(f"        '{a['pytanie']}'")
            print('    ),')
        jezyki = sorted({a['lang'] for a in wynik['aliasy']})
        for lang in jezyki:
            print(f'  potem: python embedder.py --lang {lang} --przelicz-aliasy')
        print('  sprawdz w wyjsciu, ze przeliczono liczbe wierszy wieksza od zera dla kazdego klucza')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Stosuje decyzje z przejrzanego do_przegladu.json: dla decyzji artykul dociaga '
            'brakujacy artykul, dla decyzji alias dokleja wiersz do RAG/golden_kolejka.json '
            'i wypisuje gotowy wpis do slownika ALIASY.'))
    parser.add_argument(
        '--plik', type=Path, default=KATALOG_WYJSCIA / NAZWA_DO_PRZEGLADU,
        help='sciezka do przejrzanego do_przegladu.json')
    parser.add_argument(
        '--rag', type=Path, default=RAG_DIR, help='katalog RAG na golden_kolejka.json')
    parser.add_argument(
        '--na-sucho', action='store_true',
        help='pokazuje, co by zrobil, bez pobierania i bez zapisu')
    args = parser.parse_args(argv)

    if not args.plik.exists():
        raise SystemExit(f'Nie ma pliku {args.plik}. Najpierw uruchom src/petla.py i przejrzyj wynik.')

    wpisy = wczytaj_przeglad(args.plik)
    wynik = zastosuj(wpisy, rag_dir=args.rag, na_sucho=args.na_sucho)

    licz = wynik['licz']
    print(f"Wpisow w pliku: {len(wpisy)}")
    print(f"  artykul: {licz['artykul']}")
    print(f"  alias: {licz['alias']}")
    print(f"  pomijamy: {licz['pomijamy']}")
    print(f"  nieprzejrzane (decyzja pusta): {licz['nieprzejrzane']}")
    print(f"  blad: {licz['blad']}")
    for b in wynik['bledy']:
        print(f'  {b}')

    wypisz_nastepne_kroki(wynik)

    return 1 if licz['blad'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
