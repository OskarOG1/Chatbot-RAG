'use client';

import { useReducer, useState } from 'react';
import ChatMessage from '@/components/ChatMessage';
import Composer from '@/components/Composer';
import ProgressSteps from '@/components/ProgressSteps';
import OfferButton from '@/components/OfferButton';
import SourceList from '@/components/SourceList';
import LanguageToggle from '@/components/LanguageToggle';
import InfoBanner from '@/components/InfoBanner';
import { czytajSse } from '@/lib/sse';
import {
  TEKSTY,
  jestNegacja,
  naglowekSzkicu,
  zbudujZadanie,
  type ChatResponse,
  type Lang,
  type Tryb,
  type Wiadomosc,
} from '@/lib/chat';

interface WiadomoscUi {
  role: 'user' | 'assistant';
  content: string;
  tryb?: Tryb;
  sources?: string[];
  doprecyzowanie?: string | null;
  kategoria?: string | null;
}

interface State {
  messages: WiadomoscUi[];
  historiaApi: Wiadomosc[];
  ostatniAgent: string | null;
  ostatniaKorekta: string | null;
  oferta: string | null;
  kroki: string[];
  wysylanie: boolean;
}

const stanPoczatkowy: State = {
  messages: [],
  historiaApi: [],
  ostatniAgent: null,
  ostatniaKorekta: null,
  oferta: null,
  kroki: [],
  wysylanie: false,
};

type Action =
  | { type: 'wyslij_start'; promptUser: string }
  | { type: 'krok'; tekst: string }
  | {
      type: 'zakoncz';
      wiadomoscWyslana: string;
      bezKorekty: boolean;
      dane: ChatResponse | null;
      bladTekst: string | null;
      noResponse: string;
    };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'wyslij_start':
      return {
        ...state,
        wysylanie: true,
        kroki: [],
        messages: [...state.messages, { role: 'user', content: action.promptUser }],
      };
    case 'krok':
      return { ...state, kroki: [...state.kroki, action.tekst] };
    case 'zakoncz': {
      const { dane, bladTekst, wiadomoscWyslana, bezKorekty, noResponse } = action;
      const answer = dane?.answer ?? bladTekst ?? noResponse;
      const tryb: Tryb = dane?.tryb ?? 'rag';
      const agent = dane?.agent ?? '';

      let historiaApi = state.historiaApi;
      let ostatniAgent = state.ostatniAgent;
      if (agent) {
        historiaApi = [
          ...historiaApi,
          { role: 'user', content: wiadomoscWyslana },
          { role: 'assistant', content: answer },
        ];
        ostatniAgent = agent;
      }

      let ostatniaKorekta = state.ostatniaKorekta;
      if (dane?.doprecyzowanie) {
        ostatniaKorekta = wiadomoscWyslana;
      } else if (!bezKorekty) {
        ostatniaKorekta = null;
      }

      return {
        ...state,
        wysylanie: false,
        kroki: [],
        historiaApi,
        ostatniAgent,
        ostatniaKorekta,
        oferta: dane?.oferta ?? null,
        messages: [
          ...state.messages,
          {
            role: 'assistant',
            content: answer,
            tryb,
            sources: dane?.sources ?? [],
            doprecyzowanie: dane?.doprecyzowanie ?? null,
            kategoria: dane?.kategoria ?? null,
          },
        ],
      };
    }
    default:
      return state;
  }
}

export default function Page() {
  const [lang, setLang] = useState<Lang>('pl');
  const [state, dispatch] = useReducer(reducer, stanPoczatkowy);
  const t = TEKSTY[lang];

  async function wyslij(promptUser: string) {
    const bezKorekty = jestNegacja(promptUser, lang) && Boolean(state.ostatniaKorekta);
    const wiadomosc = bezKorekty ? (state.ostatniaKorekta as string) : promptUser;

    dispatch({ type: 'wyslij_start', promptUser });

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

    dispatch({
      type: 'zakoncz',
      wiadomoscWyslana: wiadomosc,
      bezKorekty,
      dane,
      bladTekst,
      noResponse: t.noResponse,
    });
  }

  return (
    <div className="mx-auto flex h-screen max-w-3xl flex-col gap-4 p-4">
      <header className="flex items-center justify-between border-b pb-3">
        <h1 className="text-lg font-semibold">{t.ustawienia}</h1>
        <LanguageToggle lang={lang} onChange={setLang} />
      </header>

      <div className="flex-1 space-y-3 overflow-y-auto">
        {state.messages.map((m, i) => (
          <div key={i} className="space-y-1">
            {m.role === 'assistant' && m.tryb === 'email' && (
              <p className="text-sm text-gray-500">{naglowekSzkicu(lang, m.kategoria ?? null)}</p>
            )}
            <ChatMessage role={m.role} content={m.content} tryb={m.tryb} />
            {m.doprecyzowanie && <InfoBanner tekst={m.doprecyzowanie} />}
            {m.sources && m.sources.length > 0 && <SourceList zrodla={m.sources} etykieta={t.zrodla} />}
          </div>
        ))}
        {state.wysylanie && <ProgressSteps kroki={state.kroki} etykieta={t.mysle} />}
      </div>

      {state.oferta && <OfferButton tekst={state.oferta} onClick={wyslij} />}

      <Composer placeholder={t.placeholder} wyslijEtykieta={t.wyslij} disabled={state.wysylanie} onSend={wyslij} />
    </div>
  );
}
