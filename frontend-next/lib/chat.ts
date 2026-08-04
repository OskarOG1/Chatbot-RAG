export type Lang = 'pl' | 'en';

export type Tryb = 'rag' | 'email';

export type Strona = 'auto' | 'kupujacy' | 'sprzedajacy';

export interface Wiadomosc {
  role: 'user' | 'assistant';
  content: string;
}

export interface Cytat {
  n: number;
  url: string;
  tytul?: string | null;
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
  naglowek_ui: string | null;
  tryb: Tryb;
  pyta_strona: boolean;
}

export interface WyslijZadanie {
  email: string;
  temat: string;
  tresc: string;
  kategoria: string | null;
  lang: Lang;
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
  strona: Strona;
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
  suggestionsByAgent: Record<string, string[]>;
  welcome: string;
  connected: string;
  themeButtonLabel: { light: string; dark: string };
  connectError: string;
  noResponse: string;
  negacje: Set<string>;
  deleteChat: string;
  deleteCurrent: string;
  deleteAll: string;
  deleteSelected: string;
  selectMode: string;
  cancelSelect: string;
  confirmDeleteAll: string;
  confirmDeleteSelected: (n: number) => string;
  panelOpened: string;
  panelTitle: string;
  to: string;
  subjectLabel: string;
  copy: string;
  undoEdits: string;
  alignLeft: string;
  alignCenter: string;
  alignRight: string;
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
  recipientSeller: string;
  sendShort: string;
  sideAuto: string;
  sideBuying: string;
  sideSelling: string;
  sideAskBuyer: string;
  sideAskSeller: string;
}

function odmianaRozmow(n: number): string {
  if (n === 1) return 'rozmowę';
  const ostatnia = n % 10;
  const dziesiatki = n % 100;
  if (ostatnia >= 2 && ostatnia <= 4 && (dziesiatki < 10 || dziesiatki >= 20)) return 'rozmowy';
  return 'rozmów';
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
    suggestionsByAgent: {
      default: ['Jak zgłosić brak dostawy?', 'Ile mam czasu na zwrot?', 'Kiedy dostanę pieniądze?'],
      konto: ['Jak zresetować hasło?', 'Jak zmienić dane konta?', 'Podejrzewam włamanie na konto, co robić?'],
      zakupy: ['Jak zgłosić brak dostawy?', 'Ile mam czasu na zwrot?', 'Jak sprawdzić historię zakupów?'],
      platnosci: ['Kiedy dostanę pieniądze za zwrot?', 'Jak sprawdzić status płatności?', 'Jak zapłacić przez Allegro Pay?'],
    },
    welcome:
      'Witam, jestem Twoim asystentem Allegro. Mogę:\n\n* odpowiadać na pytania na podstawie bazy wiedzy centrum pomocy\n* przygotować wiadomość do sprzedawcy w sprawie reklamacji, zwrotu, faktury lub eskalacji sporu\n\nPrzy oknie wiadomości możesz wybrać, czy pytasz jako kupujący, czy jako sprzedający.\n\nNapisz, w czym mogę pomóc.',
    connected: 'Połączono z bazą wiedzy',
    themeButtonLabel: { light: 'Ciemny motyw', dark: 'Jasny motyw' },
    connectError: 'Backend nie odpowiada, spróbuj ponownie za chwilę.',
    noResponse: 'Backend nie odpowiedział, spróbuj ponownie za chwilę.',
    negacje: new Set(['nie', 'nie o to chodziło', 'nie o to mi chodziło', 'to nie to', 'źle']),
    deleteChat: 'Usuń rozmowę',
    deleteCurrent: 'Usuń bieżącą rozmowę',
    deleteAll: 'Usuń wszystkie',
    deleteSelected: 'Usuń wybrane',
    selectMode: 'Wybierz',
    cancelSelect: 'Anuluj',
    confirmDeleteAll: 'Na pewno usunąć wszystkie rozmowy?',
    confirmDeleteSelected: (n) => `Na pewno usunąć ${n} ${odmianaRozmow(n)}?`,
    panelOpened: 'Przygotowałem szkic wiadomości, zobacz panel obok.',
    panelTitle: 'Edytor wiadomości',
    to: 'Do:',
    subjectLabel: 'Temat',
    copy: 'Kopiuj',
    undoEdits: 'Cofnij edycje',
    alignLeft: 'Wyrównaj do lewej',
    alignCenter: 'Wyśrodkuj',
    alignRight: 'Wyrównaj do prawej',
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
    emailPrivacyNote: 'Nie przechowuję Twojego adresu po wysyłce; treść pytania trafia do logu w formie zredagowanej.',
    placeholder: 'Napisz wiadomość…',
    recipientSeller: 'Sprzedawca',
    sendShort: 'Wyślij',
    sideAuto: 'Auto',
    sideBuying: 'Kupuję',
    sideSelling: 'Sprzedaję',
    sideAskBuyer: 'Kupujący',
    sideAskSeller: 'Sprzedający',
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
    suggestionsByAgent: {
      default: ['How do I report an order that never arrived?', 'How long do I have to return an item?', 'When will I get my money back?'],
      konto: ['How do I reset my password?', 'How do I change my account details?', 'I suspect my account was hacked, what should I do?'],
      zakupy: ['How do I report an order that never arrived?', 'How long do I have to return an item?', 'How do I check my order history?'],
      platnosci: ['When will I get my refund?', 'How do I check the status of a payment?', 'How do I pay with Allegro Pay?'],
    },
    welcome:
      "Welcome, I'm the Allegro assistant. I can:\n\n* answer questions using the help center knowledge base\n* prepare a message to the seller about a complaint, return, invoice, or dispute escalation\n\nNext to the message box you can choose whether you're asking as a buyer or as a seller.\n\nTell me what you need help with.",
    connected: 'Connected to the knowledge base',
    themeButtonLabel: { light: 'Switch to dark theme', dark: 'Switch to light theme' },
    connectError: "The backend isn't responding right now, please try again in a moment.",
    noResponse: "The backend didn't respond, please try again in a moment.",
    negacje: new Set(['no', "that's not it", 'wrong', 'not what i meant', 'that is not what i meant']),
    deleteChat: 'Delete chat',
    deleteCurrent: 'Delete current chat',
    deleteAll: 'Delete all',
    deleteSelected: 'Delete selected',
    selectMode: 'Select',
    cancelSelect: 'Cancel',
    confirmDeleteAll: 'Delete all conversations?',
    confirmDeleteSelected: (n) => `Delete ${n} conversation${n === 1 ? '' : 's'}?`,
    panelOpened: "I've prepared a draft message, see the panel on the right.",
    panelTitle: 'Message editor',
    to: 'To:',
    subjectLabel: 'Subject',
    copy: 'Copy',
    undoEdits: 'Undo edits',
    alignLeft: 'Align left',
    alignCenter: 'Align center',
    alignRight: 'Align right',
    openDraft: 'Open message draft',
    send: 'Send message',
    sending: 'Sending…',
    toastCopied: 'Copied to clipboard',
    toastSent: (ticket) => `Sent, your ticket number is ${ticket}`,
    toastSendConfigError: 'Demo sending isn\'t configured right now, please try again later.',
    toastSendError: 'Sending failed, please try again.',
    toastInvalidEmail: 'Please enter a valid email address.',
    emailFieldLabel: 'Your email address',
    emailPlaceholder: 'e.g. jane.doe@mail.com',
    emailPrivacyNote: 'I don\'t store your address after sending; the question text is kept in the log in redacted form.',
    placeholder: 'Type a message…',
    recipientSeller: 'Seller',
    sendShort: 'Send',
    sideAuto: 'Auto',
    sideBuying: 'Buying',
    sideSelling: 'Selling',
    sideAskBuyer: 'Buyer',
    sideAskSeller: 'Seller',
  },
};

export function jestNegacja(tekst: string, lang: Lang): boolean {
  return TEKSTY[lang].negacje.has(tekst.trim().toLowerCase());
}

export function rozdzielSzkic(tekst: string): { temat: string; tresc: string } {
  const preambula =
    /^(?:Szkic wiadomości do .+?\(uzupełnij dane przed wysłaniem\):|Draft message to .+?\(fill in your details before sending\):)\s*\n+/;
  const reszta = tekst.replace(preambula, '');

  const linie = reszta.split('\n');
  let indeksLinii = -1;
  let temat = '';
  for (let i = 0; i < linie.length; i++) {
    const oczyszczona = linie[i].replace(/^[ \t]*#{0,6}[ \t]*/, '').replace(/\*\*/g, '').trim();
    const dopasowanie = /^(?:Temat|Subject):\s*(.+)$/.exec(oczyszczona);
    if (dopasowanie) {
      indeksLinii = i;
      temat = dopasowanie[1].trim();
      break;
    }
  }

  if (indeksLinii === -1) {
    return { temat: '', tresc: reszta.trim() };
  }
  const tresc = [...linie.slice(0, indeksLinii), ...linie.slice(indeksLinii + 1)]
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
  return { temat, tresc };
}

export function zbudujZadanie(
  wiadomosc: string,
  historia: Wiadomosc[],
  agentPoprzedni: string | null,
  bezKorekty: boolean,
  lang: Lang,
  strona: Strona
): ChatRequestBody {
  return {
    message: wiadomosc,
    history: historia,
    agent_poprzedni: agentPoprzedni,
    bez_korekty: bezKorekty,
    lang,
    strona,
  };
}
