'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { wczytajJezyk } from '@/lib/threads';
import type { Lang } from '@/lib/chat';

interface TrescPrywatnosci {
  back: string;
  title: string;
  who: string;
  whoText: string;
  outbound: string;
  outboundText: string;
  stored: string;
  storedText: string[];
  notStored: string;
  notStoredText: string[];
  limits: string;
  limitsText: string[];
  deletion: string;
  deletionText: string;
}

const TRESC: Record<Lang, TrescPrywatnosci> = {
  pl: {
    back: '← Wróć',
    title: 'Jak przetwarzam dane',
    who: 'Kto prowadzi to demo',
    whoText:
      'Prowadzę to demo sam, jako projekt niekomercyjny i nieoficjalny, bez żadnego związku z Allegro.',
    outbound: 'Co wychodzi na zewnątrz',
    outboundText:
      'Treść pytania razem z pasującymi fragmentami artykułów trafia do zewnętrznego dostawcy inferencji modelu językowego. Jeśli poprosisz o wysyłkę wiadomości do sprzedawcy, jej treść i podany przeze Ciebie adres email trafiają jednorazowo do usługi Resend, która dostarcza obie wiadomości (do demo skrzynki sprzedawcy i do Ciebie z potwierdzeniem).',
    stored: 'Co zapisuję',
    storedText: [
      'Log zapytań: czas, język, sekcja tematyczna, informacja czy padła odpowiedź czy odmowa, czas odpowiedzi, informacja o trafieniu w pamięć podręczną oraz treść pytania po redakcji, czyli z zamaskowanymi adresami email, numerami telefonów, tokenami alfanumerycznymi (np. numerami zamówień) i adresami URL.',
      'Pojedyncze nierozpoznane słowa z pytań, których korektor literówek nie umiał dopasować do słownika, bez treści całego pytania.',
    ],
    notStored: 'Czego nie zapisuję',
    notStoredText: [
      'Historii rozmów: żyje wyłącznie w pamięci Twojej przeglądarki (localStorage), nigdy nie trafia na serwer.',
      'Twojego adresu email po wysłaniu wiadomości do sprzedawcy.',
      'Treści wygenerowanych odpowiedzi.',
      'Pamięć podręczna odpowiedzi żyje wyłącznie w pamięci procesu serwera, maksymalnie 200 wpisów, i znika po każdym restarcie.',
    ],
    limits: 'Limity',
    limitsText: [
      '15 pytań na minutę i 200 na dobę na całe demo.',
      '5 wysyłek wiadomości na minutę na całe demo.',
    ],
    deletion: 'Jak usunąć swoje dane',
    deletionText:
      'Przycisk „Usuń wszystkie" w panelu rozmów czyści historię zapisaną w Twojej przeglądarce. Wpis w logu serwera, jeśli chcesz, żebym go usunął, mogę skasować na żądanie, napisz do mnie przez kontakt podany w repozytorium projektu na GitHubie.',
  },
  en: {
    back: '← Back',
    title: 'How I handle data',
    who: 'Who runs this demo',
    whoText:
      'I run this demo on my own, as a non commercial, unofficial project with no affiliation to Allegro.',
    outbound: 'What leaves the server',
    outboundText:
      'Your question, together with the matching article excerpts, is sent to an external language model inference provider. If you ask me to draft a message to the seller, its content and the email address you enter are sent once to the Resend service, which delivers both messages, one to the demo seller inbox and one to you with a confirmation.',
    stored: 'What I store',
    storedText: [
      'A request log: time, language, topic section, whether the request got an answer or a refusal, response time, whether it was served from cache, and the question text after redaction, meaning email addresses, phone numbers, alphanumeric tokens (such as order numbers) and URLs are masked out.',
      'Single unrecognised words from questions that the typo corrector could not match to its dictionary, never the full question text.',
    ],
    notStored: "What I don't store",
    notStoredText: [
      "Conversation history: it lives only in your browser's storage (localStorage) and never reaches the server.",
      'Your email address after sending a message to the seller.',
      'The text of generated answers.',
      "The response cache lives only in the server process's memory, capped at 200 entries, and is cleared on every restart.",
    ],
    limits: 'Limits',
    limitsText: [
      '15 questions per minute and 200 per day across the whole demo.',
      '5 message sends per minute across the whole demo.',
    ],
    deletion: 'How to delete your data',
    deletionText:
      'The "Delete all" button in the conversation panel clears the history stored in your browser. If you want me to remove a server log entry, I can do that on request, reach out through the contact listed in the project repository on GitHub.',
  },
};

export default function PrywatnoscPage() {
  const [lang, setLang] = useState<Lang>('pl');

  useEffect(() => {
    setLang(wczytajJezyk() ?? 'pl');
  }, []);

  const t = TRESC[lang];

  return (
    <div style={{ maxWidth: 640, margin: '0 auto', padding: '48px 24px' }}>
      <Link href="/" style={{ fontSize: 13 }}>{t.back}</Link>
      <h1 style={{ fontSize: 22, marginTop: 24 }}>{t.title}</h1>

      <section style={{ marginTop: 24 }}>
        <h2 style={{ fontSize: 15 }}>{t.who}</h2>
        <p style={{ marginTop: 8, color: '#666' }}>{t.whoText}</p>
      </section>

      <section style={{ marginTop: 24 }}>
        <h2 style={{ fontSize: 15 }}>{t.outbound}</h2>
        <p style={{ marginTop: 8, color: '#666' }}>{t.outboundText}</p>
      </section>

      <section style={{ marginTop: 24 }}>
        <h2 style={{ fontSize: 15 }}>{t.stored}</h2>
        <ul style={{ marginTop: 8, color: '#666', paddingLeft: 20 }}>
          {t.storedText.map((linia) => (
            <li key={linia} style={{ marginTop: 6 }}>{linia}</li>
          ))}
        </ul>
      </section>

      <section style={{ marginTop: 24 }}>
        <h2 style={{ fontSize: 15 }}>{t.notStored}</h2>
        <ul style={{ marginTop: 8, color: '#666', paddingLeft: 20 }}>
          {t.notStoredText.map((linia) => (
            <li key={linia} style={{ marginTop: 6 }}>{linia}</li>
          ))}
        </ul>
      </section>

      <section style={{ marginTop: 24 }}>
        <h2 style={{ fontSize: 15 }}>{t.limits}</h2>
        <ul style={{ marginTop: 8, color: '#666', paddingLeft: 20 }}>
          {t.limitsText.map((linia) => (
            <li key={linia} style={{ marginTop: 6 }}>{linia}</li>
          ))}
        </ul>
      </section>

      <section style={{ marginTop: 24 }}>
        <h2 style={{ fontSize: 15 }}>{t.deletion}</h2>
        <p style={{ marginTop: 8, color: '#666' }}>{t.deletionText}</p>
      </section>
    </div>
  );
}
