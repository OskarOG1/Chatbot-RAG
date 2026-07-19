## Chatbot-RAG

Chatbot RAG z 3 oddzielnymi sekcjami do klasyfikacji zapytań przez embeddingi, z własnym stylem odpowiedzi.

Dane: 141 artykułów z Allegro Pomoc (konto 34, zakupy 69, płatności 38). Cały stack jest lokalny (Ollama, FAISS, embeddingi liczone na miejscu), bo docelowy kierunek to sektor, gdzie dane nie mogą wychodzić na zewnątrz.

Projekt edukacyjny, niezwiązany z Allegro. Treść artykułów, fragmenty, embeddingi i indeksy są w `.gitignore` i nie ma ich w repozytorium — są objęte licencją Allegro. Repo zawiera wyłącznie kod, dane odtwarza się skryptami. „Sekcje" to router i 3 konfiguracje RAG, bez tool-callingu.

## Architektura

```
Pytanie użytkownika
      │
      ▼  filtry wejścia: puste / za krótkie / za długie / obcy alfabet / wzorce injection
      ▼  korektor literówek (Damerau-Levenshtein + próg częstości słowa)
      ▼  embedding (mmlw, prefiks "zapytanie: ", wymagany przy tym modelu)
ROUTER (głosowanie po 5 fragmentach, dwie sekcje przy remisie, margines=2)
      │
      ▼
WYSZUKIWANIE HYBRYDOWE — po słowach (BM25 z lematyzacją i trigramami) + po znaczeniu
(FAISS), rankingi łączone po pozycji (RRF), duplikaty wycinane po URL → 20 kandydatów
      │
      ▼
RERANKER (cross-encoder ocenia parę pytanie–fragment, okno 20) → 3 linki
      │
      ▼  odmowa: wynik rerankera < -3.2 + sędzia LLM (TAK/NIE) na near-domain — przed generacją
AGENT (system prompt sekcji + historia rozmowy + kontekst → Bielik-11B przez API / lokalnie Ollama)
      │
      ▼  wycięcie URL-i z tekstu, mapowanie cytatów [n] → źródło
      ▼  odmowa, jeśli pokrycie odpowiedzi kontekstem < 0.40 (backstop)
Odpowiedź + Źródła
```

Pierwotnym planem było zwracanie głównego linka, jednak trafny artykuł znajdował się często w top 3, a nie na pierwszym miejscu. Stąd zmiana na pokazywanie w odpowiedzi 3 linków, celność 56/60 vs 47/60 dla pojedynczego linka.

mmlw jako embedder, bo to model retrieval trenowany pod polski język, więc polski embedder łapie znaczenie lepiej niż wielojęzyczny. FAISS do wektorów, bo lokalny, szybki i wystarcza na tej skali. BM25 dołożony obok, bo sam embedding gubił pytania ze słowami-kluczami. Hybryda łączy znaczenie z dosłownym trafieniem.

Bielik jako model odpowiadający, bo polski model do polskich treści. Dwie wersje do różnych zadań: minitron 7B do jakości odpowiedzi, 1.5B do testów.

## Chunking

Pierwsza wersja to fixed-size: 576 fragmentów po 500 tokenów z zakładką 50, najprostsza metoda, świadomie wzięta jako baseline. Zakładałem, że zachowanie nagłówków wpłynie na jakość co najwyżej minimalnie — myliłem się.

Druga wersja tnie po sekcjach zamiast przez nagłówki, dokleja nagłówek do treści każdego fragmentu (wchodzi więc do embeddingu, BM25 i rerankera) i wycina wykryty spis treści. Wielosekcyjnych artykułów jest 29 ze 141. Wyszło 641 fragmentów zamiast 576, z czego 236 z nagłówkiem.

| Zestaw | top-3 przed | top-3 po | top-5 przed | top-5 po |
|---|---|---|---|---|
| czyste | 0.867 | **0.933** | 0.900 | **0.967** |
| z literówkami, sekcja z etykiety | 0.800 | **0.867** | 0.867 | 0.867 |

## Wyniki wyszukiwania

Zestaw testowy: pytania z ręcznie przypisaną sekcją i URL-em artykułu, który powinien się pojawić w wynikach. Przykłady: „jak zmienić hasło", „zapomniałem loginu", „towar nie dotarł", „paczka przyszła uszkodzona", „czym jest allegro pay", „jak rozłożyć zakup na raty", „czy sprzedawca jest wiarygodny", „jak oddać rzecz kupioną ze smartem". Top-3 oznacza, że właściwy artykuł jest wśród trzech pierwszych wyników.

Ścieżka na pierwszych 20 pytaniach:

| krok | top-3 |
|---|---|
| samo wyszukiwanie po znaczeniu (FAISS) | 10/20 |
| + BM25 i łączenie rankingów (RRF) | 12/20 |
| + rozszerzone etykiety w kilku przypadkach | 13/20 |
| + poprawki błędów blokujących wcześniejsze zmiany | 16/20 |

BM25 zmienił odpowiedzi na pytania ze słowami-kluczami, jak „jak zmienić hasło", gdzie embedding łapał „zmienić" i odpowiedź z hasła przechodziła na zmianę waluty.

Po dodaniu lematyzacji (simplemma) BM25 zaczął łapać odmiany słów. Zniknęły pudła typu „zapomniałem loginu", gdzie problemem była inna forma słowa, nie inne słowo. Na rozszerzonym zestawie 30 pytań — 28/30.

Zestaw rozszerzony do 60. Dopisałem potoczne pytania pod realne artykuły („gdzie zobaczę kiedy przyjdzie paczka", „mam kod rabatowy jak go użyć"), każda etykieta zwalidowana, że artykuł faktycznie jest w indeksie.

| metoda | top-1 | top-3 | top-5 |
|---|---|---|---|
| hybryda (RRF, bez rerankera) | — | 48/60 | 56/60 |
| + cross-encoder, okno 10 kandydatów | — | 56/60 | 57/60 |
| + cross-encoder, okno 20 kandydatów | **47/60** | **58/60** | **60/60** |

Najbardziej uczciwym wynikiem pozostaje 47/60 przy jednym linku. Reranker wybiera pięć z dwudziestu kandydatów, więc losowy wybór dałby 25%, a baza ma tylko 141 artykułów. Top-5 przestaje różnicować warianty, decyzje podejmowałem na top-3.

Przy oknie 20 pytanie „jak spłacić allegro pay" wypadło z top-3. Wokół allegro-pay jest około 18 artykułów i reranker wynosi bliski duplikat nad dokładny cel. Przegląd wartości potwierdził 20 kandydatów jako punkt, w którym wynik przestaje rosnąć; cięcie niżej kosztowało jakość.

## Literówki

Zestaw testowy jest pisany poprawną polszczyzną, realne zapytania nie. Na pytaniach z błędami top-3 spadło do 0.700, to był najsłabszy punkt.

| metoda | top-3 | top-5 |
|---|---|---|
| sam embedding | 0.700 | — |
| + BM25 na trigramach znakowych + lematyzacja | 0.800 | 0.867 |
| + korektor literówek (Damerau-Levenshtein, bez zależności) | 0.867 | 0.900 |
| + routing na dwie sekcje (margines=2, end-to-end) | 0.800 | 0.833 |

Trigramy znakowe podniosły też czyste pytania z 0.967 do 1.000. Korektor działa na słowniku zbudowanym z tytułów i treści artykułów, wariant OSA łapie transpozycje, które przechodzą przez trigramy. Naprawia `kotno→konto`, `smrtem→smartem` przed embeddingiem i przed BM25.

Nad korektorem stoi próg częstości słowa (`wordfreq`): poprawny polski wyraz o częstości powyżej 2.0 nie jest ruszany. Bez tego korektor manglował poprawne wejścia („Puść" → „push"). Świadomy efekt uboczny: literówki bez ogonków (`haslo` ma częstość 2.83) są chronione, więc nie są korygowane. Minimalna długość korygowanego słowa to 4 znaki, więc `jka→jak` przechodzi bez zmian.

Najmocniejszy efekt korektora był nie w wyszukiwaniu, tylko w routingu: trafność wyboru sekcji na zaszumionych pytaniach podskoczyła z 0.467 do 0.833. Literówka rozwala embedding zapytania, a router stoi wyłącznie na embeddingu.

## Odporność wejścia

Filtry odrzucają zapytania puste, za krótkie, za długie, napisane innym alfabetem niż łaciński (próg poniżej 0.5 liter łacińskich, cyrylica; zero fałszywych alarmów na polskim bez ogonków) oraz proste wzorce prompt injection. Realną obroną jest oparcie odpowiedzi na kontekście i próg pokrycia, filtr wzorców to jedna warstwa.

Fallback jest dwupoziomowy i sterowany korektorem, nie progiem pewności. Gdy korektor coś zmienił, nad odpowiedzią pojawia się „Szukam dla: … — czy o to chodziło?". Odpowiedź „nie" wysyła oryginał sprzed korekty z flagą `bez_korekty`. „Nie zrozumiałem" leci wyłącznie przy w pełni niezrozumiałych zdaniach, czyli gdy wszystkie słowa od 4 znaków są nieznane. Wcześniejsza wersja blokowała pytanie przy jednym nieznanym słowie — `correct('jak pozbyć się konta')` zwracał `nieznane: ['pozbyć']` i zabijał całkowicie poprawne zapytanie. Tury fallbacku nie wchodzą do historii ani do wyszukiwania, żeby nie zatruwać kontekstu.

Zapytania z nieznanymi słowami lądują w logu `trudne.jsonl` jako materiał na rozbudowę słownika i zestawu testowego.

## Odmowa odpowiedzi

Pierwsze podejście, próg pewności na wyniku wyszukiwania, odrzucone na pomiarze. 


Zostały dwa sygnały, każdy kalibrowany osobno.

Pytanie spoza bazy łapie wynik rerankera przed generacją, próg 0.05. Najniższy wynik na zestawie testowym to 0.945, najwyższy na pytaniach spoza bazy 0.005. Odmowa przed generacją oszczędza najdroższy krok.

Halucynację łapie pokrycie po generacji, próg 0.65: ile ważonych słów odpowiedzi występuje w kontekście. Waga IDF `log((1+N)/(1+df))` tłumi słowa, których w tej domenie jest wszędzie pełno („allegro", „konto", „zamówienie") i które zawyżały zwykłe pokrycie. Rozdzielenie na halucynacjach: 0.40 z wagami, 0.28 bez.

| próg | fałszywe odmowy | złapane halucynacje |
|---|---|---|
| 0.50 | 0/4 | 0/4 |
| **0.65** | **0/4** | **3/4** |

Czwarty przypadek (0.71) świadomie przepuszczony, podniesienie progu zjadłoby margines do najniższej poprawnej odpowiedzi (0.84).

Progi produkcyjne: reranker 0.05, pokrycie 0.65, częstość słowa 2.0, margines routingu 2, kandydaci 20.

LLM-as-judge: jedno wywołanie „TAK/NIE", czy kontekst odpowiada na pytanie, jest napisany, ale domyślnie wyłączony. Łapie kontekst źle dobrany tematycznie, czego żadna liczba nie łapie, ale podwaja czas odpowiedzi na CPU. 

## Cytaty i źródła

Prompt każe modelowi wstawiać `[n]` w treści i zabrania podawania URL-i. `verify_answer` wycina z tekstu wszystkie linki i osieroconą bibliografię, a `[n]` mapuje na realne źródło. Powód jest w danych: wszystkie 141 artykułów mają linki we własnej treści, więc 1.5B przepisywał je jako gotową listę i dublował sekcję „Źródła". Obce URL-e odsiewa ten sam regex, który buduje `links.json` 

Cytaty służą tylko do wyświetlania. Do odmowy odpowiedzi używam pokrycia, nie obecności `[n]`.

## Pamięć rozmowy

Historia to okno 3 tur. Wyszukiwanie leci na sklejce ostatniej tury użytkownika i bieżącego pytania, więc „a jak to zrobić z telefonu?" po pytaniu o hasło trafia tam, gdzie powinno. Przy okazji stabilizuje to routing, bo sekcja liczona jest z tego samego zapytania. Poprzednia sekcja wchodzi dodatkowo do routingu jako unia, dzięki czemu styl odpowiedzi nie zmienia się w połowie rozmowy. Wszystko bez dodatkowego wywołania modelu.

Przepisywanie pytania przez model jest zaimplementowane, ale domyślnie wyłączone, dokłada wywołanie LLM, a sklej ostatniej tury załatwia większość przypadków.

## API i frontend

Backend to FastAPI. `POST /chat` zwraca JSON z odpowiedzią, sekcją, listą źródeł i cytatami. `POST /chat/stream` to ten sam przepływ przez SSE, generator wysyła kolejne kroki (korekta, routing, wyszukiwanie, reranking, generacja), a na końcu wynik. 

Frontend to Streamlit: chat, wyświetlana sekcja, klikalne źródła, podgląd kroków na żywo, sidebar z ręcznym wyborem sekcji.

## Co sprawdziłem i odrzuciłem

Pojedynczy główny link, czyli wybór jednego źródła przez reranker z domieszką słów z tytułu (waga λ). Najlepszy wynik 47/60 przy λ=1,0, kolejne poziomy λ pogarszały, bo domieszka wciągała podobne leksykalnie, ale złe artykuły („mam kod rabatowy jak go użyć" przeleciało z trafienia w pudło). Trzy linki dawały w tym czasie 56/60 bez żadnego parametru do strojenia. Wcześniejsze warianty (suma, zliczanie, dyskont po URL) dały wynik identyczny co do jednego z baseline, bo po deduplikacji każdy URL ma dokładnie jeden fragment — nie było czego agregować.

Próg pewności na wyszukiwaniu, cztery sygnały, żaden nie rozdziela.

Odmowa przy braku cytatu `[n]`. 1.5B opiera odpowiedź na kontekście, ale nie cytuje konsekwentnie: przy trafnym wyniku 0.942 i poprawnej odpowiedzi lista cytatów bywała pusta. Odmowy leciały na dobrych odpowiedziach.

Wymuszona instrukcja cytowania („odpowiedź MUSI zawierać [n]") plus przykład. Najgorszy regres w projekcie: 1.5B zdegenerował odpowiedzi do samego spamu cytatów, czyszczenie tekstu wycinało je do pustego stringa, pokrycie spadało do zera i system odmawiał na wszystko. Wróciło do łagodnej wersji.

Pokrycie IDF jako sygnał pytania spoza bazy, wypadło tak samo jak pokrycie bez wag i było niestabilne między uruchomieniami („ile to 2+2" raz dawało 0.0, raz 0.89). Zostało przy rerankerze.

Filtr spisów treści w pierwszej wersji: diagnostyka złapała 86 z 576 fragmentów, ale po sprawdzeniu na źródle to była normalna treść (instrukcje, listy), nie spisy. Wycinanie wróciło później jako element chunkingu po sekcjach, sterowany strukturą dokumentu zamiast progiem na długość linii.

Multi-query: Bielik 1.5B generuje 2–3 parafrazy pytania, wyszukiwanie dla każdej osobno, wyniki sklejane przez RRF. Naprawiło jedno trudne pytanie, zepsuło kilka łatwych, bo w fuzji parafrazy przegłosowują oryginał: 28/30 → 24/30 przy trzech parafrazach, przy dwóch gorzej, wariant warunkowy 22/30. Możliwe, że problem jest w jakości parafraz z 1.5B, nie w mechanizmie, ale korektor i trigramy zjadły większość tego celu.

Normalizacja zapytania przed embeddingiem. „jak usunac konto" (bez ogonków i bez znaku zapytania) routowało do płatności, choć wszystkie inne warianty szły do konta. Pojedynczy graniczny przypadek, nie systematyczny błąd. Próba naprawy przez dopisywanie „?": wynik spadł z 18/20 na 15/20. Normalizacja ogonków zostaje tylko po stronie BM25, mmlw wymaga polskich znaków.

## Dopasowanie sekcji

Sweep wariantów routingu wymusiło pierwsze żywe żądanie przez API: „jak zmienić hasło" poszło do zakupów i wróciło ze źródłami o kupowaniu.

| wariant | wynik |
|---|---|
| centroid sekcji | 13/20 |
| najlepszy wynik, średnia z 3 fragmentów | 17/20 (po naprawie pomiaru) |
| najlepszy wynik, maksimum | 15/20 |
| głosowanie po 10 fragmentach | 16/20 |
| **głosowanie po 5 fragmentach** | **18/20 (wybrane)** |
| głosowanie hybrydowe (RRF) po 5 | 18/20 (równy, odrzucone) |

Centroid przegrywa przez zbyt spójną sekcję konto: wąska tematyka (logowanie, hasło, dane) daje „ostry" centroid, który przyciąga wszystkie niejednoznaczne pytania — wszystkie jego pudła wpadły w konto. Wynik wariantu top-1 wzrósł z 14/20 do 17/20, gdy naprawiłem błąd w skrypcie pomiarowym: embedding zapytania bez prefiksu „zapytanie: ", którego wymaga mmlw. W samym chatbocie prefiks był od początku, więc to poprawa pomiaru, nie routera.

Maksimum zamiast średniej premiuje pojedynczy przypadkowy fragment, przy płaskich wynikach jeden dobrze dopasowany kawałek w złej sekcji przeważa całą decyzję. Średnia wymaga zgody kilku fragmentów.

Osobne indeksy mają jeszcze jeden problem: wyniki z różnych indeksów nie są porównywalne. Stąd jeden wspólny indeks i głosowanie. każdy fragment ma w metadanych sekcję, wygrywa ta, która dominuje. Przy 10 fragmentach zakupowe przegłosowywały login i raty. Wartości od 1 do 5 dają tę samą trafność, ale 1 to najbliższy sąsiad, nie głosowanie. Zostało 5: ten sam wynik plus margines na przegłosowanie pojedynczego złego fragmentu.

Głosowanie hybrydowe dało ten sam wynik z tymi samymi pudłami przy większej złożoności, więc odpadło.

Na zaszumionych pytaniach doszedł routing warunkowy na dwie sekcje: gdy lider wygrywa przewagą nie większą niż margines, przeszukiwane są obie, a kandydaci z obu idą razem do rerankera.

| margines | trafność sekcji | top-5 | udział decyzji 2-sekcyjnych |
|---|---|---|---|
| 2 | 0.900 | 0.833 | 33% |
| 3 | 0.967 | 0.900 | 70% |

Margines 3 domyka praktycznie całą stratę routingu. Wybrałem 2, bo 3 uruchamia podwójne wyszukiwanie i reranking na 70% ruchu, co na CPU jest za drogie. Świadoma wymiana jakości na czas, nie najlepszy wynik w tabeli.

## Pomiary czasowe

| krok | czas |
|---|---|
| router | < 50 ms |
| korekta + wyszukiwanie + reranking | 1–3 s |
| generacja, Bielik 1.5B | 8–10 s |
| generacja, Bielik-minitron 7B Q4_K_M | 53–61 s |

Długa generacja z racji na sprzęt, przez co produkcyjnie system nie będzie w pełni lokalny. 

Model mmlw ładowany jest raz na moduł — wcześniej `agents.py` trzymał własną kopię używaną tylko w testach, czyli trzy modele w pamięci zamiast dwóch. Wagi IDF cache'owane na dysk z kluczem po czasie modyfikacji korpusu. Pomiary mają własny cache rerankera i embeddingów, zapisywany po każdym wyliczeniu i unieważniany przy zmianie danych, więc przerwany pomiar wznawia się od miejsca przerwania.

## Wersja produkcyjna

Projekt zaczął się w pełni lokalny (Ollama + Bielik 1.5B/7B na CPU). Do publicznego demo trzeba było dwóch rzeczy: szybszego rerankera i mocniejszego modelu bez lokalnego GPU. Lokalny stack został zachowany — w kodzie pod `# Lokalne rozwiązanie` i przez zmienne środowiskowe. Produkcja to ten sam kod z innym `.env`.

**Model przez API.** Generacja idzie na Bielika-11B przez endpoint OpenAI-compatible (Public AI). Klient (`InferenceClient`) czyta `LLM_BASE_URL`, `LLM_API_KEY`, `MODEL` z `.env`; domyślnie celuje w lokalną Ollamę (`/v1`), więc ten sam kod działa lokalnie i produkcyjnie. Retrieval (embeddingi, reranker, FAISS) zostaje lokalny na serwerze — nisza „dane nie wychodzą" dotyczy zdolności do wdrożenia w pełni lokalnego; publiczne demo używa hostowanego Bielika dla dostępności.

**Swap rerankera — 26× szybciej.** `bge-reranker-v2-m3` (568M) na CPU liczył ~43 s na zapytanie, wąskie gardło demo. Zmierzone na golden 31 (agent z etykiety, izolacja od routingu):

| reranker | rozmiar | hit@3 | hit@5 | czas/zap |
|---|---|---|---|---|
| bge-reranker-v2-m3 | 568M | 0.933 | 0.967 | 43.5 s |
| mmarco-mMiniLMv2-L12-H384 | 118M | 0.900 | 0.933 | 1.64 s |

26× szybszy za koszt jednego trafienia na każdej metryce. Baseline bge zostaje jako wariant jakościowy, odrzucony na CPU ze względu na latencję. Rozbicie czasu (mmarco): embed 0.07 s / routing 0.01 s / retrieval 0.19 s / rerank 1.6 s.

**Rekalibracja bramek odmowy.** Trzy zmiany — swap rerankera, model 1.5B→11B i przebudowa promptów (grounding oddzielony od persony, z regułą „trzymaj się słownictwa z kontekstu") — unieważniły progi spod starego stacku. Każdy z trzech sygnałów strojony osobno na golden 30 + 18 OOD; wszystkie trzy rozkłady się nakładają, więc żaden próg nie rozdziela czysto. Ustawiam je tak, by nie kaleczyły trafnych pytań, a rozróżnianie near-domain zrzucam na sędziego:

- Bramka OOD (reranker, przed generacją): `-2.0 → -3.2`. Golden min -3.12 < OOD max -0.70 — brak separacji. Próg -2.0 fałszywie ucinał realne pytanie o bezpieczeństwo „ktoś włamał się na moje konto" (-3.12) jeszcze przed generacją; -3.2 je ratuje i czyni z rerankera zgrubny, tani filtr, który bez wywołania LLM ścina 11/18 oczywistych OOD (matematyka, przepisy, kod), a resztę oddaje sędziemu.
- Pokrycie (po generacji): `0.10 → 0.40`. Nowy prompt gruntuje mocniej, więc pokrycie wzrosło po obu stronach: golden min 0.239 < OOD max 0.516, dalej bez separacji. 0.40 to backstop minimalizujący fałszywe odmowy — próg 0.52 dałby zero przecieków, ale ubiłby to samo pytanie o włamanie (pokrycie 0.477), które właśnie uratował reranker.

**Sędzia LLM na near-domain OOD.** To, czego reranker i pokrycie nie łapią (OLX, przeziębienie, założenie firmy), odsiewa jedno wywołanie „TAK/NIE" do modelu. Zmierzone na golden 31 + 18 OOD:

| sędzia | fałszywe odmowy | OOD złapane |
|---|---|---|
| Bielik-11B | 2/30 | 17/18 |
| EuroLLM-22B | 5/30 | 18/18 |

Bielik-11B wybrany — balans: 2 fałszywe odmowy za 17/18 OOD. EuroLLM surowszy (pełne OOD, ale krzywdzi 5 poprawnych) — w rezerwie pod klienta compliance, gdzie „nigdy off-topic" waży więcej niż „czasem odmówi trafnego". Tańsze modele ogólne (EuroLLM, apertus) gorzej wyczuwają polską relewancję — sprawdzone na danych. Sędzia to +1 wywołanie (~3 s), włączany przez `SEDZIA_ON`, na darmowym demo wyłączany.

Model sędziego jest odpięty od modelu odpowiadającego. Zmienna `SEDZIA_MODEL` (domyślnie równa `MODEL`) pozwala posadzić w roli sędziego tańszy, mniejszy model niż ten generujący odpowiedzi — decyzja „TAK/NIE, czy kontekst pasuje" jest znacznie lżejsza niż generacja, więc nie wymaga tej samej klasy modelu. Kod jest pod to przygotowany: wystarczy wskazać `SEDZIA_MODEL` w `.env`, żeby ciąć koszt wywołania bramki bez ruszania jakości odpowiedzi.

Bilans całego łańcucha (reranker -3.2 → sędzia → pokrycie 0.40) na bieżącym przebiegu: 2/30 trafnych pytań fałszywie odrzuconych (jedno przez sędziego, jedno przez pokrycie), 1/18 OOD przeciekające przez wszystkie trzy bramki — nieszkodliwe „przetłumacz dzień dobry na angielski", które reranker, sędzia i pokrycie kolejno przepuszczają.

Wniosek metodyczny: żaden pojedynczy sygnał (score rerankera, pokrycie IDF) nie rozdziela near-domain OOD od słabych pytań z domeny — dopiero LLM-sędzia to robi. Każda zmiana rerankera, modelu albo promptu wymusza rekalibrację bramek, bo progi są sprzężone ze stackiem.

**Rate limit i obsługa błędów.** Publiczny endpoint ma globalny limiter (15/min + 200/dzień, env-tunable) chroniący budżet API przed spamem — per-IP niżej, w Caddy, bo za proxy backend widzi tylko localhost. Błędy generacji (API padnie/timeout) łapane są w całości i zwracają komunikat „model chwilowo niedostępny" zamiast tracebacku, z logiem po stronie serwera.

## Uruchomienie

Odtworzenie danych i indeksów (raz):

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

python src/links.py
python src/links_scraping.py
python src/chunking.py
python src/embedder.py
python src/vector.py
```

Model — dwie ścieżki, wybierane przez `.env` w `src/`:

```bash
# produkcyjnie: Bielik-11B przez API (OpenAI-compatible)
LLM_BASE_URL=https://api.publicai.co/v1
LLM_API_KEY=...
MODEL=speakleash/Bielik-11B-v3.0-Instruct
HF_TOKEN=...

# lokalnie: pobierz model do Ollamy, pomiń LLM_* (domyślnie celuje w localhost:11434/v1)
# ollama pull SpeakLeash/bielik-minitron-7B-v3.0-instruct:Q4_K_M
```

```bash
uvicorn src.api:app --reload
streamlit run frontend/app.py
```

