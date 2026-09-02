export interface Zakres {
  od: string | null;
  do: string | null;
  dni: number;
  obciete: boolean;
}

export interface Ogolem {
  zapytan: number;
  odpowiedzi: number;
  odmowy: number;
  rozmowy: number;
  trafnosc: number | null;
  cache_hit: number;
  unikalne_pytania: number;
  wysylki: number;
  wysylki_ok: number;
}

export interface HistogramPozycja {
  zakres: string;
  ile: number;
}

export interface Latencja {
  mediana: number;
  p90: number;
  p95: number;
  srednia: number;
  mediana_cache: number;
  mediana_bez_cache: number;
  histogram: HistogramPozycja[];
}

export interface SekcjaPozycja {
  sekcja: string;
  ile: number;
  udzial: number;
}

export interface StronaPozycja {
  strona: string;
  ile: number;
  udzial: number;
}

export interface PowodPozycja {
  powod: string;
  ile: number;
  udzial: number;
}

export interface JezykPozycja {
  lang: string;
  ile: number;
  udzial: number;
}

export interface PozycjaDzienna {
  dzien: string;
  zapytan: number;
  odmowy: number;
  mediana_latencji: number;
  koszt_usd: number;
}

export interface TopPytanie {
  pytanie: string;
  ile: number;
}

export interface Oceny {
  gora: number;
  dol: number;
  razem: number;
  trafnosc: number | null;
  pokrycie: number;
}

export interface Koszty {
  tokeny_we: number;
  tokeny_wy: number;
  koszt_usd: number;
  koszt_na_zapytanie: number;
  pokrycie: number;
  szacowane: number;
  udzial_szacowanych: number;
}

export interface Kolumny {
  wszystkie: string[];
  domyslne: string[];
}

export interface Statystyki {
  zakres: Zakres;
  ogolem: Ogolem;
  latencja: Latencja;
  sekcje: SekcjaPozycja[];
  strony: StronaPozycja[];
  powody: PowodPozycja[];
  jezyki: JezykPozycja[];
  dzienne: PozycjaDzienna[];
  top_pytania: TopPytanie[];
  oceny: Oceny;
  koszty: Koszty;
  kolumny: Kolumny;
}

export interface Filtry {
  dni: number | null;
  od: string | null;
  do: string | null;
  lang: 'pl' | 'en' | null;
  strona: 'kupujacy' | 'sprzedajacy' | null;
}

export function parametryFiltrow(filtry: Filtry): string {
  const params = new URLSearchParams();
  if (filtry.od !== null) {
    params.set('od', filtry.od);
  }
  if (filtry.do !== null) {
    params.set('do', filtry.do);
  }
  if (filtry.dni !== null && filtry.od === null && filtry.do === null) {
    params.set('dni', String(filtry.dni));
  }
  if (filtry.lang !== null) {
    params.set('lang', filtry.lang);
  }
  if (filtry.strona !== null) {
    params.set('strona', filtry.strona);
  }
  return params.toString();
}

export function naglowkiAdmina(token: string): Record<string, string> {
  return token ? { 'x-admin-token': token } : {};
}

export async function pobierzStatystyki(filtry: Filtry, token = ''): Promise<Statystyki> {
  const res = await fetch(`/api/admin/statystyki?${parametryFiltrow(filtry)}`, {
    cache: 'no-store',
    headers: naglowkiAdmina(token),
  });
  if (!res.ok) {
    throw new Error(`Błąd pobierania statystyk: ${res.status}`);
  }
  return res.json() as Promise<Statystyki>;
}

export const ETYKIETY_KOLUMN: Record<string, string> = {
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
};

export const NAZWY_SEKCJI: Record<string, string> = {
  konto: 'Konto',
  zakupy: 'Zakupy',
  platnosci: 'Płatności',
  sprzedaz: 'Sprzedaż',
  kupujacy: 'Kupujący',
  email: 'Wiadomość do sprzedawcy',
};

export const NAZWY_STRON: Record<string, string> = {
  kupujacy: 'Kupujący',
  sprzedajacy: 'Sprzedający',
  nieznana: 'Nieznana',
};

export const NAZWY_POWODOW: Record<string, string> = {
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
};

export const NAZWY_CECH: Record<string, string> = {
  rerank_top1: 'Dopasowanie artykułu',
  pokrycie: 'Oparcie w źródłach',
  zrodlo_top1: 'Najlepiej dopasowany artykuł',
  strona_wybrana: 'Rola wybrana przez użytkownika',
  przewaga_sekcji: 'Pewność wyboru tematu',
  etap: 'Poziom odpowiedzi',
};

export function etykieta(mapa: Record<string, string>, klucz: string): string {
  return mapa[klucz] ?? klucz;
}

export function procent(wartosc: number | null, miejsca = 1): string {
  if (wartosc === null || Number.isNaN(wartosc)) {
    return 'brak danych';
  }
  return `${(wartosc * 100).toFixed(miejsca)}%`;
}

export function sekundy(wartosc: number): string {
  return `${wartosc.toFixed(2)} s`;
}

export async function resetujStatystyki(token: string): Promise<string | null> {
  const res = await fetch('/api/admin/reset-statystyk', {
    method: 'POST',
    cache: 'no-store',
    headers: { 'x-admin-token': token },
  });
  if (!res.ok) {
    const tresc = (await res.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(tresc?.detail ?? `Błąd resetowania statystyk: ${res.status}`);
  }
  const wynik = (await res.json()) as { archiwum: string | null };
  return wynik.archiwum;
}

export interface CechyPrzypadku {
  rerank_top1: number | null;
  chunkow: number;
  zrodlo_top1: string | null;
  sedzia_ok: boolean | null;
  pokrycie: number | null;
  etap: number;
  strona_wybrana: string | null;
  przewaga_sekcji: number | null;
}

export interface Przypadek {
  czas: string | null;
  ocena: 'gora' | 'dol';
  lang: string | null;
  strona: string;
  sekcja: string | null;
  pytanie: string | null;
  odpowiedz: string | null;
  id_zapytania: string | null;
  wynik: string | null;
  powod: string | null;
  latencja_s: number | null;
  cache_hit: boolean | null;
  cechy: CechyPrzypadku | null;
  diagnoza: string;
}

export interface Przypadki {
  razem: number;
  przypadki: Przypadek[];
}

export const ETYKIETY_DIAGNOZ: Record<string, string> = {
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
};

export const LEKARSTWA_DIAGNOZ: Record<string, string> = {
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
};

export async function pobierzPrzypadki(filtry: Filtry, token = ''): Promise<Przypadki> {
  const res = await fetch(`/api/admin/oceny?${parametryFiltrow(filtry)}`, {
    cache: 'no-store',
    headers: naglowkiAdmina(token),
  });
  if (!res.ok) {
    throw new Error(`Błąd pobierania ocen: ${res.status}`);
  }
  return res.json() as Promise<Przypadki>;
}

export type StatusZgloszenia = 'nowe' | 'odpowiedziano' | 'odrzucone';
export type EtykietaZgloszenia = 'luka_w_bazie' | 'prog_za_wysoki' | 'poza_zakresem' | 'spam';

export const NAZWY_STATUSOW_ZGLOSZEN: Record<StatusZgloszenia, string> = {
  nowe: 'Nowe',
  odpowiedziano: 'Odpowiedziano',
  odrzucone: 'Odrzucone',
};

export const NAZWY_ETYKIET_ZGLOSZEN: Record<EtykietaZgloszenia, string> = {
  luka_w_bazie: 'Luka w bazie',
  prog_za_wysoki: 'Próg za wysoki',
  poza_zakresem: 'Poza zakresem',
  spam: 'Spam',
};

export interface CechyZgloszenia {
  rerank_top1?: number | null;
  pokrycie?: number | null;
  zrodlo_top1?: string | null;
  strona_wybrana?: string | null;
}

export interface ZgloszenieKolejki {
  zgloszenie: string;
  czas: string | null;
  id_zapytania: string | null;
  lang: string | null;
  strona: string | null;
  sekcja: string | null;
  powod: string | null;
  pytanie: string | null;
  email: string | null;
  status: StatusZgloszenia;
  etykieta: EtykietaZgloszenia | null;
  tresc: string | null;
  ticket: string | null;
  decyzja_czas: string | null;
  wynik: string | null;
  latencja_s: number | null;
  cechy: CechyZgloszenia | null;
  diagnoza: string;
}

export interface Kolejka {
  razem: number;
  otwarte: number;
  zgloszenia: ZgloszenieKolejki[];
}

export interface OdpowiedzKolejki {
  zgloszenie: string;
  status: 'odpowiedziano' | 'odrzucone';
  etykieta?: EtykietaZgloszenia | null;
  tresc: string;
}

export async function pobierzKolejke(
  token: string,
  dni: number | null,
  status: StatusZgloszenia | null,
): Promise<Kolejka> {
  const params = new URLSearchParams();
  if (dni !== null) {
    params.set('dni', String(dni));
  }
  if (status !== null) {
    params.set('status', status);
  }
  const res = await fetch(`/api/admin/kolejka?${params.toString()}`, {
    cache: 'no-store',
    headers: { 'x-admin-token': token },
  });
  if (!res.ok) {
    const tresc = (await res.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(tresc?.detail ?? `Błąd pobierania kolejki: ${res.status}`);
  }
  return res.json() as Promise<Kolejka>;
}

export async function odpowiedzZgloszenie(
  token: string,
  dane: OdpowiedzKolejki,
): Promise<{ status: string; ticket: string | null }> {
  const res = await fetch('/api/admin/kolejka/odpowiedz', {
    method: 'POST',
    cache: 'no-store',
    headers: { 'content-type': 'application/json', 'x-admin-token': token },
    body: JSON.stringify(dane),
  });
  if (!res.ok) {
    const tresc = (await res.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(tresc?.detail ?? `Błąd zapisu odpowiedzi: ${res.status}`);
  }
  return res.json() as Promise<{ status: string; ticket: string | null }>;
}

export async function pobierzEksport(
  filtry: Filtry,
  kolumny: string[],
  format: 'csv' | 'json',
  token = '',
): Promise<{ blob: Blob; nazwa: string }> {
  const adres = `/api/admin/eksport?format=${format}&kolumny=${kolumny.join(',')}&${parametryFiltrow(filtry)}`;
  const res = await fetch(adres, { cache: 'no-store', headers: naglowkiAdmina(token) });
  if (!res.ok) {
    const tresc = (await res.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(tresc?.detail ?? `Nie udało się pobrać eksportu: ${res.status}`);
  }
  const dyspozycja = res.headers.get('content-disposition') ?? '';
  const dopasowanie = /filename="?([^"]+)"?/.exec(dyspozycja);
  const stempel = new Date().toISOString().slice(0, 10);
  return { blob: await res.blob(), nazwa: dopasowanie?.[1] ?? `eksport_${stempel}.${format}` };
}
