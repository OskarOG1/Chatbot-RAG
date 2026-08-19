'use client';

import type { ReactNode } from 'react';
import { useTheme, BODY, DISPLAY } from '@/lib/theme';

interface SekcjaZwijanaProps {
  tytul: string;
  opis?: string;
  otwarta: boolean;
  onToggle: () => void;
  children: ReactNode;
}

export default function SekcjaZwijana({ tytul, opis, otwarta, onToggle, children }: SekcjaZwijanaProps) {
  const th = useTheme();

  return (
    <section
      style={{
        background: th.surface,
        border: `1px solid ${th.line}`,
        borderRadius: 14,
        boxShadow: th.shadow,
        overflow: 'hidden',
      }}
    >
      <button
        type="button"
        onClick={onToggle}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          padding: '14px 18px',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontFamily: DISPLAY, fontSize: 15, fontWeight: 700, color: th.ink }}>{tytul}</span>
          {opis ? (
            <span style={{ fontFamily: BODY, fontSize: 12.5, color: th.ink2 }}>{opis}</span>
          ) : null}
        </span>
        <span style={{ fontFamily: BODY, fontSize: 13, color: th.ink2 }}>
          {otwarta ? 'Zwiń ▴' : 'Rozwiń ▾'}
        </span>
      </button>
      {otwarta ? (
        <div style={{ padding: '4px 18px 18px', borderTop: `1px solid ${th.lineSoft}` }}>{children}</div>
      ) : null}
    </section>
  );
}
