'use client';

import type { ReactNode } from 'react';
import { useTheme, BODY, DISPLAY } from '@/lib/theme';
import { useTekstyAdmina } from '@/lib/adminTeksty';
import { useWaskiEkran } from '@/lib/ekran';

interface SekcjaZwijanaProps {
  tytul: string;
  opis?: string;
  otwarta: boolean;
  onToggle: () => void;
  children: ReactNode;
}

export default function SekcjaZwijana({ tytul, opis, otwarta, onToggle, children }: SekcjaZwijanaProps) {
  const th = useTheme();
  const t = useTekstyAdmina();
  const waski = useWaskiEkran();

  return (
    <section
      style={{
        background: th.surface,
        border: `1px solid ${th.line}`,
        borderRadius: 14,
        boxShadow: th.shadow,
        overflow: 'hidden',
        minWidth: 0,
      }}
    >
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={otwarta}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          padding: waski ? '13px 14px' : '14px 18px',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
        }}
      >
        <span style={{ display: 'flex', alignItems: 'baseline', columnGap: 10, rowGap: 2, flexWrap: 'wrap', minWidth: 0 }}>
          <span style={{ fontFamily: DISPLAY, fontSize: 15, fontWeight: 700, color: th.ink }}>{tytul}</span>
          {opis ? (
            <span style={{ fontFamily: BODY, fontSize: 12.5, color: th.ink2 }}>{opis}</span>
          ) : null}
        </span>
        <span style={{ flex: '0 0 auto', fontFamily: BODY, fontSize: 13, color: th.ink2, whiteSpace: 'nowrap' }}>
          {otwarta ? t.zwin : t.rozwin}
        </span>
      </button>
      {otwarta ? (
        <div style={{ padding: waski ? '4px 12px 14px' : '4px 18px 18px', borderTop: `1px solid ${th.lineSoft}` }}>{children}</div>
      ) : null}
    </section>
  );
}
