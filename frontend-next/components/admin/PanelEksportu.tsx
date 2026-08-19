'use client';

import { useState } from 'react';
import {
  ETYKIETY_KOLUMN,
  parametryFiltrow,
  type Filtry,
  type Kolumny,
} from '@/lib/admin';
import { useTheme, BODY, DISPLAY } from '@/lib/theme';

export default function PanelEksportu({ filtry, kolumny }: { filtry: Filtry; kolumny: Kolumny }) {
  const th = useTheme();
  const [wybrane, setWybrane] = useState<string[]>(kolumny.domyslne);
  const [format, setFormat] = useState<'csv' | 'json'>('csv');

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

  const adres = `/api/admin/eksport?format=${format}&kolumny=${wybrane.join(',')}&${parametryFiltrow(filtry)}`;
  const brakWyboru = wybrane.length === 0;

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
        Zaznacz kolumny, które mają trafić do pliku. Filtry z góry strony obowiązują także tutaj.
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
            {ETYKIETY_KOLUMN[kolumna]}
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
      <a
        href={brakWyboru ? undefined : adres}
        download
        aria-disabled={brakWyboru}
        style={{
          alignSelf: 'flex-start',
          padding: '9px 18px',
          borderRadius: 9,
          background: brakWyboru ? th.line : th.accent,
          color: '#FFFFFF',
          fontFamily: BODY,
          fontWeight: 600,
          fontSize: 13,
          textDecoration: 'none',
          pointerEvents: brakWyboru ? 'none' : 'auto',
        }}
      >
        Pobierz plik
      </a>
    </section>
  );
}
