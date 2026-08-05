import { TEKSTY, type Cytat, type Lang, type Strona, type Wiadomosc } from './chat';

export interface WiadomoscUi {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  citations?: Cytat[];
  doprecyzowanie?: string | null;
  action?: string | null;
  pytaStrona?: boolean;
  zapytanieDoStrony?: string;
  wybranaStrona?: 'kupujacy' | 'sprzedajacy';
}

export interface PanelState {
  recipient: string;
  subject: string;
  body: string;
  originalSubject: string;
  originalBody: string;
  kategoria: string | null;
  trigger: string;
  clientEmail: string;
  sending: boolean;
  wyslano: { ticket: string; czas: number } | null;
  edytujPoWyslaniu: boolean;
  odliczanieDo: number | null;
}

export interface Thread {
  id: string;
  title: string | null;
  createdAt: number;
  updatedAt: number;
  messages: WiadomoscUi[];
  historiaApi: Wiadomosc[];
  ostatniAgent: string | null;
  ostatniaKorekta: string | null;
  panel: PanelState | null;
  panelOpen: boolean;
}

interface Zapis {
  version: number;
  activeId: string;
  threads: Thread[];
}

const STORAGE_KEY = 'allegro-rag-threads-v1';
const LANG_KEY = 'allegro-rag-lang-v1';
const STRONA_KEY = 'allegro-rag-strona-v1';
const VERSION = 1;

export function wczytajJezyk(): Lang | null {
  try {
    const zapis = localStorage.getItem(LANG_KEY);
    return zapis === 'pl' || zapis === 'en' ? zapis : null;
  } catch {
    return null;
  }
}

export function zapiszJezyk(lang: Lang): void {
  try {
    localStorage.setItem(LANG_KEY, lang);
  } catch {
    return;
  }
}

export function wczytajStrone(): Strona | null {
  try {
    const zapis = localStorage.getItem(STRONA_KEY);
    return zapis === 'auto' || zapis === 'kupujacy' || zapis === 'sprzedajacy' ? zapis : null;
  } catch {
    return null;
  }
}

export function zapiszStrone(strona: Strona): void {
  try {
    localStorage.setItem(STRONA_KEY, strona);
  } catch {
    return;
  }
}

export function nowyThread(lang: Lang): Thread {
  const teraz = Date.now();
  return {
    id: losoweId(),
    title: null,
    createdAt: teraz,
    updatedAt: teraz,
    messages: [{ id: 0, role: 'assistant', content: TEKSTY[lang].welcome }],
    historiaApi: [],
    ostatniAgent: null,
    ostatniaKorekta: null,
    panel: null,
    panelOpen: false,
  };
}

export function losoweId(): string {
  try {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID();
  } catch {
    return `t-${Math.floor(performance.now() * 1000).toString(36)}`;
  }
  return `t-${Math.floor(performance.now() * 1000).toString(36)}-${Math.floor(performance.now()).toString(36)}`;
}

export function tytulZWiadomosci(messages: WiadomoscUi[], zapas: string): string {
  const pierwszaUzytkownika = messages.find((m) => m.role === 'user');
  if (!pierwszaUzytkownika) return zapas;
  const tekst = pierwszaUzytkownika.content.trim().replace(/\s+/g, ' ');
  return tekst.length > 46 ? `${tekst.slice(0, 46)}…` : tekst;
}

export function wczytajStan(): { threads: Thread[]; activeId: string } | null {
  try {
    const surowe = localStorage.getItem(STORAGE_KEY);
    if (!surowe) return null;
    const dane = JSON.parse(surowe) as Zapis;
    if (dane.version !== VERSION || !Array.isArray(dane.threads) || dane.threads.length === 0) return null;
    const threads = dane.threads.map((th) => ({
      ...th,
      panel: th.panel ? { ...th.panel, sending: false, odliczanieDo: null } : null,
    }));
    const activeId = threads.some((th) => th.id === dane.activeId) ? dane.activeId : threads[0].id;
    return { threads, activeId };
  } catch {
    return null;
  }
}

export function usunWatki(threads: Thread[], ids: Set<string>): Thread[] {
  return threads.filter((th) => !ids.has(th.id));
}

export function podmienPowitanie(threads: Thread[], lang: Lang): Thread[] {
  return threads.map((th) => {
    if (th.messages.some((m) => m.role === 'user')) return th;
    if (th.messages.length !== 1) return th;
    return { ...th, messages: [{ id: 0, role: 'assistant', content: TEKSTY[lang].welcome }] };
  });
}

export function zapiszStan(threads: Thread[], activeId: string): void {
  try {
    const dane: Zapis = { version: VERSION, activeId, threads };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(dane));
  } catch {
    return;
  }
}
