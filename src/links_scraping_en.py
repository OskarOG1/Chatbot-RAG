import asyncio
import json
import os
from pathlib import Path
import httpx
import yaml
from bs4 import BeautifulSoup
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'
load_dotenv(Path(__file__).resolve().parent / '.env')

HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

PL_ZNAKI = set('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ')

SEMAPHORE = asyncio.Semaphore(3)

def wyglada_na_polski(html: str, tekst: str) -> bool:
    if '"language":"pl-PL"' in html:
        return True
    return any(znak in PL_ZNAKI for znak in tekst)

async def pobierz_tresc(client: httpx.AsyncClient, url: str, agent: str) -> dict | None:
   async with SEMAPHORE:
      await asyncio.sleep(0.5)

      try:
         response = await client.get(url)
         response.raise_for_status()

      except httpx.HTTPStatusError as e:
         print(f'błąd sieci: {e.response.status_code}, pomijam')
         return None

      except httpx.RequestError as e:
         print(f'błąd połączenia: {e}')
         return None

      soup = BeautifulSoup(response.text, 'html.parser')
      tytul = soup.find('h1')
      tytul = tytul.get_text(strip=True) if tytul else '(no title)'

      bloki = soup.select('div[data-role="component-wrapper"]')
      tresc = '\n\n'.join(b.get_text('\n', strip=True) for b in bloki)

      if wyglada_na_polski(response.text, tytul + '\n' + tresc):
         print(f'strona wrócila po polsku, przerywam: {url}')
         return 'polski'

      podslug = url.split('/')[5]

      return {'url': url,
             'tytul': tytul,
             'tresc': tresc,
             'agent': agent,
             'podslug': podslug}

def zapisz_md(artykul: dict, docs_dir: Path) -> None:

    nazwa = artykul['url'].rstrip('/').split('/')[-1] + '.md'
    sciezka = docs_dir / artykul['agent'] / nazwa
    sciezka.parent.mkdir(parents=True, exist_ok=True)

    meta = {k: artykul[k] for k in ('url', 'tytul', 'agent', 'podslug')}
    frontmatter = '---\n' + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + '---\n\n'
    sciezka.write_text(frontmatter + artykul['tresc'], encoding='utf-8')

async def main():

   ciasteczko = os.getenv('ALLEGRO_SESSION_COOKIE')
   if not ciasteczko:
      raise SystemExit('brak ALLEGRO_SESSION_COOKIE w środowisku, przerywam')

   jar = httpx.Cookies()
   for para in ciasteczko.split(';'):
      if '=' in para:
         nazwa, wartosc = para.strip().split('=', 1)
         jar.set(nazwa, wartosc, domain='.allegro.pl')

   links_json = RAG_DIR / 'links.json'
   with open(links_json, encoding='utf-8') as f:
      links = json.load(f)

   docs_dir = RAG_DIR / 'docs_en_off'

   async with httpx.AsyncClient(headers=HEADER, cookies=jar, timeout=15) as client:

      zadania = [
         pobierz_tresc(client, url, agent)
         for agent, urls in links.items()
         for url in urls
      ]

      wyniki = await asyncio.gather(*zadania, return_exceptions=True)

   polskie = [w for w in wyniki if w == 'polski']
   if polskie:
      raise SystemExit(f'{len(polskie)} artykułów wróciło po polsku, sesja wygasła albo cookie złe, nie zapisuję niczego')

   for artykul in wyniki:
      if isinstance(artykul, Exception):
         print(f'problem z {artykul}')
      elif artykul is not None:
         zapisz_md(artykul, docs_dir)

   pobrane = sum(1 for w in wyniki if isinstance(w, dict))
   print(f'zapisano {pobrane} / {len(wyniki)}')

if __name__ == '__main__':
    asyncio.run(main())
