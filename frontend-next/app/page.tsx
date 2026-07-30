'use client';

import { useEffect, useReducer, useRef, useState } from 'react';
import ChatMessage from '@/components/ChatMessage';
import Composer from '@/components/Composer';
import TypingBubble from '@/components/TypingBubble';
import EmailPanel from '@/components/EmailPanel';
import Topbar from '@/components/Topbar';
import Toast from '@/components/Toast';
import InfoBanner from '@/components/InfoBanner';
import { czytajSse } from '@/lib/sse';
import { ThemeContext, THEMES, type ThemeName } from '@/lib/theme';
import {
  TEKSTY,
  jestNegacja,
  rozdzielSzkic,
  zbudujZadanie,
  type ChatResponse,
  type Cytat,
  type Lang,
  type Wiadomosc,
  type WyslijOdpowiedz,
} from '@/lib/chat';

const EMAIL_WZORZEC = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface WiadomoscUi {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  citations?: Cytat[];
  doprecyzowanie?: string | null;
  action?: string | null;
}

interface PanelState {
  recipient: string;
  subject: string;
  body: string;
  originalSubject: string;
  originalBody: string;
  kategoria: string | null;
  trigger: string;
  clientEmail: string;
  sending: boolean;
}

interface State {
  messages: WiadomoscUi[];
  historiaApi: Wiadomosc[];
  ostatniAgent: string | null;
  ostatniaKorekta: string | null;
  aktualnyKrok: string | null;
  wysylanie: boolean;
}

const stanPoczatkowy: State = {
  messages: [{ id: 0, role: 'assistant', content: TEKSTY.pl.welcome }],
  historiaApi: [],
  ostatniAgent: null,
  ostatniaKorekta: null,
  aktualnyKrok: null,
  wysylanie: false,
};

type Action =
  | { type: 'busy_start' }
  | { type: 'busy_end' }
  | { type: 'krok'; tekst: string }
  | { type: 'user_bubble'; id: number; content: string }
  | {
      type: 'assistant_bubble';
      id: number;
      content: string;
      citations?: Cytat[];
      doprecyzowanie?: string | null;
      action?: string | null;
    }
  | { type: 'historia'; wiadomoscWyslana: string; odpowiedz: string; agent: string; doprecyzowanie: string | null; bezKorekty: boolean }
  | { type: 'welcome'; content: string };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'busy_start':
      return { ...state, wysylanie: true, aktualnyKrok: null };
    case 'busy_end':
      return { ...state, wysylanie: false, aktualnyKrok: null };
    case 'krok':
      return { ...state, aktualnyKrok: action.tekst };
    case 'user_bubble':
      return { ...state, messages: [...state.messages, { id: action.id, role: 'user', content: action.content }] };
    case 'assistant_bubble':
      return {
        ...state,
        messages: [
          ...state.messages,
          {
            id: action.id,
            role: 'assistant',
            content: action.content,
            citations: action.citations ?? [],
            doprecyzowanie: action.doprecyzowanie ?? null,
            action: action.action ?? null,
          },
        ],
      };
    case 'historia': {
      let historiaApi = state.historiaApi;
      let ostatniAgent = state.ostatniAgent;
      if (action.agent) {
        historiaApi = [
          ...historiaApi,
          { role: 'user', content: action.wiadomoscWyslana },
          { role: 'assistant', content: action.odpowiedz },
        ];
        ostatniAgent = action.agent;
      }
      let ostatniaKorekta = state.ostatniaKorekta;
      if (action.doprecyzowanie) {
        ostatniaKorekta = action.wiadomoscWyslana;
      } else if (!action.bezKorekty) {
        ostatniaKorekta = null;
      }
      return { ...state, historiaApi, ostatniAgent, ostatniaKorekta };
    }
    case 'welcome': {
      if (state.messages.length !== 1 || state.messages[0].id !== 0) return state;
      return { ...state, messages: [{ ...state.messages[0], content: action.content }] };
    }
    default:
      return state;
  }
}

export default function Page() {
  const [lang, setLang] = useState<Lang>('pl');
  const [themeName, setThemeName] = useState<ThemeName>('light');
  const [state, dispatch] = useReducer(reducer, stanPoczatkowy);
  const [panel, setPanel] = useState<PanelState | null>(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [streamBuffor, setStreamBuffor] = useState('');
  const idCounter = useRef(0);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const t = TEKSTY[lang];
  const th = THEMES[themeName];

  useEffect(() => {
    dispatch({ type: 'welcome', content: t.welcome });
  }, [t.welcome]);

  function nextId() {
    idCounter.current += 1;
    return idCounter.current;
  }

  function pokazToast(tekst: string) {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setToast(tekst);
    toastTimer.current = setTimeout(() => setToast(null), 2200);
  }

  async function poproszBackend(wiadomosc: string, bezKorekty: boolean): Promise<{ dane: ChatResponse | null; bladTekst: string | null }> {
    const body = zbudujZadanie(wiadomosc, state.historiaApi, state.ostatniAgent, bezKorekty, lang);
    let dane: ChatResponse | null = null;
    let bladTekst: string | null = null;

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.body) {
        bladTekst = t.noResponse;
      } else {
        for await (const ev of czytajSse(res.body)) {
          if (ev.typ === 'krok') {
            dispatch({ type: 'krok', tekst: ev.tekst });
          } else if (ev.typ === 'token') {
            setStreamBuffor((b) => b + ev.tekst);
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

  async function wyslij(promptUser: string) {
    const bezKorekty = jestNegacja(promptUser, lang) && Boolean(state.ostatniaKorekta);
    const wiadomosc = bezKorekty ? (state.ostatniaKorekta as string) : promptUser;

    dispatch({ type: 'busy_start' });
    setStreamBuffor('');
    dispatch({ type: 'user_bubble', id: nextId(), content: promptUser });

    const { dane, bladTekst } = await poproszBackend(wiadomosc, bezKorekty);

    dispatch({ type: 'busy_end' });
    setStreamBuffor('');
    dispatch({
      type: 'historia',
      wiadomoscWyslana: wiadomosc,
      odpowiedz: dane?.answer ?? '',
      agent: dane?.agent ?? '',
      doprecyzowanie: dane?.doprecyzowanie ?? null,
      bezKorekty,
    });

    if (dane?.tryb === 'email') {
      const { temat, tresc } = rozdzielSzkic(dane.answer);
      setPanel({
        recipient: lang === 'pl' ? 'Sprzedawca' : 'Seller',
        subject: temat,
        body: tresc,
        originalSubject: temat,
        originalBody: tresc,
        kategoria: dane.kategoria,
        trigger: wiadomosc,
        clientEmail: '',
        sending: false,
      });
      setPanelOpen(true);
      dispatch({ type: 'assistant_bubble', id: nextId(), content: t.panelOpened });
    } else {
      dispatch({
        type: 'assistant_bubble',
        id: nextId(),
        content: dane?.answer ?? bladTekst ?? t.noResponse,
        citations: dane?.citations ?? [],
        doprecyzowanie: dane?.doprecyzowanie ?? null,
        action: dane?.oferta ?? null,
      });
    }
  }

  function cofnijEdycjePanelu() {
    setPanel((p) => (p ? { ...p, subject: p.originalSubject, body: p.originalBody } : p));
  }

  function kopiujEmail() {
    if (!panel) return;
    navigator.clipboard?.writeText(`${panel.subject}\n\n${panel.body}`).catch(() => {});
    pokazToast(t.toastCopied);
  }

  async function wyslijEmail() {
    if (!panel || !EMAIL_WZORZEC.test(panel.clientEmail)) return;
    setPanel((p) => (p ? { ...p, sending: true } : p));

    try {
      const res = await fetch('/api/send-email', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          email: panel.clientEmail,
          temat: panel.subject,
          tresc: panel.body,
          kategoria: panel.kategoria,
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
      }
    } catch {
      pokazToast(t.toastSendError);
    }

    setPanel((p) => (p ? { ...p, sending: false } : p));
  }

  return (
    <ThemeContext.Provider value={th}>
      <div
        style={{
          width: '100%',
          height: '100vh',
          minHeight: 640,
          background: th.bgApp,
          fontFamily: 'var(--font-plus-jakarta), sans-serif',
          color: th.textPrimary,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        <Topbar
          lang={lang}
          theme={themeName}
          onSetLang={setLang}
          onToggleTheme={() => setThemeName((th2) => (th2 === 'light' ? 'dark' : 'light'))}
        />

        <div style={{ flex: '1 1 auto', display: 'flex', minHeight: 0, position: 'relative' }}>
          <div style={{ flex: '1 1 auto', display: 'flex', flexDirection: 'column', minWidth: 0 }}>
            <div
              style={{
                flex: '1 1 auto',
                overflowY: 'auto',
                padding: '28px 0',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
              }}
            >
              <div style={{ width: '100%', maxWidth: 680, display: 'flex', flexDirection: 'column', gap: 18, padding: '0 20px' }}>
                {state.messages.map((m) => (
                  <div key={m.id} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <ChatMessage role={m.role} content={m.content} citations={m.citations} action={m.action} onAction={wyslij} />
                    {m.doprecyzowanie && (
                      <div style={{ alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
                        <InfoBanner tekst={m.doprecyzowanie} />
                      </div>
                    )}
                  </div>
                ))}
                {state.wysylanie && streamBuffor && <ChatMessage role="assistant" content={streamBuffor} />}
                {state.wysylanie && !streamBuffor && <TypingBubble krok={state.aktualnyKrok} />}
              </div>
            </div>

            {panel && !panelOpen && (
              <div style={{ flex: '0 0 auto', padding: '0 20px 14px', display: 'flex', justifyContent: 'center' }}>
                <button
                  type="button"
                  onClick={() => setPanelOpen(true)}
                  style={{
                    border: `1.5px solid ${th.accent}`,
                    background: th.bgSurface,
                    color: th.accentText,
                    fontFamily: 'inherit',
                    fontWeight: 700,
                    fontSize: 13,
                    padding: '9px 16px',
                    borderRadius: 10,
                    cursor: 'pointer',
                  }}
                >
                  {t.openDraft}
                </button>
              </div>
            )}

            <div style={{ flex: '0 0 auto', padding: '16px 20px 22px', display: 'flex', justifyContent: 'center' }}>
              <Composer placeholder={t.placeholder} disabled={state.wysylanie} onSend={wyslij} />
            </div>
          </div>

          <EmailPanel
            lang={lang}
            open={panelOpen && panel !== null}
            recipient={panel?.recipient ?? ''}
            subject={panel?.subject ?? ''}
            body={panel?.body ?? ''}
            clientEmail={panel?.clientEmail ?? ''}
            emailValid={EMAIL_WZORZEC.test(panel?.clientEmail ?? '')}
            sending={panel?.sending ?? false}
            onSubjectChange={(v) => setPanel((p) => (p ? { ...p, subject: v } : p))}
            onBodyChange={(v) => setPanel((p) => (p ? { ...p, body: v } : p))}
            onClientEmailChange={(v) => setPanel((p) => (p ? { ...p, clientEmail: v } : p))}
            onClose={() => setPanelOpen(false)}
            onCopy={kopiujEmail}
            onUndo={cofnijEdycjePanelu}
            onSend={wyslijEmail}
          />

          <Toast tekst={toast} />
        </div>
      </div>
    </ThemeContext.Provider>
  );
}
