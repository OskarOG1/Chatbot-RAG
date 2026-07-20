## Chatbot-RAG

Chatbot RAG (odpowiada na podstawie bazy artykułów pomocy, nie ogólnej wiedzy modelu), 3 sekcje tematyczne wybierane przez embeddingi, każda z własnym stylem odpowiedzi.

Dane: 141 artykułów z Allegro Pomoc (konto 34, zakupy 69, płatności 38). Cały stack lokalny (Ollama, FAISS, embeddingi liczone na miejscu) pod docelowy sektor, gdzie dane nie mogą wychodzić na zewnątrz.

Projekt edukacyjny, niezwiązany z Allegro. Treść artykułów, embeddingi i indeksy są w `.gitignore` (licencja Allegro), repo zawiera tylko kod, dane odtwarza się skryptami. „Sekcje" to router i 3 konfiguracje RAG, bez tool-callingu.

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
      ▼  odmowa: wynik rerankera poniżej −4.3 albo sędzia LLM (TAK/NIE) uzna pytanie za spoza tematu
AGENT (system prompt sekcji z etykiety najlepszego fragmentu + historia rozmowy + kontekst → Bielik-11B przez API / lokalnie Ollama)
      │
      ▼  wycięcie URL-i z tekstu, mapowanie cytatów [n] → źródło
      ▼  odmowa, jeśli pokrycie odpowiedzi kontekstem jest poniżej 0.20
Odpowiedź + Źródła
```

Plan zakładał jeden główny link, ale trafny artykuł często był w top 3, nie na 1. miejscu. 3 linki: 56/60. 1 link: 47/60.

mmlw do embeddingów, trenowany pod polski język. FAISS do wektorów, lokalny i szybki. BM25 obok, bo sam embedding gubił pytania zbudowane wokół słów kluczowych. Hybryda łączy rozumienie sensu z dosłownym trafieniem.

Bielik jako model odpowiadający, trenowany pod polskie treści. Dwie wersje: minitron 7B do jakości, 1.5B do szybszych testów.

## Podział artykułów na fragmenty (chunking)

Pierwsza wersja: stała długość, 576 fragmentów po 500 tokenów z zakładką 50. Baseline. Założenie, że zachowanie nagłówków da co najwyżej minimalną różnicę, było błędne.

Druga wersja tnie po sekcjach, dokleja nagłówek do treści fragmentu (wchodzi do embeddingu, BM25 i rerankera), wycina wykryty spis treści. 29 ze 141 artykułów jest wielosekcyjnych. Wyszło 641 fragmentów zamiast 576, z czego 236 z nagłówkiem.

| Zestaw testowy | top 3, przed | top 3, po | top 5, przed | top 5, po |
|---|---|---|---|---|
| pytania bez błędów | 0.867 | **0.933** | 0.900 | **0.967** |
| pytania z literówkami, sekcja podana wprost | 0.800 | **0.867** | 0.867 | 0.867 |

## Wyniki wyszukiwania

Zestaw testowy: pytania z ręcznie przypisaną sekcją i artykułem, który powinien się pojawić w wynikach (np. „jak zmienić hasło", „towar nie dotarł", „czym jest allegro pay"). Top 3 = właściwy artykuł wśród trzech pierwszych wyników.

Droga do obecnego wyniku, pierwsze 20 pytań:

| krok | top 3 |
|---|---|
| samo wyszukiwanie po znaczeniu (FAISS) | 10/20 |
| + BM25 i łączenie rankingów (RRF) | 12/20 |
| + rozszerzone etykiety w kilku przypadkach | 13/20 |
| + poprawki błędów blokujących wcześniejsze zmiany | 16/20 |

BM25 poprawił pytania zbudowane wokół konkretnych słów: „jak zmienić hasło" łapane samym embeddingiem trafiało w artykuł o zmianie waluty (słowo „zmienić").

Lematyzacja (simplemma) nauczyła BM25 rozpoznawać odmiany słów, zamiast wymagać dokładnej formy. Zestaw 30 pytań: 28/30.

Zestaw rozszerzony do 60 pytań, dopisane potoczne sformułowania („gdzie zobaczę kiedy przyjdzie paczka"), każda etykieta zwalidowana ręcznie.

| metoda | top 1 | top 3 | top 5 |
|---|---|---|---|
| hybryda (RRF, bez rerankera) | nie mierzone | 48/60 | 56/60 |
| + cross-encoder, okno 10 kandydatów | nie mierzone | 56/60 | 57/60 |
| + cross-encoder, okno 20 kandydatów | **47/60** | **58/60** | **60/60** |

Najuczciwszy wynik to 47/60 przy jednym linku: reranker wybiera 5 z 20 kandydatów (losowo ~25%), baza ma tylko 141 artykułów. Top 5 przestał różnicować warianty, dalsze decyzje na top 3.

Przy oknie 20 pytanie „jak spłacić allegro pay" wypadło z top 3 (reranker wybrał bliski duplikat zamiast dokładnego celu, ~18 artykułów o allegro pay). 20 kandydatów to punkt, w którym wynik przestaje rosnąć; mniej wyraźnie kosztowało jakość.

## Literówki

Dawna ścieżka dochodzenia do korektora (starszy, niecommitowany zestaw pytań, sprzed obecnego rerankera): na pytaniach z błędami top 3 spadało do 0.700, najsłabszy punkt systemu.

| metoda | top 3 | top 5 |
|---|---|---|
| sam embedding | 0.700 | nie mierzone |
| + BM25 na trigramach znakowych i lematyzacji | 0.800 | 0.867 |
| + korektor literówek (Damerau-Levenshtein) | 0.867 | 0.900 |
| + wcześniejszy router na dwie sekcje (margines 2) | 0.800 | 0.833 |

Trigramy znakowe (dopasowanie po trójkach liter, tolerancyjne na literówki) podniosły też czyste pytania z 0.967 do 1.000. Korektor działa na słowniku z tytułów i treści artykułów, łapie przestawienia liter: „kotno"→„konto", „smrtem"→„smartem".

Próg częstości słowa (wordfreq) chroni poprawne wyrazy przed manglowaniem („Puść"→„push" bez tego progu). Efekt uboczny: literówki bez polskich znaków (np. „haslo") są też chronione i nie korygowane. Minimalna długość korygowanego słowa: 4 znaki.

**Aktualny pomiar, zestawy `GOLDEN` i `GOLDEN_LITEROWKI` z `measure.py`** — te same 50 pytań, jedna wersja bez błędów, druga z jedną literówką na pytanie, obecny reranker, okno 20 kandydatów. Pytania trafiają do wyszukiwania surowe, bez przejścia przez korektor (ten w produkcji działa wcześniej) — mierzę samą odporność warstwy wyszukiwania i rerankera:

| zestaw | top 3 | top 5 | czas/zapytanie |
|---|---|---|---|
| **GOLDEN, bez błędów** | **0.860** | **0.940** | 3.24 s |
| GOLDEN_LITEROWKI, z literówkami | 0.720 | 0.840 | 4.44 s |

Literówka bez korektora kosztuje 0.140 na top 3 i 0.100 na top 5, na dokładnie tych samych 50 pytaniach. BM25 na trigramach łagodzi część błędów sam z siebie, ale nie wszystkie — korektor przed wyszukiwaniem wciąż ma sens, nie jest zbędnym krokiem. Czas rośnie o ~1.2 s/zapytanie, głównie przez trudniejsze, mniej jednoznaczne dopasowania w BM25 i rerankerze.

Najmocniejszy efekt korektora był kiedyś w wyborze sekcji, nie w wyszukiwaniu: trafność na pytaniach z błędami z 0.467 do 0.833. Nieaktualne od usunięcia routingu — patrz „Zrezygnowano z dzielenia bazy na sekcje" w sekcji „Wersja produkcyjna".

## Odporność wejścia

Filtry odrzucają: puste/za krótkie/za długie zapytania, obcy alfabet (próg <0.5 liter łacińskich, zero fałszywych alarmów na polskim bez ogonków), proste wzorce prompt injection. Realną obroną jest oparcie odpowiedzi na kontekście i próg pokrycia niżej — filtr wzorców to jedna warstwa.

Obsługa niezrozumiałych pytań, dwa poziomy, sterowane korektorem, nie progiem pewności. Korektor coś poprawił → pytanie zwrotne „Szukam dla: … czy o to chodziło?", „nie" wraca do oryginału. „Nie zrozumiałem" pada tylko, gdy wszystkie słowa od 4 znaków są nieznane — wcześniejsza wersja blokowała już przy jednym nieznanym słowie („jak pozbyć się konta" odrzucane przez samo „pozbyć"). Tury z pytaniem zwrotnym nie wchodzą do historii ani wyszukiwania.

Nieznane słowa lądują w osobnym logu jako materiał na rozbudowę słownika.

## Odmowa odpowiedzi

Pierwsze podejście, próg pewności na wyniku wyszukiwania, odrzucone po pomiarach. Zostały dwa sygnały, kalibrowane osobno.

Pytanie spoza tematu: wynik rerankera przed generacją, próg 0.05. Najniższy wynik na pytaniu testowym: 0.945, najwyższy na pytaniu spoza tematu: 0.005 — wyraźny odstęp, tania odmowa (oszczędza najdroższy krok).

Halucynacje: pokrycie po generacji, próg 0.65 — ile ważonych słów odpowiedzi występuje w kontekście. Waga IDF (obniża znaczenie powszechnych słów jak „allegro", „konto") poprawiła rozróżnienie: 0.40 z wagami wobec 0.28 bez wag.

| próg | fałszywe odmowy | złapane halucynacje |
|---|---|---|
| 0.50 | 0/4 | 0/4 |
| **0.65** | **0/4** | **3/4** |

Czwarty przypadek (0.71) świadomie przepuszczony — wyższy próg zjadłby margines do najniższej poprawnej odpowiedzi (0.84).

Progi na tamtym etapie: reranker 0.05, pokrycie 0.65, częstość słowa 2.0, margines sekcji 2, kandydaci 20 (zmienione później, patrz „Wersja produkcyjna").

Ocena kontekstu przez model (TAK/NIE, czy pasuje) zaimplementowana, wtedy domyślnie wyłączona — łapie kontekst źle dobrany tematycznie, ale podwaja czas odpowiedzi na CPU.

## Cytaty i źródła

Prompt każe wstawiać odnośniki [n], zabrania gołych URL-i. Funkcja wycina linki i osieroconą bibliografię z tekstu, mapuje [n] na źródło. Powód: wszystkie 141 artykułów ma linki we własnej treści, mniejszy model (1,5B) przepisywał je jako listę i dublował „Źródła".

Cytaty służą wyłącznie do wyświetlania — do odmowy używane jest pokrycie, nie obecność [n].

## Pamięć rozmowy

Historia: okno 3 tur. Wyszukiwanie na sklejce ostatniej wypowiedzi i bieżącego pytania, więc „a jak to z telefonu?" po pytaniu o hasło trafia poprawnie. Stabilizuje też wybór sekcji, bo liczony z tej samej sklejki; poprzednia sekcja dodatkowo bierze udział w kolejnym wyborze. Bez dodatkowego wywołania modelu.

Przepisywanie pytania przez model zaimplementowane, domyślnie wyłączone — sklejenie ostatniej tury załatwia większość przypadków bez kosztu kolejnego wywołania.

## API i frontend

Backend: FastAPI. `POST /chat` zwraca JSON (odpowiedź, sekcja, źródła, cytaty). `POST /chat/stream` — ten sam proces przez SSE, kroki na bieżąco.

Frontend: Streamlit — czat, wyświetlana sekcja, klikalne źródła, podgląd kroków na żywo, panel boczny z ręcznym wyborem sekcji.

## Co sprawdziłem i odrzuciłem

Pojedynczy główny link z domieszką słów z tytułu (waga λ). Najlepszy wynik 47/60 przy λ=1,0, wyższe λ wciągały leksykalnie podobne, ale złe artykuły. 3 linki dały w tym czasie 56/60 bez parametru do strojenia.

Próg pewności na samym wyszukiwaniu, cztery sygnały — żaden nie rozdzielał trafnych pytań od nietrafnych.

Odmowa przy braku [n] w odpowiedzi. Mniejszy model (1,5B) nie cytował konsekwentnie nawet przy trafieniu 0.942 i poprawnej odpowiedzi — odmowy padały na dobrych odpowiedziach.

Wymuszona instrukcja cytowania („odpowiedź MUSI zawierać [n]"). Najgorszy regres w projekcie: model zdegenerował odpowiedzi do spamu cytatów, czyszczenie wycinało je do pustego stringa, pokrycie spadało do zera, system odmawiał na wszystko.

Pokrycie z wagami IDF jako sygnał spoza tematu (nie halucynacji). Niestabilne między uruchomieniami — „ile to 2+2" raz 0.0, raz 0.89. Zostało przy rerankerze.

Filtr spisów treści w pierwszym chunkingu: złapał 86 z 576 fragmentów jako podejrzane, po sprawdzeniu — normalna treść, nie spisy. Wróciło później jako element podziału po sekcjach.

Wielokrotne zapytania: model generował 2–3 parafrazy, wyniki sklejane przez RRF. Naprawiło jedno trudne pytanie, zepsuło łatwe (parafrazy przegłosowywały oryginał): 28/30 → 24/30 przy trzech parafrazach.

Normalizacja zapytania przed embeddingiem. „jak usunac konto" (bez ogonków) trafiało do płatności zamiast konta — pojedynczy graniczny przypadek. Próba naprawy dopisywaniem znaku zapytania: 18/20 → 15/20. Normalizacja zostaje tylko po stronie BM25.

## Dopasowanie sekcji

Testowanie wariantów wyboru sekcji, pierwsze żywe zapytanie przez API: „jak zmienić hasło" trafiło do zakupów zamiast konta.

| wariant | wynik |
|---|---|
| środek ciężkości (centroid) sekcji | 13/20 |
| najlepszy wynik, średnia z 3 fragmentów | 17/20 (po naprawie błędu w pomiarze) |
| najlepszy wynik, maksimum | 15/20 |
| głosowanie po 10 fragmentach | 16/20 |
| **głosowanie po 5 fragmentach** | **18/20 (wybrane)** |
| głosowanie hybrydowe (RRF) po 5 | 18/20 (wynik równy, odrzucone) |

Centroid przegrywał przez zbyt spójną sekcję konto — „ostry" centroid przyciągał wszystkie niejednoznaczne pytania. Wariant top-1 wzrósł z 14/20 do 17/20 po naprawie błędu w skrypcie (brak prefiksu „zapytanie: " wymaganego przez mmlw).

Maksimum premiuje pojedynczy przypadkowy fragment, średnia wymaga zgody kilku naraz. Wspólny indeks + głosowanie zamiast osobnych indeksów per sekcja (wyniki z różnych indeksów nie są porównywalne). 5 fragmentów: ten sam wynik co mniej, plus margines na pojedynczy zły fragment.

Na pytaniach z literówkami dołożony routing warunkowy na dwie sekcje przy remisie (margines):

| margines | trafność sekcji | top 5 | udział decyzji 2-sekcyjnych |
|---|---|---|---|
| 2 | 0.900 | 0.833 | 33% |
| 3 | 0.967 | 0.900 | 70% |

Margines 3 domykał stratę routingu, ale uruchamiał podwójne wyszukiwanie na 70% ruchu — za drogo na CPU. Wybrany margines 2, świadoma wymiana jakości na czas.

**Ten mechanizm został później całkowicie usunięty**, patrz „Zrezygnowano z dzielenia bazy na sekcje" niżej. Trafny na 20–30 pytaniach, ale rozszerzenie do 61 pokazało, że koszt błędów routingu przewyższa korzyść.

## Pomiary czasowe

| krok | czas |
|---|---|
| wybór sekcji | poniżej 50 ms |
| korekta + wyszukiwanie + ranking | 1–3 s |
| generacja, Bielik 1,5B | 8–10 s |
| generacja, Bielik-minitron 7B (Q4_K_M) | 53–61 s |

Długa generacja z powodu sprzętu — produkcyjnie system nie może być w pełni lokalny bez utraty responsywności.

Model mmlw ładowany raz na moduł (wcześniej trzy kopie w pamięci zamiast dwóch). Wagi IDF cache'owane na dysku, przeliczane tylko przy zmianie korpusu.

## Wersja produkcyjna

Projekt zaczął się w pełni lokalny (Ollama, Bielik 1,5B/7B na CPU). Publiczne demo wymagało szybszego rerankera i mocniejszego modelu bez własnej karty graficznej. Lokalny stack zostaje w kodzie pod „Lokalne rozwiązanie" i zmienną środowiskową — produkcja to ten sam kod z innym `.env`.

**Model przez API.** Generacja: Bielik-11B przez zewnętrzny endpoint zgodny z OpenAI (Public AI), adres/klucz/model z `.env`, domyślnie celuje w lokalną Ollamę. Wyszukiwanie zostaje lokalne na serwerze.

**Wymiana rerankera, 26 razy szybciej.** `bge-reranker-v2-m3` (568 mln) liczył ~43 s/zapytanie na CPU — główne wąskie gardło. Zestaw testowy 31 pytań, izolacja od wyboru sekcji:

| reranker | rozmiar | top 3 | top 5 | czas/zapytanie |
|---|---|---|---|---|
| bge-reranker-v2-m3 | 568 mln | 0.933 | 0.967 | 43.5 s |
| mmarco-mMiniLMv2-L12-H384 | 118 mln | 0.900 | 0.933 | 1.64 s |

26× szybciej za jedno trafienie na każdej metryce. bge zostaje w kodzie jako wariant jakościowy, odrzucony na CPU. Rozbicie czasu (mmarco): embed 0.07 s, sekcja 0.01 s, wyszukiwanie 0.19 s, ranking 1.6 s.

**Szersze okno kandydatów.** Szybszy reranker kupił budżet na więcej kandydatów:

| kandydaci | top 3 | top 5 | czas/zapytanie |
|---|---|---|---|
| 10 | 0.833 | 0.867 | 1.01 s |
| 20 (produkcja) | 0.900 | 0.933 | 2.39 s |

+2 trafienia z 30 za +1.38 s. Przy tym rozmiarze zestawu jedno trafienie waży 0.033 — sugestywne, nie rozstrzygające.

**Ponowna kalibracja progów odmowy.** Wymiana rerankera, model 1,5B→11B i przebudowa promptów unieważniły stare progi. Każdy sygnał strojony osobno na 30 pytaniach trafnych + 18 spoza tematu, rozkłady się nakładają:

- Próg rerankera przed generacją: −2.0 → −3.2. Próg −2.0 fałszywie odcinał realne pytanie o bezpieczeństwo („ktoś włamał się na moje konto", wynik −3.12); −3.2 je ratuje i tanio odcina 11/18 oczywistych pytań spoza tematu (matematyka, przepisy, kod), resztę oddaje sędziemu.
- Próg pokrycia po generacji: 0.10 → 0.40. Nowy prompt podniósł pokrycie po obu stronach (trafne min 0.239, spoza tematu max 0.516). 0.40 minimalizuje fałszywe odmowy — próg 0.52 dałby zero przecieków, ale ubiłby to samo pytanie o włamanie (pokrycie 0.477).

**Sędzia LLM na pytaniach granicznych.** To, czego reranker i pokrycie nie łapią (OLX, przeziębienie, założenie firmy), odsiewa jedno wywołanie TAK/NIE. 31 pytań trafnych + 18 spoza tematu:

| sędzia | fałszywe odmowy | złapane spoza tematu |
|---|---|---|
| Bielik-11B | 2/30 | 17/18 |
| EuroLLM-22B | 5/30 | 18/18 |

Bielik-11B wybrany jako lepszy kompromis. EuroLLM surowszy, w rezerwie pod scenariusz „nigdy nie odpowiedz nie na temat" ważniejszy niż fałszywe odmowy. Koszt: +1 wywołanie (~3 s), włączane zmienną środowiskową, na darmowym demo bywa wyłączane. Model sędziego jest niezależny od modelu odpowiadającego — osobna zmienna pozwala użyć tańszego modelu w tej roli.

Bilans łańcucha (reranker −3.2 → sędzia → pokrycie 0.40): 2/30 trafnych fałszywie odrzuconych, 1/18 spoza tematu przeciekło przez wszystkie trzy bramki (nieszkodliwe „przetłumacz dzień dobry na angielski").

Wniosek: żaden pojedynczy sygnał nie rozdziela pytań granicznych od słabych pytań z domeny, dopiero sędzia LLM to robi. Każda zmiana rerankera, modelu albo promptu wymusza rekalibrację wszystkich progów naraz.

**Limit zapytań i obsługa błędów.** Globalny limiter, domyślnie 15/min i 200/dzień (env-tunable), nie per-IP — cały ruch od frontendu wygląda dla backendu tak samo. Per-IP wymagałby wtyczki do Caddy'ego albo przekazania adresu własnym nagłówkiem. Błędy generacji (API padnie/timeout) zwracają „model chwilowo niedostępny" zamiast tracebacku, z logiem po stronie serwera.

**Limit długości odpowiedzi.** 700 → 1500 tokenów. Przy 700 najdłuższa odpowiedź w pomiarze (691 tokenów) była ucinana w pół zdania, niewidocznie w logach (pętla streamująca ignorowała przyczynę zakończenia). Bez górnego limitu koszt i czas generacji przestałyby mieć granicę, a rozwlekła odpowiedź obniża pokrycie.

**Log trudnych pytań bez treści.** Zapisywane są tylko nierozpoznane pojedyncze słowa, nie całe pytanie — maile, telefony, numery zamówień i URL-e odsiewane dopasowaniem wzorców do oryginału. Sprawdzone na 7 przypadkach: dane osobowe znikają, literówki (kotno, smrtem, blikeim) zostają.

**Błąd etykiety w bazie, zlokalizowany przez czas odmowy.** Pytanie „Sprzedawca chce, żebym zapłacił poza Allegro — czy to bezpieczne?" odrzucane stabilnie mimo że z domeny. Czas odmowy rozróżnia bramkę: <1 s filtr wejścia, ~2.9 s próg rerankera, ~6.3 s sędzia. To pytanie padało po ~6.3 s. Diagnoza: właściwy artykuł miał etykietę „konto" zamiast „zakupy", więc nigdy nie trafiał do puli kandydatów. Naprawa: poprawka mapowania + przeniesienie 3 artykułów. Kontrola regresji: top 3/top 5 bez zmian (0.900/0.933).

**Zestawy pomiarowe rozszerzone: 30→61 trafnych, 18→29 spoza tematu.** Przy 30 pytaniach jedno trafienie ważyło 0.033, zestaw pokrywał tylko 29 ze 141 artykułów. Nowe pytania spoza tematu są głównie graniczne (prowizja sprzedawcy, infolinia, notowania giełdowe) — stary zestaw zdominowany oczywistymi przypadkami zawyżał wrażenie odporności.

**Zrezygnowano z dzielenia bazy na sekcje.** Rozszerzony zestaw pokazał, że router przegrywa z przeszukaniem całej bazy na każdej osi:

| tryb | top 5 (61 pytań) | czas/zapytanie | spoza tematu odcięte samym progiem |
|---|---|---|---|
| router (dwie sekcje, margines 2) | 0.852 | 4.41 s | 5/29 |
| **cała baza, bez dzielenia** | **0.918** | **3.33 s** | **7/29** |

Router rankuje 40 par (2×20 z sekcji), cała baza — 20 kandydatów lepiej wycelowanych. Sędzia bez zmian (27/29 w obu trybach). Ręczny wybór sekcji zostaje w interfejsie, ale przestał wpływać na wynik — punkt do ewentualnego dopracowania (twardy filtr zamiast rozszerzania puli).

**Ponowna kalibracja progu rerankera: −3.2 → −4.3.** Rozkłady się nakładają (23/29 spoza tematu punktuje wyżej niż najsłabsze trafne) — jedyna rola progu to tanie odcięcie skrajności przed wywołaniem modelu:

| próg | fałszywe odmowy | spoza tematu za darmo | wywołań sędziego łącznie |
|---|---|---|---|
| −3.2 (poprzednio) | 2/61 | 11/29 | 77 |
| **−4.3 (obecnie)** | **0/61** | **5/29** | **85** |

Zero fałszywych odmów kosztem 8 dodatkowych wywołań sędziego — tanio, bo sędzia i tak łapał te pytania.

**Rozgrzewka indeksów przy starcie.** Indeksy BM25/FAISS per sekcja wczytywały się leniwie, `lifespan` rozgrzewał tylko reranker i embedder. Pierwsze zapytanie do każdej sekcji płaciło za wczytanie indeksu: 18.1 / 17.9 / 15.2 s zamiast typowych 3–7 s.

**Symulacja 100 pytań.** Cała baza, sędzia włączony, 6 kategorii. Wynik: 76/100 odpowiedzi, 24 odmowy.

| kategoria | odpowiedzi | ocena |
|---|---|---|
| zwykłe | 25/26 | dobrze |
| z literówkami | 19/21 | korektor działa |
| trzyczęściowe | 12/13 | **lepiej niż dwuczęściowe** |
| dwuczęściowe | 12/16 | 3 fałszywe odmowy |
| niejasne | 7/16 | odmowy w większości słuszne |
| spoza tematu | 1/8 | poprawnie odrzucane |

Trzyczęściowe (92%) biją dwuczęściowe (75%) — dłuższe pytanie daje rerankerowi więcej sygnału, trzy szanse na trafienie słownictwa bazy. Pytania spoza tematu trzymają się dobrze mimo braku dzielenia na sekcje: 7/8 odrzuconych, jedyny przeciek nieszkodliwy („gdzie jest siedziba allegro"). Potwierdza: bramkę niesie sędzia, nie próg.

**Bramka pokrycia marnowała wygenerowaną odpowiedź na trafnych pytaniach.** Z 24 odmów powyżej: 17 przed generacją (tanio), ale 7 po generacji (877 zmarnowanych tokenów), w tym 2 na w pełni trafnych pytaniach — retrieval trafił artykuł na 1. miejscu, model odpowiedział poprawnie, pokrycie spadło poniżej ówczesnego progu 0.40 i gotowa odpowiedź została odrzucona. Przyczyna: model parafrazuje słowami spoza kontekstu (np. „weryfikacja", „tożsamość" przy pytaniu o odzyskanie konta), więc pokrycie spada mimo trafności. Ryzyko rośnie przy dłuższych pytaniach — stąd 3/4 fałszywych odmów w kategorii dwuczęściowej.

**Ponowna kalibracja progu pokrycia: 0.40 → 0.20.** Rozkład na 29 pytaniach wieloczłonowych trafnych vs 29 spoza tematu:

| | min | p5 | mediana | max |
|---|---|---|---|---|
| trafne z domeny | 0.253 | 0.259 | 0.690 | 0.885 |
| spoza tematu | 0.042 | 0.042 | 0.228 | 0.651 |

Rozkłady się nakładają, ale bez znaczenia praktycznego — pytanie spoza tematu w ogóle nie dociera do tej bramki, jest odcięte wcześniej przez reranker i sędziego. Pokrycie to czyste zabezpieczenie przed halucynacją, nie obrona przed spoza-tematu:

| próg | fałszywe odmowy (trafne) | spoza tematu złapane (drugorzędnie) |
|---|---|---|
| 0.40 (poprzednio) | 4/29 | 25/29 |
| 0.25 | 0/29 | 15/29 |
| **0.20 (obecnie)** | **0/29** | **11/29** |

Wybrany 0.20, nie 0.25: najniższe trafne to 0.253, generacja jest lekko losowa (rozrzut 0.01–0.03), więc 0.25 zostawiłby margines 0.003. 0.20 daje margines 0.05, wciąż reagując na tekst bez oparcia w kontekście (min spoza tematu 0.042). Efekt: obie fałszywe odmowy z symulacji 100 pytań (0.253 i 0.380) teraz przechodzą.

## Wdrożenie

Demo: [ogflow.pl](https://ogflow.pl). VPS Hetzner, Ubuntu 24.04 LTS, 4 vCPU / 7.6 GB RAM / 75 GB.

| kontener | obraz | port | rola |
|---|---|---|---|
| `caddy` | caddy:2 | 80, 443 | reverse proxy, HTTPS z Let's Encrypt |
| `frontend` | python:3.13-slim | 8501 (wewn.) | Streamlit |
| `api` | python:3.13-slim | 8000 (wewn.) | FastAPI + wyszukiwanie |

API bez publicznego portu, frontend łączy się po sieci Dockera. Oba kontenery jako zwykły użytkownik. Modele HF na osobnym wolumenie, ściągane raz. `RAG/` montowane jako wolumen, nie kopiowane do obrazu (indeksy w `.gitignore`).

**Czas odpowiedzi w kontenerze.** 5 pytań × 3 powtórzenia, Bielik-11B przez API:

| metryka | wartość |
|---|---|
| mediana czasu do pierwszego fragmentu | 5.61 s |
| mediana całkowita | 6.31 s |
| maksimum | 16.57 s (pierwszy przebieg) |

Zgadza się z rozbiciem etapów (~1.9 s pipeline, ~4.4 s generacja). Pierwsze zapytanie 2–3× wolniejsze — reranker rozgrzany przy starcie, embedder mmlw dopiero przy pierwszym zapytaniu. Czas do pierwszego fragmentu ≈ czas całkowity, bo odpowiedź z API przychodzi paczką, nie strumieniem.

**Wersja Pythona w obrazie musi zgadzać się z dev.** `requirements.txt` z lokalnego środowiska (3.13); na 3.11 build padał na numpy 2.5.1 (wymaga ≥3.12, mylący komunikat błędu). torch przypięty na sztywno (2.13.0), żeby kolejne buildy nie rozjeżdżały się między sobą.

```bash
cd docker
cp .env.example .env        # LLM_API_KEY, HF_TOKEN, DOMAIN
docker compose up -d --build
```

`RAG/` i skrypty `measure_*.py` poza repo, trafiają na serwer osobno.

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
