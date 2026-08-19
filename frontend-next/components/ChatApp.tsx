'use client';

import { useEffect, useRef, useState } from 'react';
import ChatMessage from '@/components/ChatMessage';
import Composer from '@/components/Composer';
import Suggestions from '@/components/Suggestions';
import TypingBubble from '@/components/TypingBubble';
import EmailPanel from '@/components/EmailPanel';
import Rail, { type RailItem } from '@/components/Rail';
import Toast from '@/components/Toast';
import InfoBanner from '@/components/InfoBanner';
import Link from 'next/link';
import { IkonaWykres } from '@/components/Ikony';
import { czytajSse } from '@/lib/sse';
import { ThemeContext, THEMES, BODY, DISPLAY, MONO, type ThemeName } from '@/lib/theme';
import {
  TEKSTY,
  jestNegacja,
  rozdzielSzkic,
  zbudujZadanie,
  type ChatResponse,
  type Lang,
  type Strona,
  type Wiadomosc,
  type WyslijOdpowiedz,
} from '@/lib/chat';
import {
  nowyThread,
  podmienPowitanie,
  tytulZWiadomosci,
  usunWatki,
  wczytajJezyk,
  wczytajStan,
  wczytajStrone,
  zapiszJezyk,
  zapiszStan,
  zapiszStrone,
  type Thread,
} from '@/lib/threads';
import { oczyscPodglad } from '@/lib/zrodla';

const EMAIL_WZORZEC = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const OKNO_COFNIECIA_MS = 15000;

function formatCzas(ts: number): string {
  const d = new Date(ts);
  const gg = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${gg}:${mm}`;
}

function panelLink(th: { line: string; surface: string; ink2: string }) {
  return {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 7,
    padding: '6px 12px',
    borderRadius: 100,
    border: `1px solid ${th.line}`,
    background: th.surface,
    color: th.ink2,
    fontSize: 11.5,
    fontWeight: 500,
    textDecoration: 'none',
    whiteSpace: 'nowrap',
  } as const;
}

function stanPoczatkowy(): { threads: Thread[]; activeId: string } {
  const zapis = wczytajStan();
  if (zapis) return zapis;
  const th0 = nowyThread('pl');
  return { threads: [th0], activeId: th0.id };
}

export default function ChatApp() {
  const [lang, setLangState] = useState<Lang>(() => wczytajJezyk() ?? 'pl');
  const [strona, setStronaState] = useState<Strona>(() => wczytajStrone() ?? 'kupujacy');
  const [themeName, setThemeName] = useState<ThemeName>('light');
  const [seed] = useState(stanPoczatkowy);
  const [threads, setThreads] = useState<Thread[]>(seed.threads);
  const [activeId, setActiveId] = useState<string>(seed.activeId);
  const [draft, setDraft] = useState('');
  const [streamBuffor, setStreamBuffor] = useState('');
  const [sendingIds, setSendingIds] = useState<Set<string>>(new Set());
  const [aktualnyKrok, setAktualnyKrok] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [selectMode, setSelectMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const msgCounter = useRef(
    seed.threads.reduce((max, th) => th.messages.reduce((m, msg) => Math.max(m, msg.id), max), 0)
  );
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortControllers = useRef<Map<string, AbortController>>(new Map());
  const wysylkaTimery = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const threadsRef = useRef<Thread[]>(threads);
  useEffect(() => {
    threadsRef.current = threads;
  }, [threads]);

  function oznaczWysylke(id: string, wysyla: boolean) {
    setSendingIds((ids) => {
      const kopia = new Set(ids);
      if (wysyla) kopia.add(id);
      else kopia.delete(id);
      return kopia;
    });
  }
  const t = TEKSTY[lang];
  const th = THEMES[themeName];

  useEffect(() => {
    zapiszStan(threads, activeId);
  }, [threads, activeId]);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  function setLang(nowyLang: Lang) {
    setLangState(nowyLang);
    zapiszJezyk(nowyLang);
    setThreads((ts) => podmienPowitanie(ts, nowyLang));
  }

  function setStrona(nowaStrona: Strona) {
    setStronaState(nowaStrona);
    zapiszStrone(nowaStrona);
  }

  const active = threads.find((x) => x.id === activeId) ?? null;

  function nextMsgId(): number {
    msgCounter.current += 1;
    return msgCounter.current;
  }

  function pokazToast(tekst: string) {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setToast(tekst);
    toastTimer.current = setTimeout(() => setToast(null), 2200);
  }

  function updateThread(id: string, fn: (t: Thread) => Thread) {
    setThreads((ts) => ts.map((x) => (x.id === id ? { ...fn(x), updatedAt: Date.now() } : x)));
  }

  function nowaRozmowa() {
    const th0 = nowyThread(lang);
    setThreads((ts) => [th0, ...ts]);
    setActiveId(th0.id);
    setDraft('');
    setStreamBuffor('');
    pokazToast(t.newChatToast);
  }

  function wybierzThread(id: string) {
    if (id === activeId) return;
    setActiveId(id);
    setDraft('');
    setStreamBuffor('');
  }

  function usunPozostale(pozostale: Thread[], usuwanyAktywny: boolean) {
    if (pozostale.length === 0) {
      const th0 = nowyThread(lang);
      setThreads([th0]);
      setActiveId(th0.id);
      setDraft('');
      setStreamBuffor('');
      setSelectedIds(new Set());
      setSelectMode(false);
      return;
    }
    setThreads(pozostale);
    if (usuwanyAktywny) {
      const najnowszy = [...pozostale].sort((a, b) => b.updatedAt - a.updatedAt)[0];
      setActiveId(najnowszy.id);
      setDraft('');
      setStreamBuffor('');
    }
    const pozostaleId = new Set(pozostale.map((x) => x.id));
    const przyciete = new Set([...selectedIds].filter((id) => pozostaleId.has(id)));
    setSelectedIds(przyciete);
    if (przyciete.size === 0) setSelectMode(false);
  }

  function usunThread(id: string) {
    if (sendingIds.has(id)) return;
    usunPozostale(usunWatki(threads, new Set([id])), id === activeId);
  }

  function usunWszystkie() {
    if (!window.confirm(t.confirmDeleteAll)) return;
    usunPozostale([], true);
  }

  function usunWybrane() {
    if (selectedIds.size === 0) return;
    if (!window.confirm(t.confirmDeleteSelected(selectedIds.size))) return;
    usunPozostale(usunWatki(threads, selectedIds), selectedIds.has(activeId));
  }

  function przelaczTrybWyboru() {
    setSelectMode((v) => !v);
    setSelectedIds(new Set());
  }

  function przelaczWybor(id: string) {
    setSelectedIds((ids) => {
      const kopia = new Set(ids);
      if (kopia.has(id)) kopia.delete(id);
      else kopia.add(id);
      return kopia;
    });
  }

  async function poproszBackend(
    wiadomosc: string,
    bezKorekty: boolean,
    historiaApi: Wiadomosc[],
    ostatniAgent: string | null,
    tid: string,
    signal: AbortSignal,
    stronaOverride?: Strona
  ): Promise<{ dane: ChatResponse | null; bladTekst: string | null }> {
    const body = zbudujZadanie(wiadomosc, historiaApi, ostatniAgent, bezKorekty, lang, stronaOverride ?? strona);
    let dane: ChatResponse | null = null;
    let bladTekst: string | null = null;

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body),
        signal,
      });
      if (!res.body) {
        bladTekst = t.noResponse;
      } else {
        for await (const ev of czytajSse(res.body)) {
          if (ev.typ === 'krok') {
            if (tid === activeId) setAktualnyKrok(ev.tekst);
          } else if (ev.typ === 'token') {
            if (tid === activeId) setStreamBuffor((b) => b + ev.tekst);
          } else if (ev.typ === 'wynik') {
            dane = ev.dane;
          } else if (ev.typ === 'blad') {
            bladTekst = ev.tekst;
          }
        }
      }
    } catch {
      bladTekst = t.connectError;
    }

    return { dane, bladTekst };
  }

  async function wyslij(promptUser: string, stronaOverride?: Strona, pomijDymkeUzytkownika?: boolean) {
    if (!promptUser.trim()) return;
    const tid = activeId;
    const thread = threads.find((x) => x.id === tid);
    if (!thread || sendingIds.has(tid)) return;

    const bezKorekty = jestNegacja(promptUser, lang) && Boolean(thread.ostatniaKorekta);
    const wiadomosc = bezKorekty ? (thread.ostatniaKorekta as string) : promptUser;

    const controller = new AbortController();
    abortControllers.current.set(tid, controller);
    oznaczWysylke(tid, true);
    if (tid === activeId) {
      setAktualnyKrok(null);
      setStreamBuffor('');
    }
    setDraft('');

    if (!pomijDymkeUzytkownika) {
      updateThread(tid, (x) => {
        const messages = [...x.messages, { id: nextMsgId(), role: 'user' as const, content: promptUser }];
        const title = x.title ?? tytulZWiadomosci(messages, t.threadFallbackTitle);
        return { ...x, messages, title };
      });
    }

    const { dane, bladTekst } = await poproszBackend(
      wiadomosc,
      bezKorekty,
      thread.historiaApi,
      thread.ostatniAgent,
      tid,
      controller.signal,
      stronaOverride
    );

    abortControllers.current.delete(tid);
    oznaczWysylke(tid, false);
    if (tid === activeId) {
      setAktualnyKrok(null);
      setStreamBuffor('');
    }

    updateThread(tid, (x) => {
      let historiaApi = x.historiaApi;
      let ostatniAgent = x.ostatniAgent;
      if (dane?.agent && dane.agent !== 'email') {
        historiaApi = [
          ...historiaApi,
          { role: 'user', content: wiadomosc },
          { role: 'assistant', content: dane.answer },
        ];
        ostatniAgent = dane.agent;
      } else if (dane?.tryb === 'email') {
        historiaApi = [
          ...historiaApi,
          { role: 'user', content: wiadomosc },
          { role: 'assistant', content: t.mailHistoriaSkrot(dane.naglowek_ui ?? '') },
        ];
      }
      let ostatniaKorekta = x.ostatniaKorekta;
      if (dane?.doprecyzowanie) {
        ostatniaKorekta = wiadomosc;
      } else if (!bezKorekty) {
        ostatniaKorekta = null;
      }
      return { ...x, historiaApi, ostatniAgent, ostatniaKorekta };
    });

    if (dane?.tryb === 'email') {
      const rozdzielone = rozdzielSzkic(dane.answer);
      const temat = rozdzielone.temat || dane.naglowek_ui || '';
      const tresc = rozdzielone.tresc;
      updateThread(tid, (x) => ({
        ...x,
        panel: {
          recipient: t.recipientSeller,
          subject: temat,
          body: tresc,
          originalSubject: temat,
          originalBody: tresc,
          kategoria: dane.kategoria,
          trigger: wiadomosc,
          clientEmail: '',
          sending: false,
          wyslano: null,
          edytujPoWyslaniu: false,
          odliczanieDo: null,
        },
        panelOpen: true,
        messages: [...x.messages, { id: nextMsgId(), role: 'assistant', content: t.panelOpened }],
      }));
    } else {
      updateThread(tid, (x) => {
        const poprzednia = x.messages[x.messages.length - 1];
        const powtorzonaDoprecyzacja =
          Boolean(pomijDymkeUzytkownika) &&
          poprzednia?.role === 'assistant' &&
          Boolean(dane?.doprecyzowanie) &&
          poprzednia.doprecyzowanie === dane?.doprecyzowanie;
        return {
          ...x,
          messages: [
            ...x.messages,
            {
              id: nextMsgId(),
              role: 'assistant',
              content: dane?.answer ?? bladTekst ?? t.noResponse,
              citations: dane?.citations ?? [],
              doprecyzowanie: powtorzonaDoprecyzacja ? null : dane?.doprecyzowanie ?? null,
              notaSekcji: dane?.nota_sekcji ?? null,
              action: dane?.oferta ?? null,
              pytanie: wiadomosc,
              sekcja: dane?.agent && dane.agent !== 'email' ? dane.agent : null,
              ocena: null,
              idZapytania: dane?.id ?? null,
            },
          ],
        };
      });
    }
  }

  async function ocenOdpowiedz(tid: string, msgId: number, ocena: 'gora' | 'dol') {
    const thread = threadsRef.current.find((x) => x.id === tid);
    const msg = thread?.messages.find((x) => x.id === msgId);
    if (!msg || msg.ocena || !msg.pytanie) return;

    function ustaw(wartosc: 'gora' | 'dol' | null) {
      updateThread(tid, (x) => ({
        ...x,
        messages: x.messages.map((mm) => (mm.id === msgId ? { ...mm, ocena: wartosc } : mm)),
      }));
    }

    ustaw(ocena);
    try {
      const res = await fetch('/api/ocena', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          ocena,
          id_zapytania: msg.idZapytania ?? null,
          pytanie: msg.pytanie,
          odpowiedz: msg.content,
          sekcja: msg.sekcja ?? null,
          lang,
          strona,
        }),
      });
      if (!res.ok) {
        ustaw(null);
        pokazToast(t.ocenaBlad);
      }
    } catch {
      ustaw(null);
      pokazToast(t.ocenaBlad);
    }
  }

  function setPanel(fn: (p: NonNullable<Thread['panel']>) => NonNullable<Thread['panel']>) {
    updateThread(activeId, (x) => (x.panel ? { ...x, panel: fn(x.panel) } : x));
  }

  function setPanelOpen(open: boolean) {
    updateThread(activeId, (x) => ({ ...x, panelOpen: open }));
  }

  function cofnijEdycjePanelu() {
    setPanel((p) => ({ ...p, subject: p.originalSubject, body: p.originalBody }));
  }

  function kopiujEmail() {
    if (!active?.panel) return;
    navigator.clipboard?.writeText(`${active.panel.subject}\n\n${active.panel.body}`).catch(() => {});
    pokazToast(t.toastCopied);
  }

  async function wykonajWysylkeEmail(tid: string) {
    const panel = threadsRef.current.find((x) => x.id === tid)?.panel;
    if (!panel) return;
    if (!EMAIL_WZORZEC.test(panel.clientEmail)) {
      updateThread(tid, (x) => (x.panel ? { ...x, panel: { ...x.panel, odliczanieDo: null } } : x));
      pokazToast(t.toastInvalidEmail);
      return;
    }
    const ticketKorekty = panel.wyslano?.ticket ?? null;

    updateThread(tid, (x) => (x.panel ? { ...x, panel: { ...x.panel, sending: true, odliczanieDo: null } } : x));

    try {
      const res = await fetch('/api/send-email', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          email: panel.clientEmail,
          temat: panel.subject,
          tresc: panel.body,
          kategoria: panel.kategoria,
          lang,
          ticket: ticketKorekty,
        }),
      });

      if (res.status === 503) {
        pokazToast(t.toastSendConfigError);
      } else if (res.status === 422) {
        pokazToast(t.toastInvalidEmail);
      } else if (!res.ok) {
        pokazToast(t.toastSendError);
      } else {
        const dane: WyslijOdpowiedz = await res.json();
        pokazToast(t.toastSent(dane.ticket));
        const tekstWiadomosci = ticketKorekty ? t.correctedMessage(dane.ticket) : t.sentMessage(dane.ticket);
        updateThread(tid, (x) =>
          x.panel
            ? {
                ...x,
                panel: { ...x.panel, wyslano: { ticket: dane.ticket, czas: Date.now() }, edytujPoWyslaniu: false },
                messages: [...x.messages, { id: nextMsgId(), role: 'assistant' as const, content: tekstWiadomosci }],
              }
            : x
        );
      }
    } catch {
      pokazToast(t.toastSendError);
    }

    updateThread(tid, (x) => (x.panel ? { ...x, panel: { ...x.panel, sending: false } } : x));
  }

  function zaplanujWysylkeEmail() {
    const panel = active?.panel;
    if (!panel || !EMAIL_WZORZEC.test(panel.clientEmail) || panel.sending) return;
    if (panel.wyslano && !panel.edytujPoWyslaniu) return;
    const tid = activeId;
    setPanel((p) => ({ ...p, odliczanieDo: Date.now() + OKNO_COFNIECIA_MS }));
    const timer = setTimeout(() => {
      wysylkaTimery.current.delete(tid);
      wykonajWysylkeEmail(tid);
    }, OKNO_COFNIECIA_MS);
    wysylkaTimery.current.set(tid, timer);
  }

  function cofnijWysylkeEmailDla(tid: string) {
    const timer = wysylkaTimery.current.get(tid);
    if (timer) {
      clearTimeout(timer);
      wysylkaTimery.current.delete(tid);
    }
    updateThread(tid, (x) => (x.panel ? { ...x, panel: { ...x.panel, odliczanieDo: null } } : x));
  }

  function cofnijWysylkeEmail() {
    cofnijWysylkeEmailDla(activeId);
  }

  function rozpocznijEdycjePoWyslaniu() {
    setPanel((p) => ({ ...p, edytujPoWyslaniu: true }));
  }

  function odrzucPanel() {
    const panel = active?.panel;
    if (!panel) return;
    const maZmiany = panel.subject !== panel.originalSubject || panel.body !== panel.originalBody || panel.wyslano !== null;
    if (maZmiany && !window.confirm(t.confirmDiscardDraft)) return;
    const tid = activeId;
    const timer = wysylkaTimery.current.get(tid);
    if (timer) {
      clearTimeout(timer);
      wysylkaTimery.current.delete(tid);
    }
    updateThread(tid, (x) => ({ ...x, panel: null, panelOpen: false }));
  }

  if (!active) {
    return (
      <ThemeContext.Provider value={th}>
        <div style={{ width: '100%', height: '100vh', background: th.canvas }} />
      </ThemeContext.Provider>
    );
  }

  const railItems: RailItem[] = [...threads]
    .sort((a, b) => b.updatedAt - a.updatedAt)
    .map((x) => ({
      id: x.id,
      title: x.title ?? t.threadFallbackTitle,
      meta: formatCzas(x.updatedAt),
      active: x.id === activeId,
    }));

  const panelOtwarty = active.panelOpen && active.panel !== null;
  const pokazTyping = sendingIds.has(activeId);
  const wysylkiWInnychWatkach = threads.filter((x) => x.id !== activeId && x.panel?.odliczanieDo != null);

  return (
    <ThemeContext.Provider value={th}>
      <div
        style={{
          width: '100%',
          height: '100vh',
          minHeight: 660,
          display: 'flex',
          background: th.canvas,
          color: th.ink,
          fontFamily: BODY,
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <Rail
          lang={lang}
          theme={themeName}
          items={railItems}
          onNew={nowaRozmowa}
          onSelect={wybierzThread}
          onSetLang={setLang}
          onToggleTheme={() => setThemeName((x) => (x === 'light' ? 'dark' : 'light'))}
          selectMode={selectMode}
          selectedIds={selectedIds}
          onToggleSelectMode={przelaczTrybWyboru}
          onToggleSelected={przelaczWybor}
          onDeleteOne={usunThread}
          onDeleteAll={usunWszystkie}
          onDeleteSelected={usunWybrane}
        />

        <main style={{ flex: '1 1 auto', minWidth: 'min(400px, 100%)', display: 'flex', flexDirection: 'column' }}>
          <header
            style={{
              flex: '0 0 auto',
              padding: '20px 32px',
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              gap: 20,
              flexWrap: 'wrap',
              borderBottom: `1px solid ${th.line}`,
              background: th.canvas,
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 0 }}>
              <h1 style={{ margin: 0, fontFamily: DISPLAY, fontSize: 21, fontWeight: 700, letterSpacing: '-0.025em', color: th.ink }}>
                {active.title ?? t.threadFallbackTitle}
              </h1>
              <span style={{ fontFamily: MONO, fontSize: 11, color: th.ink3 }}>{t.subtitle}</span>
            </div>
            <div style={{ flex: '0 0 auto', display: 'inline-flex', alignItems: 'center', gap: 10 }}>
              <Link href="/admin" style={panelLink(th)}>
                <IkonaWykres color={th.ink2} />
                {t.panel}
              </Link>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 7,
                  padding: '6px 12px',
                  borderRadius: 100,
                  border: `1px solid ${th.line}`,
                  background: th.surface,
                  fontSize: 11.5,
                  fontWeight: 500,
                  color: th.ink2,
                }}
              >
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: th.dot, flex: '0 0 auto' }} />
                {t.connected}
              </div>
            </div>
          </header>

          <div style={{ flex: '1 1 auto', overflowY: 'auto', padding: '32px 32px 8px' }}>
            <div style={{ maxWidth: 760, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 30 }}>
              {active.messages.map((m) => (
                <div key={m.id} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <ChatMessage
                    role={m.role}
                    content={m.content}
                    lang={lang}
                    citations={m.citations}
                    notaSekcji={m.notaSekcji}
                    action={m.action}
                    onAction={wyslij}
                    ocena={m.ocena}
                    onOcena={
                      m.role === 'assistant' && m.sekcja && m.pytanie
                        ? (wybor) => ocenOdpowiedz(activeId, m.id, wybor)
                        : undefined
                    }
                  />
                  {m.doprecyzowanie && (
                    <div style={{ alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
                      <InfoBanner tekst={m.doprecyzowanie} />
                    </div>
                  )}
                </div>
              ))}
              {pokazTyping && streamBuffor && <ChatMessage role="assistant" content={oczyscPodglad(streamBuffor)} lang={lang} />}
              {pokazTyping && !streamBuffor && <TypingBubble krok={aktualnyKrok} thinking={t.connected} />}
            </div>
          </div>

          <div style={{ flex: '0 0 auto', padding: '14px 32px 24px', background: `linear-gradient(to top, ${th.canvas} 55%, transparent)` }}>
            <div style={{ maxWidth: 760, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
              {active.panel && !active.panelOpen && (
                <button
                  type="button"
                  onClick={() => setPanelOpen(true)}
                  style={{
                    alignSelf: 'flex-start',
                    border: `1px solid ${th.accentLine}`,
                    background: th.accentSoft,
                    color: th.accentInk,
                    fontFamily: BODY,
                    fontWeight: 600,
                    fontSize: 12.5,
                    padding: '8px 14px',
                    borderRadius: 100,
                    cursor: 'pointer',
                  }}
                >
                  {t.openDraft}
                </button>
              )}
              <Suggestions items={t.suggestionsByAgent[active.ostatniAgent ?? ''] ?? t.suggestionsByAgent.default} onPick={setDraft} />
              <Composer
                value={draft}
                placeholder={t.placeholder}
                hint={strona === 'kupujacy' ? t.hintBuying : t.hintSelling}
                sendLabel={t.sendShort}
                disabled={pokazTyping}
                strona={strona}
                sideBuyingLabel={t.sideBuying}
                sideSellingLabel={t.sideSelling}
                onChange={setDraft}
                onSend={() => wyslij(draft.trim())}
                onSetStrona={setStrona}
              />
            </div>
          </div>
        </main>

        <EmailPanel
          lang={lang}
          open={panelOtwarty}
          recipient={active.panel?.recipient ?? ''}
          subject={active.panel?.subject ?? ''}
          body={active.panel?.body ?? ''}
          clientEmail={active.panel?.clientEmail ?? ''}
          emailValid={EMAIL_WZORZEC.test(active.panel?.clientEmail ?? '')}
          sending={active.panel?.sending ?? false}
          wyslano={active.panel?.wyslano ? { ticket: active.panel.wyslano.ticket, czasTekst: formatCzas(active.panel.wyslano.czas) } : null}
          edytujPoWyslaniu={active.panel?.edytujPoWyslaniu ?? false}
          odliczanieDo={active.panel?.odliczanieDo ?? null}
          onSubjectChange={(v) => setPanel((p) => ({ ...p, subject: v }))}
          onBodyChange={(v) => setPanel((p) => ({ ...p, body: v }))}
          onClientEmailChange={(v) => setPanel((p) => ({ ...p, clientEmail: v }))}
          onClose={() => setPanelOpen(false)}
          onDiscard={odrzucPanel}
          onCopy={kopiujEmail}
          onUndo={cofnijEdycjePanelu}
          onSend={zaplanujWysylkeEmail}
          onCancelSend={cofnijWysylkeEmail}
          onStartEdit={rozpocznijEdycjePoWyslaniu}
        />

        {wysylkiWInnychWatkach.length > 0 && (
          <div
            style={{
              position: 'fixed',
              bottom: 20,
              left: 20,
              zIndex: 40,
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
            }}
          >
            {wysylkiWInnychWatkach.map((x) => (
              <div
                key={x.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '10px 14px',
                  borderRadius: 10,
                  border: `1px solid ${th.line}`,
                  background: th.surface,
                  color: th.ink,
                  fontSize: 12.5,
                  fontWeight: 600,
                  boxShadow: th.shadow,
                }}
              >
                {t.pendingSendOtherThread(x.title ?? t.threadFallbackTitle)}
                <button
                  type="button"
                  onClick={() => cofnijWysylkeEmailDla(x.id)}
                  style={{
                    border: `1px solid ${th.accentLine}`,
                    background: th.accentSoft,
                    color: th.accentInk,
                    borderRadius: 100,
                    padding: '5px 11px',
                    fontFamily: BODY,
                    fontWeight: 700,
                    fontSize: 11.5,
                    cursor: 'pointer',
                  }}
                >
                  {t.cancelSend}
                </button>
              </div>
            ))}
          </div>
        )}

        <Toast tekst={toast} />
      </div>
    </ThemeContext.Provider>
  );
}
