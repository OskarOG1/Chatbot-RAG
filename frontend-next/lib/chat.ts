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

export interface WyslijZadanie {
  email: string;
  temat: string;
  tresc: string;
  kategoria: string | null;
}

export interface WyslijOdpowiedz {
  ticket: string;
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
  brandSub: string;
  newChat: string;
  recent: string;
  assistant: string;
  sourcesLabel: string;
  composerHint: string;
  newChatToast: string;
  threadFallbackTitle: string;
  suggestions: string[];
  welcome: string;
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
  undoEdits: string;
  openDraft: string;
  send: string;
  sending: string;
  toastCopied: string;
  toastSent: (ticket: string) => string;
  toastSendConfigError: string;
  toastSendError: string;
  toastInvalidEmail: string;
  emailFieldLabel: string;
  emailPlaceholder: string;
  emailPrivacyNote: string;
  placeholder: string;
}

export const TEKSTY: Record<Lang, Teksty> = {
  pl: {
    title: 'Asystent Allegro',
    subtitle: 'Odpowiada na podstawie bazy wiedzy centrum pomocy',
    brandSub: 'RAG · centrum pomocy',
    newChat: 'Nowa rozmowa',
    recent: 'Ostatnie rozmowy',
    assistant: 'Asystent',
    sourcesLabel: 'Źródła z centrum pomocy',
    composerHint: 'Enter wysyła · Shift + Enter nowa linia',
    newChatToast: 'Rozpoczęto nową rozmowę',
    threadFallbackTitle: 'Nowa rozmowa',
    suggestions: ['Jak zgłosić brak dostawy?', 'Ile mam czasu na zwrot?', 'Kiedy dostanę pieniądze?'],
    welcome:
      'Witam, jestem Twoim asystentem Allegro. Mogę:\n\n* odpowiadać na pytania na podstawie bazy wiedzy centrum pomocy\n* przygotować wiadomość do sprzedawcy w sprawie reklamacji, zwrotu, faktury lub eskalacji sporu\n\nNapisz, w czym mogę pomóc.',
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
    undoEdits: 'Cofnij edycje',
    openDraft: 'Otwórz szkic wiadomości',
    send: 'Wyślij wiadomość',
    sending: 'Wysyłanie…',
    toastCopied: 'Skopiowano do schowka',
    toastSent: (ticket) => `Wysłano, numer zgłoszenia: ${ticket}`,
    toastSendConfigError: 'Wysyłka demo nie jest skonfigurowana, spróbuj ponownie później.',
    toastSendError: 'Wysyłka się nie powiodła, spróbuj ponownie.',
    toastInvalidEmail: 'Podaj poprawny adres email.',
    emailFieldLabel: 'Twój adres email',
    emailPlaceholder: 'np. jan.kowalski@poczta.pl',
    emailPrivacyNote: 'Nie przechowujemy Twojego adresu ani treści wiadomości po wysyłce.',
    placeholder: 'Napisz wiadomość…',
  },
  en: {
    title: 'Allegro Assistant',
    subtitle: 'Answers grounded in the help center knowledge base',
    brandSub: 'RAG · help center',
    newChat: 'New conversation',
    recent: 'Recent conversations',
    assistant: 'Assistant',
    sourcesLabel: 'Help center sources',
    composerHint: 'Enter sends · Shift + Enter for a new line',
    newChatToast: 'Started a new conversation',
    threadFallbackTitle: 'New conversation',
    suggestions: ['How do I report a non delivery?', 'How long do I have to return it?', 'When will I get my money back?'],
    welcome:
      "Welcome, I am your Allegro assistant. I can:\n\n* answer questions using the help center knowledge base\n* prepare a message to the seller about a complaint, return, invoice, or dispute escalation\n\nTell me what you need help with.",
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
    undoEdits: 'Undo edits',
    openDraft: 'Open message draft',
    send: 'Send message',
    sending: 'Sending…',
    toastCopied: 'Copied to clipboard',
    toastSent: (ticket) => `Sent, ticket number: ${ticket}`,
    toastSendConfigError: 'Demo sending is not configured, try again later.',
    toastSendError: 'Sending failed, try again.',
    toastInvalidEmail: 'Enter a valid email address.',
    emailFieldLabel: 'Your email address',
    emailPlaceholder: 'e.g. jane.doe@mail.com',
    emailPrivacyNote: 'We do not store your address or message content after sending.',
    placeholder: 'Type a message…',
  },
};

export function jestNegacja(tekst: string, lang: Lang): boolean {
  return TEKSTY[lang].negacje.has(tekst.trim().toLowerCase());
}

export function rozdzielSzkic(tekst: string): { temat: string; tresc: string } {
  const preambula =
    /^(?:Szkic wiadomości do .+?\(uzupełnij dane przed wysłaniem\):|Draft message to .+?\(fill in your details before sending\):)\s*\n+/;
  const reszta = tekst.replace(preambula, '');

  const wzorzecTematu = /^(?:Temat|Subject):\s*(.+)$/m;
  const dopasowanie = wzorzecTematu.exec(reszta);
  if (!dopasowanie) {
    return { temat: '', tresc: reszta.trim() };
  }
  const przed = reszta.slice(0, dopasowanie.index);
  const po = reszta.slice(dopasowanie.index + dopasowanie[0].length);
  const tresc = (przed + po).replace(/\n{3,}/g, '\n\n').trim();
  return { temat: dopasowanie[1].trim(), tresc };
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
