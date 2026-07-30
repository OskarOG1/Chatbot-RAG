'use client';

import { useState } from 'react';
import { useTheme, BODY, MONO } from '@/lib/theme';
import type { Zrodlo } from '@/lib/zrodla';

interface Props {
  zrodla: Zrodlo[];
  label: string;
}

export default function SourceList({ zrodla, label }: Props) {
  const th = useTheme();
  const [hover, setHover] = useState<number | null>(null);
  if (zrodla.length === 0) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 4 }}>
      <div style={{ fontFamily: BODY, fontSize: 10.5, fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase', color: th.ink3 }}>
        {label} · <span style={{ fontFamily: MONO }}>{zrodla.length}</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 1, border: `1px solid ${th.line}`, borderRadius: 10, overflow: 'hidden', background: th.line }}>
        {zrodla.map((z, i) => (
          <a
            key={z.url}
            href={z.url}
            target="_blank"
            rel="noopener noreferrer"
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(null)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 11,
              padding: '11px 13px',
              background: hover === i ? th.raised : th.surface,
              textDecoration: 'none',
            }}
          >
            <span
              style={{
                width: 19,
                height: 19,
                borderRadius: 5,
                background: th.accentSoft,
                border: `1px solid ${th.accentLine}`,
                color: th.accentInk,
                fontFamily: MONO,
                fontSize: 10,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flex: '0 0 auto',
              }}
            >
              {i + 1}
            </span>
            <span style={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0, flex: '1 1 auto' }}>
              <span style={{ fontFamily: BODY, fontSize: 13, fontWeight: 500, color: th.ink, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {z.tytul}
              </span>
              {z.domena && <span style={{ fontFamily: MONO, fontSize: 10, color: th.ink3 }}>{z.domena}</span>}
            </span>
            <span style={{ fontSize: 12, color: th.ink3, flex: '0 0 auto' }}>→</span>
          </a>
        ))}
      </div>
    </div>
  );
}
