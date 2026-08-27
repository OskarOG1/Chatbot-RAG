export type Lang = 'pl' | 'en';

export type Tryb = 'rag' | 'email' | 'rozmowa' | 'ogolna';

export type Strona = 'kupujacy' | 'sprzedajacy';

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
  id?: string | null;
  agent: string;
  answer: string;
  sources: string[];
  citations: Cytat[];
  doprecyzowanie: string | null;
  nota_sekcji: string | null;
  oferta: string | null;
  oferta_kategoria: string | null;
  kategoria: string | null;
  naglowek_ui: string | null;
  podpowiedzi?: string[];
  tryb: Tryb;
}

export interface WyslijZadanie {
  email: string;
  temat: string;
  tresc: string;
  kategoria: string | null;
  lang: Lang;
  ticket: string | null;
}

export interface WyslijOdpowiedz {
  ticket: string;
}

export type SseEvent =
  | { typ: 'krok'; tekst: string }
  | { typ: 'token'; tekst: string }
  | { typ: 'reset' }
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
  possibleSourcesLabel: string;
  hintBuying: string;
  hintSelling: string;
  newChatToast: string;
  threadFallbackTitle: string;
  suggestionsByAgent: Record<string, string[]>;
  welcome: string;
  thinking: string;
  panel: string;
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
  sideBuying: string;
  sideSelling: string;
  discardDraft: string;
  confirmDiscardDraft: string;
  ticketBadge: (ticket: string, czas: string) => string;
  sentMessage: (ticket: string) => string;
  correctedMessage: (ticket: string) => string;
  editAfterSend: string;
  cancelSend: string;
  sendingCountdown: (n: number) => string;
  pendingSendOtherThread: (tytul: string) => string;
  mailHistoriaSkrot: (naglowek: string) => string;
  ocenaPytanie: string;
  ocenaDzieki: string;
  ocenaBlad: string;
  ocenaTak: string;
  ocenaNie: string;
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
    possibleSourcesLabel: 'Powiązane strony centrum pomocy',
    hintBuying: 'Pytasz jako kupujący',
    hintSelling: 'Pytasz jako sprzedający',
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
    thinking: 'Szukam w centrum pomocy',
    panel: 'Panel statystyk',
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
    sideBuying: 'Kupuję',
    sideSelling: 'Sprzedaję',
    discardDraft: 'Porzuć szkic',
    confirmDiscardDraft: 'Na pewno porzucić szkic wiadomości?',
    ticketBadge: (ticket, czas) => `Zgłoszenie ${ticket}, wysłano ${czas}`,
    sentMessage: (ticket) => `Wysłano zgłoszenie ${ticket} do sprzedawcy.`,
    correctedMessage: (ticket) => `Wysłano poprawioną wersję zgłoszenia ${ticket}.`,
    editAfterSend: 'Wyślij poprawioną wersję',
    cancelSend: 'Cofnij',
    sendingCountdown: (n) => `Wysyłam za ${n} s`,
    pendingSendOtherThread: (tytul) => `Trwa odliczanie wysyłki w wątku „${tytul}"`,
    mailHistoriaSkrot: (naglowek) => `Przygotowano wiadomość do sprzedawcy: ${naglowek}.`,
    ocenaPytanie: 'Czy ta odpowiedź pomogła?',
    ocenaDzieki: 'Dzięki za ocenę',
    ocenaBlad: 'Nie udało się zapisać oceny',
    ocenaTak: 'Odpowiedź pomogła',
    ocenaNie: 'Odpowiedź nie pomogła',
  },
  en: {
    title: 'Allegro Assistant',
    subtitle: 'Answers grounded in the help center knowledge base',
    brandSub: 'RAG · help center',
    newChat: 'New conversation',
    recent: 'Recent conversations',
    assistant: 'Assistant',
    sourcesLabel: 'Help center sources',
    possibleSourcesLabel: 'Possibly related help center pages',
    hintBuying: 'Asking as a buyer',
    hintSelling: 'Asking as a seller',
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
    thinking: 'Searching the help center',
    panel: 'Statistics panel',
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
    sideBuying: 'Buying',
    sideSelling: 'Selling',
    discardDraft: 'Discard draft',
    confirmDiscardDraft: 'Discard this draft message?',
    ticketBadge: (ticket, czas) => `Ticket ${ticket}, sent ${czas}`,
    sentMessage: (ticket) => `Sent ticket ${ticket} to the seller.`,
    correctedMessage: (ticket) => `Sent a corrected version of ticket ${ticket}.`,
    editAfterSend: 'Send a corrected version',
    cancelSend: 'Undo',
    sendingCountdown: (n) => `Sending in ${n}s`,
    pendingSendOtherThread: (tytul) => `A send is counting down in the "${tytul}" chat`,
    mailHistoriaSkrot: (naglowek) => `Prepared a message to the seller: ${naglowek}.`,
    ocenaPytanie: 'Was this answer helpful?',
    ocenaDzieki: 'Thanks for the feedback',
    ocenaBlad: 'Could not save the rating',
    ocenaTak: 'The answer helped',
    ocenaNie: 'The answer did not help',
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
  const poTemacie = linie.slice(indeksLinii + 1);
  let indeksDrugiegoTematu = -1;
  for (let i = 0; i < poTemacie.length; i++) {
    const oczyszczona = poTemacie[i].replace(/^[ \t]*#{0,6}[ \t]*/, '').replace(/\*\*/g, '').trim();
    if (/^(?:Temat|Subject):\s*(.+)$/.exec(oczyszczona)) {
      indeksDrugiegoTematu = i;
      break;
    }
  }
  const resztaTresci = indeksDrugiegoTematu === -1 ? poTemacie : poTemacie.slice(0, indeksDrugiegoTematu);
  const tresc = [...linie.slice(0, indeksLinii), ...resztaTresci]
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
