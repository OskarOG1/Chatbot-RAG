'use client';

import { useState } from 'react';
import {
  ETYKIETY_KOLUMN,
  etykieta,
  pobierzEksport,
  type Filtry,
  type Kolumny,
} from '@/lib/admin';
import { useTheme, BODY, DISPLAY } from '@/lib/theme';

export default function PanelEksportu({
  filtry,
  kolumny,
  token,
}: {
  filtry: Filtry;
  kolumny: Kolumny;
  token: string;
}) {
  const th = useTheme();
  const [wybrane, setWybrane] = useState<string[]>(kolumny.domyslne);
  const [format, setFormat] = useState<'csv' | 'json'>('csv');
  const [pobieranie, setPobieranie] = useState(false);
  const [blad, setBlad] = useState<string | null>(null);

  const przelacz = (kolumna: string) => {
    setWybrane((biezace) =>
      biezace.includes(kolumna) ? biezace.filter((k) => k !== kolumna) : [...biezace, kolumna],
    );
  };

  const pigulka = (aktywna: boolean) => ({
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    borderRadius: 100,
    padding: '7px 12px',
    border: `1px solid ${aktywna ? th.accentLine : th.line}`,
    background: aktywna ? th.accentSoft : th.raised,
    color: aktywna ? th.accentInk : th.ink2,
    fontFamily: BODY,
    fontSize: 12.5,
    fontWeight: 600,
    cursor: 'pointer',
  });

  const brakWyboru = wybrane.length === 0;

  const pobierz = async () => {
    setPobieranie(true);
    setBlad(null);
    try {
      const { blob, nazwa } = await pobierzEksport(filtry, wybrane, format, token);
      const adres = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = adres;
      link.download = nazwa;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(adres);
    } catch (e) {
      setBlad(e instanceof Error ? e.message : 'Nie udało się pobrać pliku');
    } finally {
      setPobieranie(false);
    }
  };

  return (
    <section
      style={{
        background: th.surface,
        border: `1px solid ${th.line}`,
        borderRadius: 14,
        padding: 18,
        boxShadow: th.shadow,
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
      }}
    >
      <h2 style={{ margin: 0, fontFamily: DISPLAY, fontSize: 15, fontWeight: 700, color: th.ink }}>
        Eksport danych
      </h2>
      <p style={{ margin: 0, fontSize: 12.5, color: th.ink2 }}>
        Zaznacz kolumny, które mają trafić do pliku. Wybrany u góry strony okres i pozostałe filtry
        obowiązują także tutaj.
      </p>
      <div style={{ display: 'flex', gap: 8 }}>
        <button
          type="button"
          onClick={() => setWybrane(kolumny.wszystkie)}
          style={{ ...pigulka(false), fontWeight: 500 }}
        >
          Zaznacz wszystko
        </button>
        <button
          type="button"
          onClick={() => setWybrane([])}
          style={{ ...pigulka(false), fontWeight: 500 }}
        >
          Odznacz wszystko
        </button>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
        {kolumny.wszystkie.map((kolumna) => (
          <label key={kolumna} style={pigulka(wybrane.includes(kolumna))}>
            <input
              type="checkbox"
              checked={wybrane.includes(kolumna)}
              onChange={() => przelacz(kolumna)}
              style={{ accentColor: th.accent }}
            />
            {etykieta(ETYKIETY_KOLUMN, kolumna)}
          </label>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <button type="button" onClick={() => setFormat('csv')} style={pigulka(format === 'csv')}>
          CSV
        </button>
        <button type="button" onClick={() => setFormat('json')} style={pigulka(format === 'json')}>
          JSON
        </button>
      </div>
      {!token ? (
        <p style={{ margin: 0, fontSize: 12.5, color: th.ink2 }}>
          Bez tokenu administratora plik nie zawiera kolumny z treścią pytań. Token wpisujesz u góry
          strony.
        </p>
      ) : null}
      {blad ? <p style={{ margin: 0, fontSize: 12.5, color: th.ink }}>{blad}</p> : null}
      <button
        type="button"
        onClick={pobierz}
        disabled={brakWyboru || pobieranie}
        style={{
          alignSelf: 'flex-start',
          padding: '9px 18px',
          borderRadius: 9,
          border: 'none',
          background: brakWyboru || pobieranie ? th.line : th.accent,
          color: '#FFFFFF',
          fontFamily: BODY,
          fontWeight: 600,
          fontSize: 13,
          cursor: brakWyboru || pobieranie ? 'default' : 'pointer',
        }}
      >
        {pobieranie ? 'Pobieram...' : 'Pobierz plik'}
      </button>
    </section>
  );
}
