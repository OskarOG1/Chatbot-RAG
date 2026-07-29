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
  title: string;
  subtitle: string;
  connected: string;
  langButtonLabel: string;
  themeButtonLabel: { light: string; dark: string };
  connectError: string;
  noResponse: string;
  negacje: Set<string>;
  panelOpened: string;
  panelTitle: string;
  to: string;
  subjectLabel: string;
  copy: string;
  saveTemplate: string;
  regenerate: string;
  send: string;
  toastCopied: string;
  toastSaved: string;
  toastSent: string;
  placeholder: string;
}

export const TEKSTY: Record<Lang, Teksty> = {
  pl: {
    title: 'Pomoc, Asystent',
    subtitle: 'Odpowiada na podstawie bazy wiedzy centrum pomocy',
    connected: 'Połączono z bazą wiedzy',
    langButtonLabel: 'EN',
    themeButtonLabel: { light: 'Ciemny motyw', dark: 'Jasny motyw' },
    connectError: 'Backend nie odpowiada, spróbuj ponownie za chwilę.',
    noResponse: 'Backend nie odpowiedział, spróbuj ponownie za chwilę.',
    negacje: new Set(['nie', 'nie o to chodziło', 'nie o to mi chodziło', 'to nie to', 'źle']),
    panelOpened: 'Przygotowałem szkic wiadomości, zobacz panel obok.',
    panelTitle: 'Edytor wiadomości',
    to: 'Do:',
    subjectLabel: 'Temat',
    copy: 'Kopiuj',
    saveTemplate: 'Zapisz szablon',
    regenerate: 'Regeneruj',
    send: 'Wyślij wiadomość',
    toastCopied: 'Skopiowano do schowka',
    toastSaved: 'Zapisano jako szablon',
    toastSent: 'Funkcja wysyłki jest w przygotowaniu',
    placeholder: 'Napisz wiadomość…',
  },
  en: {
    title: 'Help, Assistant',
    subtitle: 'Answers grounded in the help center knowledge base',
    connected: 'Connected to knowledge base',
    langButtonLabel: 'PL',
    themeButtonLabel: { light: 'Dark theme', dark: 'Light theme' },
    connectError: "Backend isn't responding, try again in a moment.",
    noResponse: "Backend didn't respond, try again in a moment.",
    negacje: new Set(['no', "that's not it", 'wrong']),
    panelOpened: "I've prepared a draft message, see the panel on the right.",
    panelTitle: 'Message editor',
    to: 'To:',
    subjectLabel: 'Subject',
    copy: 'Copy',
    saveTemplate: 'Save template',
    regenerate: 'Regenerate',
    send: 'Send message',
    toastCopied: 'Copied to clipboard',
    toastSaved: 'Saved as template',
    toastSent: 'Sending is coming soon',
    placeholder: 'Type a message…',
  },
};

export function jestNegacja(tekst: string, lang: Lang): boolean {
  return TEKSTY[lang].negacje.has(tekst.trim().toLowerCase());
}

export function rozdzielSzkic(tekst: string): { temat: string; tresc: string } {
  const wzorzec = /^(?:Temat|Subject):\s*(.+)\n+/;
  const dopasowanie = wzorzec.exec(tekst);
  if (!dopasowanie) {
    return { temat: '', tresc: tekst };
  }
  return { temat: dopasowanie[1].trim(), tresc: tekst.slice(dopasowanie[0].length) };
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
