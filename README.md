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
      │
      ▼
WYSZUKIWANIE HYBRYDOWE, cały korpus — po słowach (BM25 z lematyzacją i trigramami) +
po znaczeniu (FAISS), rankingi łączone po pozycji (RRF), duplikaty wycinane po URL → 20 kandydatów
      │
      ▼
RERANKER (cross-encoder ocenia parę pytanie–fragment, okno 20) → 3 linki
      │
      ▼  odmowa: wynik rerankera < -4.3 + sędzia LLM (TAK/NIE) na near-domain — przed generacją
AGENT (system prompt sekcji z etykiety najlepszego fragmentu + historia rozmowy + kontekst → Bielik-11B przez API / lokalnie Ollama)
      │
      ▼  wycięcie URL-i z tekstu, mapowanie cytatów [n] → źródło
      ▼  odmowa, jeśli pokrycie odpowiedzi kontekstem < 0.20 (backstop)
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

**Ten routing został później całkowicie usunięty** — patrz „Partycjonowanie na sekcje usunięte" w sekcji Wersja produkcyjna. Powyższe zostaje jako zapis decyzji trafnej na zestawie n=20/30; rozszerzenie pomiaru do n=61 pokazało, że koszt błędów routingu przewyższa jego korzyść.

## Pomiary czasowe

| krok | czas |
|---|---|
| router | < 50 ms |
| korekta + wyszukiwanie + reranking | 1–3 s |
| generacja, Bielik 1.5B | 8–10 s |
| generacja, Bielik-minitron 7B Q4_K_M | 53–61 s |

Długa generacja z racji na sprzęt, przez co produkcyjnie system nie będzie w pełni lokalny. 

Model mmlw ładowany jest raz na moduł — wcześniej `agents.py` trzymał własną kopię używaną tylko w testach, czyli trzy modele w pamięci zamiast dwóch. Wagi IDF cache'owane na dysk z kluczem po czasie modyfikacji korpusu.

## Wersja produkcyjna

Projekt zaczął się w pełni lokalny (Ollama + Bielik 1.5B/7B na CPU). Do publicznego demo trzeba było dwóch rzeczy: szybszego rerankera i mocniejszego modelu bez lokalnego GPU. Lokalny stack został zachowany — w kodzie pod `# Lokalne rozwiązanie` i przez zmienne środowiskowe. Produkcja to ten sam kod z innym `.env`.

**Model przez API.** Generacja idzie na Bielika-11B przez endpoint OpenAI-compatible (Public AI). Klient (`InferenceClient`) czyta `LLM_BASE_URL`, `LLM_API_KEY`, `MODEL` z `.env`; domyślnie celuje w lokalną Ollamę (`/v1`), więc ten sam kod działa lokalnie i produkcyjnie. Retrieval (embeddingi, reranker, FAISS) zostaje lokalny na serwerze — nisza „dane nie wychodzą" dotyczy zdolności do wdrożenia w pełni lokalnego; publiczne demo używa hostowanego Bielika dla dostępności.

**Swap rerankera — 26× szybciej.** `bge-reranker-v2-m3` (568M) na CPU liczył ~43 s na zapytanie, wąskie gardło demo. Zmierzone na golden 31 (agent z etykiety, izolacja od routingu):

| reranker | rozmiar | hit@3 | hit@5 | czas/zap |
|---|---|---|---|---|
| bge-reranker-v2-m3 | 568M | 0.933 | 0.967 | 43.5 s |
| mmarco-mMiniLMv2-L12-H384 | 118M | 0.900 | 0.933 | 1.64 s |

26× szybszy za koszt jednego trafienia na każdej metryce. Baseline bge zostaje jako wariant jakościowy, odrzucony na CPU ze względu na latencję. Rozbicie czasu (mmarco): embed 0.07 s / routing 0.01 s / retrieval 0.19 s / rerank 1.6 s.

**Okno kandydatów rerankera.** Szybszy reranker kupił budżet na szersze okno — przy 43 s/zap ta rozmowa nie miałaby sensu:

| `k_surowe` | hit@3 | hit@5 | czas/zap |
|---|---|---|---|
| 10 | 0.833 | 0.867 | 1.01 s |
| 20 (produkcja) | 0.900 | 0.933 | 2.39 s |

Zostaje 20: +2 trafienia z 30 za +1.38 s. Przy tym rozmiarze golden setu jedno trafienie to 0.033, więc różnica jest sugestywna, nie rozstrzygająca — spójność na hit@3 i hit@5 jej nie potwierdza niezależnie, bo miary są skorelowane.

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

**Rate limit i obsługa błędów.** Publiczny endpoint ma globalny limiter (15/min + 200/dzień, env-tunable) chroniący budżet API przed spamem. Limit jest globalny, nie per-IP: łańcuch to Caddy → frontend → api, więc `X-Forwarded-For` od Caddy'ego dociera do Streamlita, a żądanie do API wychodzi już z kontenera frontendu — dla backendu każdy klient wygląda tak samo. Per-IP wymagałby albo wtyczki `caddy-ratelimit` (własny obraz przez `xcaddy`), albo przekazania adresu z `st.context.headers` własnym nagłówkiem. Globalny limit domyka koszt; per-IP domykałby dostępność — dziś jeden nadużywający wyczerpuje dzienną pulę dla wszystkich. Błędy generacji (API padnie/timeout) łapane są w całości i zwracają komunikat „model chwilowo niedostępny" zamiast tracebacku, z logiem po stronie serwera. Frontend łapie dodatkowo zerwanie strumienia (`httpx.HTTPError`) i niepoprawny SSE (`JSONDecodeError`/`KeyError`); Streamlit startuje z `--client.showErrorDetails=none`, więc nieprzewidziany wyjątek nie pokaże ścieżek kontenera ani kodu w przeglądarce.

**Limit długości odpowiedzi.** `MAX_TOKENS` 700 → 1500. Przy 700 najdłuższa odpowiedź w pomiarze miała 691 tokenów — ucinana w pół zdania. Obcięcie było niewidoczne, bo pętla streamująca ignoruje `finish_reason`: odpowiedź urwana na limicie (`length`) wygląda w logach identycznie jak zakończona normalnie (`stop`). Bez limitu nie idziemy: koszt i czas generacji przestałyby mieć górną granicę, a rozwlekła odpowiedź oddala się od kontekstu i zbija pokrycie IDF, więc bramka odrzucałaby własną poprawną odpowiedź.

**Log trudnych pytań bez treści.** `trudne.jsonl` zapisuje wyłącznie nierozpoznane tokeny, nie treść pytania. Tokeny pochodzące z maili, telefonów, numerów zamówień i URL-i są odsiewane przez dopasowanie wzorców do oryginalnego pytania — filtrowanie po samym tokenie nic by nie dało, bo tokenizer (`[^\W\d_]+`) przepuszcza tylko litery, więc `jan.kowalski@example.com` trafia do logu jako niewinne `jan`, `kowalski`, `example`. Zmierzone na 7 przypadkach: fragmenty PII znikają, literówki (`kotno`, `smrtem`, `blikeim`) zostają.

**Błąd etykiety w korpusie — zlokalizowany przez czas odmowy.** Pytanie „Sprzedawca chce, żebym zapłacił poza Allegro — czy to bezpieczne?" odrzucane stabilnie, mimo że jest z domeny. Czas odmowy rozróżnia bramkę bez zaglądania w kod: < 1 s to filtr wejścia, ~2.9 s to próg rerankera (bez LLM), ~6.3 s to sędzia (+1 wywołanie). To pytanie padało po ~6.3 s — sędzia, nie próg. Diagnoza: właściwy artykuł miał etykietę `konto` zamiast `zakupy` (kategoria `bezpieczne-zakupy` źle zmapowana), więc nigdy nie trafiał do puli kandydatów rerankera — sędzia dostawał kontekst o Allegro Pay i słusznie odmawiał. Naprawa: jedna linia mapowania + przeniesienie 3 artykułów, przebudowa indeksów. Kontrola regresji: hit@3/hit@5 na golden bez zmian (0.900/0.933).

**Zbiory pomiarowe rozszerzone: 30→61 golden, 18→29 OOD.** Przy 30 pytaniach jedno trafienie ważyło 0.033 — każda dotychczasowa różnica mieściła się w dwóch pytaniach, a golden pokrywał 29 ze 141 artykułów. Nowe OOD to głównie near-domain: pytania o Allegro poza korpusem dla kupujących (prowizja sprzedawcy, infolinia, notowania giełdowe) — stary zestaw był zdominowany przez oczywiste przypadki (matematyka, przepisy), które ucina już sam próg rerankera, więc zawyżał odporność systemu.

**Partycjonowanie na sekcje usunięte.** Rozszerzony golden pokazał, że router (opisany wyżej w „Dopasowanie sekcji") przegrywa z prostym przeszukaniem całego korpusu na każdej mierzonej osi:

| tryb | hit@5 (n=61) | czas/zap | OOD ucięte progiem (bez LLM) |
|---|---|---|---|
| router (top-2, margines 2) | 0.852 | 4.41 s | 5/29 |
| **całość, bez partycjonowania** | **0.918** | **3.33 s** | **7/29** |

Router zwykle rerankuje 40 par (po 20 z dwóch zgadywanych sekcji), przeszukanie całości — 20 z korpusu: mniej kandydatów, ale lepiej wycelowanych. Sędzia bez zmian (27/29 w obu trybach) — brak partycjonowania nie osłabia bramki odmowy. Fallback do pełnego korpusu tylko przy odmowie (próba pośrednia, przed pełnym usunięciem) nie dał nic: przecieki OOD bez zmian (2/29 z fallbackiem i bez), bo pudła routingu nie powodują odmowy, tylko pewną siebie złą odpowiedź — żadna bramka nie reaguje, więc fallback wyzwalany przez odmowę nigdy nie dostawał szansy tam, gdzie był potrzebny. Selektor sekcji w panelu bocznym zostaje w interfejsie, ale przestaje wpływać na wynik — świadomie zostawione jako punkt do ewentualnego dociągnięcia (twardy filtr wyników zamiast rozszerzania puli kandydatów).

**Rekalibracja PROG_RERANK: −3.2 → −4.3.** Rozkłady golden i OOD się nakładają (23 z 29 OOD punktuje wyżej niż najsłabsze pytanie z domeny) — żaden próg nie rozdziela ich czysto, więc jedyna sensowna rola progu to tanie odcięcie skrajności przed wywołaniem LLM, reszta należy do sędziego.

| próg | fałsz. odmowy (golden) | OOD ucięte za darmo | wywołań sędziego (golden+OOD) |
|---|---|---|---|
| −3.2 (było) | 2/61 | 11/29 | 77 |
| **−4.3 (jest)** | **0/61** | **5/29** | **85** |

Zero fałszywych odmów, kosztem 8 dodatkowych wywołań sędziego na pełnym przebiegu — tanio, bo sędzia i tak łapał te pytania (sekcja niżej), więc próg tylko przestał robić za nie robotę za darmo.

**Rozgrzewka indeksów sekcji.** `BM25_CACHE`/`FAISS_CACHE` ładują się leniwie per sekcja — `lifespan` rozgrzewał tylko reranker i embedder, więc pierwsze zapytanie trafiające w każdą sekcję płaciło za wczytanie jej indeksu. Efekt widoczny w pomiarze kontenerowym: pierwsze trzy zapytania (różne sekcje) szły 18.1 s / 17.9 s / 15.2 s zamiast typowych 3–7 s.

**Bramka pokrycia marnowała generację na trafnych pytaniach.** Symulacja 100 pytań w 6 kategoriach (`measure_sim.py`) dała 76/100 odpowiedzi. 17 odmów padło przed generacją (0 tokenów, tanio, poprawnie), ale 7 odmów PO generacji (877 zmarnowanych tokenów łącznie) — w tym dwie na w pełni trafnych pytaniach z domeny: retrieval trafił właściwy artykuł na 1. miejscu, model odpowiedział poprawnie, a `pokrycie_idf < PROG_POKRYCIA (0.40)` odrzuciło już wygenerowaną odpowiedź. Najgorszy możliwy przebieg: koszt generacji poniesiony, użytkownik i tak dostaje „nie znalazłem". Przyczyna: model parafrazuje słowami spoza kontekstu (np. przy pytaniu o odzyskiwanie konta pisze o „weryfikacji", „tożsamości"), więc pokrycie leksykalne spada mimo merytorycznej trafności — ryzyko rośnie przy dłuższych, wieloczłonowych pytaniach, stąd 3/4 fałszywych odmów akurat w kategorii dwuczęściowej.

**Rekalibracja PROG_POKRYCIA: 0.40 → 0.20.** `measure_pokrycie.py` policzył rozkład pokrycia tam, gdzie problem realnie żyje: 29 pytań wieloczłonowych z domeny (strefa fałszywych odmów) kontra 29 OOD.

| | min | p5 | mediana | max |
|---|---|---|---|---|
| legit z domeny | 0.253 | 0.259 | 0.690 | 0.885 |
| OOD | 0.042 | 0.042 | 0.228 | 0.651 |

Rozkłady się nakładają (OOD max 0.651 > legit min 0.253) — pokrycie nie jest klasyfikatorem domeny. Nieistotne w praktyce: OOD nie dociera do tej bramki, jest cięte piętro wyżej przez reranker (−4.3) i sędziego (27/29) — pokrycie to czysty backstop antyhalucynacyjny, nie obrona przed OOD, więc kolumna „OOD złapane" niżej jest redundantna.

| próg | fałsz. odmowy (legit) | OOD złapane (redundantnie) |
|---|---|---|
| 0.40 (było) | 4/29 | 25/29 |
| 0.25 | 0/29 | 15/29 |
| **0.20 (jest)** | **0/29** | **11/29** |

Wybrany 0.20, nie 0.25, mimo że oba dają 0/29 fałszywych odmów na tej próbce: najniższy legit = 0.253, a generacja jest stochastyczna (rozrzut ~0.01–0.03 na to samo pytanie), więc 0.25 zostawiłby margines zaledwie 0.003 — jeden pech w losowaniu i pytanie znów pada. 0.20 daje margines 0.05 poniżej obserwowanego minimum, wciąż odpalając się na tekście naprawdę nieopartym w kontekście (min OOD 0.042). Efekt na symulacji 100 pytań: obie fałszywe odmowy po generacji (pokrycie 0.253 i 0.380) przechodzą przy 0.20 — bramka staje się czystym zabezpieczeniem przed halucynacją, nie źródłem strat na trafnych pytaniach.

## Wdrożenie

Demo: [ogflow.pl](https://ogflow.pl). VPS Hetzner, Ubuntu 24.04 LTS, 4 vCPU / 7.6 GB RAM / 75 GB.

| kontener | obraz | port | rola |
|---|---|---|---|
| `caddy` | caddy:2 | 80, 443 | reverse proxy, HTTPS z Let's Encrypt |
| `frontend` | python:3.13-slim | 8501 (wewn.) | Streamlit |
| `api` | python:3.13-slim | 8000 (wewn.) | FastAPI + retrieval |

API nie ma publicznego portu — frontend łączy się po sieci Dockera. Oba kontenery jako uid 1000. Cache modeli HF na named volume, ściągany raz przy pierwszym starcie. `RAG/` montowane jako volume, nie kopiowane do obrazu: indeksy są w `.gitignore`, więc `COPY RAG/` dałby obraz, który buduje się poprawnie i pada dopiero w runtime.

**Latencja w kontenerze.** 5 pytań × 3 powtórzenia, Bielik-11B przez API:

| metryka | wartość |
|---|---|
| TTFT mediana | 5.61 s |
| total mediana | 6.31 s |
| total max | 16.57 s (pierwszy przebieg) |

Konteneryzacja nic nie dołożyła — 6.31 s zgadza się z rozbiciem etapów (~1.9 s pipeline + ~4.4 s generacja). Pierwsze wywołanie każdego pytania jest 2–3× wolniejsze: `lifespan` rozgrzewa reranker, ale embedder mmlw ładuje się dopiero przy pierwszym realnym zapytaniu. TTFT ≈ total (6.24 vs 6.32 s) — odpowiedź przychodzi paczką, nie strumieniem, więc streaming w UI daje mniej niż mógłby.

**Wersja Pythona w obrazie musi zgadzać się z dev.** `requirements.txt` z `pip freeze` odbija środowisko deweloperskie (3.13); na `python:3.11-slim` build padał na `numpy==2.5.1` komunikatem „from versions: …, 2.4.6", wyglądającym na nieistniejącą wersję. W rzeczywistości numpy 2.5 wymaga ≥3.12, a pip listuje tylko wydania zgodne z bieżącym Pythonem. `torch` przypięty do 2.13.0 — bez tego dwa buildy w odstępie tygodnia dają różne środowiska.

```bash
cd docker
cp .env.example .env        # LLM_API_KEY, HF_TOKEN, DOMAIN
docker compose up -d --build
```

`RAG/` i skrypty `measure_*.py` są poza repo — na serwer trafiają przez `scp`, przed buildem.

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

