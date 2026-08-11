import asyncio
import json
from pathlib import Path
import httpx
from bs4 import BeautifulSoup
from links_wspolne import HEADER, zapisz_md
ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'

SEMAPHORE = asyncio.Semaphore(3)

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
      tytul = tytul.get_text(strip=True) if tytul else '(brak tytułu)'

      bloki = soup.select('div[data-role="component-wrapper"]')
      tresc = '\n\n'.join(b.get_text('\n', strip=True) for b in bloki)

      podslug = url.split('/')[5]

      return {'url': url,
             'tytul': tytul,
             'tresc': tresc,
             'agent': agent,
             'podslug': podslug}

async def main():

   links_json = RAG_DIR / 'links.json'
   with open(links_json, encoding='utf-8') as f:
      links = json.load(f)

   docs_dir = RAG_DIR / 'docs'

   async with httpx.AsyncClient(headers=HEADER, timeout=15) as client:

      zadania = [
         pobierz_tresc(client, url, agent)
         for agent, urls in links.items()
         for url in urls
      ]

      wyniki = await asyncio.gather(*zadania, return_exceptions=True)

   for artykul in wyniki:
      if isinstance(artykul, Exception):
         print(f'problem z {artykul}')
      else:
         zapisz_md(artykul, docs_dir)

   print(f'zapisano {sum(1 for w in wyniki if isinstance(w, dict))} / {len(wyniki)}')

if __name__ == '__main__':
    asyncio.run(main())