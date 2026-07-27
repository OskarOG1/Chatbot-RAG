# Chatbot RAG — odpowiedzi wyłącznie z bazy dokumentów

Chatbot, który odpowiada na pytania **tylko na podstawie dostarczonych artykułów**, nigdy z ogólnej wiedzy modelu. Każda odpowiedź ma odnośniki do źródeł. Gdy odpowiedzi nie ma w bazie  system odmawia zamiast zmyślać.

**Demo: [ogflow.pl](https://ogflow.pl)**

Baza testowa: 141 artykułów Allegro Pomoc, 641 fragmentów. Projekt edukacyjny, niezwiązany z Allegro.

---

## Wyniki

| Co mierzone | Wynik |
|---|---|
| Właściwy artykuł w top 5 wyników | **0.918** (61 pytań) |
| Właściwy artykuł w top 5, zestaw z literówkami | 0.840 (50 pytań) |
| Fałszywe odmowy — odrzucone pytania, na które system umiał odpowiedzieć | **0/61** |
| Pytania nie na temat, poprawnie odrzucone | **7/8** |
| Mediana czasu odpowiedzi (produkcja, Docker) | 6.31 s |

Przekrój na 100 pytaniach w 6 kategoriach: 76 odpowiedzi, 24 odmowy.

| Kategoria pytań | Odpowiedzi |
|---|---|
| zwykłe | 25/26 |
| z literówkami | 19/21 |
| złożone, trzyczęściowe | 12/13 |
| złożone, dwuczęściowe | 12/16 |
| niejasne („jak to zmienić") | 7/16 |
| nie na temat | 1/8 *(odrzucanie działa)* |

---

## Co to znaczy w praktyce

**Problem, który rozwiązuje.** Chatbot podpięty prosto do modelu językowego nie bazuję na wiedzy od klienta i nie ma określonego sposobu odpowiadania. 

**Jak to jest rozwiązane.** Zanim model cokolwiek napisze, system wyszukuje właściwe fragmenty dokumentów i podaje mu je jako jedyne dopuszczalne źródło. Po wygenerowaniu odpowiedzi sprawdza, czy faktycznie się na nich opiera. Jeśli nie, odmawia odpowiedzi. 
**Trzy niezależne bramki odmowy:**

1. **Przed wyszukiwaniem** — filtry odrzucają puste, za krótkie, za długie zapytania i podstawowe próby manipulacji promptem.

2. **Przed generacją** — jeśli żaden fragment nie pasuje wystarczająco, model w ogóle nie jest wołany (oszczędza najdroższy krok). Pytania graniczne ocenia osobne wywołanie modelu: „czy da się na to odpowiedzieć z tego kontekstu, TAK/NIE"

3. **Po generacji** — sprawdzenie, ile ważnych słów odpowiedzi faktycznie występuje w źródłach. Odpowiedź oderwana od kontekstu jest odrzucana

**Dane mogą nie opuszczać serwera.** Wyszukiwanie, embeddingi i reranking działają lokalnie. Model generujący też może być lokalny, u mnie tak nie jest ze względu na ograniczenia sprzętowe.

---

## Jak to działa

```
Pytanie użytkownika
      │
      ▼  filtry wejścia: puste / za krótkie / za długie / obcy alfabet / wzorce injection
      ▼  korektor literówek (Damerau-Levenshtein + próg częstości słowa)
      ▼  embedding (mmlw, prefiks "zapytanie: ")
      │
      ▼
WYSZUKIWANIE HYBRYDOWE, cały korpus
  po słowach (BM25 z lematyzacją i trigramami) + po znaczeniu (FAISS)
  rankingi łączone po pozycji (RRF), duplikaty wycinane po URL → 20 kandydatów
      │
      ▼
RERANKER (cross-encoder ocenia parę pytanie–fragment, okno 20) → 5 linków
      │
      ▼  BRAMKA 1: wynik rerankera < −4.3 → odmowa bez wołania modelu
      ▼  BRAMKA 2: sędzia LLM (TAK/NIE) na pytaniach granicznych
      │
      ▼
GENERACJA (system prompt + historia rozmowy + kontekst → Bielik-11B przez API / lokalnie Ollama)
      │
      ▼  wycięcie URL-i z tekstu, mapowanie cytatów [n] → źródło
      ▼  BRAMKA 3: pokrycie odpowiedzi kontekstem < 0.20 → odmowa
      │
      ▼
Odpowiedź + Źródła
```

### Dobór technologii

| Element | Wybór | Dlaczego |
|---|---|---|
| Embeddingi | mmlw | Trenowany pod polski — łapie znaczenie lepiej niż model wielojęzyczny |
| Baza wektorowa | FAISS | Lokalna, szybka, wystarcza na tej skali |
| Wyszukiwanie po słowach | BM25 + lematyzacja + trigramy | Sam embedding gubił pytania zbudowane wokół konkretnych słów |
| Reranker | mmarco-mMiniLMv2 (118M) | 26× szybszy od bge-v2-m3 przy stracie jednego trafienia |
| Model odpowiadający | Bielik-11B | Polski model do polskich treści |

---

## Kluczowe decyzje: problem → rozwiązanie → wynik

### 1. Samo wyszukiwanie po znaczeniu nie wystarcza

**Problem.** „Jak zmienić hasło" trafiało w artykuł o zmianie waluty. Embedding łapał słowo „zmienić", gubił „hasło".

**Rozwiązanie.** Dołożone wyszukiwanie po słowach (BM25), oba rankingi łączone przez RRF. Potem lematyzacja, żeby BM25 rozpoznawał odmiany słów zamiast wymagać dokładnej formy.

**Wynik.** Na pierwszych 20 pytaniach: 10/20 → 12/20 po dołożeniu BM25, 16/20 po naprawie błędów blokujących. Po lematyzacji na 30 pytaniach: 28/30. 

### 2. Nagłówki w fragmentach

**Problem.** Pierwsza wersja cięła artykuły na równe kawałki po 500 tokenów. Zakładałem, że zachowanie nagłówków da co najwyżej minimalną różnicę.

**Rozwiązanie.** Cięcie po sekcjach, nagłówek doklejany do treści fragmentu (wchodzi do embeddingu, BM25 i rerankera). Wykryty spis treści wycinany. 641 fragmentów zamiast 576, z czego 236 z nagłówkiem.

**Wynik.** Myliłem się — różnica była wyraźna.

| Zestaw | top 3 przed | top 3 po | top 5 przed | top 5 po |
|---|---|---|---|---|
| pytania bez błędów | 0.867 | **0.933** | 0.900 | **0.967** |
| pytania z literówkami | 0.800 | **0.867** | 0.867 | 0.867 |

### 3. Literówki rozwalały wyszukiwanie

**Problem.** Zestaw testowy pisany poprawną polszczyzną, realne pytania nie. Na pytaniach z błędami trafność spadała do 0.700 — najsłabszy punkt systemu.

**Rozwiązanie.** Trigramy znakowe w BM25 (dopasowanie po trójkach liter, tolerancyjne na błędy) + korektor Damerau-Levenshtein na słowniku zbudowanym z treści artykułów. Nad korektorem próg częstości słowa: poprawny polski wyraz nie jest ruszany.

**Wynik.** 0.700 → 0.800 (trigramy) → 0.867 (korektor). Trigramy podniosły też czyste pytania z 0.967 do 1.000.

Aktualny pomiar odporności samej warstwy wyszukiwania:

| Zestaw | top 3 | top 5 | czas/zapytanie |
|---|---|---|---|
| bez błędów | **0.860** | **0.940** | 3.24 s |
| z jedną literówką na pytanie | 0.720 | 0.840 | 4.44 s |

Literówka bez korektora kosztuje 0.140 trafności. Korektor przed wyszukiwaniem nie jest zbędnym krokiem.



### 5. Dzielenie bazy na sekcje szkodziło

**Problem.** Pierwotnie baza była podzielona na trzy sekcje tematyczne, a osobny router zgadywał, w której szukać. Na 20-30 pytaniach wyglądało to dobrze. Podział pierwotnie był robiony w ramach nauki pod przyszłe, rozbudowane projekty. Zdawałem sobie sprawę, że przy tak małej bazie jest to niepotrzebne. 

**Rozwiązanie.** Rozszerzenie zestawu testowego do 61 pytań i porównanie z przeszukiwaniem całej bazy.

**Wynik.** Router przegrywał na każdej osi. Usunięty.

| Tryb | top 5 (61 pytań) | czas/zapytanie | pytania nie na temat odcięte za darmo |
|---|---|---|---|
| router (dwie sekcje) | 0.852 | 4.41 s | 5/29 |
| **cała baza** | **0.918** | **3.33 s** | **7/29** |

Router rankował 40 par (2×20 ze zgadywanych sekcji). Przeszukanie całości daje 20 kandydatów, ale lepiej wycelowanych.

### 6. Żaden pojedynczy próg nie odróżnia pytań granicznych

**Problem.** „Ile Allegro bierze prowizji", „kto jest właścicielem Allegro", „jak założyć sklep" — pytania blisko tematu, ale spoza bazy. Rozkłady wyników dla pytań trafnych i nietrafnych nakładają się: 23 z 29 pytań spoza bazy punktuje wyżej niż najsłabsze pytanie z domeny.

**Rozwiązanie.** Próg rerankera przestaje udawać klasyfikator. Jego jedyna rola to tanie odcięcie skrajności przed wywołaniem modelu. Rozróżnianie pytań granicznych przejmuje osobne wywołanie LLM („TAK/NIE, czy da się odpowiedzieć z tego kontekstu").

**Wynik.** Próg poluzowany z −3.2 do −4.3:

| Próg | Fałszywe odmowy | Odcięte za darmo | Wywołań sędziego |
|---|---|---|---|
| −3.2 | 2/61 | 11/29 | 77 |
| **−4.3** | **0/61** | 5/29 | 85 |

Zero fałszywych odmów kosztem 8 dodatkowych wywołań — tanio, bo sędzia i tak te pytania łapał.

Wybór sędziego:

| Model | Fałszywe odmowy | Nie na temat złapane |
|---|---|---|
| **Bielik-11B** | **2/30** | **17/18** |
| EuroLLM-22B | 5/30 | 18/18 |

Bielik jako kompromis. EuroLLM w rezerwie pod klienta, gdzie „nigdy nie odpowiadaj nie na temat" waży więcej niż okazjonalna fałszywa odmowa. Model sędziego jest odpięty od modelu odpowiadającego — decyzja TAK/NIE jest lżejsza niż generacja, więc może na niej siedzieć tańszy model.

### 7. Bramka antyhalucynacyjna wyrzucała dobre odpowiedzi

**Problem.** Z 24 odmów w symulacji 100 pytań aż 7 padło **po** generacji (877 zmarnowanych tokenów), w tym dwie na w pełni trafnych pytaniach. Wyszukiwanie trafiło właściwy artykuł na pierwsze miejsce, model odpowiedział poprawnie i odpowiedź została odrzucona. Przyczyna: model parafrazuje słowami spoza kontekstu („weryfikacja", „tożsamość" przy pytaniu o odzyskanie konta), więc pokrycie leksykalne spada mimo trafności.

**Rozwiązanie.** Rekalibracja progu pokrycia z 0.40 na 0.20, na rozkładzie 29 pytań wieloczłonowych z domeny vs 29 spoza.

|  | min | mediana | max |
|---|---|---|---|
| pytania z domeny | 0.253 | 0.690 | 0.885 |
| pytania spoza | 0.042 | 0.228 | 0.651 |

**Wynik.**

| Próg | Fałszywe odmowy |
|---|---|
| 0.40 | 4/29 |
| **0.20** | **0/29** |

Wybrany 0.20, nie 0.25: najniższe trafne pytanie ma 0.253, a generacja jest lekko losowa (rozrzut 0.01–0.03). 0.25 zostawiłby margines 0.003. 0.20 daje 0.05 i wciąż reaguje na tekst bez oparcia w źródłach.

### 8. Błąd w danych zdiagnozowany po czasie odmowy

**Problem.** Pytanie „Sprzedawca chce, żebym zapłacił poza Allegro — czy to bezpieczne?" było stabilnie odrzucane, mimo że jest z domeny.

**Rozwiązanie.** Czas odmowy wskazuje bramkę bez zaglądania w kod: <1 s to filtr wejścia, ~2.9 s to próg rerankera, ~6.3 s to sędzia. To pytanie padało po ~6.3 s — czyli sędzia dostawał zły kontekst.

**Wynik.** Właściwy artykuł miał etykietę `konto` zamiast `zakupy`, więc nigdy nie trafiał do puli kandydatów. Naprawa: jedna linia mapowania + przeniesienie 3 artykułów. Kontrola regresji: trafność bez zmian (0.900/0.933).

---

## Bezpieczeństwo i odporność

**Ochrona przed manipulacją promptem.** Filtry wejścia odrzucają znane wzorce, ale realną obroną jest oparcie odpowiedzi na kontekście i bramka pokrycia. Filtr wzorców to jedna warstwa, nie całość.

**Logi bez danych osobowych.** Zapisywane są wyłącznie nierozpoznane pojedyncze słowa, nigdy treść pytania. Maile, telefony, numery zamówień i URL-e odsiewane dopasowaniem wzorców do oryginału. Sprawdzone na 7 przypadkach: dane osobowe znikają, literówki (`kotno`, `smrtem`, `blikeim`) zostają jako materiał na rozbudowę słownika.

**Limit zapytań.** Globalny limiter, domyślnie 15/min i 200/dzień, konfigurowalny. Chroni budżet API. Limit jest globalny, nie per-IP. Przy takim projekcie i koncie zasilonym na 2$ - niepotrzebne per-IP.

**Obsługa błędów.** Awaria API zwraca „model chwilowo niedostępny" zamiast tracebacku, z logiem po stronie serwera. Streamlit startuje z wyłączonymi szczegółami błędów, więc nieprzewidziany wyjątek nie pokaże ścieżek kontenera w przeglądarce.

**Obsługa niezrozumiałych pytań.** Dwa poziomy, sterowane korektorem. Gdy korektor coś poprawił, pojawia się pytanie zwrotne „Szukam dla: … czy o to chodziło?"; „nie" wraca do oryginału. „Nie zrozumiałem" pada tylko wtedy, gdy wszystkie słowa od 4 znaków są nieznane. Tury z pytaniem zwrotnym nie wchodzą do historii ani do wyszukiwania.

---

## Cytaty, źródła i pamięć rozmowy

**Cytaty.** Prompt każe wstawiać odnośniki `[n]` i zabrania gołych URL-i. Funkcja wycina linki z tekstu i mapuje `[n]` na źródło. Powód jest w danych: wszystkie 141 artykułów mają linki we własnej treści, więc mniejszy model przepisywał je jako listę i dublował sekcję „Źródła". Cytaty służą wyłącznie do wyświetlania, do odmowy używane jest pokrycie, nie obecność `[n]`.

**Pamięć rozmowy.** Okno 3 tur. Wyszukiwanie leci na sklejce ostatniej wypowiedzi i bieżącego pytania, więc „a jak to z telefonu?" po pytaniu o hasło trafia poprawnie. Bez dodatkowego wywołania modelu.

---

## API i frontend

Backend: **FastAPI**. `POST /chat` zwraca JSON (odpowiedź, źródła, cytaty). `POST /chat/stream` — ten sam proces przez SSE, kolejne kroki na bieżąco.

Frontend: **Streamlit**. Czat, klikalne źródła, podgląd kroków na żywo.

---

## Wdrożenie

Demo: [ogflow.pl](https://ogflow.pl). VPS Hetzner, Ubuntu 24.04 LTS, 4 vCPU / 7.6 GB RAM.

| Kontener | Obraz | Rola |
|---|---|---|
| `caddy` | caddy:2 | reverse proxy, HTTPS z Let's Encrypt |
| `frontend` | python:3.13-slim | Streamlit |
| `api` | python:3.13-slim | FastAPI + wyszukiwanie |

**Czas odpowiedzi w kontenerze** (5 pytań × 3 powtórzenia):

| Metryka | Wartość |
|---|---|
| mediana do pierwszego fragmentu | 5.61 s |
| mediana całkowita | 6.31 s |
| maksimum (pierwszy przebieg) | 16.57 s |



## Załącznik: co sprawdziłem i odrzuciłem


**Pojedynczy główny link zamiast trzech.** Wybór jednego źródła z domieszką słów z tytułu (waga λ). Najlepszy wynik 47/60 przy λ=1,0; wyższe λ wciągały leksykalnie podobne, ale złe artykuły. Trzy linki dawały 56/60 bez żadnego parametru do strojenia.

**Próg pewności na samym wyszukiwaniu.** Cztery różne sygnały. Żaden nie rozdzielał pytań trafnych od nietrafnych.

**Odmowa przy braku cytatu `[n]`.** Mniejszy model (1,5B) nie cytował konsekwentnie nawet przy trafieniu 0.942 i poprawnej odpowiedzi. Odmowy padały na dobrych odpowiedziach.

**Wymuszona instrukcja cytowania.** Najgorszy regres w projekcie. Po dodaniu „odpowiedź MUSI zawierać [n]" model zdegenerował odpowiedzi do spamu cytatów, czyszczenie wycinało je do pustego stringa, pokrycie spadało do zera i system odmawiał na wszystko. Również na 1,5B, większy model nie potrzebował dodatkowych instrukcji. 

**Pokrycie IDF jako sygnał pytania spoza bazy.** Niestabilne między uruchomieniami — „ile to 2+2" raz dawało 0.0, raz 0.89.

**Filtr spisów treści.** Diagnostyka złapała 86 z 576 fragmentów jako podejrzane. Po sprawdzeniu na źródle: normalna treść, nie spisy. Wróciło później jako element cięcia po sekcjach, sterowany strukturą dokumentu zamiast progiem na długość linii.

**Multi-query.** Model generuje 2–3 parafrazy pytania, wyniki sklejane przez RRF. Naprawiło jedno trudne pytanie, zepsuło kilka łatwych — parafrazy przegłosowywały oryginał: 28/30 → 24/30 przy trzech parafrazach. Parafrazy również generował 1,5B, nie sprawdzałem na lepszym modelu. 

**Normalizacja zapytania przed embeddingiem.** „Jak usunac konto" (bez ogonków) trafiało do płatności zamiast konta. Pojedynczy graniczny przypadek. Próba naprawy przez dopisywanie znaku zapytania: 18/20 → 15/20. Normalizacja została tylko po stronie BM25 — mmlw wymaga polskich znaków.

**Przepisywanie pytania przez model.** Zaimplementowane, domyślnie wyłączone. Sklejenie ostatniej tury załatwia większość przypadków bez kosztu kolejnego wywołania.

---

## Załącznik: historia kalibracji progów

Progi są sprzężone ze stackiem. Każda zmiana rerankera, modelu albo promptu wymusza rekalibrację wszystkich naraz — poniżej zapis, jak przebiegała.

**Pierwsza kalibracja** (reranker bge, model 1,5B): próg rerankera 0.05, pokrycie 0.65. Wtedy rozkłady rozdzielały się czysto, najniższy wynik na pytaniu testowym 0.945, najwyższy na pytaniu spoza tematu 0.005.

**Po wymianie rerankera i modelu na 11B** progi przestały działać. Nowy prompt (grounding oddzielony od persony) podniósł pokrycie po obu stronach. Rozkłady zaczęły się nakładać. Próg rerankera −2.0 → −3.2, pokrycie 0.10 → 0.40.

**Po usunięciu podziału na sekcje i rozszerzeniu zestawów** (30→61 trafnych, 18→29 spoza tematu): próg rerankera −3.2 → −4.3, pokrycie 0.40 → 0.20. Stan obecny.

Nowe pytania spoza tematu są głównie graniczne (prowizja sprzedawcy, infolinia, notowania giełdowe). Stary zestaw był zdominowany oczywistymi przypadkami — matematyka, przepisy, kod — które ucina już sam próg. Zawyżał wrażenie odporności systemu.

**Pomiary czasowe pipeline'u:**

| Krok | Czas |
|---|---|
| embedding | 0.07 s |
| wyszukiwanie | 0.19 s |
| reranking | 1.6 s |
| generacja, Bielik 1,5B lokalnie | 8–10 s |
| generacja, Bielik-minitron 7B lokalnie (Q4_K_M) | 53–61 s |

Długa generacja lokalna wynika ze sprzętu. dlatego publiczne demo używa modelu przez API. 

**Limit długości odpowiedzi: 700 → 1500 tokenów.** Przy 700 najdłuższa odpowiedź w pomiarze (691 tokenów) była ucinana w pół zdania, niewidocznie w logach, pętla streamująca ignorowała przyczynę zakończenia. Bez górnego limitu koszt przestałby mieć granicę, a rozwlekła odpowiedź zbija pokrycie i bramka odrzucałaby własną poprawną odpowiedź.

**Rozgrzewka indeksów przy starcie.** Indeksy wczytywały się leniwie, `lifespan` rozgrzewał tylko reranker i embedder. Pierwsze zapytanie płaciło za wczytanie indeksu: 18.1 / 17.9 / 15.2 s zamiast typowych 3–7 s.
