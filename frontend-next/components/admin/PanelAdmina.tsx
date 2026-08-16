'use client';

import { useEffect, useState } from 'react';
import {
  pobierzStatystyki,
  procent,
  sekundy,
  NAZWY_SEKCJI,
  NAZWY_POWODOW,
  type Filtry,
  type Statystyki,
} from '@/lib/admin';
import { ThemeContext, THEMES, BODY, DISPLAY, type ThemeName } from '@/lib/theme';
import { IkonaSlonce, IkonaKsiezyc } from '@/components/Ikony';
import Karta from '@/components/admin/Karta';
import { Ramka, WykresDzienny, WykresPoziomy, WykresStron, WykresLatencji } from '@/components/admin/Wykresy';
import PanelEksportu from '@/components/admin/PanelEksportu';

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

export default function PanelAdmina() {
  const [themeName, setThemeName] = useState<ThemeName>('light');
  const [filtry, setFiltry] = useState<Filtry>({ dni: 30, lang: null, strona: null });
  const [dane, setDane] = useState<Statystyki | null>(null);
  const [ladowanie, setLadowanie] = useState(true);
  const [blad, setBlad] = useState<string | null>(null);
  const [odswiez, setOdswiez] = useState(0);
  const th = THEMES[themeName];

  useEffect(() => {
    let aktywny = true;
    setLadowanie(true);
    setBlad(null);
    pobierzStatystyki(filtry)
      .then((wynik) => {
        if (aktywny) {
          setDane(wynik);
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

  const pigulka = (aktywna: boolean) => ({
    padding: '8px 14px',
    borderRadius: 100,
    border: `1px solid ${aktywna ? th.accentLine : th.line}`,
    background: aktywna ? th.accentSoft : th.surface,
    color: aktywna ? th.accentInk : th.ink2,
    fontFamily: BODY,
    fontSize: 12.5,
    fontWeight: 600,
    cursor: 'pointer',
  });

  const rozdzielacz = <span style={{ width: 1, alignSelf: 'stretch', background: th.line }} />;

  const kupujacy = dane?.strony.find((s) => s.strona === 'kupujacy')?.ile ?? 0;
  const sprzedajacy = dane?.strony.find((s) => s.strona === 'sprzedajacy')?.ile ?? 0;
  const nieznana = dane?.strony.find((s) => s.strona === 'nieznana')?.ile ?? 0;

  return (
    <ThemeContext.Provider value={th}>
      <div style={{ minHeight: '100vh', background: th.canvas, color: th.ink, padding: '28px 24px 48px' }}>
        <div style={{ maxWidth: 1180, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 18 }}>
          <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h1 style={{ margin: 0, fontFamily: DISPLAY, fontSize: 26, fontWeight: 800 }}>Panel statystyk</h1>
              <p style={{ margin: '6px 0 0', fontFamily: BODY, fontSize: 13, color: th.ink2 }}>
                {dane?.zakres.od
                  ? `Dane od ${dane.zakres.od.slice(0, 10)} do ${dane.zakres.do?.slice(0, 10)}`
                  : 'Brak danych w wybranym zakresie'}
              </p>
            </div>
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
              }}
            >
              {themeName === 'light' ? <IkonaKsiezyc /> : <IkonaSlonce />}
            </button>
          </header>

          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 10 }}>
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

          {dane && dane.ogolem.zapytan > 0 ? (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
                gap: 14,
              }}
            >
              <Karta
                tytul="Zapytania"
                wartosc={String(dane.ogolem.zapytan)}
                podpis={`${dane.ogolem.unikalne_pytania} unikalnych pytań`}
              />
              <Karta
                tytul="Trafność z logu"
                wartosc={procent(dane.ogolem.trafnosc)}
                akcent
                podpis={`${dane.ogolem.odpowiedzi} odpowiedzi, ${dane.ogolem.odmowy} odmów`}
              />
              <Karta
                tytul="Ocena użytkowników"
                wartosc={dane.oceny.razem === 0 ? 'brak ocen' : procent(dane.oceny.trafnosc)}
                podpis={`${dane.oceny.razem} ocen, pokrycie ${procent(dane.oceny.pokrycie)}`}
              />
              <Karta
                tytul="Mediana latencji"
                wartosc={sekundy(dane.latencja.mediana)}
                podpis={`p95 ${sekundy(dane.latencja.p95)}`}
              />
              <Karta
                tytul="Trafienia cache"
                wartosc={procent(dane.ogolem.cache_hit)}
                podpis={`bez cache ${sekundy(dane.latencja.mediana_bez_cache)}`}
              />
              <Karta
                tytul="Kupujący i sprzedający"
                wartosc={`${kupujacy} / ${sprzedajacy}`}
                podpis={`nieznana strona: ${nieznana}`}
              />
              <Karta
                tytul="Koszt tokenów"
                wartosc={dane.koszty.pokrycie === 0 ? 'brak danych' : `$${dane.koszty.koszt_usd.toFixed(4)}`}
                podpis={
                  dane.koszty.pokrycie === 0
                    ? 'pomiar dołączony w kolejnym etapie'
                    : `${dane.koszty.tokeny_we + dane.koszty.tokeny_wy} tokenów, pokrycie ${procent(dane.koszty.pokrycie)}`
                }
              />
              <Karta
                tytul="Wysłane wiadomości"
                wartosc={String(dane.ogolem.wysylki_ok)}
                podpis={`${dane.ogolem.wysylki} prób wysyłki`}
              />
            </div>
          ) : null}

          {dane && dane.ogolem.zapytan > 0 ? (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))',
                gap: 16,
              }}
            >
              <Ramka tytul="Ruch dzienny">
                <WykresDzienny dane={dane.dzienne} />
              </Ramka>
              <Ramka tytul="Sekcje odpowiedzi">
                <WykresPoziomy dane={dane.sekcje as unknown as Record<string, unknown>[]} mapa={NAZWY_SEKCJI} pole="sekcja" />
              </Ramka>
              <Ramka tytul="Powody odmowy">
                <WykresPoziomy dane={dane.powody as unknown as Record<string, unknown>[]} mapa={NAZWY_POWODOW} pole="powod" />
              </Ramka>
              <Ramka tytul="Kupujący kontra sprzedający">
                <WykresStron dane={dane.strony} />
              </Ramka>
              <Ramka tytul="Rozkład latencji">
                <WykresLatencji dane={dane.latencja.histogram} />
              </Ramka>
            </div>
          ) : null}

          {dane && dane.ogolem.zapytan > 0 ? (
            <section
              style={{
                background: th.surface,
                border: `1px solid ${th.line}`,
                borderRadius: 14,
                padding: 18,
                boxShadow: th.shadow,
              }}
            >
              <h2 style={{ margin: '0 0 12px', fontFamily: DISPLAY, fontSize: 15, fontWeight: 700, color: th.ink }}>
                Najczęstsze pytania
              </h2>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: BODY, fontSize: 13 }}>
                <tbody>
                  {dane.top_pytania.map((pozycja) => (
                    <tr key={pozycja.pytanie} style={{ borderTop: `1px solid ${th.lineSoft}` }}>
                      <td style={{ padding: '8px 4px', color: th.ink2 }}>{pozycja.pytanie}</td>
                      <td
                        style={{
                          padding: '8px 4px',
                          textAlign: 'right',
                          fontWeight: 600,
                          width: 60,
                          color: th.ink,
                        }}
                      >
                        {pozycja.ile}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          ) : null}

          {dane && dane.ogolem.zapytan > 0 ? <PanelEksportu filtry={filtry} /> : null}
        </div>
      </div>
    </ThemeContext.Provider>
  );
}
