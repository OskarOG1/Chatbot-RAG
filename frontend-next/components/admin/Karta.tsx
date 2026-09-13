'use client';

import { useTheme, BODY, DISPLAY } from '@/lib/theme';
import { useWaskiEkran } from '@/lib/ekran';

interface KartaProps {
  tytul: string;
  wartosc: string;
  podpis?: string;
  akcent?: boolean;
}

export default function Karta({ tytul, wartosc, podpis, akcent = false }: KartaProps) {
  const th = useTheme();
  const waski = useWaskiEkran();

  return (
    <div
      style={{
        background: th.surface,
        border: `1px solid ${th.line}`,
        borderRadius: 14,
        padding: waski ? '13px 14px' : '16px 18px',
        boxShadow: th.shadow,
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        minWidth: 0,
        overflowWrap: 'anywhere',
      }}
    >
      <span
        style={{
          fontFamily: BODY,
          fontSize: waski ? 10.5 : 11,
          fontWeight: 600,
          letterSpacing: 0.5,
          textTransform: 'uppercase',
          color: th.ink3,
        }}
      >
        {tytul}
      </span>
      <span
        style={{
          fontFamily: DISPLAY,
          fontSize: waski ? 22 : 26,
          fontWeight: 700,
          lineHeight: 1.1,
          color: akcent ? th.accentInk : th.ink,
        }}
      >
        {wartosc}
      </span>
      {podpis ? (
        <span style={{ fontFamily: BODY, fontSize: 12, color: th.ink2 }}>{podpis}</span>
      ) : null}
    </div>
  );
}
