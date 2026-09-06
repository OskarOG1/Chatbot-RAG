# Diagnostyka czterech pytan z przebiegu ocen 2026-09-03, ktore oceniono jako zle
# z powodu retrievalu (wygral niewlasciwy artykul). Wylacznie retrieval, bez generacji,
# bo klucza do modelu nie ma lokalnie. Nie zmienia src/, korpusu ani indeksow.
#
# Wywolanie skopiowane z Pomiary/measure_regresja.py i Pomiary/measure.py:
# measure.embed(query) do embeddingu, rankings.search_reranked_multi(query, emb, sekcje,
# k=..., k_surowe=..., lang='pl') do wyszukania. Zamiast k=5 z measure.py bierzemy k=10,
# zeby zobaczyc pelna top 10 zamiast top 5.
#
# Dwie pule kandydatow per pytanie, bo prawdziwa produkcja (src/pipeline.py:303-304,
# funkcja sekcja_z_bramkami) nie przeszukuje jednej sekcji: wola
# search_reranked_multi(zapytanie, emb, strony.agenci_wszystkich_stron(), k=None,
# k_surowe=K_SUROWE_SEKCJI, lang=lang), czyli obie sekcje razem w jednym rerankingu,
# k_surowe=6 na sekcje (src/pipeline.py:35, bez override w docker/). Dopiero po tym
# src/strony.py:rozstrzygnij() decyduje, ktora "strona" wygrywa, i to ten mechanizm
# pozwala artykulowi z przeciwnej sekcji wygrac mimo ze uzytkownik jest w innej zakladce.
# Druga pula to pojedyncza sekcja z szerszym k_surowe=20, konwencja z measure_regresja.py,
# zeby sprawdzic, czy problem jest tylko na styku sekcji, czy tez w obrebie samej sekcji.
#
# Zapis przyrostowy: plik wynikowy dopisywany po kazdym pytaniu, zeby czesciowy wynik
# przetrwal ewentualne przerwanie.

import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import measure
from rankings import search_reranked_multi, wczytaj_chunki
import strony
import pipeline

WYJSCIE = ROOT / 'Pomiary' / 'outputs' / 'diagnoza_cztery_pytania.json'

SEKCJA_DO_AGENTA = strony.STRONA_DO_AGENTA  # {'kupujacy': 'kupujacy', 'sprzedajacy': 'sprzedaz'}
K_SUROWE_MERGED = pipeline.K_SUROWE_SEKCJI  # 6, taki sam jak w produkcji
K_SUROWE_SEKCJA = 20  # jak domyslne w measure_regresja.py

PYTANIA = [
    {
        'id': 1,
        'query': 'Ile wynosi prowizja od sprzedazy na Allegro?',
        'sekcja': 'sprzedajacy',
        'url_zly': 'allegro-pay-business-czym-jest-jak-dziala-i-kiedy-skorzystasz-Rd9wa7Eq6sD',
        'kandydaci_wlasciwi': [
            'https://help.allegro.com/pl/sell/a/automatyczny-rabat-transakcyjny-zwrot-prowizji-bez-wypelniania-wniosku-k1wRjemBbsV',
            'https://help.allegro.com/pl/sell/a/jak-odzyskac-rabat-transakcyjny-prowizje-od-sprzedazy-d2WoLAX5bU8',
        ],
        'uwaga': ('W korpusie chunks_sprzedaz.json (170 artykulow) nie znaleziono zadnego '
                  'artykulu z jednoznaczna stawka/tabela prowizji sprzedazowej. Dwaj '
                  'najblizsi tematycznie kandydaci dotycza ODZYSKANIA/ZWROTU prowizji '
                  '(rabat transakcyjny), nie bazowej stawki. Traktowac jako mozliwa luke '
                  'w korpusie, nie tylko problem retrievalu.'),
    },
    {
        'id': 2,
        'query': 'Produkt, który kupiłem, jest wadliwy. Jak mogę go zareklamować?',
        'sekcja': 'kupujacy',
        'url_zly': 'czym-jest-parametr-stan-3AdEKV2kaIP',
        'kandydaci_wlasciwi': [
            'https://allegro.pl/pomoc/dla-kupujacych/zasady-zwrotow-i-reklamacji/jak-zlozyc-reklamacje-na-towar-kupiony-na-allegro-yP0dwDPVEHr',
        ],
        'uwaga': None,
    },
    {
        'id': 3,
        'query': 'jak wystawić przedmiot na sprzedaż',
        'sekcja': 'sprzedajacy',
        'url_zly': 'jak-wystawic-przedmiot-na-sprzedaz-oAd1MRwERFg',
        'kandydaci_wlasciwi': [
            'https://help.allegro.com/pl/sell/a/jak-wystawic-przedmiot-na-sprzedaz-oAd1MRwERFg',
        ],
        'uwaga': ('Tu wlasciwy URL to ten sam, ktory formalnie "wygral" - pytanie jest, '
                  'ktory CHUNK tego artykulu wygrywa rerankingu, bo dedup_najlepszy w '
                  'rankings.search_reranked_multi zostawia po jednym chunku na URL.'),
    },
    {
        'id': 4,
        'query': 'paczka nie przyszła, co mam zrobić',
        'sekcja': 'kupujacy',
        'url_zly': 'gdzie-sprawdzisz-numer-i-status-swojej-przesylki-LvP7agrzOhw',
        'kandydaci_wlasciwi': [
            'https://allegro.pl/pomoc/dla-kupujacych/problemy-transakcyjne/co-mozesz-zrobic-gdy-czekasz-na-przesylke-zbyt-dlugo-xG71gn36qC4',
        ],
        'uwaga': None,
    },
]


def top_n(query: str, sekcje: list[str], k_surowe, k: int = 10) -> list[dict]:
    emb = measure.embed(query, lang='pl')
    wyniki = search_reranked_multi(query, emb, sekcje, k=k, k_surowe=k_surowe, lang='pl')
    lista = []
    for pozycja, (chunk, wynik) in enumerate(wyniki, 1):
        lista.append({
            'pozycja': pozycja,
            'url': chunk['url'],
            'tytul': chunk['tytul'],
            'agent': chunk['agent'],
            'wynik_rerankera': round(float(wynik), 4),
            'tekst_200': chunk['tekst'][:200],
        })
    return lista


def znajdz_w_liscie(lista: list[dict], url_fragment: str) -> dict | None:
    for wpis in lista:
        if url_fragment in wpis['url']:
            return wpis
    return None


def analiza_chunkow_artykulu(url_fragment: str, agent: str) -> list[dict]:
    # Wszystkie chunki jednego artykulu z surowego korpusu, bez rerankingu,
    # zeby zobaczyc co artykul w ogole zawiera (do pytania 3: czy jest tam
    # opis PIERWSZEGO wystawiania, czy tylko ponownego).
    chunki = wczytaj_chunki(agent, 'pl')
    wybrane = [c for c in chunki if url_fragment in c['url']]
    return [{'numer_chunku': i, 'tekst_200': c['tekst'][:200]}
            for i, c in enumerate(wybrane, 1)]


def diagnoza_kandydat_pozycja(url_fragment: str, top_merged: list[dict],
                               top_sekcja: list[dict]) -> dict:
    w_merged = znajdz_w_liscie(top_merged, url_fragment)
    w_sekcja = znajdz_w_liscie(top_sekcja, url_fragment)
    return {
        'w_puli_merged_top10': w_merged is not None,
        'pozycja_merged': w_merged['pozycja'] if w_merged else None,
        'wynik_merged': w_merged['wynik_rerankera'] if w_merged else None,
        'w_puli_sekcja_top10': w_sekcja is not None,
        'pozycja_sekcja': w_sekcja['pozycja'] if w_sekcja else None,
        'wynik_sekcja': w_sekcja['wynik_rerankera'] if w_sekcja else None,
    }


def zapisz_czesciowo(wyniki: list[dict]) -> None:
    WYJSCIE.parent.mkdir(parents=True, exist_ok=True)
    with open(WYJSCIE, 'w', encoding='utf-8') as w:
        json.dump(wyniki, w, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    print(f'K_SUROWE_SEKCJI (produkcja, pula merged) = {K_SUROWE_MERGED}')
    print(f'K_SUROWE (pula pojedynczej sekcji, konwencja measure_regresja.py) = {K_SUROWE_SEKCJA}')

    wyniki = []
    for p in PYTANIA:
        print(f"\n=== Pytanie {p['id']}: {p['query']} (sekcja: {p['sekcja']}) ===")
        agent_sekcji = SEKCJA_DO_AGENTA[p['sekcja']]

        top_merged = top_n(p['query'], ['kupujacy', 'sprzedaz'], K_SUROWE_MERGED, k=10)
        top_sekcja = top_n(p['query'], [agent_sekcji], K_SUROWE_SEKCJA, k=10)

        print('--- top 10, pula merged (kupujacy+sprzedaz, k_surowe=6 jak produkcja) ---')
        for w in top_merged:
            print(f"  {w['pozycja']:>2}. [{w['agent']:>9}] {w['wynik_rerankera']:>8.4f}  "
                  f"{w['url'].rsplit('/', 1)[-1][:60]}")

        print(f'--- top 10, pula pojedynczej sekcji ({agent_sekcji}, k_surowe=20) ---')
        for w in top_sekcja:
            print(f"  {w['pozycja']:>2}. {w['wynik_rerankera']:>8.4f}  "
                  f"{w['url'].rsplit('/', 1)[-1][:60]}")

        kandydaci_diag = []
        for url_kandydata in p['kandydaci_wlasciwi']:
            fragment = url_kandydata.rsplit('/', 1)[-1]
            diag = diagnoza_kandydat_pozycja(fragment, top_merged, top_sekcja)
            diag['url'] = url_kandydata
            kandydaci_diag.append(diag)
            print(f"  kandydat wlasciwy {fragment[:60]}: "
                  f"merged pozycja={diag['pozycja_merged']} wynik={diag['wynik_merged']}  "
                  f"sekcja pozycja={diag['pozycja_sekcja']} wynik={diag['wynik_sekcja']}")

        wpis = {
            'id': p['id'],
            'query': p['query'],
            'sekcja_uzytkownika': p['sekcja'],
            'url_zly_wygral': p['url_zly'],
            'top10_merged': top_merged,
            'top10_sekcja': top_sekcja,
            'kandydaci_wlasciwi': kandydaci_diag,
            'uwaga': p['uwaga'],
        }

        if p['id'] == 3:
            wpis['chunki_artykulu_zly_wygral'] = analiza_chunkow_artykulu(p['url_zly'], agent_sekcji)
            print('  chunki artykulu (surowy korpus, bez rerankingu):')
            for c in wpis['chunki_artykulu_zly_wygral']:
                print(f"    chunk {c['numer_chunku']}: {c['tekst_200'][:100]}")

        wyniki.append(wpis)
        zapisz_czesciowo(wyniki)

    print(f'\nZapisano: {WYJSCIE}')
