export interface Zakres {
  od: string | null;
  do: string | null;
  dni: number;
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

export const KOLUMNY_EKSPORTU = [
  'czas', 'lang', 'strona', 'sekcja', 'wynik', 'powod', 'powod_etap2',
  'latencja_s', 'cache_hit', 'pytanie', 'tokeny_we', 'tokeny_wy', 'koszt_usd',
] as const;

export const KOLUMNY_DOMYSLNE: string[] = [
  'czas', 'lang', 'strona', 'sekcja', 'wynik', 'powod', 'latencja_s', 'cache_hit',
];

export const ETYKIETY_KOLUMN: Record<string, string> = {
  czas: 'Czas',
  lang: 'Język',
  strona: 'Strona',
  sekcja: 'Sekcja',
  wynik: 'Wynik',
  powod: 'Powód',
  powod_etap2: 'Powód, etap 2',
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
