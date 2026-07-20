import json
import time
from bs4 import BeautifulSoup
import httpx
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'

ARTYKUL_REGEX = re.compile(
    r'^https://allegro\.pl/pomoc/dla-kupujacych/[^/]+/[^/]+-[A-Za-z0-9]{6,}$'
)


KATEGORIE = {
    "konto": [
        "rejestracja-i-aktywacja",
        "logowanie-i-haslo",
        "dane-i-ustawienia-konta",
        "bezpieczenstwo-zasady-i-naruszenia",
    ],
    "zakupy": [
        "wyszukiwanie-i-ulubione",
        "sposoby-zakupow",
        "kupony-punkty-i-programy-znizkowe",
        "historia-zakupow",
        "oceny-i-komentarze",
        "metody-dostawy",
        "problemy-transakcyjne",
        "allegro-ochrona-kupujacych",
        "korzysci-i-aktywacja-allegro-smart",
        "zakupy-i-zwroty-z-allegro-smart-",
        "allegro-smart-na-allegro-lokalnie",
        "rezygnacja-z-allegro-smart",
    ],
    "platnosci": [
        "status-platnosci",
        "allegro-pay",
        "allegro-pay-business-dla-kupujacych",
        "przelew-bankowy",
        "blik",
        "karta-platnicza-apple-pay-google-pay",
        "allegro-klik",
        "raty-i-leasing-w-allegro",
        "allegro-cash",
    ],
}


PODSLUG_DO_AGENTA = {

    "rejestracja-i-aktywacja": "konto",
    "logowanie-i-haslo": "konto",
    "dane-i-ustawienia-konta": "konto",
    "bezpieczenstwo-zasady-i-naruszenia": "konto",
    "podstawowe-informacje": "konto",
    "aktywacja-konta": "konto",
    "konto-junior": "konto",
    "bezpieczne-zakupy": "zakupy",

    "wyszukiwanie-i-ulubione": "zakupy",
    "sposoby-zakupow": "zakupy",
    "kupony-punkty-i-programy-znizkowe": "zakupy",
    "historia-zakupow": "zakupy",
    "oceny-i-komentarze": "zakupy",
    "metody-dostawy": "zakupy",
    "problemy-transakcyjne": "zakupy",
    "zasady-zwrotow-i-reklamacji": "zakupy",
    "zasady-reklamacji-i-zwrotu-towaru": "zakupy",
    "allegro-ochrona-kupujacych": "zakupy",
    "korzysci-i-aktywacja-allegro-smart": "zakupy",
    "zakupy-i-zwroty-z-allegro-smart-": "zakupy",
    "allegro-smart-na-allegro-lokalnie": "zakupy",
    "rezygnacja-z-allegro-smart": "zakupy",
    "podstawy-kupowania": "zakupy",
    "wyjatki-i-zasady-dla-wybranych-kategorii": "zakupy",
    "zakupy-firmowe": "zakupy",
    "allegro-charytatywni-kupuje": "zakupy",

    "status-platnosci": "platnosci",
    "allegro-pay": "platnosci",
    "allegro-pay-business-dla-kupujacych": "platnosci",
    "przelew-bankowy": "platnosci",
    "blik": "platnosci",
    "karta-platnicza-apple-pay-google-pay": "platnosci",
    "allegro-klik": "platnosci",
    "raty-i-leasing-w-allegro": "platnosci",
    "allegro-cash": "platnosci",
    "metody-platnosci": "platnosci",
    "informacje-ogolne": "platnosci",
    "leasing-w-allegro": "platnosci",
}

BASE_URL = 'https://allegro.pl'
HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8',
}

def wyciagnij_podslug(url: str) -> str:
    czesci = url.split("/")

    return czesci[5]

def zbierz_linki_kategorie(slug: str) -> list[str]:
    
    url = f'{BASE_URL}/pomoc/dla-kupujacych/{slug}'

    try:
        response = httpx.get(url, headers=HEADER, timeout=10)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:

        print(f' {slug}: HTTP {e.response.status_code}, pomijam')
        return []
    
    except httpx.RequestError as e:
        print(f' {slug}: błąd sieci ({e}), pomijam')
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')

    tagi = soup.find_all('a', href=lambda h: h and ARTYKUL_REGEX.match(h))

    linki = [a['href'] for a in tagi]
    linki = list(dict.fromkeys(linki))

    return linki


def main():
    wynik = {'konto':[], 'zakupy':[], 'platnosci': []}
    wszystkie_linki = set()

    for agent, slugi in KATEGORIE.items():
        for slug in slugi:

            linki = zbierz_linki_kategorie(slug)
            wszystkie_linki.update(linki)

            print(f'  {slug}: {len(linki)} linków')
            time.sleep(0.5)

    for link in wszystkie_linki:

        podslug = wyciagnij_podslug(link)
        agent = PODSLUG_DO_AGENTA.get(podslug)

        if agent:

            wynik[agent].append(link) 

        else:
            print(f'Nieznany podslug: {podslug} link: {link}')
        
    for agent, linki in wynik.items():

        print(f'{agent}: {len(linki)} linków łącznie\n')
  
    sciezka_json = RAG_DIR / 'links.json'
    with open(sciezka_json, 'w', encoding='utf-8') as f:
        json.dump(wynik, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()