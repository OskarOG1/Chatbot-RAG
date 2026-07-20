## Chatbot-RAG

Chatbot RAG (odpowiada na pytania, opierając się na bazie artykułów pomocy, zamiast na ogólnej wiedzy modelu) z 3 oddzielnymi sekcjami tematycznymi, do których zapytania są klasyfikowane przez embeddingi, każda z własnym stylem odpowiedzi.

Dane: 141 artykułów z Allegro Pomoc (konto 34, zakupy 69, płatności 38). Cały stack jest lokalny (Ollama, FAISS, embeddingi liczone na miejscu), bo docelowy kierunek to sektor, w którym dane nie mogą wychodzić na zewnątrz.

Projekt edukacyjny, niezwiązany z Allegro. Treść artykułów, fragmenty, embeddingi i indeksy są w `.gitignore` i nie ma ich w repozytorium, bo są objęte licencją Allegro. Repo zawiera wyłącznie kod, dane odtwarza się skryptami. „Sekcje" to router i 3 konfiguracje RAG, bez tool-callingu (model nie wywołuje żadnych zewnętrznych narzędzi, tylko odpowiada na podstawie dostarczonego kontekstu).

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
      ▼  odmowa: wynik rerankera poniżej −4.3 albo sędzia LLM (odpowiada TAK/NIE) uzna pytanie za spoza tematu — zanim model zacznie odpowiadać
AGENT (system prompt sekcji z etykiety najlepszego fragmentu + historia rozmowy + kontekst → Bielik-11B przez API / lokalnie Ollama)
      │
      ▼  wycięcie URL-i z tekstu, mapowanie cytatów [n] → źródło
      ▼  odmowa, jeśli pokrycie odpowiedzi kontekstem jest poniżej 0.20 (ostatnia linia obrony)
Odpowiedź + Źródła
```

Pierwotnym planem było zwracanie jednego, głównego linka, jednak trafny artykuł znajdował się często wśród trzech pierwszych wyników, a nie na samej górze. Stąd zmiana na pokazywanie w odpowiedzi 3 linków: trafność 56 na 60 pytań testowych, wobec 47 na 60 dla pojedynczego linka.

mmlw jako model do liczenia embeddingów (czyli zamiany tekstu na wektor liczb, po którym da się porównywać znaczenie zdań), bo jest trenowany pod polski język i łapie znaczenie lepiej niż model wielojęzyczny. FAISS do przechowywania i przeszukiwania tych wektorów, bo jest lokalny, szybki i wystarcza na tej skali danych. BM25 (klasyczne wyszukiwanie po dopasowaniu słów, bez rozumienia znaczenia) dołożony obok, bo sam embedding gubił pytania zbudowane wokół konkretnych słów kluczowych. Połączenie obu podejść (hybryda) łączy rozumienie sensu z dosłownym trafieniem w słowa.

Bielik jako model odpowiadający, bo to model trenowany pod polski język i polskie treści. Dwie wersje do różnych zadań: minitron 7B do jakości odpowiedzi, 1.5B do szybszych testów.

## Podział artykułów na fragmenty (chunking)

Pierwsza wersja dzieliła artykuły na fragmenty o stałej długości: 576 kawałków po 500 tokenów z zakładką 50 tokenów, żeby sąsiednie fragmenty się trochę pokrywały. To najprostsza możliwa metoda, wzięta świadomie jako punkt odniesienia. Zakładałem, że zachowanie nagłówków wpłynie na jakość co najwyżej minimalnie. Myliłem się.

Druga wersja tnie artykuły po sekcjach zamiast po sztywnej długości, dokleja nagłówek sekcji do treści każdego fragmentu (więc nagłówek wchodzi też do embeddingu, do BM25 i do rerankera) i wycina wykryty spis treści. Artykułów podzielonych na wiele sekcji jest 29 ze 141. Wyszło 641 fragmentów zamiast 576, z czego 236 ma doklejony nagłówek.

| Zestaw testowy | trafność w top 3, przed | trafność w top 3, po | trafność w top 5, przed | trafność w top 5, po |
|---|---|---|---|---|
| pytania bez błędów | 0.867 | **0.933** | 0.900 | **0.967** |
| pytania z literówkami, sekcja podana wprost | 0.800 | **0.867** | 0.867 | 0.867 |

## Wyniki wyszukiwania

Zestaw testowy: pytania z ręcznie przypisaną sekcją i adresem artykułu, który powinien się pojawić w wynikach. Przykłady: „jak zmienić hasło", „zapomniałem loginu", „towar nie dotarł", „paczka przyszła uszkodzona", „czym jest allegro pay", „jak rozłożyć zakup na raty", „czy sprzedawca jest wiarygodny", „jak oddać rzecz kupioną ze smartem". Trafność w top 3 oznacza, że właściwy artykuł jest wśród trzech pierwszych wyników wyszukiwania.

Droga dojścia do obecnego wyniku na pierwszych 20 pytaniach testowych:

| krok | trafność w top 3 |
|---|---|
| samo wyszukiwanie po znaczeniu (FAISS) | 10/20 |
| + BM25 i łączenie rankingów (RRF) | 12/20 |
| + rozszerzone etykiety w kilku przypadkach | 13/20 |
| + poprawki błędów blokujących wcześniejsze zmiany | 16/20 |

BM25 poprawił odpowiedzi na pytania zbudowane wokół konkretnych słów, jak „jak zmienić hasło", gdzie sam embedding łapał głównie słowo „zmienić" i podsuwał artykuł o zmianie waluty zamiast o haśle.

Po dodaniu lematyzacji (sprowadzania słów do formy podstawowej, biblioteka simplemma) BM25 zaczął rozpoznawać odmiany tych samych słów. Zniknęły pomyłki typu „zapomniałem loginu", gdzie problemem była inna forma gramatyczna słowa, nie inne słowo. Na rozszerzonym zestawie 30 pytań wynik wyniósł 28/30.

Zestaw rozszerzony do 60 pytań. Dopisałem pytania sformułowane potocznie, dopasowane do realnych artykułów („gdzie zobaczę kiedy przyjdzie paczka", „mam kod rabatowy jak go użyć"), każda etykieta sprawdzona ręcznie, że artykuł faktycznie jest w indeksie.

| metoda | trafność na 1. miejscu | trafność w top 3 | trafność w top 5 |
|---|---|---|---|
| hybryda (RRF, bez rerankera) | nie mierzone | 48/60 | 56/60 |
| + cross-encoder, okno 10 kandydatów | nie mierzone | 56/60 | 57/60 |
| + cross-encoder, okno 20 kandydatów | **47/60** | **58/60** | **60/60** |

Najbardziej uczciwym wynikiem pozostaje 47 na 60 przy jednym linku. Reranker wybiera pięć fragmentów z dwudziestu kandydatów, więc losowy wybór dałby około 25%, a baza ma tylko 141 artykułów, więc trafienie nie jest wcale takie proste. Trafność w top 5 przestała różnicować warianty (wszędzie blisko maksimum), więc dalsze decyzje podejmowałem patrząc na top 3.

Przy oknie 20 kandydatów pytanie „jak spłacić allegro pay" wypadło z top 3. Wokół allegro pay jest około 18 artykułów, więc reranker wybrał artykuł bardzo podobny, ale nie ten dokładnie właściwy. Przegląd różnych wartości potwierdził, że 20 kandydatów to punkt, w którym wynik przestaje rosnąć, a mniej kandydatów wyraźnie kosztowało jakość.

## Literówki

Zestaw testowy jest pisany poprawną polszczyzną, realne zapytania użytkowników nie zawsze. Na pytaniach z błędami trafność w top 3 spadła do 0.700. To był najsłabszy punkt całego systemu.

| metoda | trafność w top 3 | trafność w top 5 |
|---|---|---|
| sam embedding | 0.700 | nie mierzone |
| + BM25 na trigramach znakowych i lematyzacji | 0.800 | 0.867 |
| + korektor literówek (Damerau-Levenshtein, bez zewnętrznych zależności) | 0.867 | 0.900 |
| + wcześniejszy router na dwie sekcje (margines 2, mierzone od początku do końca) | 0.800 | 0.833 |

Trigramy znakowe (porównywanie tekstu po trójkach liter zamiast po całych słowach, co toleruje literówki) podniosły też wynik na czystych pytaniach z 0.967 do 1.000. Korektor działa na słowniku zbudowanym z tytułów i treści artykułów i łapie też przestawienia liter, które trigramom umykają. Naprawia na przykład „kotno" na „konto" i „smrtem" na „smartem", zanim tekst trafi do embeddingu i do BM25.

Nad korektorem stoi dodatkowo próg częstości słowa (biblioteka wordfreq): poprawny polski wyraz, który występuje wystarczająco często w języku, nie jest ruszany. Bez tego korektor psuł poprawne wejścia, na przykład zamieniał „Puść" na „push". Świadomy efekt uboczny: literówki bez polskich znaków diakrytycznych (na przykład „haslo" zamiast „hasło") są chronione tym samym progiem, więc nie są korygowane. Minimalna długość korygowanego słowa to 4 znaki, więc krótkie literówki typu „jka" zamiast „jak" przechodzą bez zmian.

Najmocniejszy efekt korektora był widoczny nie w samym wyszukiwaniu, tylko w wyborze sekcji: trafność wyboru sekcji na pytaniach z błędami podskoczyła z 0.467 do 0.833. Literówka rozbija embedding całego pytania, a wybór sekcji opierał się właśnie wyłącznie na embeddingu.

## Odporność wejścia

Filtry odrzucają zapytania puste, za krótkie, za długie, napisane innym alfabetem niż łaciński (na przykład cyrylicą, próg to mniej niż połowa liter łacińskich w tekście, bez fałszywych alarmów na polskim tekście pisanym bez ogonków) oraz proste próby wstrzyknięcia instrukcji do modelu (prompt injection). Realną obroną przed nadużyciami jest oparcie odpowiedzi wyłącznie na dostarczonym kontekście i próg pokrycia opisany niżej, filtr wzorców to tylko dodatkowa warstwa.

Obsługa niezrozumiałych pytań ma dwa poziomy i jest sterowana korektorem, nie jakimś progiem pewności. Gdy korektor coś poprawił, nad odpowiedzią pojawia się pytanie zwrotne: „Szukam dla: … czy o to chodziło?". Odpowiedź „nie" wysyła oryginalne, niepoprawione pytanie z osobną flagą. Komunikat „nie zrozumiałem" pojawia się wyłącznie przy w pełni niezrozumiałych zdaniach, czyli gdy wszystkie słowa dłuższe niż 4 znaki są nieznane. Wcześniejsza wersja blokowała pytanie już przy jednym nieznanym słowie, więc na przykład zapytanie „jak pozbyć się konta" było odrzucane tylko dlatego, że słowo „pozbyć" nie znalazło się w słowniku, mimo że całe pytanie było w pełni zrozumiałe. Te dodatkowe tury z pytaniem zwrotnym nie wchodzą do historii rozmowy ani do wyszukiwania, żeby nie zaśmiecać kontekstu.

Zapytania z nieznanymi słowami trafiają do osobnego logu jako materiał do rozbudowy słownika i zestawu testowego.

## Odmowa odpowiedzi

Pierwsze podejście, czyli próg pewności liczony na samym wyniku wyszukiwania, zostało odrzucone po pomiarach.

Zostały dwa sygnały, każdy kalibrowany osobno.

Pytanie spoza tematu Allegro jest łapane po wyniku rerankera, jeszcze zanim model zacznie odpowiadać, przy progu 0.05. Najniższy wynik na pytaniu z zestawu testowego to 0.945, a najwyższy na pytaniu spoza tematu to 0.005, więc odstęp jest wyraźny. Odmowa na tym etapie jest tania, bo oszczędza najdroższy krok całego procesu, czyli samo generowanie odpowiedzi.

Halucynacje (czyli sytuacje, w których model dopisuje coś, czego w kontekście nie ma) łapie pokrycie liczone po wygenerowaniu odpowiedzi, przy progu 0.65: to miara tego, ile ważonych słów odpowiedzi występuje też w dostarczonym kontekście. Waga IDF (wzór, który obniża znaczenie słów powszechnych w tej dziedzinie, takich jak „allegro", „konto" czy „zamówienie", a podnosi znaczenie słów rzadkich i konkretnych) poprawiła rozróżnienie halucynacji względem prostego liczenia pokrycia bez wag: 0.40 z wagami wobec 0.28 bez wag.

| próg | fałszywe odmowy | złapane halucynacje |
|---|---|---|
| 0.50 | 0/4 | 0/4 |
| **0.65** | **0/4** | **3/4** |

Czwarty przypadek (wynik 0.71) świadomie przepuszczony bez odmowy, bo podniesienie progu zjadłoby margines do najniższej poprawnej odpowiedzi w zestawie (0.84).

Progi na tamtym etapie projektu: reranker 0.05, pokrycie 0.65, częstość słowa 2.0, margines wyboru sekcji 2, liczba kandydatów 20 (wartości zmieniły się później, patrz sekcja „Wersja produkcyjna").

Ocena kontekstu przez model (jedno dodatkowe wywołanie z pytaniem TAK/NIE, czy kontekst w ogóle odpowiada na pytanie) jest zaimplementowana, ale w tamtym momencie była domyślnie wyłączona. Łapie sytuacje, w których kontekst jest tematycznie dobrany źle, czego żadna sama liczba nie wykryje, ale podwaja czas odpowiedzi na sprzęcie bez karty graficznej.

## Cytaty i źródła

Prompt każe modelowi wstawiać w tekście odnośniki w nawiasach kwadratowych, na przykład [n], i zabrania podawania gołych adresów URL. Osobna funkcja wycina z gotowego tekstu wszystkie linki i osierocone wpisy w bibliografii, a odnośniki [n] mapuje na rzeczywiste źródło. Powód leży w danych: wszystkie 141 artykułów ma linki we własnej treści, więc mniejszy model (1,5B) przepisywał je jako gotową listę i dublował sekcję „Źródła". Obce adresy URL odsiewa ten sam mechanizm, który buduje listę linków w danych.

Cytaty służą wyłącznie do wyświetlania użytkownikowi. Do samej decyzji o odmowie odpowiedzi używane jest pokrycie opisane wyżej, nie obecność odnośników w tekście.

## Pamięć rozmowy

Historia to okno ostatnich 3 tur rozmowy. Wyszukiwanie odbywa się na sklejce ostatniej wypowiedzi użytkownika i bieżącego pytania, więc dopytanie w stylu „a jak to zrobić z telefonu?" po pytaniu o hasło trafia tam, gdzie powinno. Przy okazji stabilizuje to też wybór sekcji, bo sekcja liczona jest z tego samego, sklejonego zapytania. Poprzednia sekcja dodatkowo bierze udział w wyborze kolejnej, dzięki czemu styl odpowiedzi nie zmienia się nagle w połowie rozmowy. Wszystko dzieje się bez dodatkowego wywołania modelu.

Przepisywanie pytania przez model (żeby doprecyzować dopytania w oderwaniu od historii) jest zaimplementowane, ale domyślnie wyłączone, bo dokłada kolejne wywołanie modelu, a sklejenie ostatniej tury załatwia większość przypadków bez tego kosztu.

## API i frontend

Backend to FastAPI. `POST /chat` zwraca odpowiedź w formacie JSON razem z sekcją, listą źródeł i cytatami. `POST /chat/stream` to ten sam proces, ale przesyłany strumieniowo (SSE): kolejne kroki (korekta, wybór sekcji, wyszukiwanie, ranking, generowanie odpowiedzi) trafiają do klienta na bieżąco, a na końcu przychodzi wynik końcowy.

Frontend to Streamlit: okno czatu, wyświetlana sekcja, klikalne źródła, podgląd kolejnych kroków na żywo, panel boczny z ręcznym wyborem sekcji.

## Co sprawdziłem i odrzuciłem

Pojedynczy główny link, czyli wybór jednego źródła przez reranker z dodatkową domieszką słów z tytułu artykułu (ważoną parametrem λ). Najlepszy wynik, 47 na 60, wypadł przy λ=1,0, a kolejne wartości λ pogarszały go, bo domieszka wciągała artykuły podobne pod względem słów, ale merytorycznie złe (na przykład pytanie „mam kod rabatowy jak go użyć" przeszło z trafienia w pomyłkę). Trzy linki dawały w tym samym czasie 56 na 60 bez żadnego dodatkowego parametru do strojenia. Wcześniejsze warianty (suma wyników, zliczanie, rabat po adresie URL) dały wynik identyczny co punkt odniesienia, bo po usunięciu duplikatów każdy adres URL ma dokładnie jeden fragment, więc nie było czego łączyć.

Próg pewności liczony na samym wyszukiwaniu, sprawdzony na czterech różnych sygnałach. Żaden nie rozdzielał dobrze pytań trafnych od nietrafnych.

Odmowa przy braku odnośnika [n] w odpowiedzi. Mniejszy model (1,5B) opierał odpowiedź na kontekście, ale nie cytował konsekwentnie: nawet przy bardzo dobrym trafieniu wyszukiwania i poprawnej merytorycznie odpowiedzi lista cytatów bywała pusta. Odmowy padały więc na dobrych odpowiedziach.

Wymuszona instrukcja cytowania w promptcie („odpowiedź MUSI zawierać [n]") razem z przykładem. Najgorszy regres w całym projekcie: mniejszy model zaczął degenerować odpowiedzi do samego spamu cytatów, oczyszczanie tekstu wycinało je do pustego ciągu znaków, pokrycie spadało do zera i system zaczynał odmawiać na wszystko. Wróciło do łagodniejszej wersji instrukcji.

Pokrycie liczone z wagami IDF jako sygnał pytania spoza tematu (a nie jako sygnał halucynacji, do czego finalnie służy). Wypadło tak samo jak pokrycie bez wag i było niestabilne między uruchomieniami, na przykład pytanie „ile to 2+2" raz dawało wynik 0.0, raz 0.89. Zostało przy rerankerze jako sygnale pytań spoza tematu.

Filtr spisów treści w pierwszej wersji chunkingu: diagnostyka złapała 86 z 576 fragmentów jako podejrzane, ale po sprawdzeniu ręcznym okazało się, że to normalna treść (instrukcje, listy), nie spisy treści. Wycinanie spisów treści wróciło później jako element podziału artykułów po sekcjach, sterowany strukturą dokumentu zamiast progiem na długość linii.

Wielokrotne zapytania: mniejszy model Bielik 1,5B generował 2 do 3 parafraz pytania, każda parafraza szła do wyszukiwania osobno, a wyniki były sklejane. Naprawiło to jedno trudne pytanie, ale zepsuło kilka łatwych, bo przy łączeniu parafrazy przegłosowywały oryginalne pytanie: wynik spadł z 28 na 30 do 24 na 30 przy trzech parafrazach, przy dwóch było jeszcze gorzej, a wariant włączany warunkowo dał 22 na 30. Możliwe, że problem leżał w jakości parafraz generowanych przez mały model, nie w samym pomyśle, ale korektor literówek i trigramy załatwiły w międzyczasie większość tych samych przypadków innym sposobem.

Normalizacja zapytania przed embeddingiem (na przykład usuwanie polskich znaków diakrytycznych). Pytanie „jak usunac konto" (bez ogonków i bez znaku zapytania) trafiało do sekcji płatności, choć wszystkie inne warianty tego pytania szły poprawnie do sekcji konto. Był to jednak pojedynczy, graniczny przypadek, nie błąd systematyczny. Próba naprawy przez automatyczne dopisywanie znaku zapytania obniżyła wynik z 18 na 20 do 15 na 20. Normalizacja ogonków zostaje więc tylko po stronie BM25, bo model mmlw wymaga polskich znaków, żeby działać poprawnie.

## Dopasowanie sekcji

Testowanie różnych wariantów wyboru sekcji wymusiło pierwsze żywe zapytanie przez API: pytanie „jak zmienić hasło" trafiło wtedy do sekcji zakupy i wróciło ze źródłami o kupowaniu zamiast o koncie.

| wariant | wynik |
|---|---|
| środek ciężkości (centroid) sekcji | 13/20 |
| najlepszy wynik, średnia z 3 fragmentów | 17/20 (po naprawie błędu w pomiarze) |
| najlepszy wynik, maksimum | 15/20 |
| głosowanie po 10 fragmentach | 16/20 |
| **głosowanie po 5 fragmentach** | **18/20 (wybrane)** |
| głosowanie hybrydowe (RRF) po 5 fragmentach | 18/20 (wynik równy, odrzucone) |

Metoda środka ciężkości przegrywała przez zbyt spójną tematycznie sekcję konto: wąska tematyka (logowanie, hasło, dane) daje bardzo „ostry" środek ciężkości, który przyciąga wszystkie niejednoznaczne pytania, więc wszystkie jego pomyłki wpadały akurat do sekcji konto. Wynik wariantu z najlepszym pojedynczym trafieniem wzrósł z 14 na 20 do 17 na 20 po naprawie błędu w samym skrypcie pomiarowym: embedding zapytania liczony był bez wymaganego przez model mmlw prefiksu „zapytanie: ". W samym chatbocie ten prefiks był obecny od początku, więc to była poprawka pomiaru, nie samego mechanizmu wyboru sekcji.

Branie maksimum zamiast średniej premiuje pojedynczy przypadkowy fragment: przy płaskich wynikach jeden dobrze dopasowany kawałek z niewłaściwej sekcji potrafi przeważyć całą decyzję. Średnia wymaga zgody kilku fragmentów naraz, więc jest bardziej odporna.

Osobne indeksy dla każdej sekcji mają jeszcze jeden problem: wyniki z różnych indeksów nie są ze sobą bezpośrednio porównywalne. Dlatego zastosowany został jeden wspólny indeks i głosowanie: każdy fragment ma w metadanych przypisaną sekcję, a wygrywa ta, która dominuje wśród najlepszych trafień. Przy 10 fragmentach sekcja zakupy przegłosowywała logowanie i raty. Wartości od 1 do 5 fragmentów dają tę samą trafność, ale przy 1 to w praktyce najbliższy sąsiad, nie prawdziwe głosowanie. Zostało 5: ten sam wynik co przy mniejszej liczbie, plus margines na to, że pojedynczy zły fragment nie przeważy całości.

Głosowanie hybrydowe dało dokładnie ten sam wynik z tymi samymi pomyłkami, tylko przy większej złożoności, więc zostało odrzucone.

Na pytaniach z literówkami dołożony został routing warunkowy na dwie sekcje: gdy lider wygrywa z przewagą nie większą niż ustalony margines, przeszukiwane są obie najlepsze sekcje naraz, a kandydaci z obu trafiają razem do rerankera.

| margines | trafność wyboru sekcji | trafność w top 5 | udział decyzji obejmujących dwie sekcje |
|---|---|---|---|
| 2 | 0.900 | 0.833 | 33% |
| 3 | 0.967 | 0.900 | 70% |

Margines 3 domykał praktycznie całą stratę wynikającą z błędnego wyboru sekcji. Wybrany został jednak margines 2, bo margines 3 uruchamiał podwójne wyszukiwanie i ranking na 70% ruchu, co na sprzęcie bez karty graficznej było zbyt kosztowne. Świadoma wymiana jakości na czas odpowiedzi, nie najlepszy wynik z tabeli.

**Ten mechanizm wyboru sekcji został później całkowicie usunięty**, patrz „Zrezygnowano z dzielenia bazy na sekcje" w sekcji „Wersja produkcyjna". Powyższe zostaje w README jako zapis decyzji, która była trafna na mniejszym zestawie testowym (20, potem 30 pytań). Rozszerzenie pomiarów do 61 pytań pokazało, że koszt błędów w wyborze sekcji przewyższa jego korzyść.

## Pomiary czasowe

| krok | czas |
|---|---|
| wybór sekcji | poniżej 50 ms |
| korekta i wyszukiwanie i ranking razem | 1–3 s |
| generowanie odpowiedzi, Bielik 1,5B | 8–10 s |
| generowanie odpowiedzi, Bielik-minitron 7B (skwantowany do Q4_K_M) | 53–61 s |

Generowanie odpowiedzi jest długie z powodu ograniczeń sprzętowych, przez co w praktyce system nie może być w pełni lokalny na docelowym sprzęcie bez utraty responsywności.

Model mmlw jest ładowany raz na cały moduł, a nie osobno dla każdego miejsca, które go używa. Wcześniej jeden z plików trzymał własną kopię modelu używaną tylko w testach, czyli w pamięci siedziały trzy modele zamiast dwóch. Wagi IDF są zapisywane w pliku na dysku i przeliczane od nowa tylko wtedy, gdy zmieni się korpus artykułów.

## Wersja produkcyjna

Projekt zaczął się jako w pełni lokalny (Ollama i Bielik 1,5B albo 7B, liczone na procesorze). Do publicznego demo trzeba było dwóch rzeczy: szybszego rerankera i mocniejszego modelu, którego nie da się rozsądnie uruchomić bez karty graficznej. Lokalny stack został przy tym zachowany w kodzie, dostępny pod komentarzem „Lokalne rozwiązanie" i przez zmienne środowiskowe. Produkcja to dokładnie ten sam kod, tylko z innym plikiem `.env`.

**Model przez API.** Generowanie odpowiedzi idzie na Bielika-11B przez zewnętrzny serwis zgodny z formatem OpenAI (Public AI). Klient czyta z pliku `.env` adres, klucz dostępu i nazwę modelu, a domyślnie celuje w lokalną instalację Ollamy, więc dokładnie ten sam kod działa i lokalnie, i na produkcji. Wyszukiwanie (embeddingi, reranker, FAISS) zostaje lokalne na serwerze, bez wysyłania danych na zewnątrz; publiczne demo korzysta z hostowanego Bielika wyłącznie po to, żeby było dostępne bez własnej karty graficznej.

**Wymiana rerankera na 26 razy szybszy.** Wcześniejszy reranker (`bge-reranker-v2-m3`, 568 milionów parametrów) na procesorze liczył około 43 sekundy na jedno zapytanie, co było głównym wąskim gardłem demo. Zmierzone na zestawie testowym 31 pytań, w izolacji od wyboru sekcji:

| reranker | rozmiar | trafność w top 3 | trafność w top 5 | czas na zapytanie |
|---|---|---|---|---|
| bge-reranker-v2-m3 | 568 mln parametrów | 0.933 | 0.967 | 43.5 s |
| mmarco-mMiniLMv2-L12-H384 | 118 mln parametrów | 0.900 | 0.933 | 1.64 s |

26 razy szybciej kosztem jednego trafienia na każdej z metryk. Większy model bge zostaje w kodzie jako wariant o wyższej jakości, ale odrzucony na procesorze ze względu na czas odpowiedzi. Rozbicie czasu dla mniejszego rerankera: embedding 0.07 s, wybór sekcji 0.01 s, wyszukiwanie 0.19 s, ranking 1.6 s.

**Szersze okno kandydatów dla rerankera.** Szybszy reranker kupił dodatkowy budżet czasowy na sprawdzanie większej liczby kandydatów, przy 43 sekundach na zapytanie ta rozmowa nie miałaby w ogóle sensu:

| liczba surowych kandydatów | trafność w top 3 | trafność w top 5 | czas na zapytanie |
|---|---|---|---|
| 10 | 0.833 | 0.867 | 1.01 s |
| 20 (wartość produkcyjna) | 0.900 | 0.933 | 2.39 s |

Zostaje 20 kandydatów: dwa dodatkowe trafienia na 30 pytań kosztem 1.38 s. Przy takim rozmiarze zestawu testowego jedno trafienie waży 0.033, więc ta różnica jest sugestywna, ale nie rozstrzygająca. To, że trafność w top 3 i w top 5 zgadzają się kierunkiem, niczego dodatkowo nie potwierdza, bo obie miary są ze sobą naturalnie powiązane.

**Ponowna kalibracja progów odmowy.** Trzy zmiany naraz, wymiana rerankera, przejście z modelu 1,5B na 11B i przebudowa promptów (oddzielenie instrukcji trzymania się faktów od instrukcji stylu, z regułą „trzymaj się słownictwa z kontekstu"), unieważniły progi dobrane pod poprzednią wersję systemu. Każdy z sygnałów strojony osobno na zestawie 30 pytań trafnych i 18 pytań spoza tematu. Wszystkie trzy rozkłady wyników się nakładają, więc żaden pojedynczy próg nie rozdziela ich w pełni czysto. Progi ustawione zostały tak, żeby nie krzywdziły pytań trafnych, a rozróżnianie pytań granicznych, bliskich tematowi ale spoza bazy, zrzucone zostało na sędziego opisanego niżej:

- Próg odrzucenia po wyniku rerankera, jeszcze przed generowaniem odpowiedzi: z −2.0 na −3.2. Najniższy wynik na pytaniu trafnym to −3.12, a najwyższy na pytaniu spoza tematu to −0.70, więc pełnej separacji nadal nie ma. Próg −2.0 fałszywie odcinał realne pytanie o bezpieczeństwo, „ktoś włamał się na moje konto" (wynik −3.12), jeszcze zanim model zaczął odpowiadać. Próg −3.2 to pytanie ratuje i sprawia, że reranker działa jak zgrubny, tani filtr: bez wywołania modelu odcina 11 z 18 oczywistych pytań spoza tematu (matematyka, przepisy kulinarne, kod programistyczny), a resztę oddaje sędziemu.
- Próg pokrycia, liczony po wygenerowaniu odpowiedzi: z 0.10 na 0.40. Przebudowany prompt trzyma model bliżej faktów, więc pokrycie wzrosło po obu stronach: najniższe pokrycie na pytaniu trafnym to 0.239, a najwyższe na pytaniu spoza tematu to 0.516, więc znowu bez pełnej separacji. Próg 0.40 to ostatnia linia obrony, dobrana tak, żeby minimalizować fałszywe odmowy. Próg 0.52 dałby zero przecieków pytań spoza tematu, ale odrzuciłby też to samo pytanie o włamanie na konto (pokrycie 0.477), które chwilę wcześniej uratował reranker.

**Ocena kontekstu przez model jako sędzia pytań granicznych.** Sygnały opisane wyżej nie łapią pytań bliskich tematycznie, ale jednak spoza bazy, na przykład o serwis OLX, o przeziębienie czy o założenie firmy. Odsiewa je dodatkowe wywołanie modelu z pytaniem TAK albo NIE. Zmierzone na 31 pytaniach trafnych i 18 pytaniach spoza tematu:

| model w roli sędziego | fałszywe odmowy | poprawnie złapane pytania spoza tematu |
|---|---|---|
| Bielik-11B | 2/30 | 17/18 |
| EuroLLM-22B | 5/30 | 18/18 |

Wybrany został Bielik-11B jako lepszy kompromis: 2 fałszywe odmowy w zamian za 17 z 18 złapanych pytań spoza tematu. EuroLLM jest surowszy (łapie wszystkie pytania spoza tematu, ale krzywdzi 5 poprawnych) i został w rezerwie pod scenariusz zgodności regulacyjnej, gdzie „nigdy nie odpowiedz nie na temat" waży więcej niż „czasem niesłusznie odmów". Tańsze modele ogólnego przeznaczenia (EuroLLM, apertus) gorzej wyczuwają, co jest polskim pytaniem na temat, a co nie, sprawdzone bezpośrednio na danych. To dodatkowe wywołanie kosztuje około 3 sekundy, włączane jest zmienną środowiskową i na darmowej wersji demo bywa wyłączane.

Model użyty jako sędzia jest niezależny od modelu, który generuje odpowiedzi. Osobna zmienna środowiskowa (domyślnie równa modelowi generującemu) pozwala posadzić w roli sędziego tańszy, mniejszy model niż ten, który pisze odpowiedzi. Decyzja typu „czy kontekst w ogóle pasuje" jest dużo lżejszym zadaniem niż napisanie pełnej odpowiedzi, więc nie wymaga tej samej klasy modelu. Kod jest pod to przygotowany: wystarczy wskazać inny model w pliku `.env`, żeby obniżyć koszt tego kroku bez wpływu na jakość samych odpowiedzi.

Bilans całego łańcucha bramek (reranker przy −3.2, potem sędzia, potem pokrycie przy 0.40) na tamtym przebiegu pomiaru: 2 z 30 trafnych pytań fałszywie odrzucone (jedno przez sędziego, jedno przez pokrycie), a 1 z 18 pytań spoza tematu przeciekło przez wszystkie trzy bramki naraz, było to nieszkodliwe „przetłumacz dzień dobry na angielski", które reranker, sędzia i pokrycie po kolei przepuściły.

Wniosek metodyczny: żaden pojedynczy sygnał (ani wynik rerankera, ani pokrycie ważone IDF) nie rozdziela w pełni pytań granicznych od słabszych pytań z domeny, dopiero ocena modelu jako sędziego to robi. Każda zmiana rerankera, modelu odpowiadającego albo promptu wymusza ponowną kalibrację wszystkich progów naraz, bo są one ze sobą powiązane.

**Limit zapytań i obsługa błędów.** Publiczny endpoint ma globalny limiter (domyślnie 15 zapytań na minutę i 200 na dzień, wartości ustawiane zmiennymi środowiskowymi), który chroni budżet na wywołania API przed nadużyciami. Limit jest globalny, a nie liczony osobno dla każdego adresu IP: ruch idzie przez Caddy do frontendu, a dopiero frontend woła API z wnętrza kontenera, więc z punktu widzenia backendu każdy klient wygląda tak samo. Liczenie osobno dla każdego adresu IP wymagałoby albo dodatkowej wtyczki do Caddy'ego zbudowanej we własnym obrazie, albo przekazywania adresu klienta dalej własnym nagłówkiem. Globalny limit zamyka temat kosztów, limit per adres zamykałby temat dostępności; obecnie jedna osoba nadużywająca systemu potrafi wyczerpać dzienną pulę dla wszystkich innych. Błędy generowania odpowiedzi (API nie odpowiada albo przekracza czas oczekiwania) są w całości przechwytywane i zwracają użytkownikowi komunikat „model chwilowo niedostępny" zamiast surowego błędu technicznego, z pełnym logiem po stronie serwera. Frontend dodatkowo łapie zerwanie połączenia strumieniowego i niepoprawnie sformatowaną odpowiedź; Streamlit uruchamiany jest z wyłączonym pokazywaniem szczegółów błędów, więc nieprzewidziany wyjątek nie pokaże w przeglądarce ścieżek plików ani fragmentów kodu z serwera.

**Limit długości odpowiedzi.** Limit tokenów podniesiony z 700 do 1500. Przy 700 najdłuższa odpowiedź w pomiarze miała 691 tokenów i była ucinana w połowie zdania. To obcięcie było niewidoczne w logach, bo pętla obsługująca strumień ignorowała informację o przyczynie zakończenia: odpowiedź urwana z powodu limitu wyglądała identycznie jak odpowiedź zakończona normalnie. Całkowite zniesienie limitu nie wchodziło w grę: koszt i czas generowania przestałyby mieć górną granicę, a zbyt rozwlekła odpowiedź oddala się od dostarczonego kontekstu i obniża pokrycie, więc bramka odrzucałaby własną, skądinąd poprawną odpowiedź.

**Log trudnych pytań bez treści pytania.** Osobny plik logu zapisuje wyłącznie nierozpoznane pojedyncze słowa, nigdy całą treść pytania. Fragmenty pochodzące z adresów e-mail, numerów telefonu, numerów zamówień i adresów URL są odsiewane przez dopasowanie wzorców do oryginalnego pytania, bo samo filtrowanie pojedynczych słów nic by nie dało: sposób dzielenia tekstu na słowa przepuszcza tylko litery, więc adres w stylu „jan.kowalski@example.com" trafiłby do logu jako pozornie niewinne „jan", „kowalski", „example". Sprawdzone na 7 przypadkach: fragmenty danych osobowych znikają, a literówki takie jak „kotno", „smrtem" czy „blikeim" zostają widoczne.

**Błąd etykiety w bazie artykułów, znaleziony po czasie trwania odmowy.** Pytanie „Sprzedawca chce, żebym zapłacił poza Allegro, czy to bezpieczne?" było odrzucane w sposób stabilny, mimo że dotyczyło tematu w pełni objętego bazą. Czas trwania odmowy pozwala rozróżnić, która bramka zadziałała, bez zaglądania w kod: poniżej 1 sekundy to filtr wejścia, około 2.9 sekundy to sam próg rerankera bez udziału modelu, a około 6.3 sekundy to odmowa sędziego (dodatkowe wywołanie modelu). To konkretne pytanie padało po około 6.3 sekundy, więc winny był sędzia, nie próg liczbowy. Diagnoza: właściwy artykuł miał w bazie przypisaną etykietę „konto" zamiast „zakupy" (kategoria o bezpiecznych zakupach była źle zmapowana), więc artykuł nigdy nie trafiał w ogóle do puli kandydatów rerankera. Sędzia dostawał więc kontekst o Allegro Pay i słusznie odmawiał, bo rzeczywiście nie pasował do pytania. Naprawa: jedna linijka poprawionego mapowania kategorii i przeniesienie 3 artykułów do właściwej etykiety, z przebudową indeksów. Kontrola pod kątem regresji: trafność w top 3 i w top 5 na zestawie testowym bez zmian (0.900 i 0.933).

**Zestawy pomiarowe rozszerzone: z 30 do 61 pytań trafnych, z 18 do 29 pytań spoza tematu.** Przy 30 pytaniach jedno trafienie ważyło 0.033, więc każda dotychczasowa różnica mieściła się w zaledwie dwóch pytaniach, a zestaw trafny pokrywał tylko 29 ze 141 artykułów. Nowe pytania spoza tematu są w większości graniczne: pytania o Allegro, ale spoza bazy dla kupujących (prowizja sprzedawcy, infolinia, notowania giełdowe spółki) — stary zestaw był zdominowany przez oczywiste przypadki (matematyka, przepisy kulinarne), które odcina już sam próg rerankera, więc sztucznie zawyżał wrażenie odporności systemu.

**Zrezygnowano z dzielenia bazy na sekcje.** Rozszerzony zestaw testowy pokazał, że router opisany wyżej w sekcji „Dopasowanie sekcji" przegrywa z prostym przeszukaniem całej bazy naraz, na każdej mierzonej osi:

| tryb | trafność w top 5 (61 pytań) | czas na zapytanie | pytania spoza tematu odcięte samym progiem, bez sędziego |
|---|---|---|---|
| router (dwie najlepsze sekcje, margines 2) | 0.852 | 4.41 s | 5/29 |
| **cała baza naraz, bez dzielenia na sekcje** | **0.918** | **3.33 s** | **7/29** |

Router zwykle rankuje 40 par kandydatów (po 20 z dwóch zgadywanych sekcji), a przeszukanie całości rankuje tylko 20 kandydatów z całej bazy: mniej kandydatów, ale lepiej wycelowanych w temat pytania. Sędzia działał bez zmian w obu trybach (27 z 29 poprawnie złapanych), więc rezygnacja z dzielenia na sekcje nie osłabiła bramki odmowy. Wcześniejsza, pośrednia próba: przeszukanie całej bazy tylko jako zapasowa ścieżka po odmowie, nie dała nic, bo pomyłki wyboru sekcji nie powodują odmowy, tylko pewną siebie, błędną odpowiedź, więc żadna bramka na to nie reaguje i zapasowa ścieżka nigdy nie dostawała szansy zadziałać tam, gdzie była naprawdę potrzebna. Ręczny wybór sekcji w panelu bocznym pozostał w interfejsie, ale przestał wpływać na wynik. Świadomie zostawione jako punkt do ewentualnego dopracowania w przyszłości, na przykład jako twardy filtr wyników zamiast rozszerzania puli kandydatów.

**Ponowna kalibracja progu rerankera: z −3.2 na −4.3.** Rozkłady wyników na pytaniach trafnych i pytaniach spoza tematu nakładają się na siebie (23 z 29 pytań spoza tematu punktuje wyżej niż najsłabsze pytanie trafne), więc żaden próg nie rozdziela ich w pełni czysto. Jedyną sensowną rolą tego progu jest więc tanie odcięcie skrajnych przypadków, zanim dojdzie do wywołania modelu, a resztą zajmuje się sędzia.

| próg | fałszywe odmowy (pytania trafne) | pytania spoza tematu odcięte za darmo | liczba wywołań sędziego łącznie |
|---|---|---|---|
| −3.2 (poprzednio) | 2/61 | 11/29 | 77 |
| **−4.3 (obecnie)** | **0/61** | **5/29** | **85** |

Zero fałszywych odmów, kosztem 8 dodatkowych wywołań sędziego na pełnym przebiegu pomiaru. To tanio, bo sędzia i tak łapał te same pytania (patrz wyżej), więc próg po prostu przestał robić za niego tę samą robotę za darmo.

**Rozgrzewka indeksów przy starcie.** Indeksy BM25 i FAISS dla poszczególnych sekcji wczytują się leniwie, czyli dopiero przy pierwszym użyciu danej sekcji. Uruchomienie serwera rozgrzewało wcześniej tylko reranker i model do embeddingów, więc pierwsze zapytanie trafiające w daną sekcję płaciło dodatkowo za wczytanie jej indeksu z dysku. Efekt był widoczny w pomiarze wykonanym w kontenerze: pierwsze trzy zapytania (każde do innej sekcji) trwały 18.1, 17.9 i 15.2 sekundy, zamiast typowych 3 do 7 sekund.

**Symulacja 100 pytań, przekrój zachowania całego systemu.** Osobny skrypt uruchomił 100 pytań w trybie przeszukiwania całej bazy, z sędzią włączonym. Pytania podzielone na 6 kategorii: zwykłe, z literówkami, niejasne (odnoszące się do czegoś wcześniej zaimkiem, bez podania kontekstu wprost), złożone z dwóch części, złożone z trzech części oraz spoza tematu. Wynik: 76 odpowiedzi na 100 pytań, 24 odmowy.

| kategoria | udzielone odpowiedzi | ocena |
|---|---|---|
| zwykłe | 25/26 | dobrze |
| z literówkami | 19/21 | korektor działa |
| złożone z trzech części | 12/13 | **lepiej niż złożone z dwóch części** |
| złożone z dwóch części | 12/16 | 3 fałszywe odmowy |
| niejasne | 7/16 | większość odmów była słuszna (pytania w stylu „jak to zmienić" bez podanego kontekstu) |
| spoza tematu | 1/8 | poprawnie odrzucane |

Kontrintuicyjny wynik: pytania trzyczęściowe (92% odpowiedzi) wypadają lepiej niż dwuczęściowe (75%). Dłuższe pytanie daje rerankerowi po prostu więcej sygnału: trzy odrębne wątki w pytaniu to trzy szanse na trafienie słownictwa z bazy, co jest efektem odwrotnym do sytuacji z pojedynczym rerankerem na węższej puli kandydatów, gdzie wielowątkowość szkodziła. Pytania spoza tematu trzymają się dobrze mimo braku dzielenia bazy na sekcje: 7 z 8 odrzuconych poprawnie, w tym pytania graniczne, takie jak „ile allegro bierze prowizji", „kto jest właścicielem allegro" czy „jak założyć sklep". Jedyny przeciek to nieszkodliwe pytanie „gdzie jest siedziba allegro". Potwierdza to wcześniejszy wniosek: bramkę pytań spoza tematu niesie głównie sędzia, nie sam próg liczbowy.

**Bramka pokrycia marnowała wygenerowaną odpowiedź na pytaniach trafnych.** Rozbicie tych samych 24 odmów z powyższej symulacji na osobne przyczyny pokazuje: 17 odmów padło jeszcze przed wygenerowaniem odpowiedzi (bez zużytych tokenów, tanio i poprawnie), ale 7 odmów padło już PO wygenerowaniu odpowiedzi (877 zmarnowanych tokenów łącznie), z czego dwie na w pełni trafnych pytaniach z domeny: wyszukiwanie trafiło właściwy artykuł na 1. miejscu, model odpowiedział merytorycznie poprawnie, a mimo to pokrycie odpowiedzi kontekstem wypadło poniżej ówczesnego progu 0.40, więc już gotowa odpowiedź została odrzucona. To najgorszy możliwy przebieg: koszt wygenerowania odpowiedzi poniesiony, a użytkownik i tak dostaje komunikat „nie znalazłem". Przyczyna: model czasem parafrazuje odpowiedź słowami spoza dostarczonego kontekstu, na przykład przy pytaniu o odzyskiwanie dostępu do konta pisał o „weryfikacji" czy „tożsamości", nawet jeśli tych dokładnych słów w danym fragmencie nie było, więc pokrycie leksykalne spadało mimo poprawności merytorycznej. Ryzyko rośnie przy dłuższych, wieloczłonowych pytaniach, stąd akurat 3 z 4 fałszywych odmów w kategorii pytań dwuczęściowych.

**Ponowna kalibracja progu pokrycia: z 0.40 na 0.20.** Osobny skrypt policzył rozkład wartości pokrycia dokładnie tam, gdzie problem realnie występował: na 29 pytaniach wieloczłonowych z domeny (czyli w strefie fałszywych odmów) w porównaniu z 29 pytaniami spoza tematu.

| | wartość minimalna | 5. percentyl | mediana | wartość maksymalna |
|---|---|---|---|---|
| pytania trafne z domeny | 0.253 | 0.259 | 0.690 | 0.885 |
| pytania spoza tematu | 0.042 | 0.042 | 0.228 | 0.651 |

Rozkłady się nakładają (najwyższa wartość dla pytania spoza tematu, 0.651, jest wyższa niż najniższa wartość dla pytania trafnego, 0.253), więc samo pokrycie nie jest wystarczającym sygnałem tematu pytania. W praktyce nie ma to jednak większego znaczenia: pytanie spoza tematu w ogóle nie dociera do tej bramki, bo jest odcinane wcześniej przez próg rerankera (−4.3) i przez sędziego (27 z 29 poprawnie złapanych). Pokrycie działa więc jako czyste zabezpieczenie przed halucynacją, a nie jako obrona przed pytaniami spoza tematu, dlatego kolumna z pytaniami spoza tematu w tabeli niżej jest tak naprawdę drugorzędna.

| próg | fałszywe odmowy (pytania trafne) | pytania spoza tematu złapane (drugorzędnie) |
|---|---|---|
| 0.40 (poprzednio) | 4/29 | 25/29 |
| 0.25 | 0/29 | 15/29 |
| **0.20 (obecnie)** | **0/29** | **11/29** |

Wybrany został próg 0.20, a nie 0.25, mimo że oba dają zero fałszywych odmów na tej próbce. Najniższa wartość dla pytania trafnego to 0.253, a generowanie odpowiedzi jest z natury trochę losowe (rozrzut rzędu 0.01 do 0.03 dla dokładnie tego samego pytania przy kolejnych próbach), więc próg 0.25 zostawiałby margines zaledwie 0.003, czyli jeden gorszy traf losowania i pytanie znów zostałoby odrzucone. Próg 0.20 daje margines 0.05 poniżej zaobserwowanego minimum, a mimo to wciąż reaguje na tekst naprawdę niemający oparcia w kontekście (minimalna wartość dla pytania spoza tematu to 0.042). Efekt na symulacji 100 pytań: obie fałszywe odmowy powstałe po wygenerowaniu odpowiedzi (przy pokryciu 0.253 i 0.380) teraz przechodzą bez odrzucenia. Bramka pokrycia staje się w ten sposób czystym zabezpieczeniem przed halucynacją, a nie źródłem strat na pytaniach, które i tak były trafne.

## Wdrożenie

Demo: [ogflow.pl](https://ogflow.pl). Serwer VPS Hetzner, Ubuntu 24.04 LTS, 4 rdzenie procesora, 7.6 GB pamięci RAM, 75 GB dysku.

| kontener | obraz | port | rola |
|---|---|---|---|
| `caddy` | caddy:2 | 80, 443 | reverse proxy, HTTPS z Let's Encrypt |
| `frontend` | python:3.13-slim | 8501 (wewnętrzny) | Streamlit |
| `api` | python:3.13-slim | 8000 (wewnętrzny) | FastAPI i wyszukiwanie |

API nie ma publicznie dostępnego portu, frontend łączy się z nim po wewnętrznej sieci Dockera. Oba kontenery działają jako zwykły użytkownik, nie jako root. Modele pobrane z Hugging Face trzymane są na osobnym wolumenie i ściągane tylko raz, przy pierwszym starcie. Katalog z danymi (`RAG/`) jest montowany jako wolumen, a nie kopiowany do obrazu: indeksy są w `.gitignore`, więc skopiowanie ich do obrazu dałoby kontener, który buduje się bez błędu, ale wysypuje się dopiero przy pierwszym użyciu.

**Czas odpowiedzi w kontenerze.** 5 pytań powtórzonych 3 razy każde, generowanie przez Bielika-11B przez zewnętrzne API:

| metryka | wartość |
|---|---|
| mediana czasu do pierwszego fragmentu odpowiedzi | 5.61 s |
| mediana całkowitego czasu odpowiedzi | 6.31 s |
| maksymalny całkowity czas odpowiedzi | 16.57 s (pierwsze uruchomienie) |

Samo uruchomienie w kontenerze nie dołożyło żadnego dodatkowego opóźnienia, 6.31 sekundy zgadza się z rozbiciem na etapy (około 1.9 s na wyszukiwanie i ranking, około 4.4 s na generowanie odpowiedzi). Pierwsze zapytanie po starcie serwera jest 2 do 3 razy wolniejsze niż kolejne, bo uruchomienie serwera rozgrzewa reranker, ale model do embeddingów mmlw wczytuje się dopiero przy pierwszym realnym zapytaniu. Czas do pierwszego fragmentu odpowiedzi jest tu praktycznie równy czasowi całkowitemu (5.61 wobec 6.31 s), bo odpowiedź od zewnętrznego API przychodzi jedną paczką, a nie prawdziwym strumieniem, więc efekt stopniowego pokazywania tekstu w interfejsie jest ograniczony.

**Wersja Pythona w obrazie musi zgadzać się z wersją używaną lokalnie.** Plik `requirements.txt` wygenerowany z lokalnego środowiska (Python 3.13) odzwierciedla właśnie tamto środowisko. Przy próbie budowy na obrazie z Pythonem 3.11 instalacja pakietów się wysypywała na numpy w wersji 2.5.1, z komunikatem sugerującym, że taka wersja w ogóle nie istnieje. W rzeczywistości numpy 2.5 wymaga Pythona co najmniej 3.12, a menedżer pakietów pokazuje tylko wydania zgodne z aktualnie używanym Pythonem, więc komunikat błędu był mylący. Wersja biblioteki torch jest przypięta na sztywno (2.13.0), bo bez tego dwie kolejne instalacje w odstępie tygodnia potrafiłyby dać dwa różne środowiska.

```bash
cd docker
cp .env.example .env        # klucz do API modelu, token Hugging Face, domena
docker compose up -d --build
```

Katalog `RAG/` i skrypty pomiarowe (`measure_*.py`) nie wchodzą do repozytorium, na serwer trafiają osobno, przed budową obrazu.

## Uruchomienie

Odtworzenie danych i indeksów, jednorazowo:

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

Model, dwie ścieżki do wyboru przez plik `.env` w katalogu `src/`:

```bash
# produkcyjnie: Bielik-11B przez API (zgodne z formatem OpenAI)
LLM_BASE_URL=https://api.publicai.co/v1
LLM_API_KEY=...
MODEL=speakleash/Bielik-11B-v3.0-Instruct
HF_TOKEN=...

# lokalnie: pobierz model do Ollamy, pomiń zmienne LLM_* (domyślnie celuje w localhost:11434/v1)
# ollama pull SpeakLeash/bielik-minitron-7B-v3.0-instruct:Q4_K_M
```

```bash
uvicorn src.api:app --reload
streamlit run frontend/app.py
```
