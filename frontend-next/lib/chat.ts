export type Lang = 'pl' | 'en';

export type Tryb = 'rag' | 'email';

export interface Wiadomosc {
  role: 'user' | 'assistant';
  content: string;
}

export interface Cytat {
  n: number;
  url: string;
}

export interface ChatResponse {
  agent: string;
  answer: string;
  sources: string[];
  citations: Cytat[];
  doprecyzowanie: string | null;
  oferta: string | null;
  oferta_kategoria: string | null;
  kategoria: string | null;
  tryb: Tryb;
}

export type SseEvent =
  | { typ: 'krok'; tekst: string }
  | { typ: 'token'; tekst: string }
  | { typ: 'wynik'; dane: ChatResponse }
  | { typ: 'blad'; kod: number; tekst: string };

export interface ChatRequestBody {
  message: string;
  history: Wiadomosc[];
  agent_poprzedni: string | null;
  bez_korekty: boolean;
  lang: Lang;
}

interface Teksty {
  ustawienia: string;
  mysle: string;
  gotowe: string;
  bladStatus: string;
  sekcja: (agent: string) => string;
  zrodla: string;
  connectError: string;
  timeoutError: string;
  httpError: string;
  parseError: string;
  noResponse: string;
  negacje: Set<string>;
  szkicNaglowek: string;
  szkicNaglowki: Record<string, string>;
  placeholder: string;
  wyslij: string;
}

export const TEKSTY: Record<Lang, Teksty> = {
  pl: {
    ustawienia: 'Ustawienia',
    mysle: 'Myślę…',
    gotowe: 'Gotowe',
    bladStatus: 'Błąd',
    sekcja: (agent) => `Sekcja: ${agent}`,
    zrodla: 'Źródła:',
    connectError: 'Backend nie odpowiada, spróbuj ponownie za chwilę.',
    timeoutError: 'Zbyt długi czas odpowiedzi, spróbuj ponownie.',
    httpError: 'Połączenie zostało przerwane, spróbuj ponownie.',
    parseError: 'Nieprawidłowa odpowiedź serwera, spróbuj ponownie.',
    noResponse: 'Backend nie odpowiedział, spróbuj ponownie za chwilę.',
    negacje: new Set(['nie', 'nie o to chodziło', 'nie o to mi chodziło', 'to nie to', 'źle']),
    szkicNaglowek: 'Szkic wiadomości do sprzedawcy',
    szkicNaglowki: {
      reklamacja: 'Szkic maila reklamacyjnego',
      zwrot: 'Szkic wiadomości o zwrocie',
      faktura: 'Szkic prośby o fakturę',
      eskalacja: 'Szkic zgłoszenia braku odpowiedzi sprzedawcy',
    },
    placeholder: 'Napisz wiadomość…',
    wyslij: 'Wyślij',
  },
  en: {
    ustawienia: 'Settings',
    mysle: 'Thinking…',
    gotowe: 'Done',
    bladStatus: 'Error',
    sekcja: (agent) => `Section: ${agent}`,
    zrodla: 'Sources:',
    connectError: "Backend isn't responding, try again in a moment.",
    timeoutError: 'Response took too long, try again.',
    httpError: 'Connection was interrupted, try again.',
    parseError: 'Invalid server response, try again.',
    noResponse: "Backend didn't respond, try again in a moment.",
    negacje: new Set(['no', "that's not it", 'wrong']),
    szkicNaglowek: 'Draft message to the seller',
    szkicNaglowki: {
      reklamacja: 'Draft complaint email',
      zwrot: 'Draft return message',
      faktura: 'Draft invoice request',
      eskalacja: 'Draft escalation message',
    },
    placeholder: 'Type a message…',
    wyslij: 'Send',
  },
};

export function jestNegacja(tekst: string, lang: Lang): boolean {
  return TEKSTY[lang].negacje.has(tekst.trim().toLowerCase());
}

export function naglowekSzkicu(lang: Lang, kategoria: string | null): string {
  const t = TEKSTY[lang];
  if (kategoria && kategoria in t.szkicNaglowki) {
    return t.szkicNaglowki[kategoria];
  }
  return t.szkicNaglowek;
}

export function zbudujZadanie(
  wiadomosc: string,
  historia: Wiadomosc[],
  agentPoprzedni: string | null,
  bezKorekty: boolean,
  lang: Lang
): ChatRequestBody {
  return {
    message: wiadomosc,
    history: historia,
    agent_poprzedni: agentPoprzedni,
    bez_korekty: bezKorekty,
    lang,
  };
}
