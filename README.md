## Chatbot-RAG

Chatbot RAG z 3 oddzielnymi sekcjami do klasyfikacji zapytań przez embeddingi, z własnym stylem odpowiedzi

Dane: 141 artykułów z Allegro Pomoc (konto 34, zakupy 69, płatności 38), pocięte na 576 chunków po 500 tokenów z zakładką 50. Jest to najprostsza metoda, jednak, co w tym przypadku istotne (zachowanie nagłówków) wpłyneło by co najwyżej minimalnie na jakość odpowiedzi. (do zmierzenia w przyszłości)

## Architektura

```
Pytanie użytkownika
      │
      ▼  embedding (mmlw, prefiks "zapytanie: ", prefiks wymagany przy tym modelu )
ROUTER (vote: Najczęściej występujący istotny wynik)
      │
      ▼
WYSZUKIWANIE HYBRYDOWE — po słowach (BM25, z lematyzacją) + po znaczeniu (FAISS),
rankingi łączone przez RRF, duplikaty artykułów wycinane po URL → top-k chunków/ osobna funkcja do zachowywania url do routingu 
      │
      ▼
AGENT (system prompt specjalizacji + kontekst → Bielik przez Ollamę)
      │
      ▼
Odpowiedź + Źródła (URL-e artykułów, top 3 istotne)
```

Pierwotnym planem było zwracanie głównego linka, jednak trafny artykuł znajdował się często w top 3, a nie na pierwszym miejscu. Stąd zmiana na pokazywanie w odpowiedzi 3 linków, celność 56/60 vs 47/60 dla pojedynczego linka.

Cały stack jest lokalny (Ollama, FAISS, embeddingi liczone na miejscu), bo docelowy kierunek to sektor, gdzie dane nie mogą wychodzić na zewnątrz.

mmlw jako embedder, bo to model retrieval trenowany pod polski język, więc polski embedder łapie znaczenie lepiej niż wielojęzyczny. FAISS do wektorów, bo lokalny, szybki i wystarcza na tej skali . BM25 dołożony obok, bo sam embedding gubił pytania ze słowami-kluczami. Hybryda łączy znaczenie z dosłownym trafieniem.

Bielik jako model odpowiadający, bo polski model do polskich treści. Dwie wersje do różnych zadań: minitron 7B do jakości odpowiedzi, 1.5B testów.

## Wyniki

Wyniki na testowych pytaniach z ręcznie dopasowanymi sekcjami i linkami. Przykłady zestawu: „jak zmienić hasło", „zapomniałem loginu", „towar nie dotarł", „paczka przyszła uszkodzona", „czym jest allegro pay", „jak rozłożyć zakup na raty", „czy sprzedawca jest wiarygodny", „jak oddać rzecz kupioną ze smartem". Każde pytanie ma ręcznie przypisaną sekcję i URL artykułu, który powinien pojawić się w top-3.

Wyszukiwanie samym FAISS — Hit@3 = 10/20. 
Po dodaniu BM25 i RRF wynik wzrósł do 12/20. 
Hybrydowe wyszukiwanie zmieniło odpowiedzi na pytania ze słowami-kluczami, jak „jak zmienić hasło", gdzie embedding łapał „zmienić" i odpowiedź z hasła przechodziła na zmianę waluty. BM25 wyłapywał te klucze i zwiększył wynik.

Rozszerzenie w kilku przypadkach etykiet z linkami — 13/20.
Wprowadzenie poprawek w kodzie, błędów, przez które potencjał wcześniejszych zmian nie był wykorzystywany — 16/20. 

Po dodaniu stemmingu (simplemma) BM25 zaczął łapać odmiany słów. Zniknęły pudła typu „zapomniałem loginu", gdzie problemem była inna forma słowa, nie inne słowo. 
Finalny wynik na bazie 30 pytań - 28/30

Zestaw pytań rozszerzony do 60 pytań. Dopisałem potoczne pytania pod realne artykuły („gdzie zobaczę kiedy przyjdzie paczka", „mam kod rabatowy jak go użyć"), każda etykieta zwalidowana, że artykuł faktycznie jest w indeksie. Na tym zbiorze hybryda bez rerankera daje 48/60 w top-3 i 56/60 w top-5.

                               | top-3|| top-5|
| hybryda (RRF, bez rerankera) | 48/60 | 56/60 |
| + cross-encoder, okno 10 kandydatów | 56/60 | 57/60 |
| + cross-encoder, okno 20 kandydatów | 58/60 | 60/60 |

Przy oknie 20 linków, pytanie: „jak spłacić allegro pay" wypadło z top-3. Wokół allegro-pay jest  około 18 artykułów i reranker wynosi bliski duplikat nad dokładny cel, więc szersze okno nie jest . Top-5 to domyka

Na bazie pytań z błędami ortograficznymi, wynik: 
| metoda | hit@3 | hit@5 |
|---|---|---|
| sam embedding | 0.700 | — |
| + BM25 n-gramowy (trigramy + lematyzacja) | 0.800 | 0.867 |
| + korektor literówek (Damerau-Levenshtein, bez zależności) | 0.867 | 0.900 |
| + routing top-2 (margines=2, end-to-end) | 0.800 | 0.833 |
## Co sprawdziłem i odrzuciłem

Pojedynczy „najlepszy link" (MAIN), czyli wybór jednego głównego źródła przez reranker z domieszką leksyki tytułu (blend z wagą λ). Najlepszy wynik 47/60 przy λ=1,0, ale kolejne poziomy λ dokładały regresy, bo blend wciągał leksykalnie podobne, złe artykuły („mam kod rabatowy jak go użyć" przeleciało z trafienia w pudło). W tym samym czasie sekcja trzech rerankowanych linków dawała 56/60 bez żadnego parametru do strojenia. MAIN wyrzucony, trzy linki są prostsze i lepsze.

Filtr TOC również się nie sprawdził przez to, że dużo artykułów zawiera listy kroków — diagnostyka złapała 86 z 576 chunków, ale po sprawdzeniu na źródle to była normalna treść (instrukcje, listy), nie spisy treści.

Multi-query: Bielik 1.5B generuje 2–3 parafrazy pytania, retrieval dla każdej osobno, wyniki skleja RRF. Na moich danych pogorszyło, naprawiło jedno trudne pytanie, zepsuło kilka łatwych, bo w fuzji parafrazy przegłosowują oryginał. 28/30 → 24/30 przy trzech parafrazach, przy dwóch jeszcze gorzej, wariant z warunkowym progiem 22/30 — wycofane. Możliwe że problem jest w jakości parafraz z 1.5B, nie w samym mechanizmie, ale większego modelu nie dało się sprawdzić w pętli pomiarowej na CPU.


Normalizacja zapytania przed embeddingiem. Przy testach API wyszło, że „jak usunac konto" (bez ogonków i bez znaku zapytania) routuje do płatności, choć wszystkie inne warianty tego pytania idą do konta. Diagnoza: pojedynczy graniczny przypadek, nie systematyczny bug, embedding w pipeline i w pomiarze liczony identycznie. Próba naprawy przez dopisywanie „?", gdy go brakuje: golden spadł z 18/20 na 15/20, odrzucone. Normalizacja ogonków zostaje tylko po stronie BM25, mmlw wymaga polskich znaków.

## Dopasowanie sekcji

Cały sweep wariantów routingu wymusiło pierwsze żywe żądanie przez API: „jak zmienić hasło" poszło do zakupów i wróciło ze źródłami o kupowaniu.

Centroid 13/20, top-1 14/20. Centroid przegrywa przez zbyt spójną sekcję konto: wąska tematyka (logowanie, hasło, dane) daje „ostry" centroid, który przyciąga wszystkie niejednoznaczne pytania, wszystkie pudła centroidu wpadły w konto. Wynik top-1 wzrósł do 17/20, gdy naprawiłem błąd w skrypcie pomiarowym: embeddowanie zapytania użytkownika bez prefiksu „zapytanie: ", którego wymaga mmlw. W pipeline prefiks był od początku, więc to poprawa pomiaru, nie routera.

Sprawdziłem wariant z max zamiast mean (top-1 liczy średnią similarity z top-3 chunków): 15/20, regres. Max premiuje pojedynczy przypadkowy chunk, przy płaskich score jeden dobrze dopasowany kawałek w złej sekcji przeważa całą decyzję. Mean wymaga zgody kilku chunków, więc jest stabilniejszy.

Osobne indeksy mają jeszcze jeden problem, score z różnych indeksów nie są porównywalne. Rozwiązanie: jeden wspólny indeks i głosowanie. Biorę top-k chunków, każdy ma w metadanych sekcję, wygrywa ta, która dominuje. Przy k=10 wyszło 16/20, zakupowe chunki przegłosowywały login i raty. Przy k=5 18/20, najlepszy wynik, naprawił między innymi „jak zmienić hasło". Wartości k od 1 do 5 dają tę samą trafność, ale k=1 to najbliższy sąsiad, nie głosowanie, jeden nietypowy chunk decyduje bez korekty. Zostało k=5, ten sam wynik plus margines na przegłosowanie pojedynczego złego chunka.

Routing hybrydowy (RRF z FAISS i BM25 na wspólnym indeksie, głosowanie po top-5) dał ten sam wynik 18/20 z tymi samymi dwoma pudłami, przy większej złożoności. Odrzucony, router zostaje szybki i czysty.

| Wariant routingu | Wynik |
|---|---|
| centroid | 13/20 |
| top-1 mean top-3 | 17/20 (po naprawie pomiaru) |
| top-1 max | 15/20 (regres, odrzucone) |
| vote k=10 | 16/20 |
| **vote k=5** | **18/20 (wybrane)** |
| hybrid RRF k=5 | 18/20 (równy, odrzucone) |

Dwa pozostałe pudła zostają świadomie. „Nie działa moja karta": karta to płatność, ale kontekst awarii ciągnie semantycznie w stronę zakupów. „Kiedy dostanę zwrot pieniędzy": sporne, zwrot pieniędzy logicznie jest przepływem płatności. Oba to nakładające się domeny zakupy/płatności, nie błędy metody. Próba dociśnięcia ich prawie na pewno cofnęłaby któreś z 18 trafień, co było widać na max i k=10, psuły więcej niż zyskiwały.


## Pomiary czasowe
 Generowanie odpowiedzi: Bielik-minitron 7B Q4_K_M ~53–61 sekund na odpowiedź, Bielik 1.5B ~8–10 sekund, ale ze spadkiem jakości — 1.5B bierze z kontekstu, tylko nie odsiewa niepotrzebnych chunków. Router < 50 ms.


Projekt edukacyjny.  „Sekcje" to router + 3 konfiguracje RAG, bez tool-callingu.