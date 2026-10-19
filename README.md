# Chatbot RAG: odpowiedzi wyłącznie z bazy dokumentów

[![CI](https://github.com/OskarOG1/Chatbot-RAG/actions/workflows/ci.yml/badge.svg)](https://github.com/OskarOG1/Chatbot-RAG/actions/workflows/ci.yml)

Chatbot, który na pytania o Allegro odpowiada **tylko na podstawie dostarczonych artykułów**, nigdy z ogólnej wiedzy modelu. Każda taka odpowiedź ma odnośniki do źródeł. Gdy odpowiedzi nie ma w bazie, system odmawia zamiast zmyślać. Pytanie spoza domeny Allegro może dostać krótką odpowiedź ogólną bez źródeł, obwarowaną własnym zestawem bramek (trzeci szczebel na diagramie niżej).

**Demo: [ogflow.pl](https://ogflow.pl)**

Baza testowa: 668 artykułów Allegro Pomoc, dwie sekcje (kupujący, sprzedający) w dwóch językach. Projekt edukacyjny, niezwiązany z Allegro.

Cały łańcuch napisany bez frameworka RAG. Zależności produkcyjne to `sentence-transformers`, `faiss-cpu`, `rank-bm25`, `simplemma`, `wordfreq`, `httpx`, `numpy`, `fastapi`, `uvicorn`. Retrieval, fuzja rankingów, bramki odmowy, orkiestracja i strumieniowanie są własne.

> Pełny zapis pracy, czyli każda decyzja z pomiarem i każda hipoteza odrzucona liczbami, jest w osobnym pliku: **[DECYZJE.md](DECYZJE.md)**. Ten README opisuje sam system i jego liczby.

---

## Liczby

| Co mierzone | Wynik |
|---|---|
| Baza wiedzy | 668 artykułów, 3828 fragmentów: PL 354 art./2386 frag., EN 314 art./1442 frag. |
| Bramka progu rerankera, obecna konfiguracja (PL, `k_surowe` 18, próg −2.75) | GOLDEN przepuszczone **49/50** · pytania spoza tematu odcięte **16/19** |
| Zestaw realny (63 pytania, obecna konfiguracja) | właściwy artykuł: top 1 **0.429** · top 3 **0.667** · top 5 **0.762** · w kontekście modelu (top 8) **0.810** |
| Trafność wyszukiwania, top 5 (pomiar historyczny, `k_surowe` 6) | kupujący PL **0.700** · sprzedaż PL **0.950** · kupujący EN **0.760** · sprzedaż EN **1.000** |
| Retrieval po aliasach (77 pytań PL ze znanym źródłem) | do generacji **76/77** · źródło wśród linków **62/77** · źródło na 1. miejscu **49/77** · trafienie sekcji **70/77** |
| Odpowiedź bez odmowy, pełny pipeline (GOLDEN, kupujący PL, 50 pytań) | **49/50** |
| Oczekiwane źródło w odpowiedzi, pełny pipeline (GOLDEN, kupujący PL, 50 pytań) | **40/50** |
| Odpowiedź bez odmowy, pełny pipeline (50 realnych pytań z forum Allegro, bez znanego źródła) | **40/50** |
| Fałszywe odmowy na bramce pokrycia | PL 0/29 · EN 1/50 |
| Pytania nie na temat złapane, pełny łańcuch (pomiar historyczny, próg −2.0) | PL **25/26** (próg rerankera 17, sędzia 8) |
| Testy jednostkowe | ok. 650 przypadków pytest, CI na każdym pushu i PR |
| Model odpowiadający | `MODEL` i `MODEL_EN` w `.env`, domyślnie apertus 8B; prefiks dostawcy przełącza wywołanie na OpenRouter |

**Skąd te liczby.** Dwa pierwsze wiersze z pomiarami opisują obecną konfigurację retrievalu (commit `4279dcf`): 18 kandydatów na sekcję, cross-encoder w int8, próg PL −2.75. Zestaw realny to 63 pytania z etykietą źródła ustaloną po przeczytaniu artykułu. Pozostałe wiersze to pomiary historyczne z wcześniejszych konfiguracji (mniej kandydatów, okno rerankera 192, próg −2.0, inny model odpowiadający) i nie zostały powtórzone na obecnej. Wiersz „trafność wyszukiwania" zmierzono 2026-08-26 przy `k_surowe` 6 na zestawach: kupujący PL i EN po 50 pytań, sprzedaż PL 20, sprzedaż EN 19, wszystkie ze znanym źródłem (`Pomiary/dane_measure.json` oraz `RAG/golden_*.json`).

**Wiersz o aliasach to inny zestaw.** 77 pytań PL (GOLDEN 50, GOLDEN_SPRZEDAŻ 20, GOLDEN_BEZPIECZEŃSTWO 7), pomiar po dołożeniu słownictwa sytuacyjnego do tekstu retrievalowego. Wobec stanu przed aliasami: źródło na pierwszym miejscu 49 wobec 42, źródło wśród linków 62 wobec 59, trafienie sekcji 70 wobec 60. Jedenaście pytań zyskało poprawny link, zero straciło.

**Znane ograniczenie.** Trafność kupujący PL i EN (0.700 i 0.760 w pomiarze historycznym) zostaje wyraźnie pod sprzedażową, bo artykuły o koncie, logowaniu i RODO nakładają się między sekcją kupujących i sprzedających. Na zestawie kupujący PL wszystkie sześć przerzutów na sekcję sprzedaży straciło oczekiwane źródło. Zablokowanie przerzutów podnosi ten wynik do 0.780, ale zabiera trafienia użytkownikowi, który stoi na drugiej zakładce, i tam spada ono do zera (`Pomiary/WYNIK_ZLA_ZAKLADKA.json`). Jawny przełącznik strony w interfejsie zamyka tę lukę dla użytkownika, który wie, po której jest stronie.

**O bramkach.** Wiersz „pytania nie na temat" mierzy cały łańcuch na 26 pytaniach spoza bazy (`OOD_SPOZA_TEMATU` 19 plus `OOD_ALLEGRO_POZA_BAZA` 7), przy dawnej konfiguracji (próg −2.0, bez kwantyzacji rerankera). Pozostałe 3 pytania z listy `OOD_DO_AUDYTU` pominięto celowo, bo to sensowne pytania sprzedawcy, na które baza ma odpowiedź, więc ich przepuszczenie nie jest błędem. Rozkład pracy między bramkami w tamtym pomiarze: próg rerankera zatrzymuje 17, sędzia kontekstu 8, przecieka 1. Fałszywe odmowy na golden: 4/50. Pełnego łańcucha nie przemierzono jeszcze przy obecnej konfiguracji; dla samego progu jest wynik 16/19 pytań spoza tematu.

**Bramka odmowy stoi na sędzim.** W pomiarze historycznym sam próg rerankera zatrzymywał 17 z 26 pytań spoza bazy, resztę łapał sędzia, czyli wywołanie modelu. Gdy sędzia jest niedostępny, zapytanie idzie dalej i trafia do logu jako `bramki_pominiete`, a przeciek rośnie z 1/26 do 9/26. Progiem tej luki nie da się zamknąć: pytania o Allegro, na które baza nie ma odpowiedzi, dostają od rerankera mediany wyższe niż pytania golden (+2.65 wobec +2.61), bo reranker mierzy podobieństwo tematu, nie obecność odpowiedzi.

**Trafność mierzy sam retrieval, nie odpowiedź.** W pomiarze historycznym pozycje 4 i 5 nie zawierały oczekiwanego źródła ani razu na żadnym zestawie PL. Na obecnym zestawie realnym tak już nie jest: top 3 daje 0.667, top 5 0.762.

**Trzy wiersze o pełnym pipeline zmierzono na Bieliku-11B.** Wyniki 49/50, 40/50 i 40/50 pochodzą sprzed przełączenia modelu odpowiadającego i nie zostały powtórzone. Opisują ten sam łańcuch z innym modelem generującym, więc są punktem odniesienia, nie stanem bieżącym. GOLDEN ma znane źródło, więc liczy się i odmowa, i trafienie. 50 pytań realnych to ręcznie odsiane pytania o Allegro z `RAG/pytania_realne.jsonl` (5096 wpisów z forum spolecznosc.allegro.pl przed czyszczeniem, przefiltrowanych Bielikiem na serwerze GPU), bez znanego źródła, więc liczy się tylko, czy system w ogóle odpowiedział: 8 odmów sędziego kontekstu, po jednej na bramce rerankera i na „model nie wie".

---

## Jak to działa

```mermaid
flowchart TD
    Q["Pytanie użytkownika"] --> F["Filtry wejścia:<br/>za krótkie / za długie / mało liter / obcy alfabet / injection"]
    F --> K["Korektor literówek (PL)<br/>Damerau-Levenshtein + próg częstości słowa"]
    K --> E["Embedding: mmlw (PL), multilingual-e5-base (EN)"]
    E --> H["Wyszukiwanie hybrydowe po obu sekcjach naraz<br/>BM25 (lematyzacja, trigramy) + FAISS, RRF → 18 kandydatów na sekcję"]
    H --> RR["Reranker: cross-encoder int8 na parach pytanie/(tytuł + alias + fragment)<br/>okno 128 tokenów, jeden fragment na artykuł"]
    RR --> ST["Wybór sekcji: sekcja użytkownika, chyba że druga ma top1 wyższy o ponad 0.5<br/>→ do 8 fragmentów, odcięte słabsze od top1 o ponad 4"]
    ST --> G1{"Bramka 1<br/>top1 rerankera poniżej progu?"}
    G1 -- tak --> D1["Odmowa etapu 1, bez sędziego i generacji"]
    G1 -- nie --> GEN["Generacja: model odpowiadający<br/>system prompt + historia rozmowy + kontekst"]
    G1 -- nie --> G2{"Bramka 2, równolegle z generacją<br/>sędzia LLM: top 3 fragmenty i pytanie o tym samym temacie?"}
    G2 -- NIE --> D2["Przerwanie strumienia, odmowa etapu 1"]
    GEN --> C["Mapowanie cytatów [n] → źródło, czyszczenie linków"]
    C --> G3{"Bramka 3<br/>brak generacji, pokrycie IDF poniżej progu,<br/>model pisze że nie wie albo odmawia w pierwszych 160 znakach?"}
    G3 -- tak --> D3["Odmowa etapu 1"]
    G3 -- nie --> A1["Odpowiedź + zacytowane źródła"]
    D2 --> S2["Etap 2: druga sekcja z tego samego rankingu<br/>(tylko po odmowie sędziego, pokrycia albo „model nie wie”)"]
    D3 --> S2
    S2 -- trafiło --> A2["Odpowiedź + Źródła + nota o zamianie sekcji"]
    S2 -- "znów odmowa" --> G4{"Bramka 4<br/>odmowa blisko bazy, temat zablokowany<br/>albo pytanie o Allegro?"}
    D1 --> G4
    G4 -- tak --> D4["Odmowa, powód z etapu 1"]
    G4 -- nie --> OG["Etap 3, warstwa ogólna:<br/>sam model, bez kontekstu z bazy"]
    OG --> G5{"Bramka 5<br/>odpowiedź pusta, za długa albo zawiera konkret<br/>(kwota, termin, artykuł prawa, adres, telefon, URL)?"}
    G5 -- tak --> D4
    G5 -- nie --> A3["Krótka odpowiedź ogólna, bez źródeł"]
```

**Bramki odmowy na pierwszym szczeblu.** Przed wyszukiwaniem odpadają pytania krótsze niż 3 znaki, dłuższe niż 500, z udziałem liter poniżej 40 procent, z udziałem alfabetu łacińskiego poniżej 50 procent oraz próby manipulacji promptem (15 wzorców, dopasowywanych także po odwróceniu leetspeaku i homoglifów cyrylicy). W PL pytanie, w którym korektor nie rozpoznał żadnego słowa od 4 liter, kończy się prośbą o przeformułowanie. Przed generacją: jeśli top1 cross-encodera nie przekracza progu, ani sędzia, ani model odpowiadający nie są wołani. Każde pytanie, które przeszło próg, ocenia sędzia LLM (łagodny filtr tematu, TAK/NIE). Po generacji liczone jest pokrycie: suma IDF lematów odpowiedzi obecnych w kontekście podzielona przez sumę IDF wszystkich lematów odpowiedzi, gdzie IDF = ln((1+N)/(1+df)) po fragmentach korpusu, a lematy to słowa od 4 liter po simplemma. Odpowiedź bez cytatu `[n]` z frazą typu „nie mam informacji” też jest odmową.

**Trzeci szczebel odpowiada bez bazy, ale nigdy o Allegro.** Gdy obie sekcje odmówią, pytanie trafia do warstwy ogólnej (`src/ogolna.py`, wyłącznik `OGOLNA_ON`). Ta warstwa odrzuca wszystko, co wygląda na pytanie o Allegro, co dotyka tematu zablokowanego albo co odpadło blisko bazy, a wygenerowaną odpowiedź kasuje, jeśli pada w niej jakikolwiek konkret: kwota, termin, artykuł prawa, adres, telefon albo odnośnik.

**Sędzia pracuje równolegle z generacją.** Pierwsze 40 kawałków strumienia czeka w buforze na jego werdykt, więc bramka nie kosztuje czasu do pierwszego tokenu. Gdy werdykt nie przyjdzie w tym czasie, odpowiedź płynie optymistycznie, a przed każdym kolejnym kawałkiem werdykt jest sprawdzany: NIE od razu zamyka strumień. Gdy bramka odrzuci odpowiedź, która już poszła do przeglądarki, klient dostaje zdarzenie `reset` i czyści to, co pokazał. Błąd albo timeout sędziego liczy się jako TAK i trafia do logu jako `bramki_pominiete`.

**Warstwa rozmowy przed RAG.** `src/rozmowa.py` klasyfikuje powitania, podziękowania, pytania o samego bota i tury sterujące („prościej", „rozwiń", potwierdzenia) zanim cokolwiek trafi do retrievalu, więc te tury nie zużywają wyszukiwania ani bramek.

**Dane mogą nie opuszczać serwera.** Wyszukiwanie, embeddingi i reranking działają lokalnie. Model generujący też może być lokalny.

---

## Retrieval

| Parametr | Wartość |
|---|---|
| Kandydaci po RRF (stała 60) podawani rerankerowi | `K_SUROWE_SEKCJI` = 18 na sekcję |
| Reranker | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`, dynamiczna kwantyzacja int8 (`RERANKER_INT8`) |
| Okno rerankera | 128 tokenów, w parze tytuł artykułu, alias i fragment |
| Kontekst do generacji | `K_CHUNKOW_SEKCJI` = 8, jeden fragment na artykuł; odcinane fragmenty słabsze od top1 o ponad `MARGINES_KONTEKSTU` = 4, minimum 3 |
| Próg rerankera | PL −2.75 (dobrany do int8), EN −3.6 |
| Próg pokrycia | PL 0.20, EN 0.35 |
| Minimalna przewaga sekcji | `PRZEWAGA_SEKCJI_MIN` = 0.5 |
| Okno historii rozmowy | 3 ostatnie wiadomości |

Wszystkie wartości to domyślne z kodu, każdą można nadpisać zmienną środowiskową.

**Dobór `k_surowe` i progu.** Na zestawie 63 realnych pytań cały zysk z liczby kandydatów leży między 16 a 18, wyżej krzywa jest płaska (artykuł w kontekście modelu: 12 → 0.730, 18 → 0.810, 24 → 0.825 za kolejne 350 ms). Próg −2.75 przy 18 kandydatach przepuszcza 49/50 GOLDEN i odcina 16/19 pytań spoza tematu (`4279dcf`). Kwantyzacja int8 skróciła medianę retrievalu z 981 na 599 ms (przy 12 kandydatach) i przesuwa wyniki cross-encodera o około punkt w dół, więc próg i int8 są dobrane parą: wyłączenie int8 wymaga podniesienia progu (`85c5c0b`). Próg EN nie był przeliczany po włączeniu int8.

**Rozstrzyganie sekcji.** Wyszukiwanie idzie po obu sekcjach naraz, a `strony.rozstrzygnij` wybiera stronę dopiero po rerankingu, wymagając przewagi 0.5 punktu. Poniżej tej przewagi użytkownik zostaje w swojej zakładce. Kalibracja na dwóch ramionach naraz, bo blokada przerzutów podnosi jedno ramię i zeruje drugie. Etap 2 nie powtarza wyszukiwania, tylko bierze fragmenty drugiej sekcji z tego samego rankingu.

**Doszywanie sąsiadów (domyślnie wyłączone).** Za flagą `DOSZYCIE_SASIADOW_ON` czołowy fragment każdej strony dostaje do kontekstu sąsiednie fragmenty tego samego artykułu (`K_SASIEDZI_SEKCJI` = 5), żeby długi artykuł proceduralny nie docierał do modelu w jednej, przypadkowej części.

**Aliasy retrievalowe.** Chunki wybranych artykułów dostają dopisane słownictwo sytuacyjne (`src/aliasy.py`), doklejane wyłącznie do tekstu idącego do BM25, embeddingu i pary rerankera, nigdy do promptu ani do wyświetlanej treści. Artykuł o odzyskaniu dostępu do konta nie używa ani razu słów „włamał", „przejął", „nieautoryzowany", przez co pięć z siedmiu sformułowań ofiary w ogóle nie wchodziło do szóstki kandydatów (pomiar przy dawnym `k_surowe` 6). Po aliasie mediana top1 tej rodziny poszła z −1.709 na 0.591, a kolumny OOD w kalibracji progu nie drgnęły.

---

## Dobór technologii

| Element | Wybór | Dlaczego |
|---|---|---|
| Embeddingi | mmlw (PL), multilingual-e5-base (EN) | Trenowany pod polski, łapie znaczenie lepiej niż model wielojęzyczny |
| Baza wektorowa | FAISS | Lokalna, szybka, wystarcza na tej skali |
| Wyszukiwanie po słowach | BM25 + lematyzacja + trigramy | Sam embedding gubił pytania zbudowane wokół konkretnych słów |
| Reranker | mmarco-mMiniLMv2 (118M), int8 | 26x szybszy od bge-v2-m3 przy stracie jednego trafienia, po zmianie okna na 192 i doklejeniu tytułu jeszcze 3.81x szybszy i trafniejszy; potem okno 128 bez straty trafień i int8 (−39 procent mediany retrievalu) |
| Model odpowiadający | konfigurowalny przez `MODEL` | Na 11 realnych pytaniach PL apertus 8B był szybszy od Bielika-11B w 11 parach na 11, mediana 3.45 s wobec 6.54 s, najgorszy przypadek 6.3 s wobec 22.7 s |
| Sędzia kontekstu | Bielik-11B (PL), Olmo-3-7B (EN) | Odpięty od modelu odpowiadającego, decyzja TAK/NIE jest lżejsza niż generacja |

**Sędzia i mail mają własne zmienne.** `SEDZIA_MODEL` oraz `EMAIL_MODEL` są niezależne od `MODEL`. Sędzia celowo, bo decyzja TAK/NIE jest innym zadaniem niż generacja. Szkic maila (`agents_mail.py`) czyta `EMAIL_MODEL` na sztywno: to nie jest decyzja poparta pomiarem, tylko stan zastany.

**Router dostawców.** Model z prefiksem `openai/`, `anthropic/`, `google/`, `x-ai/`, `deepseek/`, `meta-llama/`, `mistralai/`, `qwen/` lub `cohere/` idzie przez OpenRouter, reszta przez `LLM_BASE_URL`. `src/koszty.py` trzyma cennik wejścia i wyjścia na milion tokenów i sumuje koszt na turę, także dla wywołań sędziego i szkicu maila.

Uzasadnienia z liczbami, razem z wariantami odrzuconymi, są w [DECYZJE.md](DECYZJE.md).

---

## Pomiary wydajności

| Zmiana | Przed | Po |
|---|---|---|
| Reranker: tytuł w parze, okno 192, k=12 | punkt odniesienia | **3.81x** szybciej, wyższa trafność |
| Reranker: mmarco-mMiniLMv2 zamiast bge-v2-m3 | punkt odniesienia | **26x** szybciej, jedno trafienie mniej |
| Przeliczenie embeddingów po dociągnięciu artykułu | 220 minut na 2121 chunkach | **162 sekundy** (2095 wierszy przepisanych, 26 policzonych, kosinus 1.000 z pełnym przeliczeniem) |
| Przycinanie kontekstu sędziego | 72.7 ms zysku | odrzucone: łamie bramkę przy każdym limicie, domyślnie wyłączone |
| Kwantyzacja int8 cross-encodera (12 kandydatów, okno 128) | mediana retrievalu 981 ms | **599 ms**, dwa pytania mniej na 197 |

**Składanie macierzy zamiast pełnego przeliczania.** Chunk, którego tekst retrievalowy jest identyczny jak w starym korpusie, dostaje swój stary wiersz. Liczone są tylko teksty nowe oraz wszystkie chunki z aliasem, bo o tych drugich nie da się orzec, czy stary wektor powstał już z aliasem. Bezpiecznik: powyżej 40 nowych tekstów skrypt przerywa, bo zmieniło się wtedy więcej niż jeden dociągnięty artykuł.

**Trzy artefakty trzeba odświeżać razem.** `chunks_*.json`, `*.bm25` i `*.faiss` mają osobne cache w pamięci procesu, unieważniane po znaczniku czasu własnego pliku. Podmiana samych chunków bez przebudowy indeksu nie wywoła błędu, tylko cicho rozjedzie numerację: FAISS zwróci pozycje ze starego indeksu, a odczytane zostaną nowe fragmenty. Osobny test (`tests/test_wektory_pozycyjnie.py`) pilnuje zgodności pozycyjnej wektorów z chunkami.

---

## Bezpieczeństwo i odporność

**Manipulacja promptem.** Filtry wejścia odrzucają znane wzorce, także po odwróceniu leetspeaku, ale realną obroną jest oparcie odpowiedzi na kontekście i bramka pokrycia. Filtr wzorców to jedna warstwa, nie całość.

**Logi bez danych osobowych.** `trudne.jsonl` dostaje wyłącznie nierozpoznane pojedyncze słowa, nigdy całe pytanie. Log analityczny zapisuje treść pytania dopiero po redakcji: maile, telefony, numery zamówień i adresy URL idą do `[ukryte]`.

**Limity.** Globalny (domyślnie 15/min, 200/dzień) chroni budżet API, per IP (10/min, 40/dzień) chroni przed pojedynczym nadużywającym klientem. Osobne, luźniejsze progi mają oceny i panel. Wysyłka maila ma własny, najostrzejszy limit, bo to jedyne prawdziwe wywołanie zewnętrzne.

**Awarie nie blokują odpowiedzi, ale zostawiają ślad.** Gdy sędzia albo dane IDF są niedostępne, bramka jest pomijana, a zapytanie odnotowane w logu jako `bramki_pominiete`. Gdy w oknie 50 zapytań ponad 20 procent ma pominiętą bramkę, serwer krzyczy na stderr. Model główny ma automatyczny fallback na zapasowy.

**Panel bez tokenu jest zamknięty, ale zbieranie działa.** Bez `ADMIN_TOKEN` kolejka zgłoszeń i reset statystyk odpowiadają kodem 503, a same zgłoszenia od użytkowników zapisują się dalej. Reset jest jedyną operacją nieodwracalną, wymaga nagłówka `x-admin-token` i archiwizuje log zamiast go kasować.

---

## API i frontend

Backend: **FastAPI**. `POST /chat` zwraca JSON (odpowiedź, źródła, cytaty), `POST /chat/stream` ten sam proces przez SSE. Poza tym `POST /send-email`, `POST /ocena`, `POST /zgloszenie` oraz `GET /health`. Pod panel: `GET /admin/statystyki`, `/admin/oceny`, `/admin/kolejka`, `/admin/kolejka/eksport`, `/admin/eksport` i `POST /admin/kolejka/odpowiedz`, `/admin/resetuj-statystyki`.

Strumień SSE ma pięć typów zdarzeń: `krok` (co system właśnie robi), `token` (fragment odpowiedzi), `reset` (bramka odrzuciła to, co już poszło do przeglądarki), `wynik` (koniec tury z cytatami) i `blad`. Obsługa `reset` jest w kliencie obowiązkowa.

Każda tura zapisuje do logu analitycznego cechy decyzji: `rerank_top1`, liczbę chunków, `zrodlo_top1`, werdykt sędziego, wartość pokrycia, numer etapu drabiny, wybraną stronę, powód odmowy z listy `prog_rerank`, `sedzia`, `pokrycie`, `model_nie_wie`, `jawna_odmowa`, `brak_generacji`, oraz latencję i koszt tokenów. Panel liczy z tego rozkłady, kwantyle latencji i szeregi dzienne.

Frontend: **Next.js 16 / React 19** (`frontend-next/`, ok. 5.6 tys. linii TSX). Czat ze streamingiem, klikalne cytaty, panel edycji maila z porzuceniem szkicu, 15-sekundowym oknem na cofnięcie wysyłki i korektą po wysłaniu, oraz panel analityczny pod `/admin` z wykresami Recharts. Przeglądarka nie rozmawia z FastAPI bezpośrednio, wszystko idzie przez Route Handlery, więc jeden origin i zero CORS.

**Cytaty.** Prompt każe wstawiać odnośniki `[n]` i zabrania gołych adresów URL. Kod wycina linki i dopisane przez model listy źródeł, mapuje `[n]` na źródło, a użytkownik widzi wyłącznie źródła faktycznie zacytowane. Główną bramką po generacji jest pokrycie; brak `[n]` liczy się tylko w bramce „model nie wie”.

**Podpowiedzi kontekstowe.** Po odpowiedzi generowane są trzy propozycje kolejnych pytań, budowane ze śródtytułów artykułów z kontekstu (do 3 adresów), bez wywołania modelu.

**Pamięć rozmowy.** Okno 3 ostatnich wiadomości. Dopytania wykryte tanim detektorem są przepisywane przez model na samodzielne pytanie przed wyszukiwaniem, więc „a co jeśli sprzedawca nie odpowiada?" po pytaniu o reklamację trafia poprawnie.

---

## Wersja dwujęzyczna i wysyłka maila

Druga, równoległa ścieżka dla klienta anglojęzycznego: własny embedder (`multilingual-e5-base`), własny indeks, własny sędzia i własne progi odmowy (`prog_rerank` −3.6, `prog_pokrycia` 0.35 wobec −2.75 i 0.20 dla polskiego). Język z żądania ma pierwszeństwo (frontend zawsze go wysyła); detekcja po częstości słów działa, gdy klient API języka nie poda.

Panel edycji maila ma prawdziwy przycisk wysyłki. Treść idzie do stałej demo-skrzynki sprzedawcy, a potwierdzenie z numerem zgłoszenia na adres klienta, przez REST Resend, bez SMTP. Bez skonfigurowanego `RESEND_API_KEY` wysyłka zwraca czytelny błąd konfiguracji, nigdy fałszywy sukces. Log serwera zapisuje tylko numer zgłoszenia, kategorię, powód odmowy dostawcy i wynik, nigdy adresu ani treści.

---

## Pętla uczenia z produkcji

Odmowa z powodem z listy `prog_rerank`, `sedzia`, `pokrycie`, `model_nie_wie`, `jawna_odmowa` albo `brak_generacji` może trafić do kolejki zgłoszeń (`RAG/kolejka.jsonl`, identyfikator 12 znaków hex, retencja adresu 30 dni). Panel pozwala oznaczyć zgłoszenie etykietą `luka_w_bazie`, `prog_za_wysoki`, `poza_zakresem` albo `spam`. Dla luki w bazie `src/petla.py` składa listę do przeglądu z propozycją źródła i wynikiem rerankera, `src/dociagnij.py` pobiera brakujący artykuł do korpusu, a `src/zastosuj_przeglad.py` stosuje decyzje człowieka.

Brama adresów w `dociagnij.py`: 184 z 184 prawdziwych adresów pomocy kupującego przechodzą, 7 z 7 adresów o złej głębokości ścieżki, złym hoście lub schemacie `http` jest odrzucanych przed pobraniem.

Pierwsze domknięcie pętli na żywym zgłoszeniu: dociągnięcie brakującego artykułu plus alias podniosło wynik rerankera dla pytania z −3.568 na +2.548.

---

## Struktura repozytorium

```
src/            backend: pipeline, bramki, retrieval, agenci, API, pętla uczenia
frontend-next/  frontend Next.js, czat i panel analityczny
tests/          ok. 650 przypadków pytest, bez wywołań modelu
docker/         compose, Dockerfile API, Caddy, skrypty kopii zapasowych
RAG/            korpus (artykuły .md i chunks_*.json); indeksy i logi poza gitem
Pomiary/        część skryptów pomiarowych; surowe przebiegi i raporty poza gitem
```

Repozytorium zawiera korpus: artykuły w `RAG/docs*` i pocięte fragmenty w `RAG/chunks_*.json`. Zbudowane indeksy (`*.faiss`, `*.bm25`, `*.npy`) i logi są poza gitem. Skrypty ETL (scraping, chunking, scalanie korpusu, embedder, budowa indeksów) są w `src/`.

Szczegóły: [DECYZJE.md](DECYZJE.md).
