'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  pobierzStatystyki,
  procent,
  sekundy,
  etykieta,
  NAZWY_SEKCJI,
  NAZWY_STRON,
  NAZWY_POWODOW,
  resetujStatystyki,
  pobierzPrzypadki,
  ETYKIETY_DIAGNOZ,
  LEKARSTWA_DIAGNOZ,
  type Filtry,
  type Statystyki,
  type Przypadki,
} from '@/lib/admin';
import { ThemeContext, THEMES, BODY, DISPLAY, type ThemeName } from '@/lib/theme';
import { IkonaSlonce, IkonaKsiezyc } from '@/components/Ikony';
import Karta from '@/components/admin/Karta';
import SekcjaZwijana from '@/components/admin/SekcjaZwijana';
import {
  Ramka,
  WykresDzienny,
  WykresPoziomy,
  WykresStron,
  WykresLatencji,
  WykresKosztu,
} from '@/components/admin/Wykresy';
import PanelEksportu from '@/components/admin/PanelEksportu';
import KolejkaZgloszen from '@/components/admin/KolejkaZgloszen';

const OKRESY: { etykieta: string; dni: number | null }[] = [
  { etykieta: '7 dni', dni: 7 },
  { etykieta: '30 dni', dni: 30 },
  { etykieta: '90 dni', dni: 90 },
  { etykieta: 'Wszystko', dni: null },
];

const JEZYKI: { etykieta: string; lang: 'pl' | 'en' | null }[] = [
  { etykieta: 'Wszystkie', lang: null },
  { etykieta: 'Polski', lang: 'pl' },
  { etykieta: 'Angielski', lang: 'en' },
];

const STRONY: { etykieta: string; strona: 'kupujacy' | 'sprzedajacy' | null }[] = [
  { etykieta: 'Wszyscy', strona: null },
  { etykieta: 'Kupujący', strona: 'kupujacy' },
  { etykieta: 'Sprzedający', strona: 'sprzedajacy' },
];

const ZAKLADKI = ['Przegląd', 'Jakość i odmowy', 'Pytania', 'Oceny', 'Kolejka', 'Eksport'] as const;
type Zakladka = (typeof ZAKLADKI)[number];

const PYTANIA_WIDOCZNE = 6;

export default function PanelAdmina() {
  const [themeName, setThemeName] = useState<ThemeName>('light');
  const [filtry, setFiltry] = useState<Filtry>({ dni: 30, lang: null, strona: null });
  const [dane, setDane] = useState<Statystyki | null>(null);
  const [ladowanie, setLadowanie] = useState(true);
  const [blad, setBlad] = useState<string | null>(null);
  const [odswiez, setOdswiez] = useState(0);
  const [zaktualizowano, setZaktualizowano] = useState<Date | null>(null);
  const [zakladka, setZakladka] = useState<Zakladka>('Przegląd');
  const [pozostaleOtwarte, setPozostaleOtwarte] = useState(false);
  const [ruchOtwarty, setRuchOtwarty] = useState(true);
  const [sekcjeOtwarte, setSekcjeOtwarte] = useState(true);
  const [stronyOtwarte, setStronyOtwarte] = useState(true);
  const [latencjaOtwarta, setLatencjaOtwarta] = useState(false);
  const [wszystkiePytania, setWszystkiePytania] = useState(false);
  const [resetOtwarty, setResetOtwarty] = useState(false);
  const [resetowanie, setResetowanie] = useState(false);
  const [komunikatResetu, setKomunikatResetu] = useState<string | null>(null);
  const [tokenResetu, setTokenResetu] = useState('');
  const [przypadki, setPrzypadki] = useState<Przypadki | null>(null);
  const [bladPrzypadkow, setBladPrzypadkow] = useState<string | null>(null);
  const th = THEMES[themeName];

  const potwierdzResetStatystyk = async () => {
    setResetowanie(true);
    setKomunikatResetu(null);
    try {
      const archiwum = await resetujStatystyki(tokenResetu);
      setKomunikatResetu(
        archiwum
          ? 'Statystyki zresetowane, poprzednie dane zarchiwizowane na serwerze'
          : 'Statystyki zresetowane, nie było czego archiwizować',
      );
      setResetOtwarty(false);
      setTokenResetu('');
      setOdswiez((n) => n + 1);
    } catch (blad) {
      setKomunikatResetu(
        blad instanceof Error ? blad.message : 'Nie udało się zresetować statystyk',
      );
    } finally {
      setResetowanie(false);
    }
  };

  useEffect(() => {
    let aktywny = true;
    setLadowanie(true);
    setBlad(null);
    pobierzStatystyki(filtry)
      .then((wynik) => {
        if (aktywny) {
          setDane(wynik);
          setZaktualizowano(new Date());
        }
      })
      .catch(() => {
        if (aktywny) {
          setBlad('Nie udało się pobrać statystyk');
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
  }, [filtry, odswiez]);

  useEffect(() => {
    if (zakladka !== 'Oceny') {
      return;
    }
    let aktywny = true;
    setBladPrzypadkow(null);
    pobierzPrzypadki(filtry.dni)
      .then((wynik) => {
        if (aktywny) {
          setPrzypadki(wynik);
        }
      })
      .catch(() => {
        if (aktywny) {
          setBladPrzypadkow('Nie udało się pobrać ocen');
        }
      });
    return () => {
      aktywny = false;
    };
  }, [zakladka, filtry.dni, odswiez]);

  const pigulka = (aktywna: boolean) => ({
    height: 34,
    whiteSpace: 'nowrap' as const,
    padding: '0 14px',
    borderRadius: 100,
    border: `1px solid ${aktywna ? th.accentLine : th.line}`,
    background: aktywna ? th.accentSoft : th.surface,
    color: aktywna ? th.accentInk : th.ink2,
    fontFamily: BODY,
    fontSize: 12.5,
    fontWeight: 600,
    cursor: 'pointer',
  });

  const etykietaGrupy = {
    fontFamily: BODY,
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: '.07em',
    textTransform: 'uppercase' as const,
    color: th.ink3,
    marginRight: 2,
  };

  const rozdzielacz = <span style={{ width: 1, alignSelf: 'stretch', background: th.line, margin: '0 4px' }} />;

  const kupujacy = dane?.strony.find((s) => s.strona === 'kupujacy')?.ile ?? 0;
  const sprzedajacy = dane?.strony.find((s) => s.strona === 'sprzedajacy')?.ile ?? 0;

  const powodyPosortowane = [...(dane?.powody ?? [])].sort((a, b) => b.ile - a.ile);
  const topPowod = powodyPosortowane[0] ?? null;
  const udzialOdmow = dane && dane.ogolem.zapytan > 0 ? dane.ogolem.odmowy / dane.ogolem.zapytan : null;

  const pytaniaWidoczne = wszystkiePytania ? dane?.top_pytania ?? [] : (dane?.top_pytania ?? []).slice(0, PYTANIA_WIDOCZNE);

  const tabStyl = (aktywna: boolean) => ({
    position: 'relative' as const,
    padding: '10px 16px 12px',
    background: 'none',
    border: 'none',
    borderBottom: `3px solid ${aktywna ? th.accent : 'transparent'}`,
    fontFamily: BODY,
    fontSize: 14,
    fontWeight: 600 as const,
    color: aktywna ? th.ink : th.ink2,
    cursor: 'pointer',
    marginBottom: -1,
  });

  return (
    <ThemeContext.Provider value={th}>
      <div style={{ minHeight: '100vh', background: th.canvas, color: th.ink, padding: '28px 24px 48px' }}>
        <div style={{ maxWidth: 1180, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 18 }}>
          <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 24 }}>
            <div>
              <h1 style={{ margin: 0, fontFamily: DISPLAY, fontSize: 26, fontWeight: 800 }}>Panel statystyk</h1>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6, fontFamily: BODY, fontSize: 13, color: th.ink2 }}>
                <span>
                  {dane?.zakres.od
                    ? `Dane od ${dane.zakres.od.slice(0, 10)} do ${dane.zakres.do?.slice(0, 10)}`
                    : 'Brak danych w wybranym zakresie'}
                </span>
                {zaktualizowano ? (
                  <>
                    <span style={{ width: 4, height: 4, borderRadius: 999, background: th.ink3 }} />
                    <span>
                      odświeżono o{' '}
                      {zaktualizowano.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </>
                ) : null}
              </div>
              {komunikatResetu ? (
                <div style={{ marginTop: 4, fontFamily: BODY, fontSize: 12.5, color: th.ink2 }}>{komunikatResetu}</div>
              ) : null}
            </div>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10, flex: '0 0 auto' }}>
              <Link
                href="/"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  height: 36,
                  padding: '0 14px',
                  borderRadius: 100,
                  border: `1px solid ${th.line}`,
                  background: th.surface,
                  color: th.ink2,
                  fontFamily: BODY,
                  fontSize: 13,
                  fontWeight: 500,
                  textDecoration: 'none',
                  whiteSpace: 'nowrap',
                }}
              >
                Wróć do czatu
              </Link>
              <button
                type="button"
                onClick={() => setResetOtwarty(true)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  height: 36,
                  padding: '0 14px',
                  borderRadius: 100,
                  border: `1px solid ${th.line}`,
                  background: th.surface,
                  color: th.ink2,
                  fontFamily: BODY,
                  fontSize: 13,
                  fontWeight: 500,
                  whiteSpace: 'nowrap',
                  cursor: 'pointer',
                }}
              >
                Resetuj statystyki
              </button>
              <button
                type="button"
                onClick={() => setThemeName(themeName === 'light' ? 'dark' : 'light')}
                aria-label="Zmień motyw"
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: '50%',
                  border: `1px solid ${th.line}`,
                  background: th.surface,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  color: th.ink2,
                  flex: '0 0 auto',
                }}
              >
                {themeName === 'light' ? <IkonaKsiezyc /> : <IkonaSlonce />}
              </button>
            </div>
          </header>

          <div style={{ display: 'flex', gap: 6, borderBottom: `1px solid ${th.line}` }}>
            {ZAKLADKI.map((nazwa) => (
              <button key={nazwa} type="button" onClick={() => setZakladka(nazwa)} style={tabStyl(zakladka === nazwa)}>
                {nazwa}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 8 }}>
            <span style={etykietaGrupy}>Okres</span>
            {OKRESY.map((opcja) => (
              <button
                key={opcja.etykieta}
                type="button"
                onClick={() => setFiltry((f) => ({ ...f, dni: opcja.dni }))}
                style={pigulka(filtry.dni === opcja.dni)}
              >
                {opcja.etykieta}
              </button>
            ))}
            {rozdzielacz}
            <span style={etykietaGrupy}>Język</span>
            {JEZYKI.map((opcja) => (
              <button
                key={opcja.etykieta}
                type="button"
                onClick={() => setFiltry((f) => ({ ...f, lang: opcja.lang }))}
                style={pigulka(filtry.lang === opcja.lang)}
              >
                {opcja.etykieta}
              </button>
            ))}
            {rozdzielacz}
            <span style={etykietaGrupy}>Rola</span>
            {STRONY.map((opcja) => (
              <button
                key={opcja.etykieta}
                type="button"
                onClick={() => setFiltry((f) => ({ ...f, strona: opcja.strona }))}
                style={pigulka(filtry.strona === opcja.strona)}
              >
                {opcja.etykieta}
              </button>
            ))}
          </div>

          {blad ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, color: th.ink2, fontSize: 13 }}>
              <span>{blad}</span>
              <button type="button" onClick={() => setOdswiez((n) => n + 1)} style={pigulka(false)}>
                Spróbuj ponownie
              </button>
            </div>
          ) : null}

          {ladowanie && !dane ? (
            <p style={{ color: th.ink2, fontSize: 13 }}>Wczytuję dane...</p>
          ) : null}

          {dane && dane.ogolem.zapytan === 0 ? (
            <p style={{ color: th.ink2, fontSize: 13 }}>Brak danych w wybranym zakresie.</p>
          ) : null}

          {dane && dane.ogolem.zapytan > 0 && zakladka === 'Przegląd' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 14 }}>
                <Karta
                  tytul="Zapytania"
                  wartosc={String(dane.ogolem.zapytan)}
                  podpis={`${dane.ogolem.unikalne_pytania} unikalnych pytań`}
                />
                <Karta
                  tytul="Trafność"
                  wartosc={procent(dane.ogolem.trafnosc)}
                  akcent
                  podpis={`${dane.ogolem.odpowiedzi} odpowiedzi, ${dane.ogolem.odmowy} odmów`}
                />
                <Karta
                  tytul="Odmowy"
                  wartosc={String(dane.ogolem.odmowy)}
                  podpis={udzialOdmow !== null ? procent(udzialOdmow) : 'brak danych'}
                />
                <Karta
                  tytul="Mediana latencji"
                  wartosc={sekundy(dane.latencja.mediana)}
                />
              </div>

              <SekcjaZwijana
                tytul="Pozostałe metryki"
                otwarta={pozostaleOtwarte}
                onToggle={() => setPozostaleOtwarte((v) => !v)}
              >
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 14 }}>
                  <Karta
                    tytul="Ocena użytkowników"
                    wartosc={dane.oceny.razem === 0 ? 'brak ocen' : procent(dane.oceny.trafnosc)}
                    podpis={`${dane.oceny.razem} ocen, pokrycie ${procent(dane.oceny.pokrycie)}`}
                  />
                  <Karta
                    tytul="Trafienia cache"
                    wartosc={procent(dane.ogolem.cache_hit)}
                    podpis={`bez cache ${sekundy(dane.latencja.mediana_bez_cache)}`}
                  />
                  <Karta
                    tytul="Koszt tokenów"
                    wartosc={dane.koszty.pokrycie === 0 ? 'brak danych' : `$${dane.koszty.koszt_usd.toFixed(4)}`}
                  />
                  <Karta
                    tytul="Wysłane wiadomości"
                    wartosc={String(dane.ogolem.wysylki_ok)}
                    podpis={`${dane.ogolem.wysylki} prób wysyłki`}
                  />
                </div>
              </SekcjaZwijana>

              <SekcjaZwijana tytul="Ruch dzienny" otwarta={ruchOtwarty} onToggle={() => setRuchOtwarty((v) => !v)}>
                <div style={{ width: '100%', height: 260 }}>
                  <WykresDzienny dane={dane.dzienne} />
                </div>
              </SekcjaZwijana>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: 16 }}>
                <SekcjaZwijana
                  tytul="Sekcje odpowiedzi"
                  otwarta={sekcjeOtwarte}
                  onToggle={() => setSekcjeOtwarte((v) => !v)}
                >
                  <div style={{ width: '100%', height: 260 }}>
                    <WykresPoziomy dane={dane.sekcje as unknown as Record<string, unknown>[]} mapa={NAZWY_SEKCJI} pole="sekcja" />
                  </div>
                </SekcjaZwijana>
                <SekcjaZwijana
                  tytul="Kupujący kontra sprzedający"
                  opis={`${kupujacy} / ${sprzedajacy}`}
                  otwarta={stronyOtwarte}
                  onToggle={() => setStronyOtwarte((v) => !v)}
                >
                  <div style={{ width: '100%', height: 260 }}>
                    <WykresStron dane={dane.strony} />
                  </div>
                </SekcjaZwijana>
              </div>

              <SekcjaZwijana
                tytul="Rozkład latencji"
                otwarta={latencjaOtwarta}
                onToggle={() => setLatencjaOtwarta((v) => !v)}
              >
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: 16 }}>
                  <div style={{ width: '100%', height: 260 }}>
                    <WykresLatencji dane={dane.latencja.histogram} />
                  </div>
                  {dane.koszty.pokrycie > 0 ? (
                    <div style={{ width: '100%', height: 260 }}>
                      <WykresKosztu dane={dane.dzienne} />
                    </div>
                  ) : null}
                </div>
              </SekcjaZwijana>
            </div>
          ) : null}

          {dane && dane.ogolem.zapytan > 0 && zakladka === 'Jakość i odmowy' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
                <Karta
                  tytul="Odmowy łącznie"
                  wartosc={String(dane.ogolem.odmowy)}
                  podpis={udzialOdmow !== null ? `${procent(udzialOdmow)} wszystkich zapytań` : 'brak danych'}
                />
                <Karta
                  tytul="Ocena użytkowników"
                  wartosc={dane.oceny.razem === 0 ? 'brak ocen' : procent(dane.oceny.trafnosc)}
                  podpis={`${dane.oceny.razem} ocen, pokrycie ${procent(dane.oceny.pokrycie)}`}
                />
                <div
                  style={{
                    background: th.accentSoft,
                    border: `1px solid ${th.accentLine}`,
                    borderRadius: 14,
                    padding: '16px 18px',
                    boxShadow: th.shadow,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 6,
                    minWidth: 0,
                  }}
                >
                  <span style={{ fontFamily: BODY, fontSize: 11, fontWeight: 600, letterSpacing: 0.5, textTransform: 'uppercase', color: th.accentInk }}>
                    Do naprawy najpierw
                  </span>
                  <span style={{ fontFamily: DISPLAY, fontSize: 18, fontWeight: 700, lineHeight: 1.25, color: th.accentInk }}>
                    {topPowod ? etykieta(NAZWY_POWODOW, topPowod.powod) : 'brak odmów w okresie'}
                  </span>
                  {topPowod ? (
                    <span style={{ fontFamily: BODY, fontSize: 12, color: th.accentInk }}>
                      {topPowod.ile} odmów, {procent(topPowod.udzial)}
                    </span>
                  ) : null}
                </div>
              </div>

              <Ramka tytul="Powody odmowy">
                {dane.powody.length > 0 ? (
                  <WykresPoziomy dane={dane.powody as unknown as Record<string, unknown>[]} mapa={NAZWY_POWODOW} pole="powod" />
                ) : (
                  <p style={{ color: th.ink2, fontSize: 13 }}>Brak odmów w wybranym zakresie.</p>
                )}
              </Ramka>
            </div>
          ) : null}

          {dane && dane.ogolem.zapytan > 0 && zakladka === 'Pytania' ? (
            <section
              style={{
                background: th.surface,
                border: `1px solid ${th.line}`,
                borderRadius: 14,
                boxShadow: th.shadow,
                overflow: 'hidden',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 18px 12px' }}>
                <h2 style={{ margin: 0, fontFamily: DISPLAY, fontSize: 15, fontWeight: 700, color: th.ink }}>
                  Najczęstsze pytania
                </h2>
                <span style={{ fontFamily: BODY, fontSize: 12.5, color: th.ink2 }}>
                  {dane.ogolem.unikalne_pytania} unikalnych · pokazane {pytaniaWidoczne.length}
                </span>
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: BODY, fontSize: 13 }}>
                <tbody>
                  {pytaniaWidoczne.map((pozycja) => (
                    <tr key={pozycja.pytanie} style={{ borderTop: `1px solid ${th.lineSoft}` }}>
                      <td style={{ padding: '10px 18px', color: th.ink2 }}>{pozycja.pytanie}</td>
                      <td style={{ padding: '10px 18px', textAlign: 'right', fontWeight: 600, width: 60, color: th.ink }}>
                        {pozycja.ile}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(dane.top_pytania.length > PYTANIA_WIDOCZNE) ? (
                <button
                  type="button"
                  onClick={() => setWszystkiePytania((v) => !v)}
                  style={{
                    width: '100%',
                    padding: 14,
                    background: 'none',
                    border: 'none',
                    borderTop: `1px solid ${th.lineSoft}`,
                    cursor: 'pointer',
                    fontFamily: BODY,
                    fontSize: 13,
                    fontWeight: 700,
                    color: th.accentInk,
                  }}
                >
                  {wszystkiePytania ? 'Pokaż tylko najczęstsze ▴' : `Pokaż ${dane.top_pytania.length} najczęstszych ▾`}
                </button>
              ) : null}
            </section>
          ) : null}

          {zakladka === 'Oceny' ? (
            <section
              style={{
                background: th.surface,
                border: `1px solid ${th.line}`,
                borderRadius: 14,
                boxShadow: th.shadow,
                overflow: 'hidden',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 18px 12px' }}>
                <h2 style={{ margin: 0, fontFamily: DISPLAY, fontSize: 15, fontWeight: 700, color: th.ink }}>
                  Ocenione odpowiedzi
                </h2>
                {przypadki ? (
                  <span style={{ fontFamily: BODY, fontSize: 12.5, color: th.ink2 }}>
                    {przypadki.razem} razem · {przypadki.przypadki.filter((p) => p.ocena === 'dol').length} negatywnych
                  </span>
                ) : null}
              </div>

              {bladPrzypadkow ? (
                <p style={{ padding: '0 18px 16px', color: th.ink2, fontSize: 13 }}>{bladPrzypadkow}</p>
              ) : null}

              {!bladPrzypadkow && przypadki === null ? (
                <p style={{ padding: '0 18px 16px', color: th.ink2, fontSize: 13 }}>Ładuję oceny</p>
              ) : null}

              {!bladPrzypadkow && przypadki && przypadki.razem === 0 ? (
                <p style={{ padding: '0 18px 16px', color: th.ink2, fontSize: 13 }}>
                  Brak ocen w wybranym okresie. Kciuk pod odpowiedzią zapisuje przypadek do tej tabeli.
                </p>
              ) : null}

              {przypadki && przypadki.razem > 0 ? (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: BODY, fontSize: 13 }}>
                    <thead>
                      <tr style={{ borderTop: `1px solid ${th.lineSoft}` }}>
                        {['Czas', 'Ocena', 'Diagnoza', 'Do poprawy', 'Sekcja', 'Pytanie', 'Rerank top1', 'Pokrycie', 'Etap', 'Wybrana strona', 'Przewaga sekcji'].map((naglowek) => (
                          <th
                            key={naglowek}
                            style={{ padding: '10px 18px', textAlign: 'left', color: th.ink3, fontSize: 11, fontWeight: 700, letterSpacing: '.05em', textTransform: 'uppercase' as const, whiteSpace: 'nowrap' }}
                          >
                            {naglowek}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {przypadki.przypadki.map((p, i) => (
                        <tr key={`${p.czas ?? ''}-${i}`} style={{ borderTop: `1px solid ${th.lineSoft}` }}>
                          <td style={{ padding: '10px 18px', color: th.ink2, whiteSpace: 'nowrap' }}>
                            {p.czas ? p.czas.slice(0, 16).replace('T', ' ') : '—'}
                          </td>
                          <td style={{ padding: '10px 18px', color: th.ink2, whiteSpace: 'nowrap' }}>
                            {p.ocena === 'gora' ? 'w górę' : 'w dół'}
                          </td>
                          <td style={{ padding: '10px 18px', color: th.ink }}>
                            {ETYKIETY_DIAGNOZ[p.diagnoza] ?? p.diagnoza}
                          </td>
                          <td style={{ padding: '10px 18px', color: th.ink2 }}>
                            {LEKARSTWA_DIAGNOZ[p.diagnoza] ?? ''}
                          </td>
                          <td style={{ padding: '10px 18px', color: th.ink2, whiteSpace: 'nowrap' }}>
                            {p.sekcja ? (NAZWY_SEKCJI[p.sekcja] ?? p.sekcja) : '—'}
                          </td>
                          <td style={{ padding: '10px 18px', color: th.ink2, maxWidth: 320 }}>
                            {p.pytanie ? (p.pytanie.length > 80 ? `${p.pytanie.slice(0, 80)}…` : p.pytanie) : '—'}
                          </td>
                          <td style={{ padding: '10px 18px', textAlign: 'right', color: th.ink2 }}>
                            {p.cechy?.rerank_top1 ?? '—'}
                          </td>
                          <td style={{ padding: '10px 18px', textAlign: 'right', color: th.ink2 }}>
                            {p.cechy?.pokrycie ?? '—'}
                          </td>
                          <td style={{ padding: '10px 18px', textAlign: 'right', color: th.ink2 }}>
                            {p.cechy?.etap ?? '—'}
                          </td>
                          <td style={{ padding: '10px 18px', color: th.ink2, whiteSpace: 'nowrap' }}>
                            {p.cechy?.strona_wybrana ? (NAZWY_STRON[p.cechy.strona_wybrana] ?? p.cechy.strona_wybrana) : '—'}
                          </td>
                          <td style={{ padding: '10px 18px', textAlign: 'right', color: th.ink2 }}>
                            {p.cechy?.przewaga_sekcji ?? '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </section>
          ) : null}

          {zakladka === 'Kolejka' ? <KolejkaZgloszen dni={filtry.dni} /> : null}

          {dane && dane.ogolem.zapytan > 0 && zakladka === 'Eksport' ? (
            <PanelEksportu filtry={filtry} kolumny={dane.kolumny} />
          ) : null}
        </div>

        {resetOtwarty ? (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.45)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 100,
              padding: 24,
            }}
          >
            <div
              style={{
                background: th.surface,
                border: `1px solid ${th.line}`,
                borderRadius: 14,
                boxShadow: th.shadow,
                padding: 22,
                maxWidth: 380,
                width: '100%',
                display: 'flex',
                flexDirection: 'column',
                gap: 12,
              }}
            >
              <h2 style={{ margin: 0, fontFamily: DISPLAY, fontSize: 17, fontWeight: 700, color: th.ink }}>
                Zresetować statystyki?
              </h2>
              <p style={{ margin: 0, fontFamily: BODY, fontSize: 13.5, color: th.ink2, lineHeight: 1.5 }}>
                Dotychczasowe dane zostaną zarchiwizowane na serwerze i wyzerowane na tym panelu.
                Tej operacji nie da się cofnąć z tego miejsca. Wymaga tokenu administratora.
              </p>
              <input
                type="password"
                value={tokenResetu}
                onChange={(e) => setTokenResetu(e.target.value)}
                placeholder="Token administratora"
                autoComplete="off"
                style={{
                  height: 38,
                  padding: '0 12px',
                  borderRadius: 9,
                  border: `1px solid ${th.line}`,
                  background: th.raised,
                  color: th.ink,
                  fontFamily: BODY,
                  fontSize: 13,
                }}
              />
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 4 }}>
                <button
                  type="button"
                  onClick={() => setResetOtwarty(false)}
                  disabled={resetowanie}
                  style={{
                    height: 36,
                    padding: '0 16px',
                    borderRadius: 100,
                    border: `1px solid ${th.line}`,
                    background: th.surface,
                    color: th.ink2,
                    fontFamily: BODY,
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: resetowanie ? 'default' : 'pointer',
                  }}
                >
                  Anuluj
                </button>
                <button
                  type="button"
                  onClick={potwierdzResetStatystyk}
                  disabled={resetowanie || !tokenResetu}
                  style={{
                    height: 36,
                    padding: '0 16px',
                    borderRadius: 100,
                    border: `1px solid ${th.accentLine}`,
                    background: th.accent,
                    color: '#fff',
                    fontFamily: BODY,
                    fontSize: 13,
                    fontWeight: 700,
                    cursor: resetowanie ? 'default' : 'pointer',
                    opacity: resetowanie ? 0.7 : 1,
                  }}
                >
                  {resetowanie ? 'Resetuję...' : 'Tak, resetuj'}
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </ThemeContext.Provider>
  );
}
