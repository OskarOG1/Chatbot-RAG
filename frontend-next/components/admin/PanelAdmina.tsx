'use client';

import { Fragment, useCallback, useEffect, useRef, useState, type CSSProperties } from 'react';
import Link from 'next/link';
import {
  pobierzStatystyki,
  procent,
  sekundy,
  etykieta,
  resetujStatystyki,
  pobierzPrzypadki,
  type Filtry,
  type Statystyki,
  type Przypadki,
} from '@/lib/admin';
import { JezykAdminaContext, TEKSTY_ADMINA, opisBledu, type Zakladka } from '@/lib/adminTeksty';
import type { Lang } from '@/lib/chat';
import { useWaskiEkran } from '@/lib/ekran';
import { jezykStartowy, wczytajJezyk, zapiszJezyk } from '@/lib/threads';
import { ThemeContext, THEMES, BODY, DISPLAY, MONO, type ThemeName } from '@/lib/theme';
import { FlagaGb, FlagaPl, IkonaSlonce, IkonaKsiezyc } from '@/components/Ikony';
import Karta from '@/components/admin/Karta';
import SekcjaZwijana from '@/components/admin/SekcjaZwijana';
import {
  Ramka,
  BrakTrendu,
  WykresDzienny,
  WykresPoziomy,
  WykresStron,
  WykresLatencji,
  WykresKosztu,
  WYSOKOSC,
  wysokoscPoziomego,
} from '@/components/admin/Wykresy';
import PanelEksportu from '@/components/admin/PanelEksportu';
import WyborZakresu from '@/components/admin/WyborZakresu';
import KolejkaZgloszen from '@/components/admin/KolejkaZgloszen';

const ZAKLADKI: Zakladka[] = ['przeglad', 'jakosc', 'pytania', 'oceny', 'kolejka', 'eksport'];

const PYTANIA_WIDOCZNE = 6;

function kluczZapytania(filtry: Filtry, token: string, odswiez: number): string {
  return JSON.stringify([filtry, token, odswiez]);
}

type KomunikatResetu = { rodzaj: 'zarchiwizowane' } | { rodzaj: 'bez_archiwum' } | { rodzaj: 'blad'; blad: unknown };

export default function PanelAdmina() {
  const [themeName, setThemeName] = useState<ThemeName>('light');
  const [lang, setLang] = useState<Lang>(jezykStartowy);
  const [filtry, setFiltry] = useState<Filtry>({ dni: 7, od: null, do: null, lang: null, strona: null });
  const [dane, setDane] = useState<Statystyki | null>(null);
  const [wynikStatystyk, setWynikStatystyk] = useState<{ klucz: string; blad: unknown } | null>(null);
  const [odswiez, setOdswiez] = useState(0);
  const [zaktualizowano, setZaktualizowano] = useState<Date | null>(null);
  const [zakladka, setZakladka] = useState<Zakladka>('przeglad');
  const [pozostaleOtwarte, setPozostaleOtwarte] = useState(false);
  const [ruchOtwarty, setRuchOtwarty] = useState(true);
  const [sekcjeOtwarte, setSekcjeOtwarte] = useState(true);
  const [stronyOtwarte, setStronyOtwarte] = useState(true);
  const [latencjaOtwarta, setLatencjaOtwarta] = useState(false);
  const [wszystkiePytania, setWszystkiePytania] = useState(false);
  const [resetOtwarty, setResetOtwarty] = useState(false);
  const [resetowanie, setResetowanie] = useState(false);
  const [komunikatResetu, setKomunikatResetu] = useState<KomunikatResetu | null>(null);
  const [token, setToken] = useState('');
  const [tokenWpisywany, setTokenWpisywany] = useState('');
  const [tokenOtwarty, setTokenOtwarty] = useState(false);
  const [przypadki, setPrzypadki] = useState<Przypadki | null>(null);
  const [wynikOcen, setWynikOcen] = useState<{ klucz: string; blad: unknown } | null>(null);
  const waski = useWaskiEkran();
  const th = THEMES[themeName];
  const t = TEKSTY_ADMINA[lang];
  const pasekZakladek = useRef<HTMLDivElement | null>(null);
  const [przewijaniePaska, setPrzewijaniePaska] = useState({ lewo: false, prawo: false });

  const zmierzPasek = useCallback(() => {
    const pasek = pasekZakladek.current;
    if (!pasek) {
      return;
    }
    const lewo = pasek.scrollLeft > 2;
    const prawo = pasek.scrollLeft + pasek.clientWidth < pasek.scrollWidth - 2;
    setPrzewijaniePaska((stan) => (stan.lewo === lewo && stan.prawo === prawo ? stan : { lewo, prawo }));
  }, []);

  useEffect(() => {
    const pasek = pasekZakladek.current;
    if (!pasek) {
      return undefined;
    }
    const obserwator = new ResizeObserver(zmierzPasek);
    obserwator.observe(pasek);
    const klatka = requestAnimationFrame(zmierzPasek);
    return () => {
      obserwator.disconnect();
      cancelAnimationFrame(klatka);
    };
  }, [zmierzPasek, lang]);

  const wybierzZakladke = (klucz: Zakladka, przycisk: HTMLButtonElement) => {
    setZakladka(klucz);
    const pasek = pasekZakladek.current;
    if (!pasek) {
      return;
    }
    const cel = przycisk.offsetLeft - (pasek.clientWidth - przycisk.offsetWidth) / 2;
    pasek.scrollTo({ left: Math.max(0, cel), behavior: 'smooth' });
  };

  const wskaznikPaska = (strona: 'lewo' | 'prawo'): CSSProperties => ({
    position: 'absolute',
    top: 0,
    bottom: 1,
    [strona === 'lewo' ? 'left' : 'right']: 0,
    width: 44,
    zIndex: 2,
    pointerEvents: 'none',
    display: 'flex',
    alignItems: 'center',
    justifyContent: strona === 'lewo' ? 'flex-start' : 'flex-end',
    padding: waski ? '0 8px 3px' : '0 2px 3px',
    background: `linear-gradient(to ${strona === 'lewo' ? 'right' : 'left'}, ${th.canvas} 45%, transparent)`,
    color: th.ink3,
    fontFamily: BODY,
    fontSize: 20,
    lineHeight: 1,
  });

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  useEffect(() => {
    const zmianaWInnejKarcie = () => {
      const zapisany = wczytajJezyk();
      if (zapisany) {
        setLang(zapisany);
      }
    };
    window.addEventListener('storage', zmianaWInnejKarcie);
    return () => window.removeEventListener('storage', zmianaWInnejKarcie);
  }, []);

  const ustawJezyk = (nowy: Lang) => {
    setLang(nowy);
    zapiszJezyk(nowy);
  };

  const potwierdzResetStatystyk = async () => {
    setResetowanie(true);
    setKomunikatResetu(null);
    try {
      const archiwum = await resetujStatystyki(token);
      setKomunikatResetu({ rodzaj: archiwum ? 'zarchiwizowane' : 'bez_archiwum' });
      setResetOtwarty(false);
      setOdswiez((n) => n + 1);
    } catch (e) {
      setKomunikatResetu({ rodzaj: 'blad', blad: e });
    } finally {
      setResetowanie(false);
    }
  };

  useEffect(() => {
    let aktywny = true;
    const klucz = kluczZapytania(filtry, token, odswiez);
    pobierzStatystyki(filtry, token)
      .then((wynik) => {
        if (aktywny) {
          setDane(wynik);
          setZaktualizowano(new Date());
          setWynikStatystyk({ klucz, blad: null });
        }
      })
      .catch((e) => {
        if (aktywny) {
          setWynikStatystyk({ klucz, blad: e ?? true });
        }
      });
    return () => {
      aktywny = false;
    };
  }, [filtry, token, odswiez]);

  useEffect(() => {
    if (zakladka !== 'oceny') {
      return;
    }
    let aktywny = true;
    const klucz = kluczZapytania(filtry, token, odswiez);
    pobierzPrzypadki(filtry, token)
      .then((wynik) => {
        if (aktywny) {
          setPrzypadki(wynik);
          setWynikOcen({ klucz, blad: null });
        }
      })
      .catch((e) => {
        if (aktywny) {
          setWynikOcen({ klucz, blad: e ?? true });
        }
      });
    return () => {
      aktywny = false;
    };
  }, [zakladka, filtry, token, odswiez]);

  const kluczBiezacy = kluczZapytania(filtry, token, odswiez);
  const ladowanie = wynikStatystyk?.klucz !== kluczBiezacy;
  const blad = wynikStatystyk?.klucz === kluczBiezacy ? wynikStatystyk.blad : null;
  const bladPrzypadkow = wynikOcen?.klucz === kluczBiezacy ? wynikOcen.blad : null;

  const okresy: { etykieta: string; dni: number | null }[] = [
    { etykieta: t.okresy.dni7, dni: 7 },
    { etykieta: t.okresy.dni30, dni: 30 },
    { etykieta: t.okresy.dni90, dni: 90 },
    { etykieta: t.okresy.wszystko, dni: null },
  ];

  const jezyki: { etykieta: string; lang: 'pl' | 'en' | null }[] = [
    { etykieta: t.jezyki.wszystkie, lang: null },
    { etykieta: t.jezyki.pl, lang: 'pl' },
    { etykieta: t.jezyki.en, lang: 'en' },
  ];

  const strony: { etykieta: string; strona: 'kupujacy' | 'sprzedajacy' | null }[] = [
    { etykieta: t.strony.wszyscy, strona: null },
    { etykieta: t.strony.kupujacy, strona: 'kupujacy' },
    { etykieta: t.strony.sprzedajacy, strona: 'sprzedajacy' },
  ];

  const pigulka = (aktywna: boolean) => ({
    height: 34,
    whiteSpace: 'nowrap' as const,
    padding: waski ? '0 12px' : '0 14px',
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
    minWidth: waski ? 58 : undefined,
  };

  const grupaFiltrow: CSSProperties = { display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 8 };

  const rozdzielacz = waski ? null : <span style={{ width: 1, alignSelf: 'stretch', background: th.line, margin: '0 4px' }} />;

  const przyciskNaglowka: CSSProperties = {
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
    cursor: 'pointer',
  };

  const siatkaKart = (minimum: number): CSSProperties => ({
    display: 'grid',
    gridTemplateColumns: `repeat(auto-fit, minmax(min(${waski ? 140 : minimum}px, 100%), 1fr))`,
    gap: waski ? 10 : 14,
  });

  const siatkaWykresow: CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(min(420px, 100%), 1fr))',
    gap: waski ? 12 : 16,
  };

  const kupujacy = dane?.strony.find((s) => s.strona === 'kupujacy')?.ile ?? 0;
  const sprzedajacy = dane?.strony.find((s) => s.strona === 'sprzedajacy')?.ile ?? 0;

  const powodyPosortowane = [...(dane?.powody ?? [])].sort((a, b) => b.ile - a.ile);
  const topPowod = powodyPosortowane[0] ?? null;
  const udzialOdmow = dane && dane.ogolem.zapytan > 0 ? dane.ogolem.odmowy / dane.ogolem.zapytan : null;

  const pytaniaWidoczne = wszystkiePytania ? dane?.top_pytania ?? [] : (dane?.top_pytania ?? []).slice(0, PYTANIA_WIDOCZNE);

  const tabStyl = (aktywna: boolean) => ({
    position: 'relative' as const,
    flex: '0 0 auto',
    whiteSpace: 'nowrap' as const,
    padding: waski ? '10px 12px 12px' : '10px 16px 12px',
    background: 'none',
    border: 'none',
    borderBottom: `3px solid ${aktywna ? th.accent : 'transparent'}`,
    fontFamily: BODY,
    fontSize: waski ? 13.5 : 14,
    fontWeight: 600 as const,
    color: aktywna ? th.ink : th.ink2,
    cursor: 'pointer',
  });

  const tekstResetu = (k: KomunikatResetu) => {
    if (k.rodzaj === 'zarchiwizowane') return t.resetZarchiwizowane;
    if (k.rodzaj === 'bez_archiwum') return t.resetBezArchiwum;
    return opisBledu(k.blad, t.bladResetu, lang);
  };

  const lokalizacja = lang === 'en' ? 'en-GB' : 'pl-PL';

  const wierszeOcen = (przypadki?.przypadki ?? []).map((p, i) => ({
    klucz: `${p.czas ?? ''}-${i}`,
    komorki: [
      p.czas ? p.czas.slice(0, 16).replace('T', ' ') : '—',
      p.ocena === 'gora' ? t.kciukGora : t.kciukDol,
      t.diagnozy[p.diagnoza] ?? p.diagnoza,
      t.lekarstwa[p.diagnoza] ?? '',
      p.sekcja ? (t.sekcje[p.sekcja] ?? p.sekcja) : '—',
      p.pytanie ? (p.pytanie.length > 80 ? `${p.pytanie.slice(0, 80)}…` : p.pytanie) : '—',
      String(p.cechy?.rerank_top1 ?? '—'),
      String(p.cechy?.pokrycie ?? '—'),
      String(p.cechy?.etap ?? '—'),
      p.cechy?.strona_wybrana ? (t.nazwyStron[p.cechy.strona_wybrana] ?? p.cechy.strona_wybrana) : '—',
      String(p.cechy?.przewaga_sekcji ?? '—'),
    ],
  }));

  const stylKolumnOcen: CSSProperties[] = [
    { whiteSpace: 'nowrap' },
    { whiteSpace: 'nowrap' },
    { color: th.ink },
    {},
    { whiteSpace: 'nowrap' },
    { maxWidth: 320 },
    { textAlign: 'right' },
    { textAlign: 'right' },
    { textAlign: 'right' },
    { whiteSpace: 'nowrap' },
    { textAlign: 'right' },
  ];

  return (
    <JezykAdminaContext.Provider value={lang}>
      <ThemeContext.Provider value={th}>
        <div style={{ minHeight: '100vh', background: th.canvas, color: th.ink, padding: waski ? '16px 12px 40px' : '28px 24px 48px' }}>
          <div style={{ maxWidth: 1180, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: waski ? 14 : 18 }}>
            <header
              style={{
                display: 'flex',
                flexDirection: waski ? 'column' : 'row',
                justifyContent: 'space-between',
                alignItems: waski ? 'stretch' : 'flex-start',
                gap: waski ? 12 : 24,
              }}
            >
              <div style={{ minWidth: 0 }}>
                <h1 style={{ margin: 0, fontFamily: DISPLAY, fontSize: waski ? 22 : 26, fontWeight: 800 }}>{t.tytul}</h1>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    columnGap: 8,
                    rowGap: 2,
                    marginTop: 6,
                    fontFamily: BODY,
                    fontSize: 13,
                    color: th.ink2,
                  }}
                >
                  <span>
                    {dane?.zakres.od
                      ? t.daneOdDo(dane.zakres.od.slice(0, 10), dane.zakres.do?.slice(0, 10) ?? '')
                      : t.brakDanychWZakresie}
                  </span>
                  {zaktualizowano ? (
                    <>
                      <span style={{ width: 4, height: 4, borderRadius: 999, background: th.ink3 }} />
                      <span>
                        {t.odswiezono}{' '}
                        {zaktualizowano.toLocaleTimeString(lokalizacja, { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </>
                  ) : null}
                </div>
                {komunikatResetu ? (
                  <div style={{ marginTop: 4, fontFamily: BODY, fontSize: 12.5, color: th.ink2 }}>{tekstResetu(komunikatResetu)}</div>
                ) : null}
              </div>
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  alignItems: 'center',
                  justifyContent: waski ? 'flex-start' : 'flex-end',
                  gap: waski ? 8 : 10,
                  flex: waski ? undefined : '0 1 auto',
                }}
              >
                <Link href="/" style={przyciskNaglowka}>
                  {t.wrocDoCzatu}
                </Link>
                <button type="button" onClick={() => setResetOtwarty(true)} style={przyciskNaglowka}>
                  {t.resetuj}
                </button>
                {token ? (
                  <button
                    type="button"
                    onClick={() => {
                      setToken('');
                      setTokenWpisywany('');
                      setTokenOtwarty(false);
                    }}
                    style={{
                      ...przyciskNaglowka,
                      border: `1px solid ${th.accentLine}`,
                      background: th.accentSoft,
                      color: th.accentInk,
                      fontWeight: 600,
                    }}
                  >
                    {t.wylogujToken}
                  </button>
                ) : tokenOtwarty ? (
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      setToken(tokenWpisywany);
                      setTokenOtwarty(false);
                    }}
                    style={{ display: 'flex', gap: 6, flex: waski ? '1 1 100%' : undefined }}
                  >
                    <input
                      type="password"
                      value={tokenWpisywany}
                      onChange={(e) => setTokenWpisywany(e.target.value)}
                      placeholder={t.tokenPlaceholder}
                      autoComplete="off"
                      autoFocus
                      style={{
                        height: 36,
                        width: waski ? 'auto' : 190,
                        flex: waski ? '1 1 auto' : undefined,
                        minWidth: 0,
                        padding: '0 12px',
                        borderRadius: 100,
                        border: `1px solid ${th.line}`,
                        background: th.raised,
                        color: th.ink,
                        fontFamily: BODY,
                        fontSize: waski ? 16 : 13,
                      }}
                    />
                    <button
                      type="submit"
                      disabled={!tokenWpisywany}
                      style={{
                        height: 36,
                        padding: '0 14px',
                        borderRadius: 100,
                        border: 'none',
                        background: tokenWpisywany ? th.accent : th.line,
                        color: '#FFFFFF',
                        fontFamily: BODY,
                        fontSize: 13,
                        fontWeight: 600,
                        cursor: tokenWpisywany ? 'pointer' : 'default',
                      }}
                    >
                      {t.odblokuj}
                    </button>
                  </form>
                ) : (
                  <button type="button" onClick={() => setTokenOtwarty(true)} title={t.tokenPodpowiedz} style={przyciskNaglowka}>
                    {t.wpiszToken}
                  </button>
                )}
                <div
                  role="group"
                  aria-label={t.jezykInterfejsu}
                  style={{ display: 'flex', padding: 2, borderRadius: 100, background: th.raised, border: `1px solid ${th.line}` }}
                >
                  {(['pl', 'en'] as const).map((kod) => {
                    const aktywny = lang === kod;
                    return (
                      <button
                        key={kod}
                        type="button"
                        aria-pressed={aktywny}
                        onClick={() => ustawJezyk(kod)}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 6,
                          height: 30,
                          padding: '0 10px',
                          border: 'none',
                          borderRadius: 100,
                          background: aktywny ? th.surface : 'transparent',
                          boxShadow: aktywny ? th.shadow : 'none',
                          color: aktywny ? th.ink : th.ink3,
                          fontFamily: MONO,
                          fontSize: 11,
                          fontWeight: 500,
                          lineHeight: 1,
                          cursor: 'pointer',
                        }}
                      >
                        {kod === 'pl' ? <FlagaPl /> : <FlagaGb />}
                        {kod.toUpperCase()}
                      </button>
                    );
                  })}
                </div>
                <button
                  type="button"
                  onClick={() => setThemeName(themeName === 'light' ? 'dark' : 'light')}
                  aria-label={t.zmienMotyw}
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

            <div style={{ position: 'relative', margin: waski ? '0 -12px' : undefined }}>
              <div
                ref={pasekZakladek}
                className="dc-bez-paska"
                onScroll={zmierzPasek}
                style={{
                  position: 'relative',
                  display: 'flex',
                  gap: waski ? 2 : 6,
                  borderBottom: `1px solid ${th.line}`,
                  overflowX: 'auto',
                  padding: waski ? '0 12px' : undefined,
                }}
              >
                {ZAKLADKI.map((klucz) => (
                  <button
                    key={klucz}
                    type="button"
                    aria-pressed={zakladka === klucz}
                    onClick={(e) => wybierzZakladke(klucz, e.currentTarget)}
                    style={tabStyl(zakladka === klucz)}
                  >
                    {t.zakladki[klucz]}
                  </button>
                ))}
              </div>
              {przewijaniePaska.lewo ? <div aria-hidden style={wskaznikPaska('lewo')}>‹</div> : null}
              {przewijaniePaska.prawo ? <div aria-hidden style={wskaznikPaska('prawo')}>›</div> : null}
            </div>

            <div
              style={{
                display: 'flex',
                flexDirection: waski ? 'column' : 'row',
                flexWrap: 'wrap',
                alignItems: waski ? 'stretch' : 'center',
                gap: waski ? 10 : 8,
              }}
            >
              <div style={grupaFiltrow}>
                <span style={etykietaGrupy}>{t.okres}</span>
                {okresy.map((opcja) => (
                  <button
                    key={opcja.etykieta}
                    type="button"
                    onClick={() => setFiltry((f) => ({ ...f, dni: opcja.dni, od: null, do: null }))}
                    style={pigulka(filtry.od === null && filtry.dni === opcja.dni)}
                  >
                    {opcja.etykieta}
                  </button>
                ))}
                <WyborZakresu
                  od={filtry.od}
                  do={filtry.do}
                  aktywny={filtry.od !== null}
                  onZmiana={(od, doDnia) => setFiltry((f) => ({ ...f, od, do: doDnia }))}
                />
              </div>
              {rozdzielacz}
              <div style={grupaFiltrow}>
                <span style={etykietaGrupy}>{t.jezyk}</span>
                {jezyki.map((opcja) => (
                  <button
                    key={opcja.etykieta}
                    type="button"
                    onClick={() => setFiltry((f) => ({ ...f, lang: opcja.lang }))}
                    style={pigulka(filtry.lang === opcja.lang)}
                  >
                    {opcja.etykieta}
                  </button>
                ))}
              </div>
              {rozdzielacz}
              <div style={grupaFiltrow}>
                <span style={etykietaGrupy}>{t.rola}</span>
                {strony.map((opcja) => (
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
            </div>

            {blad ? (
              <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 12, color: th.ink2, fontSize: 13 }}>
                <span>{opisBledu(blad, t.bladStatystyk, lang)}</span>
                <button type="button" onClick={() => setOdswiez((n) => n + 1)} style={pigulka(false)}>
                  {t.sprobujPonownie}
                </button>
              </div>
            ) : null}

            {ladowanie && !dane ? <p style={{ color: th.ink2, fontSize: 13 }}>{t.wczytuje}</p> : null}

            {dane && dane.ogolem.zapytan === 0 ? <p style={{ color: th.ink2, fontSize: 13 }}>{t.brakDanychKropka}</p> : null}

            {dane && dane.ogolem.zapytan > 0 && zakladka === 'przeglad' ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: waski ? 12 : 16 }}>
                <div style={siatkaKart(190)}>
                  <Karta
                    tytul={t.zadanePytania}
                    wartosc={String(dane.ogolem.zapytan)}
                    podpis={t.roznychPytan(dane.ogolem.unikalne_pytania)}
                  />
                  <Karta
                    tytul={t.udzieloneOdpowiedzi}
                    wartosc={String(dane.ogolem.odpowiedzi)}
                    akcent
                    podpis={t.wszystkichPytan(procent(dane.ogolem.trafnosc, t.brakDanych))}
                  />
                  <Karta
                    tytul={t.bezOdpowiedzi}
                    wartosc={String(dane.ogolem.odmowy)}
                    podpis={udzialOdmow !== null ? t.wszystkichPytan(procent(udzialOdmow, t.brakDanych)) : t.brakDanych}
                  />
                  <Karta tytul={t.typowyCzas} wartosc={sekundy(dane.latencja.mediana)} podpis={t.typowyCzasPodpis} />
                </div>

                <p style={{ margin: 0, fontFamily: BODY, fontSize: 12.5, color: th.ink3, lineHeight: 1.5 }}>
                  {t.bezOdpowiedziWyjasnienie}
                </p>

                <SekcjaZwijana
                  tytul={t.pozostaleLiczby}
                  otwarta={pozostaleOtwarte}
                  onToggle={() => setPozostaleOtwarte((v) => !v)}
                >
                  <div style={siatkaKart(190)}>
                    <Karta
                      tytul={t.kciukiWGore}
                      wartosc={dane.oceny.razem === 0 ? t.brakOcen : procent(dane.oceny.trafnosc, t.brakDanych)}
                      podpis={t.ocenPodpis(dane.oceny.razem, procent(dane.oceny.pokrycie, t.brakDanych))}
                    />
                    <Karta
                      tytul={t.zPamieci}
                      wartosc={procent(dane.ogolem.cache_hit, t.brakDanych)}
                      podpis={t.bezPamieci(sekundy(dane.latencja.mediana_bez_cache))}
                    />
                    <Karta
                      tytul={t.kosztModelu}
                      wartosc={dane.koszty.pokrycie === 0 ? t.brakDanych : `$${dane.koszty.koszt_usd.toFixed(4)}`}
                    />
                    <Karta
                      tytul={t.wyslaneWiadomosci}
                      wartosc={String(dane.ogolem.wysylki_ok)}
                      podpis={t.probWysylki(dane.ogolem.wysylki)}
                    />
                  </div>
                </SekcjaZwijana>

                <SekcjaZwijana tytul={t.pytaniaDzien} otwarta={ruchOtwarty} onToggle={() => setRuchOtwarty((v) => !v)}>
                  <div style={{ width: '100%', height: WYSOKOSC }}>
                    <WykresDzienny dane={dane.dzienne} />
                  </div>
                </SekcjaZwijana>

                <div style={siatkaWykresow}>
                  <SekcjaZwijana tytul={t.tematyPytan} otwarta={sekcjeOtwarte} onToggle={() => setSekcjeOtwarte((v) => !v)}>
                    <div style={{ width: '100%', height: wysokoscPoziomego(dane.sekcje.length, waski) }}>
                      <WykresPoziomy dane={dane.sekcje as unknown as Record<string, unknown>[]} mapa={t.sekcje} pole="sekcja" />
                    </div>
                  </SekcjaZwijana>
                  <SekcjaZwijana
                    tytul={t.ktoPyta}
                    opis={t.ktoPytaOpis(kupujacy, sprzedajacy)}
                    otwarta={stronyOtwarte}
                    onToggle={() => setStronyOtwarte((v) => !v)}
                  >
                    <div style={{ width: '100%', height: WYSOKOSC }}>
                      <WykresStron dane={dane.strony} />
                    </div>
                  </SekcjaZwijana>
                </div>

                <SekcjaZwijana tytul={t.jakSzybko} otwarta={latencjaOtwarta} onToggle={() => setLatencjaOtwarta((v) => !v)}>
                  <div style={siatkaWykresow}>
                    <div style={{ width: '100%', height: WYSOKOSC }}>
                      <WykresLatencji dane={dane.latencja.histogram} />
                    </div>
                    {dane.koszty.pokrycie > 0 ? (
                      <div style={{ width: '100%', height: WYSOKOSC }}>
                        <WykresKosztu dane={dane.dzienne} />
                      </div>
                    ) : null}
                  </div>
                </SekcjaZwijana>
              </div>
            ) : null}

            {dane && dane.ogolem.zapytan > 0 && zakladka === 'jakosc' ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: waski ? 12 : 16 }}>
                <div style={siatkaKart(220)}>
                  <Karta
                    tytul={t.pytaniaBezOdpowiedzi}
                    wartosc={String(dane.ogolem.odmowy)}
                    podpis={udzialOdmow !== null ? t.wszystkichPytan(procent(udzialOdmow, t.brakDanych)) : t.brakDanych}
                  />
                  <Karta
                    tytul={t.kciukiWGore}
                    wartosc={dane.oceny.razem === 0 ? t.brakOcen : procent(dane.oceny.trafnosc, t.brakDanych)}
                    podpis={t.ocenPodpis(dane.oceny.razem, procent(dane.oceny.pokrycie, t.brakDanych))}
                  />
                  <div
                    style={{
                      gridColumn: waski ? '1 / -1' : undefined,
                      background: th.accentSoft,
                      border: `1px solid ${th.accentLine}`,
                      borderRadius: 14,
                      padding: waski ? '13px 14px' : '16px 18px',
                      boxShadow: th.shadow,
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 6,
                      minWidth: 0,
                    }}
                  >
                    <span style={{ fontFamily: BODY, fontSize: 11, fontWeight: 600, letterSpacing: 0.5, textTransform: 'uppercase', color: th.accentInk }}>
                      {t.najczestszaPrzyczyna}
                    </span>
                    <span style={{ fontFamily: DISPLAY, fontSize: 18, fontWeight: 700, lineHeight: 1.25, color: th.accentInk }}>
                      {topPowod ? etykieta(t.powody, topPowod.powod) : t.brakOdmow}
                    </span>
                    {topPowod ? (
                      <span style={{ fontFamily: BODY, fontSize: 12, color: th.accentInk }}>
                        {t.przyczynaPodpis(topPowod.ile, procent(topPowod.udzial, t.brakDanych))}
                      </span>
                    ) : null}
                  </div>
                </div>

                <Ramka tytul={t.dlaczegoNie} opis={t.dlaczegoNieOpis} wysokosc={wysokoscPoziomego(dane.powody.length, waski)}>
                  {dane.powody.length > 0 ? (
                    <WykresPoziomy dane={dane.powody as unknown as Record<string, unknown>[]} mapa={t.powody} pole="powod" />
                  ) : (
                    <BrakTrendu tekst={t.kazdePytanie} />
                  )}
                </Ramka>
              </div>
            ) : null}

            {dane && dane.ogolem.zapytan > 0 && zakladka === 'pytania' ? (
              <section
                style={{
                  background: th.surface,
                  border: `1px solid ${th.line}`,
                  borderRadius: 14,
                  boxShadow: th.shadow,
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    columnGap: 12,
                    rowGap: 4,
                    padding: waski ? '14px 14px 10px' : '16px 18px 12px',
                  }}
                >
                  <h2 style={{ margin: 0, fontFamily: DISPLAY, fontSize: 15, fontWeight: 700, color: th.ink }}>
                    {t.najczestszePytania}
                  </h2>
                  <span style={{ fontFamily: BODY, fontSize: 12.5, color: th.ink2 }}>
                    {t.pytaniaLicznik(dane.ogolem.unikalne_pytania, pytaniaWidoczne.length)}
                  </span>
                </div>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: BODY, fontSize: 13 }}>
                  <tbody>
                    {pytaniaWidoczne.map((pozycja) => (
                      <tr key={pozycja.pytanie} style={{ borderTop: `1px solid ${th.lineSoft}` }}>
                        <td style={{ padding: waski ? '10px 14px' : '10px 18px', color: th.ink2, overflowWrap: 'anywhere' }}>{pozycja.pytanie}</td>
                        <td style={{ padding: waski ? '10px 14px' : '10px 18px', textAlign: 'right', fontWeight: 600, width: 60, color: th.ink }}>
                          {pozycja.ile}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {dane.top_pytania.length > PYTANIA_WIDOCZNE ? (
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
                    {wszystkiePytania ? t.pokazNajczestsze : t.pokazWszystkie(dane.top_pytania.length)}
                  </button>
                ) : null}
              </section>
            ) : null}

            {zakladka === 'oceny' ? (
              <section
                style={{
                  background: th.surface,
                  border: `1px solid ${th.line}`,
                  borderRadius: 14,
                  boxShadow: th.shadow,
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    columnGap: 12,
                    rowGap: 4,
                    padding: waski ? '14px 14px 10px' : '16px 18px 12px',
                  }}
                >
                  <h2 style={{ margin: 0, fontFamily: DISPLAY, fontSize: 15, fontWeight: 700, color: th.ink }}>
                    {t.ocenioneOdpowiedzi}
                  </h2>
                  {przypadki ? (
                    <span style={{ fontFamily: BODY, fontSize: 12.5, color: th.ink2 }}>
                      {t.ocenLicznik(przypadki.razem, przypadki.przypadki.filter((p) => p.ocena === 'dol').length)}
                    </span>
                  ) : null}
                </div>

                {bladPrzypadkow ? (
                  <p style={{ padding: '0 18px 16px', color: th.ink2, fontSize: 13 }}>{opisBledu(bladPrzypadkow, t.bladOcen, lang)}</p>
                ) : null}

                {!bladPrzypadkow && przypadki === null ? (
                  <p style={{ padding: '0 18px 16px', color: th.ink2, fontSize: 13 }}>{t.ladujeOceny}</p>
                ) : null}

                {!bladPrzypadkow && przypadki && przypadki.razem === 0 ? (
                  <p style={{ padding: '0 18px 16px', color: th.ink2, fontSize: 13 }}>{t.brakOcenOpis}</p>
                ) : null}

                {przypadki && przypadki.razem > 0 && waski ? (
                  <div style={{ borderTop: `1px solid ${th.lineSoft}` }}>
                    {wierszeOcen.map(({ klucz, komorki }, i) => (
                      <div
                        key={klucz}
                        style={{
                          padding: '12px 14px',
                          borderTop: i > 0 ? `1px solid ${th.lineSoft}` : 'none',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 8,
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, fontFamily: BODY, fontSize: 12.5, color: th.ink2 }}>
                          <span>{komorki[0]}</span>
                          <span style={{ fontWeight: 600, color: th.ink }}>{komorki[1]}</span>
                        </div>
                        <dl
                          style={{
                            margin: 0,
                            display: 'grid',
                            gridTemplateColumns: 'minmax(0, 42%) 1fr',
                            gap: '4px 12px',
                            fontFamily: BODY,
                            fontSize: 12.5,
                            overflowWrap: 'anywhere',
                          }}
                        >
                          {komorki.slice(2).map((wartosc, j) => (
                            <Fragment key={t.kolumnyOcen[j + 2]}>
                              <dt style={{ color: th.ink3 }}>{t.kolumnyOcen[j + 2]}</dt>
                              <dd style={{ margin: 0, color: j === 0 ? th.ink : th.ink2 }}>{wartosc || '—'}</dd>
                            </Fragment>
                          ))}
                        </dl>
                      </div>
                    ))}
                  </div>
                ) : null}

                {przypadki && przypadki.razem > 0 && !waski ? (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: BODY, fontSize: 13 }}>
                      <thead>
                        <tr style={{ borderTop: `1px solid ${th.lineSoft}` }}>
                          {t.kolumnyOcen.map((naglowek) => (
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
                        {wierszeOcen.map(({ klucz, komorki }) => (
                          <tr key={klucz} style={{ borderTop: `1px solid ${th.lineSoft}` }}>
                            {komorki.map((wartosc, j) => (
                              <td key={t.kolumnyOcen[j]} style={{ padding: '10px 18px', color: th.ink2, ...stylKolumnOcen[j] }}>
                                {wartosc}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : null}
              </section>
            ) : null}

            {zakladka === 'kolejka' ? <KolejkaZgloszen dni={filtry.dni} token={token} onToken={setToken} /> : null}

            {dane && dane.ogolem.zapytan > 0 && zakladka === 'eksport' ? (
              <PanelEksportu filtry={filtry} kolumny={dane.kolumny} token={token} />
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
                padding: waski ? 16 : 24,
              }}
            >
              <div
                role="dialog"
                aria-modal="true"
                aria-label={t.resetPytanie}
                style={{
                  background: th.surface,
                  border: `1px solid ${th.line}`,
                  borderRadius: 14,
                  boxShadow: th.shadow,
                  padding: waski ? 18 : 22,
                  maxWidth: 380,
                  width: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12,
                }}
              >
                <h2 style={{ margin: 0, fontFamily: DISPLAY, fontSize: 17, fontWeight: 700, color: th.ink }}>{t.resetPytanie}</h2>
                <p style={{ margin: 0, fontFamily: BODY, fontSize: 13.5, color: th.ink2, lineHeight: 1.5 }}>{t.resetOpis}</p>
                {!token ? <p style={{ margin: 0, fontFamily: BODY, fontSize: 13, color: th.ink2 }}>{t.resetBezTokenu}</p> : null}
                <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'flex-end', gap: 8, marginTop: 4 }}>
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
                    {t.anuluj}
                  </button>
                  <button
                    type="button"
                    onClick={potwierdzResetStatystyk}
                    disabled={resetowanie || !token}
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
                    {resetowanie ? t.resetuje : t.takResetuj}
                  </button>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </ThemeContext.Provider>
    </JezykAdminaContext.Provider>
  );
}
