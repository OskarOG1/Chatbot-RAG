import asyncio
import json
import random
import re
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from links_wspolne import USER_AGENT, zapisz_md

ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'

PL_ZNAKI = set('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ')

MIN_ODSTEP = 3.0
MAX_ODSTEP = 6.0


def wyglada_na_polski(html: str, tekst: str) -> bool:
    if '"language":"pl-PL"' in html:
        return True
    return any(znak in PL_ZNAKI for znak in tekst)


async def odrzuc_zgody(strona) -> None:
    przycisk = strona.get_by_role('button', name=re.compile('nie zgadzam|do not agree|odrzuć|reject', re.I))
    try:
        await przycisk.click(timeout=5000)
    except Exception:
        pass


async def przelacz_na_angielski(context) -> None:
    strona = await context.new_page()
    await strona.goto('https://allegro.pl/pomoc')
    await odrzuc_zgody(strona)

    przycisk = strona.get_by_role('button', name=re.compile('change language|zmień język', re.I))
    await przycisk.click()

    select = strona.locator('#language-select')
    await select.wait_for(state='visible', timeout=15000)
    await select.select_option('en-US')

    zatwierdz = strona.get_by_role('button', name=re.compile(r'^(zmień|change)$', re.I))
    await zatwierdz.click()

    jezyk = None
    for _ in range(20):
        await asyncio.sleep(0.5)
        jezyk = await strona.evaluate('document.documentElement.lang')
        if jezyk.startswith('en'):
            break
    await strona.close()

    if not jezyk or not jezyk.startswith('en'):
        raise SystemExit(f'przełączenie na angielski się nie powiodło (lang={jezyk!r}), przerywam bez pobierania')


async def pobierz_tresc(context, url: str, agent: str) -> dict | str | None:
    strona = await context.new_page()
    try:
        odpowiedz = await strona.goto(url, timeout=15000)
        if odpowiedz is None or odpowiedz.status != 200:
            status = odpowiedz.status if odpowiedz else 'brak odpowiedzi'
            print(f'{url}: HTTP {status}, pomijam')
            return None

        html = await strona.content()
        soup = BeautifulSoup(html, 'html.parser')
        tytul = soup.find('h1')
        tytul = tytul.get_text(strip=True) if tytul else '(no title)'

        bloki = soup.select('div[data-role="component-wrapper"]')
        tresc = '\n\n'.join(b.get_text('\n', strip=True) for b in bloki)
    finally:
        await strona.close()

    if wyglada_na_polski(html, tytul + '\n' + tresc):
        return 'polski'

    podslug = url.split('/')[5]
    return {'url': url, 'tytul': tytul, 'tresc': tresc, 'agent': agent, 'podslug': podslug}


async def pobierz_wszystkie(zadania: list[tuple[str, str]], docs_dir: Path) -> dict:
    async with async_playwright() as playwright:
        przegladarka = await playwright.chromium.launch()
        context = await przegladarka.new_context(user_agent=USER_AGENT)

        await przelacz_na_angielski(context)

        zapisane = 0
        bez_wersji_en = []
        for agent, url in zadania:
            await asyncio.sleep(random.uniform(MIN_ODSTEP, MAX_ODSTEP))
            wynik = await pobierz_tresc(context, url, agent)
            if wynik == 'polski':
                bez_wersji_en.append(url)
            elif wynik is not None:
                zapisz_md(wynik, docs_dir)
                zapisane += 1

        await przegladarka.close()

    return {'zapisane': zapisane, 'razem': len(zadania), 'bez_wersji_en': bez_wersji_en}


async def main():
    links_json = RAG_DIR / 'links.json'
    with open(links_json, encoding='utf-8') as f:
        links = json.load(f)

    zadania = [(agent, url) for agent, urls in links.items() for url in urls]
    docs_dir = RAG_DIR / 'docs_en_off'

    wynik = await pobierz_wszystkie(zadania, docs_dir)
    print(f"zapisano {wynik['zapisane']} / {wynik['razem']}")
    if wynik['bez_wersji_en']:
        print(f"bez wersji EN ({len(wynik['bez_wersji_en'])}):")
        for url in wynik['bez_wersji_en']:
            print(f'  {url}')


if __name__ == '__main__':
    asyncio.run(main())
