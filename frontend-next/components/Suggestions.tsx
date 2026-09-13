'use client';

import { useState } from 'react';
import { useTheme, BODY } from '@/lib/theme';
import { useWaskiEkran } from '@/lib/ekran';

interface Props {
  items: string[];
  onPick: (tekst: string) => void;
}

export default function Suggestions({ items, onPick }: Props) {
  const th = useTheme();
  const waski = useWaskiEkran();
  const [hover, setHover] = useState<number | null>(null);
  if (items.length === 0) return null;

  return (
    <div
      className={waski ? 'dc-bez-paska' : undefined}
      style={{
        display: 'flex',
        gap: 7,
        flexWrap: waski ? 'nowrap' : 'wrap',
        overflowX: waski ? 'auto' : undefined,
        margin: waski ? '0 -10px' : undefined,
        padding: waski ? '2px 10px 6px' : undefined,
      }}
    >
      {items.map((label, i) => (
        <button
          key={label}
          type="button"
          className="dc-chip"
          onClick={() => onPick(label)}
          onMouseEnter={() => setHover(i)}
          onMouseLeave={() => setHover(null)}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            flex: waski ? '0 0 auto' : undefined,
            whiteSpace: waski ? 'nowrap' : undefined,
            padding: '8px 14px',
            borderRadius: 100,
            border: `1px solid ${hover === i ? th.accentLine : th.line}`,
            background: hover === i ? th.accentSoft : th.surface,
            color: hover === i ? th.accentInk : th.ink2,
            boxShadow: hover === i ? 'none' : th.shadow,
            fontFamily: BODY,
            fontSize: 12.5,
            fontWeight: 600,
            lineHeight: 1.35,
            cursor: 'pointer',
          }}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
