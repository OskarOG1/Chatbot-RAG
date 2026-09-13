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

export class BladZapytania extends Error {
  status: number;
  detail: string | null;

  constructor(status: number, detail: string | null) {
    super(detail ?? `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

async function bladOdpowiedzi(res: Response): Promise<BladZapytania> {
  const tresc = (await res.json().catch(() => null)) as { detail?: unknown } | null;
  const detail = typeof tresc?.detail === 'string' ? tresc.detail : null;
  return new BladZapytania(res.status, detail);
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
    throw await bladOdpowiedzi(res);
  }
  return res.json() as Promise<Statystyki>;
}

export function etykieta(mapa: Record<string, string>, klucz: string): string {
  return mapa[klucz] ?? klucz;
}

export function procent(wartosc: number | null, brak: string, miejsca = 1): string {
  if (wartosc === null || Number.isNaN(wartosc)) {
    return brak;
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
    throw await bladOdpowiedzi(res);
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

export async function pobierzPrzypadki(filtry: Filtry, token = ''): Promise<Przypadki> {
  const res = await fetch(`/api/admin/oceny?${parametryFiltrow(filtry)}`, {
    cache: 'no-store',
    headers: naglowkiAdmina(token),
  });
  if (!res.ok) {
    throw await bladOdpowiedzi(res);
  }
  return res.json() as Promise<Przypadki>;
}

export type StatusZgloszenia = 'nowe' | 'odpowiedziano' | 'odrzucone';
export type EtykietaZgloszenia = 'luka_w_bazie' | 'prog_za_wysoki' | 'poza_zakresem' | 'spam';

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
    throw await bladOdpowiedzi(res);
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
    throw await bladOdpowiedzi(res);
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
    throw await bladOdpowiedzi(res);
  }
  const dyspozycja = res.headers.get('content-disposition') ?? '';
  const dopasowanie = /filename="?([^"]+)"?/.exec(dyspozycja);
  const stempel = new Date().toISOString().slice(0, 10);
  return { blob: await res.blob(), nazwa: dopasowanie?.[1] ?? `eksport_${stempel}.${format}` };
}
