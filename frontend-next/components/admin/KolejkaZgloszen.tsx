'use client';

import { useCallback, useEffect, useState } from 'react';
import { useTheme, BODY, DISPLAY } from '@/lib/theme';
import {
  pobierzKolejke,
  odpowiedzZgloszenie,
  type Kolejka,
  type StatusZgloszenia,
  type EtykietaZgloszenia,
  type ZgloszenieKolejki,
} from '@/lib/admin';
import { opisBledu, useJezykAdmina, useTekstyAdmina } from '@/lib/adminTeksty';
import { useWaskiEkran } from '@/lib/ekran';

interface Props {
  dni: number | null;
  token: string;
  onToken: (token: string) => void;
}

const ETYKIETY: EtykietaZgloszenia[] = ['luka_w_bazie', 'prog_za_wysoki', 'poza_zakresem', 'spam'];

type Komunikat = { rodzaj: 'pusta' } | { rodzaj: 'wyslano'; numer: string | null } | { rodzaj: 'odrzucono' } | { rodzaj: 'blad'; blad: unknown };

export default function KolejkaZgloszen({ dni, token, onToken }: Props) {
  const th = useTheme();
  const t = useTekstyAdmina();
  const lang = useJezykAdmina();
  const waski = useWaskiEkran();
  const [tokenWpisywany, setTokenWpisywany] = useState('');
  const [status, setStatus] = useState<StatusZgloszenia | null>('nowe');
  const [dane, setDane] = useState<Kolejka | null>(null);
  const [wynik, setWynik] = useState<{ klucz: string; blad: unknown } | null>(null);
  const [odswiez, setOdswiez] = useState(0);
  const [rozwiniete, setRozwiniete] = useState<string | null>(null);

  const statusy: { etykieta: string; wartosc: StatusZgloszenia | null }[] = [
    { etykieta: t.statusyKolejki.nowe, wartosc: 'nowe' },
    { etykieta: t.statusyKolejki.odpowiedziano, wartosc: 'odpowiedziano' },
    { etykieta: t.statusyKolejki.odrzucone, wartosc: 'odrzucone' },
    { etykieta: t.statusyKolejki.wszystkie, wartosc: null },
  ];

  useEffect(() => {
    if (!token) {
      return;
    }
    let aktywny = true;
    const klucz = JSON.stringify([token, dni, status, odswiez]);
    pobierzKolejke(token, dni, status)
      .then((pobrane) => {
        if (aktywny) {
          setDane(pobrane);
          setWynik({ klucz, blad: null });
        }
      })
      .catch((e) => {
        if (aktywny) {
          setDane(null);
          setWynik({ klucz, blad: e ?? true });
        }
      });
    return () => {
      aktywny = false;
    };
  }, [token, dni, status, odswiez]);

  const kluczBiezacy = JSON.stringify([token, dni, status, odswiez]);
  const blad = wynik?.klucz === kluczBiezacy ? wynik.blad : null;
  const ladowanie = token !== '' && wynik?.klucz !== kluczBiezacy;

  const odswiezPoZapisie = useCallback(async () => {
    setOdswiez((n) => n + 1);
  }, []);

  const ramka = {
    background: th.surface,
    border: `1px solid ${th.line}`,
    borderRadius: 14,
    boxShadow: th.shadow,
    overflow: 'hidden' as const,
  };

  function wyloguj() {
    onToken('');
    setTokenWpisywany('');
    setDane(null);
    setWynik(null);
  }

  if (!token) {
    return (
      <section style={{ ...ramka, padding: waski ? '16px 14px 18px' : '20px 20px 24px' }}>
        <h2 style={{ margin: 0, fontFamily: DISPLAY, fontSize: 15, fontWeight: 700, color: th.ink }}>
          {t.kolejkaTytul}
        </h2>
        <p style={{ fontFamily: BODY, fontSize: 13, color: th.ink2, marginTop: 10, maxWidth: 560 }}>{t.kolejkaWstep}</p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onToken(tokenWpisywany);
          }}
          style={{ display: 'flex', gap: 10, marginTop: 12, flexWrap: 'wrap' }}
        >
          <input
            type="password"
            value={tokenWpisywany}
            placeholder={t.tokenMaly}
            onChange={(e) => setTokenWpisywany(e.target.value)}
            style={{ ...pole(th, waski), marginTop: 0, flex: '1 1 200px', width: 'auto', minWidth: 0 }}
          />
          <button type="submit" disabled={!tokenWpisywany} style={przyciskGlowny(th, !tokenWpisywany)}>
            {t.pokazKolejke}
          </button>
        </form>
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
          padding: waski ? '14px 14px 10px' : '16px 18px 12px',
        }}
      >
        <h2 style={{ margin: 0, fontFamily: DISPLAY, fontSize: 15, fontWeight: 700, color: th.ink }}>
          {t.kolejkaTytul}
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          {dane ? (
            <span style={{ fontFamily: BODY, fontSize: 12.5, color: th.ink2 }}>
              {t.kolejkaLicznik(dane.otwarte, dane.razem)}
            </span>
          ) : null}
          {statusy.map((s) => {
            const aktywny = s.wartosc === status;
            return (
              <button
                key={s.wartosc ?? 'wszystkie'}
                type="button"
                onClick={() => setStatus(s.wartosc)}
                style={{
                  height: waski ? 34 : 30,
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
          <button type="button" onClick={wyloguj} style={przyciskCichy(th)}>
            {t.wylogujToken}
          </button>
        </div>
      </div>

      {blad ? (
        <p style={{ padding: '0 18px 16px', color: th.accentInk, fontSize: 13 }}>{opisBledu(blad, t.bladKolejki, lang)}</p>
      ) : null}
      {!blad && ladowanie && dane === null ? (
        <p style={{ padding: '0 18px 16px', color: th.ink2, fontSize: 13 }}>{t.ladujeKolejke}</p>
      ) : null}
      {!blad && dane && dane.zgloszenia.length === 0 ? (
        <p style={{ padding: '0 18px 16px', color: th.ink2, fontSize: 13 }}>{t.brakZgloszen}</p>
      ) : null}

      {dane && dane.zgloszenia.length > 0 ? (
        <div style={{ borderTop: `1px solid ${th.lineSoft}` }}>
          {dane.zgloszenia.map((z) => (
            <Wiersz
              key={z.zgloszenie}
              z={z}
              rozwiniete={rozwiniete === z.zgloszenie}
              onToggle={() => setRozwiniete(rozwiniete === z.zgloszenie ? null : z.zgloszenie)}
              onZapisano={odswiezPoZapisie}
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
  onZapisano: () => Promise<void>;
  token: string;
}

function Wiersz({ z, rozwiniete, onToggle, onZapisano, token }: WierszProps) {
  const th = useTheme();
  const t = useTekstyAdmina();
  const lang = useJezykAdmina();
  const waski = useWaskiEkran();
  const [tresc, setTresc] = useState('');
  const [etykieta, setEtykieta] = useState<EtykietaZgloszenia | ''>('');
  const [zapis, setZapis] = useState(false);
  const [komunikat, setKomunikat] = useState<Komunikat | null>(null);

  const nowe = z.status === 'nowe';
  const czasCzytelny = (wartosc: string | null) => (wartosc ? wartosc.slice(0, 16).replace('T', ' ') : t.brak);

  async function wyslij(docelowyStatus: 'odpowiedziano' | 'odrzucone') {
    if (zapis) return;
    if (docelowyStatus === 'odpowiedziano' && !tresc.trim()) {
      setKomunikat({ rodzaj: 'pusta' });
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
      setKomunikat(docelowyStatus === 'odpowiedziano' ? { rodzaj: 'wyslano', numer: wynik.ticket } : { rodzaj: 'odrzucono' });
      await onZapisano();
    } catch (e) {
      setKomunikat({ rodzaj: 'blad', blad: e });
    } finally {
      setZapis(false);
    }
  }

  function tekstKomunikatu(k: Komunikat): string {
    if (k.rodzaj === 'pusta') return t.pustaOdpowiedz;
    if (k.rodzaj === 'wyslano') return t.wyslanoNumer(k.numer ?? t.brak);
    if (k.rodzaj === 'odrzucono') return t.odrzucono;
    return opisBledu(k.blad, t.bladZapisu, lang);
  }

  const brakWartosci = (wartosc: number | null | undefined) => (wartosc === null || wartosc === undefined ? t.brak : String(wartosc));

  return (
    <div style={{ borderBottom: `1px solid ${th.lineSoft}` }}>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={rozwiniete}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: waski ? 10 : 16,
          padding: waski ? '12px 14px' : '14px 18px',
          background: 'none',
          border: 'none',
          textAlign: 'left',
          cursor: 'pointer',
        }}
      >
        <span style={{ display: 'flex', flexDirection: 'column', gap: 5, minWidth: 0, overflowWrap: 'anywhere' }}>
          <span style={{ fontFamily: BODY, fontSize: 13.5, color: th.ink, fontWeight: 600 }}>
            {z.pytanie ?? t.brakTresciPytania}
          </span>
          <span style={{ fontFamily: BODY, fontSize: 12, color: th.ink2, display: 'flex', columnGap: 8, rowGap: 2, flexWrap: 'wrap' }}>
            {[
              z.powod ? t.powody[z.powod] ?? z.powod : t.brakPowodu,
              z.sekcja ? t.sekcje[z.sekcja] ?? z.sekcja : t.brakTematu,
              t.dopasowanie(brakWartosci(z.cechy?.rerank_top1)),
              t.oparcie(brakWartosci(z.cechy?.pokrycie)),
            ].map((tekst, i, wszystkie) => (
              <span key={i}>{i < wszystkie.length - 1 ? `${tekst} ·` : tekst}</span>
            ))}
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
          {t.statusy[z.status] ?? z.status}
        </span>
      </button>

      {rozwiniete ? (
        <div style={{ padding: waski ? '0 14px 16px' : '0 18px 18px', display: 'flex', flexDirection: 'column', gap: 12 }}>
          <dl
            style={{
              margin: 0,
              display: 'grid',
              gridTemplateColumns: waski ? '1fr' : 'auto 1fr',
              gap: waski ? '2px 0' : '4px 14px',
              fontFamily: BODY,
              fontSize: 12.5,
              overflowWrap: 'anywhere',
            }}
          >
            <dt style={{ color: th.ink3, marginTop: waski ? 6 : 0 }}>{t.numerZgloszenia}</dt>
            <dd style={{ margin: 0, color: th.ink2 }}>{z.zgloszenie}</dd>
            <dt style={{ color: th.ink3, marginTop: waski ? 6 : 0 }}>{t.zgloszono}</dt>
            <dd style={{ margin: 0, color: th.ink2 }}>{czasCzytelny(z.czas)}</dd>
            <dt style={{ color: th.ink3, marginTop: waski ? 6 : 0 }}>{t.adresZwrotny}</dt>
            <dd style={{ margin: 0, color: th.ink2 }}>{z.email ?? t.brak}</dd>
            <dt style={{ color: th.ink3, marginTop: waski ? 6 : 0 }}>{t.najlepszyArtykul}</dt>
            <dd style={{ margin: 0, color: th.ink2 }}>{z.cechy?.zrodlo_top1 ?? t.brak}</dd>
            <dt style={{ color: th.ink3, marginTop: waski ? 6 : 0 }}>{t.coZawiodlo}</dt>
            <dd style={{ margin: 0, color: th.ink2 }}>{t.diagnozy[z.diagnoza] ?? z.diagnoza}</dd>
            {z.tresc ? (
              <>
                <dt style={{ color: th.ink3, marginTop: waski ? 6 : 0 }}>{t.poprzedniaOdpowiedz}</dt>
                <dd style={{ margin: 0, color: th.ink2 }}>{z.tresc}</dd>
              </>
            ) : null}
          </dl>

          {nowe ? (
            <>
              <textarea
                value={tresc}
                onChange={(e) => setTresc(e.target.value)}
                placeholder={t.odpowiedzPlaceholder}
                rows={5}
                maxLength={8000}
                style={{ ...pole(th, waski), resize: 'vertical', fontFamily: BODY, lineHeight: 1.5 }}
              />
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
                <select
                  value={etykieta}
                  onChange={(e) => setEtykieta(e.target.value as EtykietaZgloszenia | '')}
                  style={{ ...pole(th, waski), marginTop: 0, width: waski ? '100%' : 'auto', padding: '9px 12px' }}
                >
                  <option value="">{t.bezEtykiety}</option>
                  {ETYKIETY.map((klucz) => (
                    <option key={klucz} value={klucz}>
                      {t.etykietyZgloszen[klucz]}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => wyslij('odpowiedziano')}
                  disabled={zapis}
                  style={przyciskGlowny(th, zapis)}
                >
                  {zapis ? t.zapisuje : t.wyslijOdpowiedz}
                </button>
                <button
                  type="button"
                  onClick={() => wyslij('odrzucone')}
                  disabled={zapis}
                  style={przyciskCichy(th)}
                >
                  {t.odrzuc}
                </button>
              </div>
            </>
          ) : null}

          {komunikat ? (
            <span style={{ fontFamily: BODY, fontSize: 12.5, color: th.ink }}>{tekstKomunikatu(komunikat)}</span>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

type Motyw = ReturnType<typeof useTheme>;

function pole(th: Motyw, waski: boolean) {
  return {
    width: '100%',
    marginTop: 12,
    border: `1px solid ${th.line}`,
    background: th.surface,
    color: th.ink,
    borderRadius: 9,
    padding: '10px 12px',
    fontFamily: BODY,
    fontSize: waski ? 16 : 13.5,
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
