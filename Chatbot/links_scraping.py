import asyncio
import json
from pathlib import Path
import httpx
from bs4 import BeautifulSoup

HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8',
}

SEMAPHORE = asyncio.Semaphore(3)

async def pobierz_tresc(client: httpx.AsyncClient, url: str, agent: str ) -> dict | None:
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
      tytul = tytul.get_text(strip=True)

      bloki = soup.select('div[data-role="component-wrapper"]')
      tresc = '\n\n'.join(b.get_text('\n', strip=True) for b in bloki)

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
    
    frontmatter = (
        f'---\n'
        f'url: {artykul["url"]}\n'
        f'tytul: {artykul["tytul"]}\n'
        f'agent: {artykul["agent"]}\n'
        f'podslug: {artykul["podslug"]}\n'
        f'---\n\n'
    )
    sciezka.write_text(frontmatter + artykul['tresc'], encoding='utf-8')

async def main():
   
   with open('links.json', encoding='utf-8') as f:
      links = json.load(f)
    
   docs_dir = Path('docs')
   
   async with httpx.AsyncClient(headers=HEADER, timeout=15) as client:
     
      zadania = [
         pobierz_tresc(client, url, agent)
         for agent, urls in links.items()
         for url in urls
      ]
      
      wyniki = await asyncio.gather(*zadania)

   for artykul in wyniki:
      if artykul:
         zapisz_md(artykul, docs_dir)

   print(f'zapisano {sum(1 for w in wyniki if w)} / {len(wyniki)}')

if __name__ == '__main__':
    asyncio.run(main())