# Chatbot-RAG

Chatbot RAG z 3 oddzielnymi sekcjami do klasyfikacji zapytań, z własnym stylem odpowiedzi, klasyfikacja przez embeddingi, nie LLM.

Projekt edukacyjny. W repo jest tylko kod, treści artykułów nie ma — pobiera je scraper bezpośrednio ze źródła. „Sekcje" to router + 3 konfiguracje RAG, bez tool-callingu.

Dane: 141 artykułów z Allegro Pomoc (konto 34, zakupy 69, płatności 38), pocięte na 576 chunków po 500 tokenów z zakładką 50. Scraping asynchroniczny — httpx + asyncio z semaforem.

## Architektura

```
Pytanie użytkownika
      │
      ▼  embedding (mmlw, prefiks "zapytanie: ", liczony RAZ)
ROUTER (classify_top1: top-1 score na 3 indeksach FAISS, bez LLM)
      │
      ▼
WYSZUKIWANIE HYBRYDOWE — po słowach (BM25, z lematyzacją) + po znaczeniu (FAISS),
rankingi łączone przez RRF, duplikaty artykułów wycinane po URL → top-k chunków
      │
      ▼
AGENT (system prompt specjalizacji + kontekst → Bielik przez Ollamę)
      │
      ▼
Odpowiedź + Źródła (URL-e artykułów)
```

Cały stack jest lokalny (Ollama, FAISS, embeddingi liczone na miejscu), bo docelowy kierunek to sektor, gdzie dane nie mogą wychodzić na zewnątrz — RODO, publiczny, farmacja. Nic nie leci do API w chmurze.

mmlw jako embedder, bo to model retrieval trenowany pod polski — korpus jest polski, więc polski embedder łapie znaczenie lepiej niż wielojęzyczny. FAISS do wektorów, bo lokalny, szybki i wystarcza na tej skali (576 chunków). BM25 dołożony obok, bo sam embedding gubił pytania ze słowami-kluczami — hybryda łączy znaczenie z dosłownym trafieniem.

Bielik jako model odpowiadający, bo polski model do polskich treści. Dwie wersje do różnych zadań: minitron 7B do jakości odpowiedzi, 1.5B do szybkiej iteracji w pętli pomiarowej.

## Jak uruchomić

Repo zawiera tylko kod. Artefakty (indeksy FAISS, korpus BM25, chunki) i treści artykułów nie są w repo, więc pierwsze uruchomienie trzeba zacząć od pobrania danych i zbudowania indeksów.

Środowisko. Python 3.11, Windows/PowerShell. Tworzysz i aktywujesz venv, potem instalujesz zależności.

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt

Model. Odpowiedzi generuje Bielik przez Ollamę. Docelowo używany jest Bielik-minitron 7B (lepsza jakość, odsiewa śmieciowe chunki), ale przy pętli pomiarowej na CPU jedna odpowiedź trwa około minuty, więc do testów wygodniejszy jest Bielik 1.5B (szybszy, słabsza selekcja kontekstu). Ollama musi być uruchomiona w tle.

    ollama pull SpeakLeash/bielik-minitron-7B-v3.0-instruct:Q4_K_M
    ollama pull SpeakLeash/bielik-1.5b-v3.0-instruct:Q8_0

Budowa danych i indeksów. Skrypty odpalasz z katalogu src w tej kolejności. Najpierw links.py zbiera adresy artykułów, potem links_scraping.py pobiera ich treść do docs, chunking.py tnie artykuły na chunki, embedder.py liczy embeddingi, a vector.py buduje indeksy FAISS i korpus BM25. Każdy krok zapisuje artefakty do RAG, z których korzysta następny.

    python links.py
    python links_scraping.py
    python chunking.py
    python embedder.py
    python vector.py

Uruchomienie. Po zbudowaniu artefaktów odpalasz pipeline z pytaniem wpisanym w bloku __main__.

    python pipeline.py

Pomiar. Wynik Hit@3 na golden secie liczy measure.py.

    python measure.py

## Wyniki

Wyniki na testowych pytaniach z ręcznie dopasowanymi sekcjami i linkami. Przykłady z golden: „jak zmienić hasło", „zapomniałem loginu", „towar nie dotarł", „paczka przyszła uszkodzona", „czym jest allegro pay", „jak rozłożyć zakup na raty", „czy sprzedawca jest wiarygodny", „jak oddać rzecz kupioną ze smartem". Każde pytanie ma ręcznie przypisaną sekcję i URL artykułu, który powinien pojawić się w top-3.

Wyszukiwanie samym FAISS — Hit@3 = 0,50. Po dodaniu BM25 i RRF wynik wzrósł do 0,60. Hybrydowe wyszukiwanie zmieniło odpowiedzi na pytania ze słowami-kluczami, jak „jak zmienić hasło", gdzie embedding łapał „zmienić" i odpowiedź z hasła przechodziła na zmianę waluty. BM25 wyłapywał te klucze i zwiększył wynik.

Rozszerzenie w kilku przypadkach etykiet z linkami — 0,65. Wprowadzenie poprawek w kodzie, błędów, przez które potencjał wcześniejszych zmian nie był wykorzystywany — 0,75. Naprawa buga w korpusie BM25, przez który tytuły artykułów nie wchodziły do wyszukiwania (literał zamiast f-stringa) — 0,80.

Po dodaniu stemmingu (simplemma) BM25 zaczął łapać odmiany słów — zniknęły pudła typu „zapomniałem loginu", gdzie problemem była inna forma słowa, nie inne słowo. Na rozszerzonej bazie 30 pytań wynik wzrósł z 0,90 do 0,93.

Po rozszerzeniu bazy na 30 pytań i dodaniu stemmingu wynik wygląda następująco:

| Wersja | Metoda | Hit@3 (golden 30) | Hit@3 (golden 20) |
|---|---|---|---|
| v1 | FAISS only (cosine, IndexFlatIP + normalize_L2) | 0.53 | 0.50 |
| v2 | BM25 + FAISS + RRF (K=60) + dedup po URL + normalizacja PL + stemming | **0.93** | 0.80 (bez stemmingu) |

## Co sprawdziłem i odrzuciłem

Reranker odrzucony bez budowania — sprawdziłem pudła po dedupie: trafnych artykułów w ogóle nie było w rankingu, więc reranker nie miałby czego układać. Nie dokładam zależności, która nic nie naprawi.

Filtr TOC również się nie sprawdził przez to, że dużo artykułów zawiera listy kroków — diagnostyka złapała 86 z 576 chunków, ale po sprawdzeniu na źródle to była normalna treść (instrukcje, listy), nie spisy treści.

Mlti-query: Bielik 1.5B generuje 2–3 parafrazy pytania, retrieval dla każdej osobno, wyniki skleja RRF. Na moich danych pogorszyło — naprawiło jedno trudne pytanie, zepsuło kilka łatwych, bo w fuzji parafrazy przegłosowują oryginał. 0,93 → 0,80 przy trzech parafrazach, przy dwóch jeszcze gorzej, wariant z warunkowym progiem 0,73 — wycofane. Możliwe że problem jest w jakości parafraz z 1.5B, nie w samym mechanizmie, ale większego modelu nie dało się sprawdzić w pętli pomiarowej na CPU.

Chciałem jeszcze dodać odpowiedź „nie wiem" dla pytań spoza bazy. Typowa rada to próg na podobieństwie — sprawdziłem trzy warianty (score RRF, cosine top-1, margines top1−top2) i żaden nie oddziela pytań trafnych od śmieciowych, rozkłady się nakładają. Dense retrieval zawsze coś zwrócić. Działające wyjście to ocena kontekstu przez LLM po retrievalu, ale to dodatkowy call na każde pytanie — na CPU.

Sprawdziłem też wspólny indeks dla wszystkich chunków z wyborem najczęstszej sekcji z top-k, zamiast osobnego routera. Na 20 pytaniach przegrał 16 do 17 — naprawił „jak zmienić hasło", ale zepsuł „zapomniałem loginu" i „towar nie dotarł". Na 30 pytaniach wyszedł remis 0,83 = 0,83, więc został prostszy wariant. Po stemmingu wspólny indeks pokazuje 0,87 — różnica jednego pytania, za mało żeby zmieniać decyzję, do sprawdzenia na większej bazie.

## Dopasowanie sekcji

Centroid 13/20 — top-1 14/20. Centroid przegrywa przez zbyt spójną sekcję konto: wąska tematyka (logowanie, hasło, dane) daje „ostry" centroid, który przyciąga wszystkie niejednoznaczne pytania — wszystkie pudła centroidu wpadły w konto. Top-1 nie ma tego problemu.

Wynik top-1 wzrósł do 17/20, gdy naprawiłem błąd w skrypcie pomiarowym — embeddowanie zapytania użytkownika bez prefiksu „zapytanie: ", którego wymaga model mmlw. W pipeline prefiks był od początku, więc to poprawa pomiaru, nie routera. Na bazie 30 pytań: 0,83 (25/30).

## Pomiary czasowe

Scraping 141 artykułów — 15 sekund (async, sync wychodził ~2 minuty). Generowanie odpowiedzi: Bielik-minitron 7B Q4_K_M ~53–61 sekund na odpowiedź, Bielik 1.5B ~8–10 sekund, ale ze spadkiem jakości — 1.5B bierze z kontekstu, tylko nie odsiewa śmieciowych chunków. Router < 50 ms.

## Roadmap

FastAPI,  Streamlit (chat UI z klikalnymi cytatami),  Docker + pytest + GitHub Actions.
