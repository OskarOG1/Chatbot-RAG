import argparse
import asyncio
import json
import re
from pathlib import Path

import links_wspolne

ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'

WZORZEC_ADRESU = re.compile(
    r'^https://allegro\.pl/pomoc/[a-z][a-z-]*/[a-z0-9][a-z0-9-]*/[A-Za-z0-9-]+$'
)
WZORZEC_ADRESU_SPRZEDAZ = re.compile(
    r'^https://help\.allegro\.com/(pl|en)/sell/a/[A-Za-z0-9-]+$'
)

KATALOGI = {
    ('kupujacy', 'pl'): 'docs',
    ('kupujacy', 'en'): 'docs_en',
    ('sprzedaz', 'pl'): 'docs_sprzedaz',
    ('sprzedaz', 'en'): 'docs_sprzedaz_en',
}


def poprawny_adres_pomocy(url: str) -> bool:
    url = url or ''
    return bool(WZORZEC_ADRESU.match(url) or WZORZEC_ADRESU_SPRZEDAZ.match(url))


def adres_sprzedazowy(url: str) -> bool:
    return bool(WZORZEC_ADRESU_SPRZEDAZ.match(url or ''))


def rodzina_agenta(agent: str) -> str:
    return 'sprzedaz' if agent == 'sprzedaz' else 'kupujacy'


def katalog_dokumentow(agent: str, lang: str, rag_dir: Path = RAG_DIR) -> Path:
    nazwa = KATALOGI[(rodzina_agenta(agent), lang)]
    return rag_dir / nazwa


def plik_linkow(agent: str, lang: str, rag_dir: Path = RAG_DIR) -> tuple[Path, str]:
    if rodzina_agenta(agent) == 'sprzedaz':
        return rag_dir / f'links_sprzedaz_{lang}.json', 'sprzedaz'
    return rag_dir / 'links.json', agent


def sciezka_pliku_artykulu(artykul: dict, docs_dir: Path) -> Path:
    nazwa = artykul['url'].rstrip('/').split('/')[-1] + '.md'
    return docs_dir / artykul['agent'] / nazwa


def dopisz_link(sciezka_links: Path, agent: str, url: str) -> bool:
    if sciezka_links.exists():
        with open(sciezka_links, encoding='utf-8') as r:
            links = json.load(r)
    else:
        links = {}

    lista = links.setdefault(agent, [])
    if url in lista:
        return False

    lista.append(url)
    with open(sciezka_links, 'w', encoding='utf-8') as w:
        json.dump(links, w, ensure_ascii=False, indent=2)
    return True


def pobierz_z_sieci(url: str, agent: str) -> dict | None:
    import httpx

    async def uruchom():
        async with httpx.AsyncClient(
                headers=links_wspolne.HEADER, timeout=15, follow_redirects=True) as client:
            if adres_sprzedazowy(url):
                import links_scraping_sprzedaz
                return await links_scraping_sprzedaz.pobierz_tresc(client, url, 'sell')
            import links_scraping
            return await links_scraping.pobierz_tresc(client, url, agent)

    return asyncio.run(uruchom())


def wykonaj(url: str, agent: str, lang: str, rag_dir: Path = RAG_DIR, pobieracz=pobierz_z_sieci) -> int:
    if not poprawny_adres_pomocy(url):
        raise SystemExit(
            f'Adres {url} nie pasuje do zadnego wzorca artykulu pomocy: '
            f'https://allegro.pl/pomoc/<dzial>/<kategoria>/<artykul> ani '
            f'https://help.allegro.com/<pl|en>/sell/a/<artykul>. Nic nie pobieram.')

    docs_dir = katalog_dokumentow(agent, lang, rag_dir)
    sciezka_links, klucz_links = plik_linkow(agent, lang, rag_dir)

    artykul = pobieracz(url, agent)
    if artykul is None:
        raise SystemExit(
            f'Nie udalo sie pobrac {url}. Nie zapisuje pliku ani nie dopisuje adresu, '
            f'zeby nie zglaszac domknietej luki, ktora zostala otwarta.')

    docelowy = sciezka_pliku_artykulu(artykul, docs_dir)
    if docelowy.exists():
        print(f'Nadpisuje istniejacy artykul {docelowy}, to odswiezenie tresci.')
    else:
        print(f'Zapisuje nowy artykul {docelowy}.')
    links_wspolne.zapisz_md(artykul, docs_dir)

    if dopisz_link(sciezka_links, klucz_links, url):
        print(f'Dopisano adres do {sciezka_links} pod kluczem {klucz_links}.')
    else:
        print(f'Adres jest juz w {sciezka_links} pod kluczem {klucz_links}, pomijam dopisanie.')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Pobiera jeden artykul pomocy Allegro, zapisuje go jako plik md we wlasciwym '
            'katalogu dokumentow i dopisuje adres do RAG/links.json.'))
    parser.add_argument('--url', required=True, help='pelny adres artykulu pomocy')
    parser.add_argument(
        '--agent', required=True,
        help='agent docelowy, np. konto, zakupy, platnosci albo sprzedaz')
    parser.add_argument('--lang', default='pl', choices=['pl', 'en'])
    args = parser.parse_args(argv)

    return wykonaj(args.url, args.agent, args.lang)


if __name__ == '__main__':
    raise SystemExit(main())
