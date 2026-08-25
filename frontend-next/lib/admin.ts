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
  lang: 'pl' | 'en' | null;
  strona: 'kupujacy' | 'sprzedajacy' | null;
}

export function parametryFiltrow(filtry: Filtry): string {
  const params = new URLSearchParams();
  if (filtry.dni !== null) {
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

export async function pobierzStatystyki(filtry: Filtry): Promise<Statystyki> {
  const res = await fetch(`/api/admin/statystyki?${parametryFiltrow(filtry)}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Błąd pobierania statystyk: ${res.status}`);
  }
  return res.json() as Promise<Statystyki>;
}

export const ETYKIETY_KOLUMN: Record<string, string> = {
  czas: 'Czas',
  lang: 'Język',
  strona: 'Strona',
  sekcja: 'Sekcja',
  wynik: 'Wynik',
  powod: 'Powód',
  latencja_s: 'Latencja (s)',
  cache_hit: 'Trafienie cache',
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
  prog_rerank: 'Za słabe dopasowanie w bazie',
  sedzia: 'Sędzia odrzucił kontekst',
  brak_generacji: 'Model nie wygenerował odpowiedzi',
  pokrycie: 'Odpowiedź za słabo oparta na źródłach',
  model_nie_wie: 'Model przyznał, że nie wie',
  jawna_odmowa: 'Jawna odmowa modelu',
  nie_zrozumialem: 'Pytanie niezrozumiałe',
  mail_doprecyzuj: 'Wymaga doprecyzowania do maila',
  guard_za_krotkie: 'Pytanie za krótkie',
  guard_za_dlugie: 'Pytanie za długie',
  guard_nie_rozumiem: 'Guard nie rozpoznał pytania',
  guard_zly_alfabet: 'Niedozwolony alfabet',
  guard_injekcja: 'Wykryto próbę wstrzyknięcia promptu',
  brak_danych: 'Brak danych źródłowych',
  pytanie_o_strone: 'Pytanie o inną rolę (stary automatyczny routing)',
  odmowa: 'Odmowa bez podanego powodu',
  brak_wyniku: 'Pipeline nie zwrócił wyniku',
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
  tresc: 'Zła treść przy dobrym kontekście',
  retrieval: 'Brak trafienia w wyszukiwaniu',
  sedzia: 'Sędzia odrzucił kontekst',
  pokrycie: 'Za niskie pokrycie odpowiedzi',
  generacja: 'Model nie odpowiedział',
  guard: 'Zatrzymane przez guard',
  literowki: 'Nierozpoznane słowa',
  doprecyzowanie: 'Pytanie o stronę',
  rozmowa: 'Tura rozmowy',
  inna: 'Inna przyczyna',
  brak_sladu: 'Brak śladu zapytania',
};

export const LEKARSTWA_DIAGNOZ: Record<string, string> = {
  tresc: 'prompt generacji',
  retrieval: 'korpus, chunking, aliasy',
  sedzia: 'próg sędziego',
  pokrycie: 'próg pokrycia',
  generacja: 'prompt generacji',
  guard: 'reguły guardów',
  literowki: 'słownik korektora',
  doprecyzowanie: 'treść doprecyzowania',
  brak_sladu: 'ocena sprzed wdrożenia identyfikatorów',
};

export async function pobierzPrzypadki(dni: number | null): Promise<Przypadki> {
  const params = new URLSearchParams();
  if (dni !== null) {
    params.set('dni', String(dni));
  }
  const res = await fetch(`/api/admin/oceny?${params.toString()}`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Błąd pobierania ocen: ${res.status}`);
  }
  return res.json() as Promise<Przypadki>;
}
