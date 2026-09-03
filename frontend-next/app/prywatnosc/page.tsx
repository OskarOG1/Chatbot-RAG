'use client';

import { useState } from 'react';
import Link from 'next/link';
import { wczytajJezyk } from '@/lib/threads';
import type { Lang } from '@/lib/chat';

interface TrescPrywatnosci {
  back: string;
  title: string;
  who: string;
  whoText: string;
  system: string;
  systemText: string;
  model: string;
  modelText: string[];
  compliance: string;
  complianceText: string;
  outbound: string;
  outboundText: string;
  stored: string;
  storedText: string[];
  notStored: string;
  notStoredText: string[];
  limits: string;
  limitsText: string[];
}

const TRESC: Record<Lang, TrescPrywatnosci> = {
  pl: {
    back: '← Wróć',
    title: 'Jak przetwarzam dane',
    who: 'Administrator',
    whoText:
      'Administratorem danych przetwarzanych w tym demo jest Oskar Grohman, kontakt: grohmanoskar@gmail.com. Projekt ma charakter niekomercyjny i nieoficjalny, bez żadnego związku z Allegro.',
    system: 'Charakter systemu i ograniczenia',
    systemText:
      'System został zaprojektowany tak, aby móc działać w całości lokalnie, bez wysyłania jakichkolwiek danych poza infrastrukturę, na której jest uruchomiony. W obecnej konfiguracji demonstracyjnej, ze względu na ograniczenia sprzętowe środowiska testowego (brak lokalnego GPU o wystarczającej mocy), część obliczeń jest zlecana zewnętrznemu dostawcy inferencji modelu językowego. To ograniczenie infrastrukturalne tej instancji demo, nie architektury systemu.',
    model: 'Model i infrastruktura',
    modelText: [
      'Model generujący odpowiedzi jest konfigurowalny osobno dla każdego języka. Obecnie dla polskiej wersji to Gemini 2.5 Flash (Google), wywoływany przez OpenRouter, a dla angielskiej Apertus 8B (swiss-ai/apertus-8b-instruct), udostępniany przez Public AI (publicai.co).',
      'Model oceniający trafność odpowiedzi (drugi etap weryfikacji, niewidoczny dla użytkownika): Bielik 11B v3.0 dla języka polskiego i Olmo 3 7B dla języka angielskiego, oba przez Public AI, niezależnie od dostawcy modelu odpowiadającego.',
      'Serwer aplikacji (backend, frontend, indeks wyszukiwania) jest hostowany w Finlandii, na terenie Unii Europejskiej.',
    ],
    compliance: 'Zgodność z AI Act',
    complianceText:
      'System stanowi chatbota w rozumieniu art. 50 unijnego rozporządzenia w sprawie sztucznej inteligencji (AI Act) i podlega obowiązkowi przejrzystości wynikającemu z tego przepisu. Niniejsza informacja stanowi jego realizację: informuję jawnie, że rozmawiasz z systemem sztucznej inteligencji, a nie z człowiekiem, a wygenerowane odpowiedzi mogą zawierać błędy.',
    outbound: 'Co wychodzi na zewnątrz',
    outboundText:
      'Treść pytania razem z pasującymi fragmentami artykułów trafia do dostawcy inferencji wskazanego w sekcji powyżej. Jeśli poprosisz o wysyłkę wiadomości do sprzedawcy, jej treść i podany przez Ciebie adres email trafiają jednorazowo do usługi Resend, która dostarcza obie wiadomości: do demo skrzynki sprzedawcy oraz do Ciebie, z potwierdzeniem.',
    stored: 'Co zapisuję',
    storedText: [
      'Log zapytań: czas, język, sekcja tematyczna, informacja czy padła odpowiedź czy odmowa, czas odpowiedzi, informacja o trafieniu w pamięć podręczną oraz treść pytania po redakcji, czyli z zamaskowanymi adresami email, numerami telefonów, tokenami alfanumerycznymi (np. numerami zamówień) i adresami URL.',
      'Pojedyncze nierozpoznane słowa z pytań, których korektor literówek nie umiał dopasować do słownika, bez treści całego pytania.',
      'Adres email podany przy przekazaniu pytania człowiekowi trafia do kolejki zgłoszeń. Zostaje usunięty po udzieleniu odpowiedzi przez operatora, a jeśli odpowiedź nie padnie, najpóźniej po 30 dniach od zgłoszenia. Kopie zapasowe kolejki mają rotację 14 dni, więc pełne usunięcie ze wszystkich kopii następuje w tym oknie, nie natychmiast. Adres służy wyłącznie do odesłania odpowiedzi.',
      'Pytanie przekazane człowiekowi trafia do kolejki w postaci zredagowanej, bo backend bierze je z logu zapytań, a nie z Twojej przeglądarki.',
    ],
    notStored: 'Czego nie zapisuję',
    notStoredText: [
      'Historii rozmów: żyje wyłącznie w pamięci Twojej przeglądarki (localStorage), nigdy nie trafia na serwer.',
      'Twojego adresu email po wysłaniu wiadomości do sprzedawcy: wysyłka do sprzedawcy przekazuje go jednorazowo do usługi Resend i nie zapisuje na serwerze.',
      'Treści wygenerowanych odpowiedzi.',
      'Pamięć podręczna odpowiedzi żyje wyłącznie w pamięci procesu serwera, maksymalnie 200 wpisów, i znika po każdym restarcie.',
    ],
    limits: 'Limity',
    limitsText: [
      '15 pytań na minutę i 200 na dobę na całe demo.',
      '5 wysyłek wiadomości na minutę na całe demo.',
    ],
  },
  en: {
    back: '← Back',
    title: 'How I handle data',
    who: 'Data controller',
    whoText:
      'The data controller for this demo is Oskar Grohman, contact: grohmanoskar@gmail.com. The project is non commercial and unofficial, with no affiliation to Allegro.',
    system: 'System design and current limitations',
    systemText:
      'This system is designed to run entirely on local infrastructure, without sending any data outside the environment it runs on. In its current demo configuration, due to hardware limits of the test environment (no local GPU with sufficient capacity), part of the computation is delegated to an external language model inference provider. This is a limitation of this particular demo instance, not of the system architecture.',
    model: 'Model and infrastructure',
    modelText: [
      'The answer generation model is configurable separately per language. It is currently Gemini 2.5 Flash (Google), called through OpenRouter, for the Polish version, and Apertus 8B (swiss-ai/apertus-8b-instruct), served by Public AI (publicai.co), for the English version.',
      'Answer quality judge model (a second, internal verification step not shown to the user): Bielik 11B v3.0 for Polish and Olmo 3 7B for English, both through Public AI, independent of the answering model provider.',
      'The application server (backend, frontend, search index) is hosted in Finland, within the European Union.',
    ],
    compliance: 'AI Act compliance',
    complianceText:
      'This system is a chatbot within the meaning of Article 50 of the EU Artificial Intelligence Act (AI Act) and is subject to the transparency obligation set out there. This notice fulfils that obligation: I am informing you explicitly that you are interacting with an artificial intelligence system, not a human, and that generated answers may contain errors.',
    outbound: 'What leaves the server',
    outboundText:
      'Your question, together with the matching article excerpts, is sent to the inference provider named in the section above. If you ask me to draft a message to the seller, its content and the email address you enter are sent once to the Resend service, which delivers both messages: one to the demo seller inbox and one to you, with a confirmation.',
    stored: 'What I store',
    storedText: [
      'A request log: time, language, topic section, whether the request got an answer or a refusal, response time, whether it was served from cache, and the question text after redaction, meaning email addresses, phone numbers, alphanumeric tokens (such as order numbers) and URLs are masked out.',
      'Single unrecognised words from questions that the typo corrector could not match to its dictionary, never the full question text.',
      'The email address you enter when you pass a question to a person goes into the request queue. It is deleted once an operator answers, and if no answer ever comes, at the latest 30 days after the request. Queue backups are rotated every 14 days, so full removal from all backup copies happens within that window, not immediately. The address is used only to send you the answer.',
      'A question passed to a person enters the queue in redacted form, because the backend takes it from the request log, not from your browser.',
    ],
    notStored: "What I don't store",
    notStoredText: [
      "Conversation history: it lives only in your browser's storage (localStorage) and never reaches the server.",
      'Your email address after sending a message to the seller: sending to the seller passes it once to the Resend service and does not store it on the server.',
      'The text of generated answers.',
      "The response cache lives only in the server process's memory, capped at 200 entries, and is cleared on every restart.",
    ],
    limits: 'Limits',
    limitsText: [
      '15 questions per minute and 200 per day across the whole demo.',
      '5 message sends per minute across the whole demo.',
    ],
  },
};

export default function PrywatnoscPage() {
  const [lang] = useState<Lang>(() => wczytajJezyk() ?? 'pl');

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
        <h2 style={{ fontSize: 15 }}>{t.system}</h2>
        <p style={{ marginTop: 8, color: '#666' }}>{t.systemText}</p>
      </section>

      <section style={{ marginTop: 24 }}>
        <h2 style={{ fontSize: 15 }}>{t.model}</h2>
        <ul style={{ marginTop: 8, color: '#666', paddingLeft: 20 }}>
          {t.modelText.map((linia) => (
            <li key={linia} style={{ marginTop: 6 }}>{linia}</li>
          ))}
        </ul>
      </section>

      <section style={{ marginTop: 24 }}>
        <h2 style={{ fontSize: 15 }}>{t.compliance}</h2>
        <p style={{ marginTop: 8, color: '#666' }}>{t.complianceText}</p>
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
    </div>
  );
}
