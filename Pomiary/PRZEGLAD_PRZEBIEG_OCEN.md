# Przeglad przebiegu ocen (gemini-2.5-flash)

Pozycji: 38. Dwie czesci, wypelniaj po kolei, nie zagladaj do czesci 2
przed wypelnieniem czesci 1.

## Czesc 1: czy odpowiedz w ogole istnieje

Przy kazdym pytaniu zmien `ISTNIEJE: ?` na `T` albo `N`.
`T` znaczy, ze odpowiedz na to pytanie JEST w bazie pomocy Allegro, `N`, ze jej tam nie ma.
To cecha pytania i korpusu, nie systemu. Raz oceniona posluzy kazdemu przyszlemu wariantowi,
wiec tej pracy nie trzeba bedzie powtarzac. Odpowiedzi systemu sa nizej i teraz ich nie czytaj.

### 0. [A] Ile mam czasu na zwrot?
ISTNIEJE: T

### 1. [A] jak zlozyc nowe polecenie zaplaty
ISTNIEJE: T

### 2. [A] ile mam czasu na zwrot
ISTNIEJE: T

### 3. [A] zapomniałem loginu
ISTNIEJE: T

### 4. [A] czy da się zalogować bez wpisywania hasła
ISTNIEJE: T

### 5. [A] Ile wynosi prowizja od sprzedazy?
ISTNIEJE: T

### 6. [A] Co zrobic gdy kupujący zalicytował dla żartów?
ISTNIEJE: T

### 7. [A] Ile wynosi prowizja od sprzedazy na Allegro?
ISTNIEJE: T

### 8. [B] jak długo mam na zwrot towaru
ISTNIEJE: T

### 9. [B] napisz mi maila o reklamacji wadliwego produktu
ISTNIEJE: T

### 10. [B] jak zaplacic kartsa
ISTNIEJE: T

### 11. [B] Produkt, który kupiłem, jest wadliwy. Jak mogę go zareklamować?
ISTNIEJE: T

### 12. [B] Chce zwrocic buty, sa za male, przygotuj mi maila do sprzedawcy
ISTNIEJE: T

### 13. [B] Zapomniałem hasła do konta
ISTNIEJE: T

### 14. [B] Ile mam dni na zwrot towaru?
ISTNIEJE: T

### 15. [B] Przygotuj proszę szkic maila reklamacyjnego do sprzedawcy.
ISTNIEJE: T

### 16. [B] Chce napisac mail bo produkt jest uszkodzony
ISTNIEJE: T

### 17. [B] Chcę złożyć reklamację, produkt przyszedł uszkodzony
ISTNIEJE: T

### 18. [B] chce zwrocic zamowione buty, nie pasuja, jak to zrobic
ISTNIEJE: T

### 19. [B] Jak długo mam na zwrot towaru?
ISTNIEJE: T

### 20. [B] jak kupic i zaplacic za przedmiot w ramach aukcji allegro dla wosp
ISTNIEJE: T

### 21. [B] Jak usunąć konto na allegro
ISTNIEJE: T

### 22. [B] jak wystawić przedmiot na sprzedaż
ISTNIEJE: T

### 23. [B] Jak zarejestrować konto firmowe?
ISTNIEJE: T

### 24. [B] Jak zgłosić brak dostawy?
ISTNIEJE: T

### 25. [B] jak zmienic haslo do konta
ISTNIEJE: T

### 26. [B] jak zmienic haslo na allegro
ISTNIEJE: T

### 27. [B] Jak zwrocic towar kupiony w ramach allegro smart
ISTNIEJE: T

### 28. [B] Napisz mi maila do sprzedawcy w sprawie braku dostawy paczki
ISTNIEJE: T

### 29. [B] Napisz mi maila o zwrot produktu
ISTNIEJE: T

### 30. [B] Napisz mi maila w sprawie reklamacji uszkodzonego produktu
ISTNIEJE: T

### 31. [B] Napisz mi maila w sprawie zwrotu produktu
ISTNIEJE: T

### 32. [B] napisz mi maila, bo sprzedawca nie odpowiada od tygodnia
ISTNIEJE: T

### 33. [B] napisz mi wiadomość o zwrocie produktu
ISTNIEJE: T

### 34. [B] Napisz za mnie wiadomość do sprzedawcy w tej sprawie
ISTNIEJE: T

### 35. [B] paczka nie przyszła, co mam zrobić
ISTNIEJE: T

### 36. [B] produkt ktory kupilem jest uszkodzony, co mam zrobic
ISTNIEJE: T

### 37. [B] Przygotuj proszę szkic wiadomości o zwrocie produktu.
ISTNIEJE: T


## Czesc 2: czy odpowiedz jest dobra

Przy kazdej pozycji zmien `OCENA: ?` na `D` (dobra), `Z` (zla) albo `X` (system odmowil).
Zla to takze odpowiedz prawdziwa, ale nie na zadane pytanie.

### 0. Ile mam czasu na zwrot?
(odpowiedz, tryb rag)
OCENA: Z

```
Rozumiem to jako pytanie o terminy zwrotów pieniędzy od sprzedającego po zakupie na Allegro. Zgodnie z informacjami [3]:

- przy anulowaniu opłaconego zakupu sprzedający ma 48 godzin na zwrot pieniędzy;
- przy odstąpieniu od umowy zwrot powinien nastąpić niezwłocznie, czyli w ciągu 7 dni kalendarzowych od zmiany statusu przesyłki na Dostarczona, nie później niż 14 dni od momentu przesłania formularza zwrotu towaru;
- przy składaniu reklamacji sprzedający ma na zwrot od 2 do 14 dni kalendarzowych od odebrania przesyłki zwrotnej.

Kontekst nie zawiera informacji o terminach na zwrot towaru przez kupującego.
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/zasady-reklamacji-i-zwrotu-towaru/zwrot-pieniedzy-od-sprzedajacego-WvvzEWZWgc9

### 1. jak zlozyc nowe polecenie zaplaty
(ODMOWA, powod sedzia)
OCENA: X

```
Nie znalazłem tej informacji w bazie pomocy Allegro. Sprawdź bezpośrednio w Centrum Pomocy: https://allegro.pl/pomoc
```

### 2. ile mam czasu na zwrot
(odpowiedz, tryb rag)
OCENA: Z

```
Masz od 1 do 7 dni kalendarzowych na ocenę zwróconego przedmiotu i dokonanie zwrotu wpłaty po odebraniu przesyłki zwrotnej [2].
```
zrodla: https://help.allegro.com/pl/sell/a/jak-zwrocic-wplate-kupujacemu-wwBPbRl5Bfe

### 3. zapomniałem loginu
(odpowiedz, tryb rag)
OCENA: Z

```
Rozumiem to jako pytanie o odzyskanie loginu po jego zapomnieniu. Kontekst [1] i [4] podają ogólną procedurę logowania, ale nie zawiera informacji, jak odzyskać zapomniany login. W materiałach nie ma opisu procedury przywracania loginu ani kontaktu w tym celu — wskazują jedynie na reset hasła przez SMS lub mejl (przy założeniu, że znasz swój adres email). Brak również informacji o tym, co zrobić, gdy nie pamiętasz samego loginu. W związku z tym nie mam w dostępnych źródłach szczegółowej instrukcji przywracania loginu. Aby uzyskać pomoc w tej sprawie, skontaktuj się z obsługą Allegro — [1].
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/logowanie-i-haslo/jak-odzyskac-dostep-do-konta-gdy-nie-mozesz-sie-zalogowac-0KvwX8YAocP, https://allegro.pl/pomoc/dla-kupujacych/logowanie-i-haslo/jak-mozesz-sie-logowac-na-allegro-680LWko8DTv

### 4. czy da się zalogować bez wpisywania hasła
(odpowiedz, tryb rag)
OCENA: Z

```
Na podstawie dostępnego kontekstu, domyślny sposób logowania wymaga podania loginu lub adresu e-mail oraz hasła [3]. Kontekst nie zawiera informacji ani wskazówek dotyczących logowania bez hasła, na przykład przez uwierzytelnianie biometryczne, jednorazowe kody, uwierzytelnianie przez Google lub Facebook bez osobnego hasła Allegro, ani żadnej innej metody pomijającej wpisanie hasła. Dlatego nie da się zalogować bez wpisania hasła zgodnie z opisanymi procedurami.
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/logowanie-i-haslo/jak-mozesz-sie-logowac-na-allegro-680LWko8DTv

### 5. Ile wynosi prowizja od sprzedazy?
(ODMOWA, powod prog_rerank)
OCENA: X

```
Nie znalazłem tej informacji w bazie pomocy Allegro. Sprawdź bezpośrednio w Centrum Pomocy: https://allegro.pl/pomoc
```

### 6. Co zrobic gdy kupujący zalicytował dla żartów?
(ODMOWA, powod prog_rerank)
OCENA: X

```
Nie znalazłem tej informacji w bazie pomocy Allegro. Sprawdź bezpośrednio w Centrum Pomocy: https://allegro.pl/pomoc
```

### 7. Ile wynosi prowizja od sprzedazy na Allegro?
(odpowiedz, tryb rag)
OCENA: Z

```
Nie mogę podać jednej, ogólnej wartości prowizji od sprzedaży na Allegro, ponieważ zależna jest ona od konkretnych warunków oferty.

Zgodnie z [1], wysokość prowizji w usłudze Allegro Pay Business zależy od terminu płatności:
* do 30 dni – prowizja bez opłat,
* do 60 dni – prowizja 4,5%,
* przy płatności w ratach – prowizja 3,08% w skali miesiąca.

Ponadto, zgodnie z [2] i [4], sprzedający sam ustala koszt wysyłki, który jest dodatkowym kosztem obciążającym kupującego, a nie prowizją od sprzedającego.
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/allegro-pay-business-dla-kupujacych/allegro-pay-business-czym-jest-jak-dziala-i-kiedy-skorzystasz-Rd9wa7Eq6sD, https://allegro.pl/pomoc/dla-kupujacych/oplaty-za-sprzedaz-na-allegro-lokalnie/jakie-sa-oplaty-na-allegro-lokalnie-jD47BK7zjU7, https://allegro.pl/pomoc/dla-kupujacych/metody-dostawy/jak-korzystac-z-allegro-inpost-xG71gn3VRuW

### 8. jak długo mam na zwrot towaru
(odpowiedz, tryb rag)
OCENA: Z

```
Na czas zwrotu wpływa przyczyna rezygnacji z zakupu. Jeśli anulujesz opłacony zakup, sprzedający ma 48 godzin na zwrot pieniędzy [1]. Jeśli odstępujesz od umowy, zwrot powinien nastąpić niezwłocznie po otrzymaniu towaru, czyli maksymalnie w ciągu 7 dni kalendarzowych licząc od dnia Dostarczona przesyłki zwrotnej, nie dłużej niż 14 dni od momentu wysłania formularza zwrotu [1]. W przypadku reklamacji sprzedający ma na zwrot od 2 do 14 dni kalendarzowych od odebrania przesyłki [1]. W sytuacji produktu wpisanego na listę towarów niebezpiecznych, sprzedający jest zobowiązany zwrócić pieniądze nawet po upływie 14 dni i mimo używania produktu [4]. Szczegółowy czas zwrotu nadpłaty wynosi zazwyczaj kilka dni roboczych, maksymalnie do 14 dni od powstania nadpłaty [3].
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/zasady-reklamacji-i-zwrotu-towaru/zwrot-pieniedzy-od-sprzedajacego-WvvzEWZWgc9, https://allegro.pl/pomoc/dla-kupujacych/zasady-zwrotow-i-reklamacji/zakupiony-produkt-zostal-wpisany-na-liste-towarow-niebezpiecznych-safety-gate-co-robic-b2zajAPZ7uR, https://allegro.pl/pomoc/dla-kupujacych/allegro-pay/nadplata-z-tytulu-umow-allegro-pay-0A73bn1lvFW

### 9. napisz mi maila o reklamacji wadliwego produktu
(odpowiedz, tryb email)
OCENA: D

```
Szkic wiadomości do sprzedawcy (uzupełnij dane przed wysłaniem):

Temat: Reklamacja wadliwego produktu - zamówienie [numer zamówienia]

Treść:

Dzień dobry,

nawiązując do zakupu dokonanego dnia [data zakupu] w ramach zamówienia o numerze [numer zamówienia], zgłaszam reklamację dotyczącą wadliwego produktu.

Otrzymany przedmiot [nazwa produktu] nie działa prawidłowo/jest uszkodzony/nie spełnia opisanych w ofercie parametrów. Szczegółowy opis problemu: [dokładny opis wady, np. „przestał działać po 3 dniach użytkowania”, „widoczne pęknięcia obudowy”].

W związku z powyższym, w ramach obowiązujących przepisów i regulaminu Allegro, wnoszę o:

- naprawę produktu,
- wymianę na nowy, wolny od wad egzemplarz,
- zwrot środków w wysokości ceny zakupu.

Proszę o informację zwrotną dotyczącą dalszych kroków w procesie reklamacyjnym.

Z poważaniem,
[Twoje imię i nazwisko]
```

### 10. jak zaplacic kartsa
(odpowiedz, tryb rag)
OCENA: D

```
1. Jeśli nie masz zapisanej karty w ustawieniach konta: wybierz opcję karta płatnicza w formularzu dostawy i płatności, wprowadź numer, datę ważności i kod CVV2/CVC2, wybierz „użyj tylko raz" lub „użyj i zapisz na przyszłość", a następnie kliknij [1].
2. Jeśli masz zapisaną jedną kartę płatniczą: w formularzu dostawy i płatności kliknij opcję karta płatnicza, a następnie kliknij.
3. Jeśli masz zapisane kilka kart płatniczych: w formularzu dostawy i płatności wybierz opcję karta płatnicza, a następnie wybierz konkretną kartę i kliknij [1].
4. Pamiętaj, że podczas płatności kartą bank może poprosić o dodatkową weryfikację 3D Secure — podaj kod SMS lub potwierdź płatność w aplikacji banku [1].
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/karta-platnicza-apple-pay-google-pay/jak-zaplacic-karta-za-zakupy-z8DmgWz2wIo

### 11. Produkt, który kupiłem, jest wadliwy. Jak mogę go zareklamować?
(odpowiedz, tryb rag)
OCENA: Z

```
1. Zgłoś reklamację z tytułu towaru niezgodnego z umową. 2. Ustal z kupującym sposób odesłania wadliwego produktu – możesz poprosić o jego zwrot lub pozostawienie u niego. 3. Prześlij zamówiony produkt w taki sposób, jaki ustalicie wspólnie (np. z etykietą zwrotną lub odebrany osobiście na własny koszt). 4. Jako sprzedający poniesiesz koszty naprawy, wymiany oraz koszty transportu (w obie strony). 5. Jeśli w kontekście występują szczególne parametry stanu produktu (np. „Uszkodzony lub na części”), wskazane jest, by kupujący udostępnił produkt w opisanym stanie, abyś mógł ocenić roszczenie zgodnie z opisem z [2].
```
zrodla: https://help.allegro.com/pl/sell/a/czym-jest-parametr-stan-3AdEKV2kaIP

### 12. Chce zwrocic buty, sa za male, przygotuj mi maila do sprzedawcy
(odpowiedz, tryb email)
OCENA: D

```
Szkic wiadomości do sprzedawcy (uzupełnij dane przed wysłaniem):

Temat: Odstąpienie od umowy - zwrot butów z powodu niewłaściwego rozmiaru

Treść:

Szanowni Państwo,

Zgodnie z przysługującym mi prawem do odstąpienia od umowy w ciągu 14 dni od zakupu, chciałbym/chciałabym zwrócić zakupione buty. Powodem zwrotu jest niewłaściwy rozmiar, który uniemożliwia ich użytkowanie.

Numer zamówienia: [numer zamówienia]  
Data zakupu: [data zakupu]  

Proszę o potwierdzenie otrzymania tej wiadomości oraz przesłanie instrukcji dotyczących procedury zwrotu. Zgodnie z informacjami, produkt powinien zostać odesłany w ciągu 14 dni od zgłoszenia zwrotu.

Oczekuję na dalsze kroki, w tym informacje o sposobie wysyłki oraz danych do zwrotu pieniędzy.

Z poważaniem,
[Twoje imię i nazwisko]

[Kupiłem/kupiłam] buty, które okazały się za małe, dlatego odstępuję od umowy i proszę o zwrot środków.
```

### 13. Zapomniałem hasła do konta
(odpowiedz, tryb rag)
OCENA: D

```
Rozumiem to jako pytanie o procedurę resetowania hasła do konta Allegro, gdy zostało ono zapomniane. Aby zresetować hasło, postępuj zgodnie z instrukcją: [1] kliknij na stronie logowania opcję „Odzyskaj hasło", [1] wpisz adres e-mail lub login używany na Allegro, [1] wybierz metodę odzyskania przez SMS (wymagane jest podanie numeru telefonu powiązanego z kontem), [1] postępuj zgodnie z instrukcjami wyświetlanymi na ekranie, aż otrzymasz jednorazowy kod i będziesz mógł ustawić nowe hasło. Pamiętaj, że aby móc resetować hasło przez SMS, konto musi być powiązane z adresem e-mail z dozwolonej listy oraz musisz mieć włączone dwustopniowe logowanie jako dodatkowe zabezpieczenie. Jeśli nie pamiętasz adresu e-mail lub metoda przez SMS nie działa, skontaktuj się z obsługą Allegro [1].
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/logowanie-i-haslo/jak-odzyskac-dostep-do-konta-gdy-nie-mozesz-sie-zalogowac-0KvwX8YAocP

### 14. Ile mam dni na zwrot towaru?
(odpowiedz, tryb rag)
OCENA: Z

```
Rozumiem to jako pytanie o ogólny czas na zwrot towaru. Zależy to od powodu:
- przy anulowaniu opłaconego zakupu sprzedający zwraca pieniądze w ciągu 48 godzin [2];
- przy odstąpieniu od umowy zwrot następuje niezwłocznie, najpóźniej w ciągu 7 dni kalendarzowych po dostarczeniu przesyłki zwrotnej, a łącznie nie dłużej niż 14 dni od wysłania formularza zwrotu [2];
- przy reklamacji sprzedający zwraca pieniądze w ciągu od 2 do 14 dni kalendarzowych od odebrania przesyłki zwrotnej [2].
Nie podano ogólnego limitu dni na zwrot bez wskazania konkretnego powodu.
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/zasady-reklamacji-i-zwrotu-towaru/zwrot-pieniedzy-od-sprzedajacego-WvvzEWZWgc9

### 15. Przygotuj proszę szkic maila reklamacyjnego do sprzedawcy.
(odpowiedz, tryb email)
OCENA: D

```
Szkic wiadomości do sprzedawcy (uzupełnij dane przed wysłaniem):

Temat: Zgłoszenie reklamacji - niezgodność produktu z opisem

Treść:

Dzień dobry,

W nawiązaniu do zamówienia o numerze [numer zamówienia], zakupionego dnia [data zakupu], chciałbym/chciałabym zgłosić niezgodność produktu z opisem. Otrzymany przedmiot [krótki opis problemu, np. „nie działa zgodnie z deklaracją” lub „posiada wady wizualne”] nie spełnia oczekiwań wynikających z oferty.

W związku z powyższym, zgodnie z obowiązującymi zasadami, proszę o:
- naprawę produktu,
- wymianę na nowy, zgodny z opisem egzemplarz,
- zwrot środków w ramach reklamacji.

Proszę o informację zwrotną w ciągu 24 godzin od otrzymania tej wiadomości. W przypadku braku odpowiedzi, skorzystam z dalszych kroków procedury reklamacyjnej, w tym ewentualnego wsparcia ze strony Allegro.

Z poważaniem,
[Twoje imię i nazwisko]
```

### 16. Chce napisac mail bo produkt jest uszkodzony
(odpowiedz, tryb ogolna)
OCENA: Z

```
Napisz wiadomość do sprzedawcy przez Allegro – w zakładce „Wiadomości” lub „Kontakt” w aukcji – i krótko opisz problem: co jest uszkodzone, kiedy to zauważyłeś i jak chcesz rozwiązać sytuację (np. zwrot, wymiana, naprawa). Dołącz zdjęcia uszkodzenia, jeśli to możliwe.
```

### 17. Chcę złożyć reklamację, produkt przyszedł uszkodzony
(odpowiedz, tryb rag)
OCENA: D

```
Rozumiem to jako reklamację uszkodzonego produktu po jego dostarczeniu. Możesz to zrobić w zakładce Moje zakupy, klikając w szczegółach konkretnego zakupu (zgodnie z [1]). W formularzu wybierz produkt, opisz uszkodzenia i dołącz zdjęcia (zgodnie z [2]), podając wszystkie wymagane dane, w tym numer przesyłki i opis szkody. Jeśli produkt pochodzi z Allegro Lokalnie, kieruj reklamację bezpośrednio do sprzedającego (zgodnie z [3]), możesz żądać naprawy, wymiany, obniżki ceny lub odstąpienia od umowy. Jeśli otrzymałeś niewłaściwy produkt lub paczkę z błędem adresowym, zgłoś to poprzez Allegro, a platforma skontaktuje się z przewoźnikiem (zgodnie z [4]), ale w przypadku uszkodzenia samego towaru procedura reklamacji przebiega poprzez formularz w zakupach (zgodnie z [1] i [2]).
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/zasady-zwrotow-i-reklamacji/jak-zlozyc-reklamacje-na-towar-kupiony-na-allegro-yP0dwDPVEHr, https://allegro.pl/pomoc/dla-kupujacych/metody-dostawy/program-dostaw-allegro-delivery-informacje-dla-kupujacych-Bvw1bwrMmIz, https://allegro.pl/pomoc/dla-kupujacych/zakupy-na-allegro-lokalnie/produkt-kupiony-na-allegro-lokalnie-nie-dotarl-lub-jest-niezgodny-z-opisem-co-moge-zrobic-K6qzy67wvhl, https://allegro.pl/pomoc/dla-kupujacych/zasady-zwrotow-i-reklamacji/dotarl-do-mnie-zly-produkt-lub-paczka-co-zrobic-MREb1kEG4sw

### 18. chce zwrocic zamowione buty, nie pasuja, jak to zrobic
(odpowiedz, tryb ogolna)
OCENA: Z

```
Aby zwrócić buty, które nie pasują, najpierw sprawdź regulamin sklepu, w którym je kupiłeś – znajdziesz tam informacje o czasie i warunkach zwrotu. Zazwyczaj musisz zalogować się na swoje konto, przejść do historii zamówień, wybrać dane zamówienie i znaleźć opcję „zwrot towaru”. Przygotuj buty zgodnie z instrukcją – najczęściej muszą być w oryginalnym opakowaniu, nienoszone i z wszystkimi akcesoriami.
```

### 19. Jak długo mam na zwrot towaru?
(odpowiedz, tryb rag)
OCENA: Z

```
Rozumiem to jako pytanie o czas, w którym musisz dokonać zwrotu towaru.

Z kontekstu wynika, że terminy zależą od sytuacji:
- Jeśli anulujesz opłacony zakup – sprzedający powinien zwrócić pieniądze w ciągu 48 godzin [2].
- Przy odstąpieniu od umowy – sprzedający powinien zwrócić pieniądze niezwłocznie po otrzymaniu i sprawdzeniu towaru – w ciągu 7 dni kalendarzowych od dnia zmiany statusu przesyłki zwrotnej na Dostarczona, nie dłużej niż 14 dni od momentu przesłania przez Ciebie Formularza zwrotu towaru [2].
- Przy składaniu reklamacji – sprzedający ma na zwrot pieniędzy od 2 do 14 dni kalendarzowych od momentu odebrania przesyłki zwrotnej [2].

Kontekst nie zawiera ogólnego terminu na zwrot towaru; informacje te są zależne od konkretnego powodu i typu zwrotu.
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/zasady-reklamacji-i-zwrotu-towaru/zwrot-pieniedzy-od-sprzedajacego-WvvzEWZWgc9

### 20. jak kupic i zaplacic za przedmiot w ramach aukcji allegro dla wosp
(odpowiedz, tryb rag)
OCENA: D

```
Aby kupić i zapłacić za przedmiot wystawiony w ramach Aukcji Allegro dla WOŚP, postępuj tak jak w przypadku standardowych aukcji na Allegro. Możesz to zrobić na trzy sposoby:

1. Kliknij opcję **kup teraz** – dokonasz płatności z góry operatorem PayU.
2. Dodaj przedmiot do **koszyka** – zapłacisz z góry tym samym sposobem, także gdy łączysz go z innymi ofertami.
3. Wygrywając **licytację** – zapłata również nastąpi z góry operatorem PayU.

Pamiętaj, że za przedmioty w ramach Aukcji dla WOŚP nie możesz zapłacić **za pobraniem**, **przelewem tradycyjnym**, ani **ratami** czy **Allegro Pay** – płatność musi być dokonana z góry.

Kwota wpłacona za przedmiot oraz ewentualna dodatkowa darowizna trafi bezpośrednio na konto Fundacji Wielkiej Orkiestry Świątecznej Pomocy, a sprzedający otrzymuje pieniądze tylko na pokrycie kosztów dostawy. [1]
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/allegro-dla-wosp/jak-kupic-i-zaplacic-za-przedmiot-w-ramach-aukcji-allegro-dla-wosp-5VPP5VeEwHB

### 21. Jak usunąć konto na allegro
(odpowiedz, tryb rag)
OCENA: D

```
Aby usunąć konto na Allegro, prześlij wypowiedzenie umowy, np. wiadomością e-mail lub za pośrednictwem formularza kontaktu z Allegro. Po złożeniu wypowiedzenia konto zostanie usunięte po upływie 30 dni, o ile w tym czasie nie dokonasz zakupu ani wystawienia przedmiotu na Allegro lub Allegro Lokalnie. Po usunięciu konta możesz założyć nowe. [1]
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/dane-i-ustawienia-konta/jak-zamknac-konto-na-allegro-PDa207G8aun

### 22. jak wystawić przedmiot na sprzedaż
(odpowiedz, tryb rag)
OCENA: Z

```
1. Jeśli masz konto zwykłe lub niezweryfikowane konto firmowe, wybierz opcję Możesz też wystawić przez dotychczasowy formularz [1].
2. W zakładce Mój asortyment zaznacz odpowiednią ofertę lub kilka ofert, a następnie wybierz opcję i na rozwiniętej liście kliknij [1].
3. Jeśli chcesz wprowadzić zmiany w ofercie przed ponownym wystawieniem, kliknij opcję (trzy pionowe kropki po prawej stronie oferty), a następnie z rozwiniętej listy wybierz (dla ofert kup teraz oraz ogłoszeń) lub (dla licytacji) [1].
4. Jeśli korzystasz z One Fulfillment by Allegro, wybierz Magazyn Allegro obsługuje za mnie, aby utworzyć ofertę [2].
5. W przypadku problemów z wystawianiem sprawdź komunikaty — np. „Ten produkt możesz sprzedawać tylko samodzielnie" [2] lub „Nie mamy jeszcze tego produktu" [2] — i postępuj zgodnie z wyświetloną instrukcją.
```
zrodla: https://help.allegro.com/pl/sell/a/jak-wystawic-przedmiot-na-sprzedaz-oAd1MRwERFg, https://help.allegro.com/pl/sell/a/jak-wystawic-i-edytowac-oferte-w-one-fulfillment-by-allegro-7G6ElRyeLiZ

### 23. Jak zarejestrować konto firmowe?
(odpowiedz, tryb rag)
OCENA: D

```
Zarejestruj konto firmowe w kilku prostych krokach: przejdź na stronę rejestracji, uzupełnij wszystkie pola formularza korzystając z podpowiedzi, kliknij – system pobierze dane z GUS, CEIDG lub VIES; jeśli nie będzie to możliwe, samodzielnie uzupełnij dane firmy. NIP musi być zgodny z adresem siedziby. Na końcu formularza kliknij; na podany adres e-mail otrzymasz wiadomość do potwierdzenia rejestracji [1].
```
zrodla: https://help.allegro.com/pl/sell/a/jak-zarejestrowac-konto-firmowe-BvdR471wbT3

### 24. Jak zgłosić brak dostawy?
(odpowiedz, tryb rag)
OCENA: D

```
Rozumiem to jako pytanie o zgłoszenie problemu z brakiem paczki. Od 3 sierpnia zgłaszasz problemy transakcyjne tak samo, jak dotychczas: wchodzisz w zakładkę Moje zakupy, rozwiń szczegóły zakupu i wybierasz „zgłoś reklamację lub problem". Twoje zgłoszenie trafi do odpowiedniej sekcji w zależności od rodzaju problemu – do Dyskusji, jeśli chodzi o przesyłkę (np. paczka się nie pojawiła), lub do Centrum Wiadomości, jeśli problem dotyczy samego produktu lub zwrotu. [1]
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/problemy-transakcyjne/jak-od-3-sierpnia-zglaszac-problemy-z-zakupami-od-sprzedajacych-z-kont-zwyklych-prywatnych-1nGAz9lDgT5

### 25. jak zmienic haslo do konta
(odpowiedz, tryb rag)
OCENA: D

```
Aby zmienić hasło do konta Allegro, należy przejść do zakładki „Logowanie i hasło" [1], kliknąć „Zmień hasło", wpisać aktualne hasło, nowe hasło oraz jego potwierdzenie, a następnie kliknąć [1]. Po zmianie hasła nastąpi wylogowanie ze wszystkich urządzeń.
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/logowanie-i-haslo/jak-zmienic-haslo-na-allegro-B826XYkbXsA

### 26. jak zmienic haslo na allegro
(odpowiedz, tryb rag)
OCENA: D

```
Aby zmienić hasło na Allegro, wykonaj następujące kroki opisane w [1]:

1. Przejdź do zakładki „Logowanie i hasło".
2. Kliknij przycisk „Zmień hasło".
3. W pierwszym polu wpisz aktualne hasło.
4. W kolejnym polu wpisz nowe hasło.
5. W ostatnim polu wpisz to samo nowe hasło jeszcze raz, aby je potwierdzić i sprawdzić poprawność.
6. Kliknij przycisk „Zmień".

Po zmianie hasła zostaniesz wylogowany z wszystkich urządzeń dla bezpieczeństwa, a ponowne zalogowanie będzie wymagało użycia nowego hasła.
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/logowanie-i-haslo/jak-zmienic-haslo-na-allegro-B826XYkbXsA

### 27. Jak zwrocic towar kupiony w ramach allegro smart
(odpowiedz, tryb rag)
OCENA: D

```
Rozumiem to jako pytanie o procedurę darmowego zwrotu towaru zakupionego w ramach Allegro Smart!. 
1. Sprawdź, czy możesz zwrócić produkt w zakładce Moje zakupy (zgodnie z [1]), aby upewnić się, że sprzedający dopuszcza zwroty i nie minął Ci 14‑dniowy (lub wydłużony) termin odstąpienia od umowy. 
2. Przejdź do zakładki Moje zakupy i kliknij szczegóły zakupu, a następnie przycisk (zgodnie z [1]). 
3. Wskaż produkty do zwrotu, zaznacz odpowiedni powód zwrotu dla każdego z nich i, jeśli zamówienie zawierało opcję dostawy przy odbiorze, podaj dane do zwrotu pieniędzy (zgodnie z [1]). 
4. Jeśli reklamacja dotyczy przesyłki w ramach Allegro Smart! i termin zwrotu jeszcze nie minął – w formularzu zobaczysz opcję „Bezpłatny zwrot w ramach Allegro Smart!” – wybierz ją, aby samodzielnie wygenerować bezpłatną etykietę do odesłania (zgodnie z [2]). 
5. Jeśli sprzedający wymaga odesłania produktu (np. przy reklamacji niezgodności) – ustal z nim metodę wysyłki i upewnij się, że koszt przesyłki pokrywa sprzedający (zgodnie z [2]). 
6. W razie problemów skorzystaj z Allegro Ochrony Kupujących – możesz otrzymać zwrot do 20 000 zł (zgodnie z [4]).
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/zakupy-i-zwroty-z-allegro-smart-/jak-zwrocic-produkty-kupione-w-ramach-allegro-smart-dykrmbo5qTz, https://allegro.pl/pomoc/dla-kupujacych/zasady-zwrotow-i-reklamacji/jak-zwrocic-zakup-i-odeslac-produkt-do-sprzedajacego-GDeq5VeKRHD, https://allegro.pl/pomoc/dla-kupujacych/allegro-ochrona-kupujacych/jak-dziala-allegro-ochrona-kupujacych-qzdAg2Klbsl

### 28. Napisz mi maila do sprzedawcy w sprawie braku dostawy paczki
(odpowiedz, tryb email)
OCENA: Z

```
Szkic wiadomości do sprzedawcy (uzupełnij dane przed wysłaniem):

Temat: Brak dostawy zamówienia [numer zamówienia]

Witam,

W odniesieniu do zamówienia o numerze [numer zamówienia], zakupionego dnia [data zakupu], chciałbym zgłosić brak dostawy. Pomimo upływu 180 dni od daty zakupu, przesyłka nie dotarła do mnie.

W związku z powyższym, proszę o wyjaśnienie sytuacji oraz podjęcie odpowiednich kroków w celu rozwiązania problemu. Oczekuję pełnego zwrotu środków lub informacji o statusie zamówienia.

Proszę o odpowiedź w ciągu 24 godzin w dni robocze. W przypadku braku reakcji, będę zmuszony skorzystać z pomocy Allegro.

Z poważaniem,
[Imię i nazwisko]
```

### 29. Napisz mi maila o zwrot produktu
(odpowiedz, tryb email)
OCENA: D

```
Szkic wiadomości do sprzedawcy (uzupełnij dane przed wysłaniem):

Temat: [Odstąpienie od umowy - zwrot produktu]

Treść:

Dzień dobry,

Zgodnie z przysługującym mi prawem do odstąpienia od umowy w ciągu 14 dni od daty zakupu, chciałbym/chciałabym zwrócić produkt zakupiony u Państwa. Numer zamówienia: [numer zamówienia], data zakupu: [data zakupu].

Powodem zwrotu jest [tutaj należy wpisać konkretny powód zwrotu, np. „niezgodność z opisem” lub „zmiana decyzji”]. 

Proszę o potwierdzenie otrzymania tej wiadomości oraz instrukcje dotyczące dalszych kroków zwrotu. Zgodnie z informacjami, mam 14 dni na odesłanie produktu od momentu przesłania formularza zwrotu.

Oczekuję na Państwa odpowiedź.

Z poważaniem,
[Imię i nazwisko kupującego]

---

Uwaga: W powyższym szkicu należy uzupełnić placeholdery ([numer zamówienia], [data zakupu], [konkretny powód zwrotu]) oraz podpisać się imieniem i nazwiskiem kupującego. Treść powinna być dostosowana do rzeczywistej sytuacji i zgodna z przebiegiem rozmowy.
```

### 30. Napisz mi maila w sprawie reklamacji uszkodzonego produktu
(odpowiedz, tryb email)
OCENA: D

```
Szkic wiadomości do sprzedawcy (uzupełnij dane przed wysłaniem):

Temat: Reklamacja uszkodzonego produktu - zamówienie [numer zamówienia]

Treść:

Szanowny Sprzedawco,

W nawiązaniu do zakupu dokonanego dnia [data zakupu] (zamówienie [numer zamówienia]), zgłaszam problem z otrzymanym produktem. Po odbiorze przesyłki stwierdziłem/stwierdziłam, że [nazwa produktu] jest uszkodzony/uszkodzona. Uszkodzenie polega na [krótki opis uszkodzenia, np. „pękniętej obudowie”, „brakującym elemencie”].

W związku z powyższym, w ramach obowiązującej procedury reklamacyjnej, proszę o:

1. Naprawę produktu lub
2. Wymianę na nowy, nieuszkodzony egzemplarz, lub
3. Zwrot pieniędzy w wysokości ceny zakupu.

Do niniejszego zgłoszenia załączam zdjęcia dokumentujące uszkodzenie.

Proszę o informację zwrotną dotyczącą dalszych kroków w procesie reklamacyjnym.

Z poważaniem,
[Twoje imię i nazwisko]

---

Uwagi:
- Zastąp placeholdery rzeczywistymi danymi (np. [numer zamówienia], [data zakupu], [nazwa produktu]).
- Jeśli produkt był zakupiony przez Allegro Lokalnie, upewnij się, że minęła godzina od zaksięgowania wpłaty.
- W przypadku braku odpowiedzi od sprzedawcy w ciągu 24 godzin, skorzystaj z opcji „[poproś Allegro o pomoc]” w Dyskusji.
```

### 31. Napisz mi maila w sprawie zwrotu produktu
(odpowiedz, tryb email)
OCENA: D

```
Szkic wiadomości do sprzedawcy (uzupełnij dane przed wysłaniem):

Temat: [Odstąpienie od umowy - zwrot produktu]

Treść:

Dzień dobry,

Zgodnie z przysługującym mi prawem do odstąpienia od umowy w ciągu 14 dni od otrzymania produktu, informuję o mojej decyzji dotyczącej zwrotu następującego produktu:

[Nazwa produktu]
Numer zamówienia: [numer zamówienia]
Data zakupu: [data zakupu]

Powód zwrotu: [wybrany powód, np. niezgodność z opisem, uszkodzenie, zmiana zdania]

Proszę o wskazanie dokładnej procedury zwrotu, w tym adresu do wysyłki oraz ewentualnych dodatkowych kroków. Zgodnie z informacjami, zamówienie zostało złożone w ramach Allegro Smart!, więc chciał[a]bym skorzystać z darmowego zwrotu.

Oczekuję na potwierdzenie otrzymania tej wiadomości oraz instrukcje dotyczące dalszych działań.

Z poważaniem,
[Imię i nazwisko kupującego]

---

Uwagi do uzupełnienia przed wysłaniem:
- Wstaw rzeczywistą nazwę produktu, numer zamówienia i datę zakupu.
- Wybierz odpowiedni powód zwrotu z dostępnych opcji.
- Jeśli nie dotyczy Allegro Smart!, zmodyfikuj odpowiednio fragment o darmowym zwrocie.
```

### 32. napisz mi maila, bo sprzedawca nie odpowiada od tygodnia
(odpowiedz, tryb email)
OCENA: D

```
Szkic wiadomości do Allegro (uzupełnij dane przed wysłaniem):

Temat: Prośba o interwencję w nierozwiązanej dyskusji ze sprzedającym

Treść:

Szanowni Państwo,

Zwracam się z prośbą o interwencję w związku z nierozwiązaną dyskusją dotyczącą zamówienia numer [uzupełnij numer zamówienia], zakupionego dnia [uzupełnij datę zakupu].

Sprzedawca nie odpowiada na moje wiadomości od tygodnia, mimo że zgodnie z zasadami Allegro powinien odnieść się do zgłoszenia w ciągu 24 godzin. Problem dotyczy [krótki opis problemu, np. „braku dostawy produktu”].

Próbowałem/am rozwiązać sprawę samodzielnie, ale sprzedawca nie podjął żadnych działań. W związku z tym, zgodnie z informacjami z Centrum Pomocy Allegro, proszę o włączenie się do dyskusji i pomoc w rozwiązaniu sporu.

Proszę o sprawdzenie, czy sprzedawca przestrzega regulaminu Allegro, oraz o podjęcie odpowiednich kroków w celu zapewnienia realizacji mojego zamówienia lub zwrotu środków.

Z góry dziękuję za pomoc.

Z poważaniem
[Twoje imię i nazwisko]

Uwaga: Przed wysłaniem wiadomości uzupełnij brakujące dane (numer zamówienia, datę zakupu) oraz dostosuj opis problemu do konkretnej sytuacji.
```

### 33. napisz mi wiadomość o zwrocie produktu
(odpowiedz, tryb email)
OCENA: D

```
Szkic wiadomości do sprzedawcy (uzupełnij dane przed wysłaniem):

Temat: [Odstąpienie od umowy - zwrot produktu]

Treść:

Dzień dobry,

Zgodnie z przysługującym mi prawem do odstąpienia od umowy w ciągu 14 dni od daty zakupu, chciałbym/chciałabym zwrócić produkt zakupiony u Państwa dnia [data zakupu]. Numer zamówienia: [numer zamówienia].

Powodem zwrotu jest [krótki opis powodu zwrotu, np. „niezgodność z oczekiwaniami”].

Proszę o potwierdzenie możliwości zwrotu oraz instrukcję dotyczącą wysyłki zwracanego produktu. Zgodnie z informacjami, zwrot powinien nastąpić w ciągu 14 dni od daty przesłania formularza zwrotu.

Oczekuję na Państwa odpowiedź w sprawie dalszych kroków.

Z poważaniem,
[Imię i nazwisko]

[Uwaga: Wszystkie placeholdery ([data zakupu], [numer zamówienia], [powód zwrotu]) należy uzupełnić przed wysłaniem wiadomości.]
```

### 34. Napisz za mnie wiadomość do sprzedawcy w tej sprawie
(ODMOWA, powod mail_doprecyzuj)
OCENA: X

```
Nie jestem pewien, o jaki rodzaj wiadomości chodzi: reklamację uszkodzonego towaru, zwrot, prośbę o fakturę czy zgłoszenie braku odpowiedzi sprzedawcy? Napisz proszę dokładniej.
```

### 35. paczka nie przyszła, co mam zrobić
(odpowiedz, tryb rag)
OCENA: Z

```
Rozumiem to jako pytanie o działanie, gdy paczka nie dotarła do Ciebie pomimo prawidłowo złożonego zamówienia. Na podstawie kontekstu [2] i [2] najpierw sprawdź, czy powiadomienie o problemie nie zostało wysłane do Ciebie:

1. Wejdź w zakładkę „Moje przesyłki" lub „Moje zakupy" w swoim koncie Allegro, aby zobaczyć aktualny status zamówienia i dowiedzieć się o ewentualnych opóźnieniach.
2. Sprawdź swoją skrzynkę mejlową oraz powiadomienia w aplikacji Allegro – mogą tam być informacje o zmianie terminu dostawy lub problemach z przesyłką.
3. Jeśli nie widzisz informacji w tych miejscach (co może wynikać z błędów w danych dostawy lub ukrycia zamówienia – patrz [2]), skontaktuj się z obsługą klienta Allegro, aby zgłosić brak paczki i ustalić dalsze kroki (np. potwierdzenie braku doręczenia przez przewoźnika).

Kontekst nie zawiera informacji o tym, co zrobić, gdy paczka nie dotarła wcale (brak jakiegokolwiek powiadomienia lub statusu), a nie tylko jest opóźniona – w takim przypadku najpewniejszym krokiem jest zgłoszenie problemu do Allegro.
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/metody-dostawy/gdzie-sprawdzisz-numer-i-status-swojej-przesylki-LvP7agrzOhw

### 36. produkt ktory kupilem jest uszkodzony, co mam zrobic
(odpowiedz, tryb rag)
OCENA: D

```
Rozumiem to jako: chcesz wiedzieć, co zrobić, gdy zakupiony produkt jest uszkodzony.

1. Skontaktuj się ze sprzedającym – to pierwszy krok, aby ustalić, jak najlepiej rozwiązać problem (np. zwrot, reklamacja, wymiana). Dane kontaktowe znajdziesz w powiadomieniu o zakupie [2].

2. Przygotuj paczkę do odesłania – jeśli zdecydujesz się na zwrot, zapakuj produkt tak, aby nie został dodatkowo uszkodzony w transporcie [1]. Użyj odpowiedniego opakowania i zabezpiecz zawartość.

3. Oderwij poprzednią etykietę nadawczą, jeśli jest na opakowaniu – przed wysyłką koniecznie usuń ją, aby uniknąć problemów z identyfikacją przesyłki [1].

4. Dołącz nową etykietę lub kod zwrotu – zależnie od wybranej metody dostawy, na paczce musi być widoczny aktualny dokument zwrotny [1].

5. Jeśli przewoźnik uszkodzi paczkę w transporcie, mimo prawidłowego opakowania, możesz potrzebować dokumentu z wynikiem reklamacji do przewoźnika [3]. Spisz protokół szkody z kurierem, jeśli opakowanie było uszkodzone przy dostawie.

6. Jeśli produkt był wadliwy od początku i jest niezgodny z opisem, możesz złożyć reklamację u sprzedającego [2] lub skorzystać z ochrony Allegro, jeśli taką miałeś wykupioną.
```
zrodla: https://allegro.pl/pomoc/dla-kupujacych/zakupy-na-allegro-lokalnie/produkt-kupiony-na-allegro-lokalnie-nie-dotarl-lub-jest-niezgodny-z-opisem-co-moge-zrobic-K6qzy67wvhl, https://allegro.pl/pomoc/dla-kupujacych/zasady-zwrotow-i-reklamacji/jak-zwrocic-zakup-i-odeslac-produkt-do-sprzedajacego-GDeq5VeKRHD, https://allegro.pl/pomoc/dla-kupujacych/allegro-ochrona-kupujacych/jak-dziala-allegro-ochrona-kupujacych-qzdAg2Klbsl

### 37. Przygotuj proszę szkic wiadomości o zwrocie produktu.
(odpowiedz, tryb email)
OCENA: D

```
Szkic wiadomości do sprzedawcy (uzupełnij dane przed wysłaniem):

Temat: [Odstąpienie od umowy i zwrot produktu - nr zamówienia: [numer zamówienia], data zakupu: [data zakupu]]

Szanowny Sprzedawco,

Niniejszym informuję, że korzystam z przysługującego mi prawa do odstąpienia od umowy zawartej na odległość w dniu [data zakupu] (zgodnie z obowiązującymi przepisami, w terminie do 14 dni od otrzymania produktu). 

Powód zwrotu: [powód zwrotu, np. niezgodność z opisem, wada produktu, zmiana decyzji].

Proszę o wskazanie sposobu odesłania produktu oraz potwierdzenie adresu do zwrotu. Zobowiązuję się do odesłania produktu w stanie niezmienionym, w ciągu 14 dni od daty przesłania niniejszej wiadomości.

Oczekuję również zwrotu środków na konto, z którego dokonano płatności.

W załączeniu przesyłam wypełniony formularz odstąpienia od umowy (jeśli jest wymagany).

Proszę o potwierdzenie otrzymania tej wiadomości oraz instrukcji dotyczących zwrotu.

Z poważaniem,
[Twoje imię i nazwisko]

[Uwaga: Wszystkie placeholdery (np. [numer zamówienia], [data zakupu], [powód zwrotu]) należy uzupełnić przed wysłaniem wiadomości.]
```
