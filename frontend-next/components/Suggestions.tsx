'use client';

import { useState } from 'react';
import { useTheme, BODY } from '@/lib/theme';

interface Props {
  items: string[];
  onPick: (tekst: string) => void;
}

export default function Suggestions({ items, onPick }: Props) {
  const th = useTheme();
  const [hover, setHover] = useState<number | null>(null);
  if (items.length === 0) return null;

  return (
    <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}>
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
