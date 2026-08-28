'use client';

import { useCallback, useEffect, useState } from 'react';
import { useTheme, BODY, DISPLAY } from '@/lib/theme';
import {
  pobierzKolejke,
  odpowiedzZgloszenie,
  NAZWY_POWODOW,
  NAZWY_SEKCJI,
  NAZWY_STATUSOW_ZGLOSZEN,
  NAZWY_ETYKIET_ZGLOSZEN,
  type Kolejka,
  type StatusZgloszenia,
  type EtykietaZgloszenia,
  type ZgloszenieKolejki,
} from '@/lib/admin';

interface Props {
  dni: number | null;
}

const STATUSY: { etykieta: string; wartosc: StatusZgloszenia | null }[] = [
  { etykieta: 'Nowe', wartosc: 'nowe' },
  { etykieta: 'Odpowiedziane', wartosc: 'odpowiedziano' },
  { etykieta: 'Odrzucone', wartosc: 'odrzucone' },
  { etykieta: 'Wszystkie', wartosc: null },
];

const ETYKIETY: EtykietaZgloszenia[] = ['luka_w_bazie', 'prog_za_wysoki', 'poza_zakresem', 'spam'];

function czasCzytelny(wartosc: string | null): string {
  return wartosc ? wartosc.slice(0, 16).replace('T', ' ') : 'brak';
}

export default function KolejkaZgloszen({ dni }: Props) {
  const th = useTheme();
  const [token, setToken] = useState('');
  const [status, setStatus] = useState<StatusZgloszenia | null>('nowe');
  const [dane, setDane] = useState<Kolejka | null>(null);
  const [blad, setBlad] = useState<string | null>(null);
  const [ladowanie, setLadowanie] = useState(false);
  const [odswiez, setOdswiez] = useState(0);
  const [rozwiniete, setRozwiniete] = useState<string | null>(null);

  const wczytaj = useCallback(() => {
    if (!token) {
      setDane(null);
      return;
    }
    let aktywny = true;
    setLadowanie(true);
    setBlad(null);
    pobierzKolejke(token, dni, status)
      .then((wynik) => {
        if (aktywny) {
          setDane(wynik);
        }
      })
      .catch((e) => {
        if (aktywny) {
          setDane(null);
          setBlad(e instanceof Error ? e.message : 'Nie udało się pobrać kolejki');
        }
      })
      .finally(() => {
        if (aktywny) {
          setLadowanie(false);
        }
      });
    return () => {
      aktywny = false;
    };
  }, [token, dni, status]);

  useEffect(() => wczytaj(), [wczytaj, odswiez]);

  const ramka = {
    background: th.surface,
    border: `1px solid ${th.line}`,
    borderRadius: 14,
    boxShadow: th.shadow,
    overflow: 'hidden' as const,
  };

  if (!token) {
    return (
      <section style={{ ...ramka, padding: '20px 20px 24px' }}>
        <h2 style={{ margin: 0, fontFamily: DISPLAY, fontSize: 15, fontWeight: 700, color: th.ink }}>
          Kolejka zgłoszeń
        </h2>
        <p style={{ fontFamily: BODY, fontSize: 13, color: th.ink2, marginTop: 10, maxWidth: 560 }}>
          Wpisz token administratora, żeby zobaczyć zgłoszenia. Bez tokenu lista jest niedostępna, a nie
          pusta.
        </p>
        <input
          type="password"
          value={token}
          placeholder="token administratora"
          onChange={(e) => setToken(e.target.value)}
          style={pole(th)}
        />
      </section>
    );
  }

  return (
    <section style={ramka}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          flexWrap: 'wrap',
          padding: '16px 18px 12px',
        }}
      >
        <h2 style={{ margin: 0, fontFamily: DISPLAY, fontSize: 15, fontWeight: 700, color: th.ink }}>
          Kolejka zgłoszeń
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          {dane ? (
            <span style={{ fontFamily: BODY, fontSize: 12.5, color: th.ink2 }}>
              {dane.otwarte} otwartych · {dane.razem} w widoku
            </span>
          ) : null}
          {STATUSY.map((s) => {
            const aktywny = s.wartosc === status;
            return (
              <button
                key={s.etykieta}
                type="button"
                onClick={() => setStatus(s.wartosc)}
                style={{
                  height: 30,
                  padding: '0 12px',
                  borderRadius: 100,
                  border: `1px solid ${aktywny ? th.accentLine : th.line}`,
                  background: aktywny ? th.accentSoft : th.surface,
                  color: aktywny ? th.accentInk : th.ink2,
                  fontFamily: BODY,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {s.etykieta}
              </button>
            );
          })}
          <button type="button" onClick={() => setToken('')} style={przyciskCichy(th)}>
            Wyloguj token
          </button>
        </div>
      </div>

      {blad ? <p style={{ padding: '0 18px 16px', color: th.accentInk, fontSize: 13 }}>{blad}</p> : null}
      {!blad && ladowanie && dane === null ? (
        <p style={{ padding: '0 18px 16px', color: th.ink2, fontSize: 13 }}>Ładuję kolejkę</p>
      ) : null}
      {!blad && dane && dane.zgloszenia.length === 0 ? (
        <p style={{ padding: '0 18px 16px', color: th.ink2, fontSize: 13 }}>
          Brak zgłoszeń w tym widoku.
        </p>
      ) : null}

      {dane && dane.zgloszenia.length > 0 ? (
        <div style={{ borderTop: `1px solid ${th.lineSoft}` }}>
          {dane.zgloszenia.map((z) => (
            <Wiersz
              key={z.zgloszenie}
              z={z}
              rozwiniete={rozwiniete === z.zgloszenie}
              onToggle={() => setRozwiniete(rozwiniete === z.zgloszenie ? null : z.zgloszenie)}
              onZapisano={() => setOdswiez((n) => n + 1)}
              token={token}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}

interface WierszProps {
  z: ZgloszenieKolejki;
  rozwiniete: boolean;
  onToggle: () => void;
  onZapisano: () => void;
  token: string;
}

function Wiersz({ z, rozwiniete, onToggle, onZapisano, token }: WierszProps) {
  const th = useTheme();
  const [tresc, setTresc] = useState('');
  const [etykieta, setEtykieta] = useState<EtykietaZgloszenia | ''>('');
  const [zapis, setZapis] = useState(false);
  const [komunikat, setKomunikat] = useState<string | null>(null);

  const nowe = z.status === 'nowe';

  async function wyslij(docelowyStatus: 'odpowiedziano' | 'odrzucone') {
    if (zapis) return;
    if (docelowyStatus === 'odpowiedziano' && !tresc.trim()) {
      setKomunikat('Odpowiedź nie może być pusta.');
      return;
    }
    setZapis(true);
    setKomunikat(null);
    try {
      const wynik = await odpowiedzZgloszenie(token, {
        zgloszenie: z.zgloszenie,
        status: docelowyStatus,
        etykieta: etykieta || null,
        tresc: tresc.trim(),
      });
      setKomunikat(
        docelowyStatus === 'odpowiedziano'
          ? `Wysłano, numer wiadomości ${wynik.ticket ?? 'brak'}.`
          : 'Zgłoszenie odrzucone.',
      );
      onZapisano();
    } catch (e) {
      setKomunikat(e instanceof Error ? e.message : 'Nie udało się zapisać.');
    } finally {
      setZapis(false);
    }
  }

  return (
    <div style={{ borderBottom: `1px solid ${th.lineSoft}` }}>
      <button
        type="button"
        onClick={onToggle}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: 16,
          padding: '14px 18px',
          background: 'none',
          border: 'none',
          textAlign: 'left',
          cursor: 'pointer',
        }}
      >
        <span style={{ display: 'flex', flexDirection: 'column', gap: 5, minWidth: 0 }}>
          <span style={{ fontFamily: BODY, fontSize: 13.5, color: th.ink, fontWeight: 600 }}>
            {z.pytanie ?? 'brak treści pytania'}
          </span>
          <span style={{ fontFamily: BODY, fontSize: 12, color: th.ink2, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <span>{NAZWY_POWODOW[z.powod ?? ''] ?? z.powod ?? 'brak powodu'}</span>
            <span>·</span>
            <span>{z.sekcja ? NAZWY_SEKCJI[z.sekcja] ?? z.sekcja : 'brak sekcji'}</span>
            <span>·</span>
            <span>rerank {z.cechy?.rerank_top1 ?? 'brak'}</span>
            <span>·</span>
            <span>pokrycie {z.cechy?.pokrycie ?? 'brak'}</span>
          </span>
        </span>
        <span
          style={{
            flexShrink: 0,
            fontFamily: BODY,
            fontSize: 11,
            fontWeight: 700,
            padding: '3px 9px',
            borderRadius: 100,
            background: nowe ? th.accentSoft : th.lineSoft,
            color: nowe ? th.accentInk : th.ink2,
          }}
        >
          {NAZWY_STATUSOW_ZGLOSZEN[z.status]}
        </span>
      </button>

      {rozwiniete ? (
        <div style={{ padding: '0 18px 18px', display: 'flex', flexDirection: 'column', gap: 12 }}>
          <dl style={{ margin: 0, display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '4px 14px', fontFamily: BODY, fontSize: 12.5 }}>
            <dt style={{ color: th.ink3 }}>Numer</dt>
            <dd style={{ margin: 0, color: th.ink2 }}>{z.zgloszenie}</dd>
            <dt style={{ color: th.ink3 }}>Zgłoszono</dt>
            <dd style={{ margin: 0, color: th.ink2 }}>{czasCzytelny(z.czas)}</dd>
            <dt style={{ color: th.ink3 }}>Adres zwrotny</dt>
            <dd style={{ margin: 0, color: th.ink2 }}>{z.email ?? 'brak'}</dd>
            <dt style={{ color: th.ink3 }}>Źródło top1</dt>
            <dd style={{ margin: 0, color: th.ink2 }}>{z.cechy?.zrodlo_top1 ?? 'brak'}</dd>
            <dt style={{ color: th.ink3 }}>Diagnoza</dt>
            <dd style={{ margin: 0, color: th.ink2 }}>{z.diagnoza}</dd>
            {z.tresc ? (
              <>
                <dt style={{ color: th.ink3 }}>Poprzednia odpowiedź</dt>
                <dd style={{ margin: 0, color: th.ink2 }}>{z.tresc}</dd>
              </>
            ) : null}
          </dl>

          {nowe ? (
            <>
              <textarea
                value={tresc}
                onChange={(e) => setTresc(e.target.value)}
                placeholder="Odpowiedź do użytkownika"
                rows={5}
                maxLength={8000}
                style={{ ...pole(th), resize: 'vertical', fontFamily: BODY, lineHeight: 1.5 }}
              />
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
                <select
                  value={etykieta}
                  onChange={(e) => setEtykieta(e.target.value as EtykietaZgloszenia | '')}
                  style={{ ...pole(th), width: 'auto', padding: '9px 12px' }}
                >
                  <option value="">bez etykiety</option>
                  {ETYKIETY.map((klucz) => (
                    <option key={klucz} value={klucz}>
                      {NAZWY_ETYKIET_ZGLOSZEN[klucz]}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => wyslij('odpowiedziano')}
                  disabled={zapis}
                  style={przyciskGlowny(th, zapis)}
                >
                  {zapis ? 'Zapisuję' : 'Wyślij odpowiedź'}
                </button>
                <button
                  type="button"
                  onClick={() => wyslij('odrzucone')}
                  disabled={zapis}
                  style={przyciskCichy(th)}
                >
                  Odrzuć
                </button>
              </div>
            </>
          ) : null}

          {komunikat ? (
            <span style={{ fontFamily: BODY, fontSize: 12.5, color: th.ink }}>{komunikat}</span>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

type Motyw = ReturnType<typeof useTheme>;

function pole(th: Motyw) {
  return {
    width: '100%',
    marginTop: 12,
    border: `1px solid ${th.line}`,
    background: th.surface,
    color: th.ink,
    borderRadius: 9,
    padding: '10px 12px',
    fontFamily: BODY,
    fontSize: 13.5,
    outline: 'none',
  } as const;
}

function przyciskGlowny(th: Motyw, disabled: boolean) {
  return {
    padding: '10px 16px',
    borderRadius: 9,
    border: 'none',
    background: disabled ? th.accentSoft : th.accent,
    color: disabled ? th.accentInk : '#FFFFFF',
    fontFamily: BODY,
    fontSize: 13,
    fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer',
  } as const;
}

function przyciskCichy(th: Motyw) {
  return {
    padding: '10px 14px',
    borderRadius: 9,
    border: `1px solid ${th.line}`,
    background: th.surface,
    color: th.ink2,
    fontFamily: BODY,
    fontSize: 12.5,
    fontWeight: 600,
    cursor: 'pointer',
  } as const;
}
