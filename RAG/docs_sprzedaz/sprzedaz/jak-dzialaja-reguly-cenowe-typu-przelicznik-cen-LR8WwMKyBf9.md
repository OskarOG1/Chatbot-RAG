---
url: https://help.allegro.com/pl/sell/a/jak-dzialaja-reguly-cenowe-typu-przelicznik-cen-LR8WwMKyBf9
tytul: Jak działają reguły cenowe typu Przelicznik cen
agent: sprzedaz
podslug: jak-wystawiac-oferty
---



Przelicznik cen to reguła cenowa, która aktualizuje cenę oferty na wybranym rynku zagranicznym na podstawie:
ceny tej oferty na Twoim rynku rejestracji
informacji o kursach, które publikuje Europejski Bank Centralny.
Dzięki temu możesz utrzymać spójną politykę cenową na wielu rynkach, a także reagować na zmiany kursów walut.

Za pomocą reguł cenowych typu Przelicznik cen możesz zarządzać cenami ofert na rynkach zagranicznych. Nie możesz użyć tej reguły, aby zarządzać ceną na swoim rynku rejestracji.

Jak działa Przelicznik cen
Podane przez Ciebie ceny w walucie Twojego rynku rejestracji przeliczamy na inne waluty według wzoru:
cena w walucie rynku rejestracji
x
kurs walut
=
cena w walucie sprzedaży danego rynku
Podczas przeliczania cen
zaokrąglamy otrzymane kwoty
– tak, aby były zgodne ze standardem rynkowym i nominałami, które są dostępne dla danej waluty.

Gdy przeliczasz cenę z innej waluty na:
To kwotę po przewalutowaniu zaokrąglamy matematycznie:
Przykłady
korony czeskie (CZK)
To kwotę po przewalutowaniu zaokrąglamy matematycznie:
do pełnych koron, czyli 0 miejsc po przecinku
Przykłady
15,09 CZK → 15 CZK
345,5391 CZK → 346 CZK
euro (EUR)
To kwotę po przewalutowaniu zaokrąglamy matematycznie:
do eurocentów, czyli 2 miejsca po przecinku
Przykłady
1,2993 EUR → 1,30 EUR
90,3298 EUR → 90,33 EUR
polskie złotówki (PLN)
To kwotę po przewalutowaniu zaokrąglamy matematycznie:
do groszy, czyli 2 miejsca po przecinku
Przykłady
2437,9841 PLN → 2437,98 PLN
156,5012 PLN → 156,50 PLN
Przy zaokrąglaniu
forintów węgierskich (HUF)
stosujemy inne, bardziej szczegółowe reguły – w zależności od kwoty otrzymanej bezpośrednio po przewalutowaniu. Sprawdzisz je w tabeli poniżej.
Gdy kwota po przeliczeniu z innej waluty na forinty to:
To taką kwotę po przewalutowaniu zaokrąglimy:
Przykłady
2,50–7,49 HUF
To taką kwotę po przewalutowaniu zaokrąglimy:
do 5 HUF
Przykłady
2,55 HUF → 5 HUF
6,8924 HUF → 5 HUF
7,50–9,99 HUF
To taką kwotę po przewalutowaniu zaokrąglimy:
do 10 HUF
Przykłady
8,12 HUF → 10 HUF
9,9823 HUF → 10 HUF
powyżej 10 HUF, a po matematycznym zaokrągleniu jej cyfra jedności to 0, 1 lub 2
To taką kwotę po przewalutowaniu zaokrąglimy:
do wielokrotności 10 HUF
Przykłady
10,41 HUF → 10 HUF
83 412,3311 HUF → 83 410 HUF
powyżej 10 HUF, a po matematycznym zaokrągleniu jej cyfra jedności to 3, 4, 5, 6 lub 7
To taką kwotę po przewalutowaniu zaokrąglimy:
do wielokrotności 5 HUF
Przykłady
1912,74 HUF → 1915 HUF
20 017,3492 HUF → 20 015 HUF
powyżej 10 HUF, a po matematycznym zaokrągleniu jej cyfra jedności to 8 lub 9
To taką kwotę po przewalutowaniu zaokrąglimy:
do wielokrotności 10 HUF
Przykłady
917,95 HUF → 920 HUF
3209,1125 HUF → 3210 HUF
Gdy po przeliczeniu z innej waluty otrzymasz kwotę niższą niż 2,50 HUF – nie udostępnisz takiej oferty na allegro.hu. Minimalna cena produktu na tym rynku to
5 HUF
.

Jeśli
stworzysz własną regułę cenową typu Przelicznik cen
, możemy też dodawać lub odejmować określony procent lub kwotę do ceny przed jej przewalutowaniem.
Przykładowo, jeśli stworzysz regułę, która dodaje 5%, przeliczymy cenę według wzoru:
(
cena w walucie rynku rejestracji
+
5% ceny w walucie rynku rejestracji
) x
kurs walut
=
cena w walucie sprzedaży danego rynku

Wystawiasz ofertę z ceną
15 zł
i udostępniasz ją na allegro.sk.
Dla rynku allegro.sk ustawiasz regułę cenową, która:
dodaje 10%
do ceny w złotówkach
korzysta z
Przelicznika cen
, aby przeliczyć tę kwotę na euro po aktualnym kursie.
Aby ustalić cenę na słowacki rynek, najpierw dodamy 10% do ceny w złotówkach – będzie to 16,50 zł.
Kurs walut, który jest aktualny dla Przelicznika cen w tym dniu, to 1 PLN = 0,231 EUR. Dlatego po przeliczeniu cena Twojej oferty na allegro.sk będzie równa
3,81 EUR
.
Kilka dni później w tej samej ofercie obniżasz cenę w złotówkach do
14 zł
.
Zastosujemy wtedy Twoją regułę, aby zaktualizować cenę w euro. Po dodaniu 10% do nowej ceny w złotówkach otrzymamy 15,40 zł – tę kwotę przeliczymy po aktualnym kursie (1 PLN = 0,246 EUR). Nowa cena na allegro.sk wyniesie zatem
3,79 EUR
.

Kiedy aktualizujemy ceny w ofertach z tą regułą
Przelicznik nie aktualizuje cen automatycznie po każdej zmianie kursu walut
. To Ty decydujesz, kiedy chcesz przeliczyć ceny w swoich ofertach.
Gdy połączysz regułę cenową typu Przelicznik cen z ofertą, pierwszy raz zaktualizujemy w niej cenę na rynku zagranicznym. Od tego czasu będziemy aktualizować tę cenę za każdym razem, gdy:
zmienisz cenę tej oferty na swoim rynku rejestracji
klikniesz [przelicz ceny] w zakładce
Mój asortyment
wznowisz tę ofertę
– jeśli została wcześniej zakończona
edytujesz regułę cenową połączoną z ofertą – jeśli korzystasz z
własnej reguły cenowej
.

Jeśli chcesz, aby ceny w Twoich ofertach przeliczały się automatycznie – skorzystaj z
Automatycznego Przelicznika cen
.

Jak przeliczyć ceny jednym kliknięciem
Otwórz
Mój asortyment
.
Na dole zobaczysz sekcję z informacją o aktualnych kursach walut i opcją przeliczanie ceny we wszystkich ofertach z włączonym Przelicznikiem cen.
Kliknij przycisk [przelicz ceny].
Gotowe! W każdej z tych ofert podaną przez Ciebie cenę w walucie rynku rejestracji jednorazowo przeliczymy na walutę obowiązującą na rynkach, na których udostępniasz swoje oferty.
Może to potrwać do kilku godzin
.
W ten sposób przeliczysz ceny wyłącznie w
aktywnych
ofertach.
Jeśli chcesz przeliczyć ceny w ofertach o statusie:
aktywna
,
szkic
,
zaplanowana
lub
zakończona
, skorzystaj z grupowej edycji ofert:
Otwórz zakładkę
Mój asortyment
.
Zaznacz oferty, w których chcesz przeliczyć ceny.
Na zielonym pasku na dole strony wybierz [warunki sprzedaży], a następnie [Cena].
W oknie, które zobaczysz, wybierz regułę cenową Przelicznik cen lub nazwę
własnej reguły tego typu
.
Kliknij [zapisz zmiany].
W każdej z tych ofert podaną przez Ciebie cenę w złotówkach jednorazowo przeliczymy na walutę obowiązującą na rynkach, na których udostępniasz swoje oferty.
Może to potrwać do kilku godzin
.
Co to jest Automatyczny Przelicznik cen
Automatyczny Przelicznik cen włączy się sam
, jeśli spełniasz 2 warunki:
masz dodaną regułę cenową typu Przelicznik cen
korzystasz z
Abonamentu Allegro
.
Jak działa Automatyczny Przelicznik cen
Jeżeli kurs walut zmieni się o co najmniej 1% względem
ostatniej masowej aktualizacji ceny
–
automatycznie
dostosujemy cenę w walucie rynku zagranicznego we wszystkich ofertach, w których masz włączony
Przelicznik cen
, w tym we wszystkich ofertach:
z Twoją własną regułą typu Przelicznik cen
w których został włączony Przelicznik cen podczas udostępniania ich na rynki zagraniczne.
W ofertach z włączonym Przelicznikiem cen, ceny przeliczą się również, gdy:
zmienisz cenę na rynku rejestracji
wznowisz ofertę – jeśli została wcześniej zakończona
edytujesz regułę cenową połączoną z ofertą – jeśli korzystasz z własnej reguły cenowej.

Jeśli nie chcesz korzystać z Automatycznego Przelicznika cen – możesz go wyłączyć w dowolnej chwili w zakładce
Automatyczne ceny
.

Czym jest ostatnia masowa aktualizacja ceny
To moment, w którym po raz ostatni zaktualizowaliśmy ceny w ofertach:
gdy ceny zostały przeliczone za pomocą opcji [przelicz ceny] w zakładce
Mój asortyment
lub
automatycznie, ponieważ kurs walut zmienił się o co najmniej 1% od poprzedniej masowej aktualizacji.
Kiedy będziemy przeliczać ceny
Za każdym razem, gdy referencyjny kurs walut ogłaszany przez Europejski Bank Centralny z dnia poprzedzającego dzień przewalutowania zmieni się o co najmniej 1% od poprzedniej masowej aktualizacji.
Dodatkowe informacje
Tak samo jak
pozostałe reguły cenowe
, Przelicznik cen
nie zadziała w ofertach, które aktualnie biorą udział w kampaniach lub programach
, jeśli udział oferty w takiej kampanii ma ścisły związek z jej ceną. Przykłady takich kampanii i programów to: AlleObniżka, Allegro Ceny czy Smart! Week. Gdy Twoja oferta zakończy udział w kampanii, ponownie zaczniemy stosować w niej wybraną regułę cenową.
Gdy w ofercie korzystasz z Przelicznika cen, ale zdecydujesz się ustawić w niej
własną cenę w walucie innego rynku
– automatycznie wyłączymy Przelicznik cen w tej ofercie.