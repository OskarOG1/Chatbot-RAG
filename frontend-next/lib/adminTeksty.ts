import { createContext, useContext } from 'react';
import type { Lang } from './chat';
import { BladZapytania } from './admin';

export type Zakladka = 'przeglad' | 'jakosc' | 'pytania' | 'oceny' | 'kolejka' | 'eksport';

export interface TekstyAdmina {
  tytul: string;
  daneOdDo: (od: string, doDnia: string) => string;
  brakDanychWZakresie: string;
  odswiezono: string;
  wrocDoCzatu: string;
  resetuj: string;
  wylogujToken: string;
  tokenPlaceholder: string;
  odblokuj: string;
  tokenPodpowiedz: string;
  wpiszToken: string;
  zmienMotyw: string;
  jezykInterfejsu: string;
  okres: string;
  jezyk: string;
  rola: string;
  okresy: { dni7: string; dni30: string; dni90: string; wszystko: string };
  jezyki: { wszystkie: string; pl: string; en: string };
  strony: { wszyscy: string; kupujacy: string; sprzedajacy: string };
  zakladki: Record<Zakladka, string>;
  sprobujPonownie: string;
  wczytuje: string;
  brakDanychKropka: string;
  bladStatystyk: string;
  bladOcen: string;
  resetZarchiwizowane: string;
  resetBezArchiwum: string;
  bladResetu: string;
  bladTokenu: string;
  bladLimitu: string;
  zadanePytania: string;
  roznychPytan: (n: number) => string;
  udzieloneOdpowiedzi: string;
  wszystkichPytan: (procent: string) => string;
  bezOdpowiedzi: string;
  brakDanych: string;
  typowyCzas: string;
  typowyCzasPodpis: string;
  bezOdpowiedziWyjasnienie: string;
  pozostaleLiczby: string;
  kciukiWGore: string;
  brakOcen: string;
  ocenPodpis: (razem: number, pokrycie: string) => string;
  zPamieci: string;
  bezPamieci: (czas: string) => string;
  kosztModelu: string;
  wyslaneWiadomosci: string;
  probWysylki: (n: number) => string;
  pytaniaDzien: string;
  tematyPytan: string;
  ktoPyta: string;
  ktoPytaOpis: (kupujacy: number, sprzedajacy: number) => string;
  jakSzybko: string;
  pytaniaBezOdpowiedzi: string;
  najczestszaPrzyczyna: string;
  brakOdmow: string;
  przyczynaPodpis: (ile: number, udzial: string) => string;
  dlaczegoNie: string;
  dlaczegoNieOpis: string;
  kazdePytanie: string;
  najczestszePytania: string;
  pytaniaLicznik: (unikalne: number, widoczne: number) => string;
  pokazNajczestsze: string;
  pokazWszystkie: (n: number) => string;
  ocenioneOdpowiedzi: string;
  ocenLicznik: (razem: number, negatywne: number) => string;
  ladujeOceny: string;
  brakOcenOpis: string;
  kolumnyOcen: string[];
  kciukGora: string;
  kciukDol: string;
  resetPytanie: string;
  resetOpis: string;
  resetBezTokenu: string;
  anuluj: string;
  resetuje: string;
  takResetuj: string;
  zwin: string;
  rozwin: string;
  zaMaloDniTrend: string;
  zaMaloDniKoszt: string;
  seriaPytania: string;
  seriaBezOdpowiedzi: string;
  seriaLiczba: string;
  seriaKoszt: string;
  eksportTytul: string;
  eksportOpis: string;
  zaznaczWszystko: string;
  odznaczWszystko: string;
  eksportBezTokenu: string;
  bladPliku: string;
  pobieram: string;
  pobierzPlik: string;
  dniTygodnia: string[];
  miesiace: string[];
  zakresEtykieta: (od: string, doDnia: string) => string;
  wybraneDni: string;
  poprzedniMiesiac: string;
  nastepnyMiesiac: string;
  kliknijPoczatek: string;
  kliknijKoniec: string;
  wybrano: (od: string, doDnia: string) => string;
  wyczysc: string;
  pokazZakres: string;
  statusyKolejki: { nowe: string; odpowiedziano: string; odrzucone: string; wszystkie: string };
  brak: string;
  bladKolejki: string;
  kolejkaTytul: string;
  kolejkaWstep: string;
  tokenMaly: string;
  pokazKolejke: string;
  kolejkaLicznik: (otwarte: number, razem: number) => string;
  ladujeKolejke: string;
  brakZgloszen: string;
  pustaOdpowiedz: string;
  wyslanoNumer: (numer: string) => string;
  odrzucono: string;
  bladZapisu: string;
  brakTresciPytania: string;
  brakPowodu: string;
  brakTematu: string;
  dopasowanie: (wartosc: string) => string;
  oparcie: (wartosc: string) => string;
  numerZgloszenia: string;
  zgloszono: string;
  adresZwrotny: string;
  najlepszyArtykul: string;
  coZawiodlo: string;
  poprzedniaOdpowiedz: string;
  odpowiedzPlaceholder: string;
  bezEtykiety: string;
  zapisuje: string;
  wyslijOdpowiedz: string;
  odrzuc: string;
  sekcje: Record<string, string>;
  nazwyStron: Record<string, string>;
  powody: Record<string, string>;
  kolumny: Record<string, string>;
  diagnozy: Record<string, string>;
  lekarstwa: Record<string, string>;
  statusy: Record<string, string>;
  etykietyZgloszen: Record<string, string>;
  przedzialyLatencji: Record<string, string>;
}

export const TEKSTY_ADMINA: Record<Lang, TekstyAdmina> = {
  pl: {
    tytul: 'Panel statystyk',
    daneOdDo: (od, doDnia) => `Dane od ${od} do ${doDnia}`,
    brakDanychWZakresie: 'Brak danych w wybranym zakresie',
    odswiezono: 'odświeżono o',
    wrocDoCzatu: 'Wróć do czatu',
    resetuj: 'Resetuj statystyki',
    wylogujToken: 'Wyloguj token',
    tokenPlaceholder: 'Token administratora',
    odblokuj: 'Odblokuj',
    tokenPodpowiedz: 'Bez tokenu panel nie pokazuje treści pytań ani odpowiedzi',
    wpiszToken: 'Wpisz token',
    zmienMotyw: 'Zmień motyw',
    jezykInterfejsu: 'Język interfejsu',
    okres: 'Okres',
    jezyk: 'Język',
    rola: 'Rola',
    okresy: { dni7: 'Ostatnie 7 dni', dni30: '30 dni', dni90: '90 dni', wszystko: 'Wszystko' },
    jezyki: { wszystkie: 'Wszystkie', pl: 'Polski', en: 'Angielski' },
    strony: { wszyscy: 'Wszyscy', kupujacy: 'Kupujący', sprzedajacy: 'Sprzedający' },
    zakladki: {
      przeglad: 'Przegląd',
      jakosc: 'Jakość i odmowy',
      pytania: 'Pytania',
      oceny: 'Oceny',
      kolejka: 'Kolejka',
      eksport: 'Eksport',
    },
    sprobujPonownie: 'Spróbuj ponownie',
    wczytuje: 'Wczytuję dane...',
    brakDanychKropka: 'Brak danych w wybranym zakresie.',
    bladStatystyk: 'Nie udało się pobrać statystyk',
    bladOcen: 'Nie udało się pobrać ocen',
    resetZarchiwizowane: 'Statystyki zresetowane, poprzednie dane zarchiwizowane na serwerze',
    resetBezArchiwum: 'Statystyki zresetowane, nie było czego archiwizować',
    bladResetu: 'Nie udało się zresetować statystyk',
    bladTokenu: 'Brak uprawnień: sprawdź token administratora',
    bladLimitu: 'Za dużo zapytań naraz, spróbuj za chwilę',
    zadanePytania: 'Zadane pytania',
    roznychPytan: (n) => `${n} różnych pytań`,
    udzieloneOdpowiedzi: 'Udzielone odpowiedzi',
    wszystkichPytan: (procent) => `${procent} wszystkich pytań`,
    bezOdpowiedzi: 'Bez odpowiedzi',
    brakDanych: 'brak danych',
    typowyCzas: 'Typowy czas odpowiedzi',
    typowyCzasPodpis: 'połowa odpowiedzi przychodzi szybciej',
    bezOdpowiedziWyjasnienie:
      'Bez odpowiedzi oznacza świadome wstrzymanie się: pytanie wykraczało poza bazę wiedzy albo poza tematykę Allegro. Asystent nie zgaduje, kiedy nie ma pokrycia w artykułach.',
    pozostaleLiczby: 'Pozostałe liczby',
    kciukiWGore: 'Kciuki w górę',
    brakOcen: 'brak ocen',
    ocenPodpis: (razem, pokrycie) => `${razem} ocen, oceniono ${pokrycie} odpowiedzi`,
    zPamieci: 'Odpowiedzi z pamięci',
    bezPamieci: (czas) => `bez pamięci ${czas}`,
    kosztModelu: 'Koszt modelu',
    wyslaneWiadomosci: 'Wysłane wiadomości',
    probWysylki: (n) => `${n} prób wysyłki`,
    pytaniaDzien: 'Pytania dzień po dniu',
    tematyPytan: 'Tematy pytań',
    ktoPyta: 'Kto pyta',
    ktoPytaOpis: (kupujacy, sprzedajacy) => `kupujący ${kupujacy}, sprzedający ${sprzedajacy}`,
    jakSzybko: 'Jak szybko przychodzą odpowiedzi',
    pytaniaBezOdpowiedzi: 'Pytania bez odpowiedzi',
    najczestszaPrzyczyna: 'Najczęstsza przyczyna',
    brakOdmow: 'brak odmów w okresie',
    przyczynaPodpis: (ile, udzial) => `${ile} razy, ${udzial} pytań bez odpowiedzi`,
    dlaczegoNie: 'Dlaczego asystent nie odpowiedział',
    dlaczegoNieOpis: 'Wstrzymanie się jest zamierzone: bez pokrycia w artykułach asystent nie zgaduje.',
    kazdePytanie: 'W tym okresie asystent odpowiedział na każde pytanie.',
    najczestszePytania: 'Najczęstsze pytania',
    pytaniaLicznik: (unikalne, widoczne) => `${unikalne} różnych pytań · widocznych ${widoczne}`,
    pokazNajczestsze: 'Pokaż tylko najczęstsze ▴',
    pokazWszystkie: (n) => `Pokaż ${n} najczęstszych ▾`,
    ocenioneOdpowiedzi: 'Ocenione odpowiedzi',
    ocenLicznik: (razem, negatywne) => `${razem} razem · ${negatywne} negatywnych`,
    ladujeOceny: 'Ładuję oceny',
    brakOcenOpis: 'Brak ocen w wybranym okresie. Kciuk pod odpowiedzią dopisuje wiersz do tej tabeli.',
    kolumnyOcen: [
      'Kiedy',
      'Ocena',
      'Co zawiodło',
      'Co poprawić',
      'Temat',
      'Pytanie',
      'Dopasowanie artykułu',
      'Oparcie w źródłach',
      'Poziom odpowiedzi',
      'Rola użytkownika',
      'Pewność wyboru tematu',
    ],
    kciukGora: 'kciuk w górę',
    kciukDol: 'kciuk w dół',
    resetPytanie: 'Zresetować statystyki?',
    resetOpis:
      'Dotychczasowe dane zostaną zarchiwizowane na serwerze i wyzerowane na tym panelu. Tej operacji nie da się cofnąć z tego miejsca. Wymaga tokenu administratora.',
    resetBezTokenu: 'Najpierw wpisz token administratora u góry strony.',
    anuluj: 'Anuluj',
    resetuje: 'Resetuję...',
    takResetuj: 'Tak, resetuj',
    zwin: 'Zwiń ▴',
    rozwin: 'Rozwiń ▾',
    zaMaloDniTrend: 'Za mało dni, żeby pokazać trend. Wróć po kolejnym dniu z ruchem.',
    zaMaloDniKoszt: 'Za mało dni, żeby pokazać koszt w czasie.',
    seriaPytania: 'Pytania',
    seriaBezOdpowiedzi: 'Bez odpowiedzi',
    seriaLiczba: 'Liczba',
    seriaKoszt: 'Koszt dzienny (USD)',
    eksportTytul: 'Eksport danych',
    eksportOpis:
      'Zaznacz kolumny, które mają trafić do pliku. Wybrany u góry strony okres i pozostałe filtry obowiązują także tutaj.',
    zaznaczWszystko: 'Zaznacz wszystko',
    odznaczWszystko: 'Odznacz wszystko',
    eksportBezTokenu:
      'Bez tokenu administratora plik nie zawiera kolumny z treścią pytań. Token wpisujesz u góry strony.',
    bladPliku: 'Nie udało się pobrać pliku',
    pobieram: 'Pobieram...',
    pobierzPlik: 'Pobierz plik',
    dniTygodnia: ['pn', 'wt', 'śr', 'cz', 'pt', 'so', 'nd'],
    miesiace: [
      'styczeń',
      'luty',
      'marzec',
      'kwiecień',
      'maj',
      'czerwiec',
      'lipiec',
      'sierpień',
      'wrzesień',
      'październik',
      'listopad',
      'grudzień',
    ],
    zakresEtykieta: (od, doDnia) => `${od} do ${doDnia}`,
    wybraneDni: 'Wybrane dni',
    poprzedniMiesiac: 'Poprzedni miesiąc',
    nastepnyMiesiac: 'Następny miesiąc',
    kliknijPoczatek: 'Kliknij dzień początkowy.',
    kliknijKoniec: 'Kliknij dzień końcowy.',
    wybrano: (od, doDnia) => `Wybrano ${od} do ${doDnia}.`,
    wyczysc: 'Wyczyść',
    pokazZakres: 'Pokaż ten zakres',
    statusyKolejki: { nowe: 'Nowe', odpowiedziano: 'Odpowiedziane', odrzucone: 'Odrzucone', wszystkie: 'Wszystkie' },
    brak: 'brak',
    bladKolejki: 'Nie udało się pobrać kolejki',
    kolejkaTytul: 'Kolejka zgłoszeń',
    kolejkaWstep:
      'Wpisz token administratora, żeby zobaczyć zgłoszenia. Bez tokenu lista jest niedostępna, a nie pusta. Trafiają tu pytania, na które asystent nie odpowiedział, a użytkownik poprosił o kontakt.',
    tokenMaly: 'token administratora',
    pokazKolejke: 'Pokaż kolejkę',
    kolejkaLicznik: (otwarte, razem) => `${otwarte} otwartych · ${razem} w widoku`,
    ladujeKolejke: 'Ładuję kolejkę',
    brakZgloszen: 'Brak zgłoszeń w tym widoku.',
    pustaOdpowiedz: 'Odpowiedź nie może być pusta.',
    wyslanoNumer: (numer) => `Wysłano, numer wiadomości ${numer}.`,
    odrzucono: 'Zgłoszenie odrzucone.',
    bladZapisu: 'Nie udało się zapisać.',
    brakTresciPytania: 'brak treści pytania',
    brakPowodu: 'brak powodu',
    brakTematu: 'brak tematu',
    dopasowanie: (wartosc) => `dopasowanie artykułu ${wartosc}`,
    oparcie: (wartosc) => `oparcie w źródłach ${wartosc}`,
    numerZgloszenia: 'Numer zgłoszenia',
    zgloszono: 'Zgłoszono',
    adresZwrotny: 'Adres zwrotny',
    najlepszyArtykul: 'Najlepiej dopasowany artykuł',
    coZawiodlo: 'Co zawiodło',
    poprzedniaOdpowiedz: 'Poprzednia odpowiedź',
    odpowiedzPlaceholder: 'Odpowiedź do użytkownika',
    bezEtykiety: 'bez etykiety',
    zapisuje: 'Zapisuję',
    wyslijOdpowiedz: 'Wyślij odpowiedź',
    odrzuc: 'Odrzuć',
    sekcje: {
      konto: 'Konto',
      zakupy: 'Zakupy',
      platnosci: 'Płatności',
      sprzedaz: 'Sprzedaż',
      kupujacy: 'Kupujący',
      email: 'Wiadomość do sprzedawcy',
    },
    nazwyStron: {
      kupujacy: 'Kupujący',
      sprzedajacy: 'Sprzedający',
      nieznana: 'Nieznana',
    },
    powody: {
      prog_rerank: 'Nie znaleziono pasującego artykułu',
      sedzia: 'Znalezione artykuły nie pasowały do pytania',
      brak_generacji: 'Asystent nie ułożył odpowiedzi',
      pokrycie: 'Odpowiedź za słabo oparta na artykułach',
      model_nie_wie: 'Asystent przyznał, że nie wie',
      jawna_odmowa: 'Asystent odmówił odpowiedzi',
      nie_zrozumialem: 'Pytanie niezrozumiałe',
      mail_doprecyzuj: 'Trzeba dopytać przed wysłaniem wiadomości',
      guard_za_krotkie: 'Pytanie za krótkie',
      guard_za_dlugie: 'Pytanie za długie',
      guard_nie_rozumiem: 'Nie rozpoznano treści pytania',
      guard_zly_alfabet: 'Pytanie w niedozwolonym alfabecie',
      guard_injekcja: 'Próba manipulacji asystentem',
      brak_danych: 'Brak materiałów w bazie wiedzy',
      pytanie_o_strone: 'Pytanie do innej roli (dawne kierowanie automatyczne)',
      odmowa: 'Brak odpowiedzi bez podanego powodu',
      brak_wyniku: 'Awaria przetwarzania',
      ogolna_temat: 'Pytanie spoza tematyki Allegro',
      ogolna_domena: 'Pytanie spoza obsługiwanej dziedziny',
      ogolna_blisko_bazy: 'Pytanie zbyt bliskie bazie, by odpowiadać z ogólnej wiedzy',
      ogolna_konkrety: 'Odpowiedź ogólna wchodziła w szczegóły Allegro',
      ogolna_pusta: 'Pusta odpowiedź ogólna',
      ogolna_dluga: 'Odpowiedź ogólna za długa',
      ogolna_model_nie_wie: 'Asystent nie znał odpowiedzi także bez bazy',
      ogolna_jawna_odmowa: 'Odmowa także bez bazy wiedzy',
      ogolna_brak_generacji: 'Brak odpowiedzi także bez bazy wiedzy',
    },
    kolumny: {
      czas: 'Data i godzina',
      lang: 'Język',
      strona: 'Rola użytkownika',
      sekcja: 'Temat',
      wynik: 'Wynik',
      powod: 'Powód braku odpowiedzi',
      powod_ogolna: 'Powód odmowy bez bazy wiedzy',
      latencja_s: 'Czas odpowiedzi (s)',
      cache_hit: 'Odpowiedź z pamięci',
      pytanie: 'Pytanie',
      tokeny_we: 'Tokeny wejściowe',
      tokeny_wy: 'Tokeny wyjściowe',
      koszt_usd: 'Koszt (USD)',
    },
    diagnozy: {
      ok: 'Dobra odpowiedź',
      tresc: 'Dobre materiały, słaba odpowiedź',
      retrieval: 'Wyszukiwarka nie znalazła artykułu',
      sedzia: 'Materiały odrzucone jako niepasujące',
      pokrycie: 'Odpowiedź za słabo oparta na artykułach',
      generacja: 'Asystent nie ułożył odpowiedzi',
      guard: 'Zatrzymane przez zabezpieczenia',
      literowki: 'Nierozpoznane słowa',
      doprecyzowanie: 'Dopytanie o rolę',
      ogolna: 'Odpowiedź bez bazy wiedzy',
      rozmowa: 'Zwykła wymiana zdań',
      inna: 'Inna przyczyna',
      brak_sladu: 'Brak zapisu przebiegu zapytania',
    },
    lekarstwa: {
      tresc: 'instrukcja dla asystenta',
      retrieval: 'baza artykułów i słownictwo',
      sedzia: 'czułość oceny materiałów',
      pokrycie: 'wymóg oparcia w artykułach',
      generacja: 'instrukcja dla asystenta',
      guard: 'reguły zabezpieczeń',
      literowki: 'słownik poprawek',
      doprecyzowanie: 'treść dopytania',
      ogolna: 'reguły odpowiedzi bez bazy',
      brak_sladu: 'ocena sprzed wprowadzenia identyfikatorów',
    },
    statusy: {
      nowe: 'Nowe',
      odpowiedziano: 'Odpowiedziano',
      odrzucone: 'Odrzucone',
    },
    etykietyZgloszen: {
      luka_w_bazie: 'Luka w bazie',
      prog_za_wysoki: 'Próg za wysoki',
      poza_zakresem: 'Poza zakresem',
      spam: 'Spam',
    },
    przedzialyLatencji: {},
  },
  en: {
    tytul: 'Statistics panel',
    daneOdDo: (od, doDnia) => `Data from ${od} to ${doDnia}`,
    brakDanychWZakresie: 'No data in the selected range',
    odswiezono: 'refreshed at',
    wrocDoCzatu: 'Back to chat',
    resetuj: 'Reset statistics',
    wylogujToken: 'Clear token',
    tokenPlaceholder: 'Admin token',
    odblokuj: 'Unlock',
    tokenPodpowiedz: 'Without a token the panel hides the text of questions and answers',
    wpiszToken: 'Enter token',
    zmienMotyw: 'Change theme',
    jezykInterfejsu: 'Interface language',
    okres: 'Period',
    jezyk: 'Language',
    rola: 'Role',
    okresy: { dni7: 'Last 7 days', dni30: '30 days', dni90: '90 days', wszystko: 'All time' },
    jezyki: { wszystkie: 'All', pl: 'Polish', en: 'English' },
    strony: { wszyscy: 'Everyone', kupujacy: 'Buyers', sprzedajacy: 'Sellers' },
    zakladki: {
      przeglad: 'Overview',
      jakosc: 'Quality and refusals',
      pytania: 'Questions',
      oceny: 'Ratings',
      kolejka: 'Queue',
      eksport: 'Export',
    },
    sprobujPonownie: 'Try again',
    wczytuje: 'Loading data...',
    brakDanychKropka: 'No data in the selected range.',
    bladStatystyk: 'Could not load the statistics',
    bladOcen: 'Could not load the ratings',
    resetZarchiwizowane: 'Statistics reset, previous data archived on the server',
    resetBezArchiwum: 'Statistics reset, there was nothing to archive',
    bladResetu: 'Could not reset the statistics',
    bladTokenu: 'Not authorised: check the admin token',
    bladLimitu: 'Too many requests at once, try again in a moment',
    zadanePytania: 'Questions asked',
    roznychPytan: (n) => `${n} distinct ${n === 1 ? 'question' : 'questions'}`,
    udzieloneOdpowiedzi: 'Answers given',
    wszystkichPytan: (procent) => `${procent} of all questions`,
    bezOdpowiedzi: 'Unanswered',
    brakDanych: 'no data',
    typowyCzas: 'Typical response time',
    typowyCzasPodpis: 'half of the answers arrive faster',
    bezOdpowiedziWyjasnienie:
      'Unanswered means a deliberate abstention: the question went beyond the knowledge base or outside Allegro topics. The assistant does not guess when the articles do not cover the question.',
    pozostaleLiczby: 'Other numbers',
    kciukiWGore: 'Thumbs up',
    brakOcen: 'no ratings',
    ocenPodpis: (razem, pokrycie) => `${razem} ${razem === 1 ? 'rating' : 'ratings'}, ${pokrycie} of answers rated`,
    zPamieci: 'Answers from cache',
    bezPamieci: (czas) => `without cache ${czas}`,
    kosztModelu: 'Model cost',
    wyslaneWiadomosci: 'Messages sent',
    probWysylki: (n) => `${n} send ${n === 1 ? 'attempt' : 'attempts'}`,
    pytaniaDzien: 'Questions day by day',
    tematyPytan: 'Question topics',
    ktoPyta: 'Who is asking',
    ktoPytaOpis: (kupujacy, sprzedajacy) => `buyers ${kupujacy}, sellers ${sprzedajacy}`,
    jakSzybko: 'How fast answers arrive',
    pytaniaBezOdpowiedzi: 'Unanswered questions',
    najczestszaPrzyczyna: 'Most common reason',
    brakOdmow: 'no refusals in this period',
    przyczynaPodpis: (ile, udzial) => `${ile === 1 ? 'once' : `${ile} times`}, ${udzial} of unanswered questions`,
    dlaczegoNie: 'Why the assistant did not answer',
    dlaczegoNieOpis: 'Abstaining is intentional: without coverage in the articles the assistant does not guess.',
    kazdePytanie: 'In this period the assistant answered every question.',
    najczestszePytania: 'Most common questions',
    pytaniaLicznik: (unikalne, widoczne) => `${unikalne} distinct ${unikalne === 1 ? 'question' : 'questions'} · ${widoczne} shown`,
    pokazNajczestsze: 'Show only the most common ▴',
    pokazWszystkie: (n) => `Show ${n} most common ▾`,
    ocenioneOdpowiedzi: 'Rated answers',
    ocenLicznik: (razem, negatywne) => `${razem} total · ${negatywne} negative`,
    ladujeOceny: 'Loading ratings',
    brakOcenOpis: 'No ratings in the selected period. A thumb under an answer adds a row to this table.',
    kolumnyOcen: [
      'When',
      'Rating',
      'What failed',
      'What to fix',
      'Topic',
      'Question',
      'Article match',
      'Source grounding',
      'Answer level',
      'User role',
      'Topic choice confidence',
    ],
    kciukGora: 'thumbs up',
    kciukDol: 'thumbs down',
    resetPytanie: 'Reset the statistics?',
    resetOpis:
      'Current data will be archived on the server and cleared from this panel. This cannot be undone from here. Requires the admin token.',
    resetBezTokenu: 'Enter the admin token at the top of the page first.',
    anuluj: 'Cancel',
    resetuje: 'Resetting...',
    takResetuj: 'Yes, reset',
    zwin: 'Collapse ▴',
    rozwin: 'Expand ▾',
    zaMaloDniTrend: 'Not enough days to show a trend. Come back after another day with traffic.',
    zaMaloDniKoszt: 'Not enough days to show cost over time.',
    seriaPytania: 'Questions',
    seriaBezOdpowiedzi: 'Unanswered',
    seriaLiczba: 'Count',
    seriaKoszt: 'Daily cost (USD)',
    eksportTytul: 'Data export',
    eksportOpis:
      'Select the columns to include in the file. The period and other filters chosen at the top of the page apply here too.',
    zaznaczWszystko: 'Select all',
    odznaczWszystko: 'Clear all',
    eksportBezTokenu:
      'Without the admin token the file does not include the question text column. Enter the token at the top of the page.',
    bladPliku: 'Could not download the file',
    pobieram: 'Downloading...',
    pobierzPlik: 'Download file',
    dniTygodnia: ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su'],
    miesiace: [
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December',
    ],
    zakresEtykieta: (od, doDnia) => `${od} to ${doDnia}`,
    wybraneDni: 'Custom dates',
    poprzedniMiesiac: 'Previous month',
    nastepnyMiesiac: 'Next month',
    kliknijPoczatek: 'Click the start day.',
    kliknijKoniec: 'Click the end day.',
    wybrano: (od, doDnia) => `Selected ${od} to ${doDnia}.`,
    wyczysc: 'Clear',
    pokazZakres: 'Show this range',
    statusyKolejki: { nowe: 'New', odpowiedziano: 'Answered', odrzucone: 'Rejected', wszystkie: 'All' },
    brak: 'none',
    bladKolejki: 'Could not load the queue',
    kolejkaTytul: 'Request queue',
    kolejkaWstep:
      'Enter the admin token to see the requests. Without a token the list is unavailable, not empty. It collects questions the assistant did not answer where the user asked to be contacted.',
    tokenMaly: 'admin token',
    pokazKolejke: 'Show queue',
    kolejkaLicznik: (otwarte, razem) => `${otwarte} open · ${razem} in view`,
    ladujeKolejke: 'Loading queue',
    brakZgloszen: 'No requests in this view.',
    pustaOdpowiedz: 'The answer cannot be empty.',
    wyslanoNumer: (numer) => `Sent, message number ${numer}.`,
    odrzucono: 'Request rejected.',
    bladZapisu: 'Could not save.',
    brakTresciPytania: 'no question text',
    brakPowodu: 'no reason',
    brakTematu: 'no topic',
    dopasowanie: (wartosc) => `article match ${wartosc}`,
    oparcie: (wartosc) => `source grounding ${wartosc}`,
    numerZgloszenia: 'Request number',
    zgloszono: 'Submitted',
    adresZwrotny: 'Reply address',
    najlepszyArtykul: 'Best matching article',
    coZawiodlo: 'What failed',
    poprzedniaOdpowiedz: 'Previous answer',
    odpowiedzPlaceholder: 'Answer to the user',
    bezEtykiety: 'no label',
    zapisuje: 'Saving',
    wyslijOdpowiedz: 'Send answer',
    odrzuc: 'Reject',
    sekcje: {
      konto: 'Account',
      zakupy: 'Purchases',
      platnosci: 'Payments',
      sprzedaz: 'Selling',
      kupujacy: 'Buyers',
      email: 'Message to the seller',
    },
    nazwyStron: {
      kupujacy: 'Buyers',
      sprzedajacy: 'Sellers',
      nieznana: 'Unknown',
    },
    powody: {
      prog_rerank: 'No matching article found',
      sedzia: 'Found articles did not match the question',
      brak_generacji: 'The assistant did not compose an answer',
      pokrycie: 'Answer too weakly grounded in the articles',
      model_nie_wie: 'The assistant admitted it does not know',
      jawna_odmowa: 'The assistant refused to answer',
      nie_zrozumialem: 'Question not understood',
      mail_doprecyzuj: 'Details needed before sending a message',
      guard_za_krotkie: 'Question too short',
      guard_za_dlugie: 'Question too long',
      guard_nie_rozumiem: 'Question content not recognised',
      guard_zly_alfabet: 'Question in an unsupported alphabet',
      guard_injekcja: 'Attempt to manipulate the assistant',
      brak_danych: 'No material in the knowledge base',
      pytanie_o_strone: 'Question for the other role (former automatic routing)',
      odmowa: 'No answer and no reason given',
      brak_wyniku: 'Processing failure',
      ogolna_temat: 'Question outside Allegro topics',
      ogolna_domena: 'Question outside the supported domain',
      ogolna_blisko_bazy: 'Question too close to the knowledge base to answer from general knowledge',
      ogolna_konkrety: 'General answer went into Allegro specifics',
      ogolna_pusta: 'Empty general answer',
      ogolna_dluga: 'General answer too long',
      ogolna_model_nie_wie: 'The assistant did not know the answer without the knowledge base either',
      ogolna_jawna_odmowa: 'Refusal without the knowledge base as well',
      ogolna_brak_generacji: 'No answer without the knowledge base either',
    },
    kolumny: {
      czas: 'Date and time',
      lang: 'Language',
      strona: 'User role',
      sekcja: 'Topic',
      wynik: 'Result',
      powod: 'Reason for no answer',
      powod_ogolna: 'Refusal reason without the knowledge base',
      latencja_s: 'Response time (s)',
      cache_hit: 'Answer from cache',
      pytanie: 'Question',
      tokeny_we: 'Input tokens',
      tokeny_wy: 'Output tokens',
      koszt_usd: 'Cost (USD)',
    },
    diagnozy: {
      ok: 'Good answer',
      tresc: 'Good material, weak answer',
      retrieval: 'Search did not find the article',
      sedzia: 'Material rejected as not matching',
      pokrycie: 'Answer too weakly grounded in the articles',
      generacja: 'The assistant did not compose an answer',
      guard: 'Stopped by safeguards',
      literowki: 'Unrecognised words',
      doprecyzowanie: 'Asked about the role',
      ogolna: 'Answer without the knowledge base',
      rozmowa: 'Small talk',
      inna: 'Other reason',
      brak_sladu: 'No record of how the query was processed',
    },
    lekarstwa: {
      tresc: 'assistant instructions',
      retrieval: 'article base and vocabulary',
      sedzia: 'sensitivity of the material check',
      pokrycie: 'article grounding requirement',
      generacja: 'assistant instructions',
      guard: 'safeguard rules',
      literowki: 'correction dictionary',
      doprecyzowanie: 'wording of the clarifying question',
      ogolna: 'rules for answers without the knowledge base',
      brak_sladu: 'rating from before query identifiers were introduced',
    },
    statusy: {
      nowe: 'New',
      odpowiedziano: 'Answered',
      odrzucone: 'Rejected',
    },
    etykietyZgloszen: {
      luka_w_bazie: 'Knowledge base gap',
      prog_za_wysoki: 'Threshold too high',
      poza_zakresem: 'Out of scope',
      spam: 'Spam',
    },
    przedzialyLatencji: {
      '0 do 2 s': '0 to 2 s',
      '2 do 5 s': '2 to 5 s',
      '5 do 10 s': '5 to 10 s',
      '10 do 20 s': '10 to 20 s',
      'ponad 20 s': 'over 20 s',
    },
  },
};

export const JezykAdminaContext = createContext<Lang>('pl');

export function useJezykAdmina(): Lang {
  return useContext(JezykAdminaContext);
}

export function useTekstyAdmina(): TekstyAdmina {
  return TEKSTY_ADMINA[useContext(JezykAdminaContext)];
}

export function opisBledu(blad: unknown, domyslny: string, lang: Lang): string {
  const t = TEKSTY_ADMINA[lang];
  if (!(blad instanceof BladZapytania)) return domyslny;
  if (lang === 'pl' && blad.detail) return blad.detail;
  if (blad.status === 401) return t.bladTokenu;
  if (blad.status === 429) return t.bladLimitu;
  return `${domyslny} (HTTP ${blad.status})`;
}
