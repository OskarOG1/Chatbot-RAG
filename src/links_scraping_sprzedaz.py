import argparse
import asyncio
import json
import re
import time
from pathlib import Path
import httpx
from bs4 import BeautifulSoup
from links_wspolne import HEADER, zapisz_md

ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'

DEPARTAMENTY = {
    'pl': ['konto', 'produkty', 'ustawienia-ofert', 'zwiekszaj-sprzedaz', 'obsluga-zamowien',
           'sprzedaz-za-granice', 'dostawa-i-allegro-smart', 'finanse', 'jakosc-sprzedazy'],
    'en': ['account', 'products', 'offer-settings', 'grow-your-sales', 'order-management',
           'international-sales', 'delivery-and-allegro-smart', 'finance', 'sales-quality'],
}

MIN_ZNAKOW = 200
SEMAPHORE = asyncio.Semaphore(3)


def odkryj_kategorie(client: httpx.Client, lang: str) -> list[str]:
    kolejka = list(DEPARTAMENTY[lang])
    odwiedzone = set()
    kategorie = set()
    wzorzec_d = re.compile(rf'/sell/{lang}/d/([A-Za-z0-9-]+)')
    wzorzec_c = re.compile(rf'/{lang}/sell/c/([A-Za-z0-9-]+)')

    while kolejka:
        slug = kolejka.pop(0)
        if slug in odwiedzone:
            continue
        odwiedzone.add(slug)

        try:
            odpowiedz = client.get(f'https://help.allegro.com/{lang}/sell/d/{slug}')
            odpowiedz.raise_for_status()
        except httpx.HTTPError as e:
            print(f'  departament {slug}: {e}, pomijam')
            continue

        kategorie.update(wzorzec_c.findall(odpowiedz.text))
        for kandydat in wzorzec_d.findall(odpowiedz.text):
            if kandydat not in odwiedzone:
                kolejka.append(kandydat)
        time.sleep(0.4)

    print(f'  departamentów odwiedzonych: {len(odwiedzone)}, kategorii znalezionych: {len(kategorie)}')
    return sorted(kategorie)


def zbierz_linki_kategorii(client: httpx.Client, lang: str, slug: str) -> list[str]:
    wzorzec_a = re.compile(rf'/{lang}/sell/a/[A-Za-z0-9-]+')
    try:
        odpowiedz = client.get(f'https://help.allegro.com/{lang}/sell/c/{slug}')
        odpowiedz.raise_for_status()
    except httpx.HTTPError as e:
        print(f'  kategoria {slug}: {e}, pomijam')
        return []

    linki = sorted(set(wzorzec_a.findall(odpowiedz.text)))
    return [f'https://help.allegro.com{sciezka}' for sciezka in linki]


async def pobierz_tresc(client: httpx.AsyncClient, url: str, podslug: str) -> dict | None:
    async with SEMAPHORE:
        await asyncio.sleep(0.5)

        try:
            odpowiedz = await client.get(url)
            odpowiedz.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f'błąd sieci: {e.response.status_code}, pomijam {url}')
            return None
        except httpx.RequestError as e:
            print(f'błąd połączenia: {e}, pomijam {url}')
            return None

        soup = BeautifulSoup(odpowiedz.text, 'html.parser')
        tytul = soup.find('h1')
        tytul = tytul.get_text(strip=True) if tytul else '(brak tytułu)'

        bloki = soup.select('div[data-role="component-wrapper"]')
        tresc = '\n\n'.join(b.get_text('\n', strip=True) for b in bloki)

        if len(tresc) < MIN_ZNAKOW:
            print(f'zbyt krótka treść ({len(tresc)} znaków), pomijam {url}')
            return None

        return {'url': url, 'tytul': tytul, 'tresc': tresc, 'agent': 'sprzedaz', 'podslug': podslug}


async def pobierz_wszystkie(zadania: list[tuple[str, str]], docs_dir: Path) -> dict:
    async with httpx.AsyncClient(headers=HEADER, timeout=15, follow_redirects=True) as client:
        wyniki = await asyncio.gather(
            *(pobierz_tresc(client, url, podslug) for url, podslug in zadania),
            return_exceptions=True,
        )

    zapisano = 0
    for artykul in wyniki:
        if isinstance(artykul, Exception):
            print(f'problem: {artykul}')
        elif artykul is not None:
            zapisz_md(artykul, docs_dir)
            zapisano += 1

    return {'zapisano': zapisano, 'znalezione': len(zadania)}


def main(lang: str) -> None:
    header_lang = dict(HEADER, **{'Accept-Language': f'{lang};q=0.9'})

    with httpx.Client(headers=header_lang, timeout=15, follow_redirects=True) as client:
        print(f'odkrywanie kategorii ({lang})...')
        kategorie = odkryj_kategorie(client, lang)

        zadania = []
        znalezione_urle = set()
        for slug in kategorie:
            linki = zbierz_linki_kategorii(client, lang, slug)
            print(f'  {slug}: {len(linki)} linków')
            for url in linki:
                if url not in znalezione_urle:
                    znalezione_urle.add(url)
                    zadania.append((url, slug))
            time.sleep(0.4)

    print(f'artykułów do pobrania: {len(zadania)}')

    docs_dir = RAG_DIR / ('docs_sprzedaz' if lang == 'pl' else 'docs_sprzedaz_en')
    wynik = asyncio.run(pobierz_wszystkie(zadania, docs_dir))
    print(f"zapisano {wynik['zapisano']} / {wynik['znalezione']}")

    links_json = RAG_DIR / f'links_sprzedaz_{lang}.json'
    with open(links_json, 'w', encoding='utf-8') as w:
        json.dump({'sprzedaz': sorted(znalezione_urle)}, w, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', default='pl', choices=['pl', 'en'])
    args = parser.parse_args()
    main(args.lang)
