'use client';

import { useEffect, useRef, useState } from 'react';
import { useTheme, BODY } from '@/lib/theme';

interface Props {
  od: string | null;
  do: string | null;
  aktywny: boolean;
  onZmiana: (od: string | null, doDnia: string | null) => void;
}

const DNI_TYGODNIA = ['pn', 'wt', 'śr', 'cz', 'pt', 'so', 'nd'];

const MIESIACE = [
  'styczeń',
  'luty',
  'marzec',
  'kwiecień',
  'maj',
  'czerwiec',
  'lipiec',
  'sierpień',
  'wrzesień',
  'październik',
  'listopad',
  'grudzień',
];

function naTekst(data: Date): string {
  const miesiac = String(data.getMonth() + 1).padStart(2, '0');
  const dzien = String(data.getDate()).padStart(2, '0');
  return `${data.getFullYear()}-${miesiac}-${dzien}`;
}

function zTekstu(wartosc: string | null): Date | null {
  if (!wartosc) {
    return null;
  }
  const [rok, miesiac, dzien] = wartosc.split('-').map(Number);
  if (!rok || !miesiac || !dzien) {
    return null;
  }
  return new Date(rok, miesiac - 1, dzien);
}

function czytelna(wartosc: string): string {
  const data = zTekstu(wartosc);
  return data ? `${data.getDate()} ${MIESIACE[data.getMonth()].slice(0, 3)}` : wartosc;
}

function siatkaMiesiaca(miesiac: Date): (Date | null)[] {
  const pierwszy = new Date(miesiac.getFullYear(), miesiac.getMonth(), 1);
  const ile = new Date(miesiac.getFullYear(), miesiac.getMonth() + 1, 0).getDate();
  const przesuniecie = (pierwszy.getDay() + 6) % 7;
  const komorki: (Date | null)[] = Array(przesuniecie).fill(null);
  for (let d = 1; d <= ile; d += 1) {
    komorki.push(new Date(miesiac.getFullYear(), miesiac.getMonth(), d));
  }
  while (komorki.length % 7 !== 0) {
    komorki.push(null);
  }
  return komorki;
}

export default function WyborZakresu({ od, do: doDnia, aktywny, onZmiana }: Props) {
  const th = useTheme();
  const [otwarty, setOtwarty] = useState(false);
  const [miesiac, setMiesiac] = useState(() => {
    const start = zTekstu(od) ?? new Date();
    return new Date(start.getFullYear(), start.getMonth(), 1);
  });
  const [szkicOd, setSzkicOd] = useState<string | null>(od);
  const [szkicDo, setSzkicDo] = useState<string | null>(doDnia);
  const kotwica = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!otwarty) {
      return;
    }
    const pozaPanelem = (e: MouseEvent) => {
      if (kotwica.current && !kotwica.current.contains(e.target as Node)) {
        setOtwarty(false);
      }
    };
    const klawisz = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOtwarty(false);
      }
    };
    document.addEventListener('mousedown', pozaPanelem);
    document.addEventListener('keydown', klawisz);
    return () => {
      document.removeEventListener('mousedown', pozaPanelem);
      document.removeEventListener('keydown', klawisz);
    };
  }, [otwarty]);

  const wybierz = (dzien: Date) => {
    const tekst = naTekst(dzien);
    if (szkicOd === null || szkicDo !== null) {
      setSzkicOd(tekst);
      setSzkicDo(null);
      return;
    }
    if (tekst < szkicOd) {
      setSzkicDo(szkicOd);
      setSzkicOd(tekst);
      return;
    }
    setSzkicDo(tekst);
  };

  const zastosuj = () => {
    if (szkicOd === null) {
      return;
    }
    onZmiana(szkicOd, szkicDo ?? szkicOd);
    setOtwarty(false);
  };

  const wyczysc = () => {
    setSzkicOd(null);
    setSzkicDo(null);
    onZmiana(null, null);
    setOtwarty(false);
  };

  const dzisiaj = naTekst(new Date());
  const komorki = siatkaMiesiaca(miesiac);

  const etykietaPrzycisku = od ? `${czytelna(od)} do ${czytelna(doDnia ?? od)}` : 'Wybrane dni';

  const stanKomorki = (tekst: string) => {
    if (szkicOd !== null && szkicDo !== null && tekst > szkicOd && tekst < szkicDo) {
      return 'srodek';
    }
    if (tekst === szkicOd || tekst === szkicDo) {
      return 'kraniec';
    }
    return 'zwykla';
  };

  return (
    <div ref={kotwica} style={{ position: 'relative' }}>
      <button
        type="button"
        className="dc-chip"
        onClick={() => {
          if (!otwarty) {
            setSzkicOd(od);
            setSzkicDo(doDnia);
          }
          setOtwarty((v) => !v);
        }}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 7,
          height: 34,
          padding: '0 14px',
          borderRadius: 100,
          border: `1px solid ${aktywny ? th.accentLine : th.line}`,
          background: aktywny ? th.accentSoft : th.surface,
          color: aktywny ? th.accentInk : th.ink2,
          fontFamily: BODY,
          fontSize: 12.5,
          fontWeight: 600,
          cursor: 'pointer',
          whiteSpace: 'nowrap',
        }}
      >
        {etykietaPrzycisku}
        <span style={{ fontSize: 9, opacity: 0.7 }}>{otwarty ? '▲' : '▼'}</span>
      </button>

      {otwarty ? (
        <div
          style={{
            position: 'absolute',
            top: 40,
            left: 0,
            zIndex: 60,
            width: 292,
            padding: 14,
            borderRadius: 14,
            border: `1px solid ${th.line}`,
            background: th.surface,
            boxShadow: th.shadowLift,
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <button
              type="button"
              onClick={() => setMiesiac(new Date(miesiac.getFullYear(), miesiac.getMonth() - 1, 1))}
              aria-label="Poprzedni miesiąc"
              style={strzalka(th)}
            >
              {'‹'}
            </button>
            <span style={{ fontFamily: BODY, fontSize: 13, fontWeight: 700, color: th.ink }}>
              {MIESIACE[miesiac.getMonth()]} {miesiac.getFullYear()}
            </span>
            <button
              type="button"
              onClick={() => setMiesiac(new Date(miesiac.getFullYear(), miesiac.getMonth() + 1, 1))}
              aria-label="Następny miesiąc"
              style={strzalka(th)}
            >
              {'›'}
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 2 }}>
            {DNI_TYGODNIA.map((nazwa) => (
              <span
                key={nazwa}
                style={{
                  textAlign: 'center',
                  fontFamily: BODY,
                  fontSize: 10.5,
                  fontWeight: 700,
                  letterSpacing: '.04em',
                  textTransform: 'uppercase',
                  color: th.ink3,
                  padding: '2px 0 4px',
                }}
              >
                {nazwa}
              </span>
            ))}
            {komorki.map((dzien, i) => {
              if (dzien === null) {
                return <span key={`pusto-${i}`} />;
              }
              const tekst = naTekst(dzien);
              const stan = stanKomorki(tekst);
              const przyszly = tekst > dzisiaj;
              return (
                <button
                  key={tekst}
                  type="button"
                  disabled={przyszly}
                  onClick={() => wybierz(dzien)}
                  style={{
                    height: 32,
                    border: 'none',
                    borderRadius: stan === 'srodek' ? 6 : 8,
                    background:
                      stan === 'kraniec'
                        ? th.accent
                        : stan === 'srodek'
                          ? th.accentSoft
                          : 'transparent',
                    color:
                      stan === 'kraniec'
                        ? '#FFFFFF'
                        : przyszly
                          ? th.ink3
                          : stan === 'srodek'
                            ? th.accentInk
                            : th.ink,
                    fontFamily: BODY,
                    fontSize: 12.5,
                    fontWeight: stan === 'zwykla' ? 500 : 700,
                    cursor: przyszly ? 'default' : 'pointer',
                    opacity: przyszly ? 0.35 : 1,
                    outline: tekst === dzisiaj && stan === 'zwykla' ? `1px solid ${th.line}` : 'none',
                  }}
                >
                  {dzien.getDate()}
                </button>
              );
            })}
          </div>

          <p style={{ margin: 0, fontFamily: BODY, fontSize: 11.5, color: th.ink3 }}>
            {szkicOd === null
              ? 'Kliknij dzień początkowy.'
              : szkicDo === null
                ? 'Kliknij dzień końcowy.'
                : `Wybrano ${szkicOd} do ${szkicDo}.`}
          </p>

          <div style={{ display: 'flex', gap: 8, justifyContent: 'space-between' }}>
            <button type="button" onClick={wyczysc} style={cichy(th)}>
              Wyczyść
            </button>
            <button
              type="button"
              onClick={zastosuj}
              disabled={szkicOd === null}
              className="dc-akcja"
              style={{
                height: 32,
                padding: '0 16px',
                borderRadius: 100,
                border: 'none',
                background: szkicOd === null ? th.lineSoft : th.accent,
                color: szkicOd === null ? th.ink3 : '#FFFFFF',
                fontFamily: BODY,
                fontSize: 12.5,
                fontWeight: 700,
                cursor: szkicOd === null ? 'default' : 'pointer',
              }}
            >
              Pokaż ten zakres
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

type Motyw = ReturnType<typeof useTheme>;

function strzalka(th: Motyw) {
  return {
    width: 28,
    height: 28,
    borderRadius: 8,
    border: `1px solid ${th.line}`,
    background: th.raised,
    color: th.ink2,
    fontSize: 15,
    lineHeight: 1,
    cursor: 'pointer',
  } as const;
}

function cichy(th: Motyw) {
  return {
    height: 32,
    padding: '0 14px',
    borderRadius: 100,
    border: `1px solid ${th.line}`,
    background: th.surface,
    color: th.ink2,
    fontFamily: BODY,
    fontSize: 12.5,
    fontWeight: 600,
    cursor: 'pointer',
  } as const;
}
