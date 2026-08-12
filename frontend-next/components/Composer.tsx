'use client';

import { type CSSProperties, type KeyboardEvent } from 'react';
import { useTheme, BODY, MONO } from '@/lib/theme';
import { type Strona } from '@/lib/chat';
import { IkonaWyslij } from './Ikony';

const AKCENT_SEGMENT = '#C43E00';

interface Props {
  value: string;
  placeholder: string;
  hint: string;
  sendLabel: string;
  disabled: boolean;
  strona: Strona;
  sideBuyingLabel: string;
  sideSellingLabel: string;
  onChange: (v: string) => void;
  onSend: () => void;
  onSetStrona: (strona: Strona) => void;
}

export default function Composer({
  value,
  placeholder,
  hint,
  sendLabel,
  disabled,
  strona,
  sideBuyingLabel,
  sideSellingLabel,
  onChange,
  onSend,
  onSetStrona,
}: Props) {
  const th = useTheme();
  const pusty = !value.trim();

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && !pusty) onSend();
    }
  }

  return (
    <div style={{ border: `1px solid ${th.line}`, borderRadius: 14, background: th.surface, boxShadow: th.shadow, overflow: 'hidden' }}>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={1}
        disabled={disabled}
        style={{
          width: '100%',
          border: 'none',
          outline: 'none',
          resize: 'none',
          background: 'transparent',
          color: th.ink,
          fontFamily: BODY,
          fontSize: 14.5,
          lineHeight: 1.6,
          padding: '15px 17px 6px',
          maxHeight: 140,
        }}
      />
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, padding: '8px 12px 11px 17px' }}>
        <span style={{ fontFamily: MONO, fontSize: 10.5, color: th.ink3, minWidth: 0 }}>{hint}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: '0 0 auto' }}>
          <StronaPrzelacznik
            strona={strona}
            sideBuyingLabel={sideBuyingLabel}
            sideSellingLabel={sideSellingLabel}
            onSetStrona={onSetStrona}
          />
          <button
            type="button"
            onClick={onSend}
            disabled={disabled || pusty}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '9px 14px',
              borderRadius: 8,
              border: 'none',
              background: AKCENT_SEGMENT,
              color: '#FFFFFF',
              fontFamily: BODY,
              fontSize: 12.5,
              fontWeight: 600,
              cursor: disabled || pusty ? 'default' : 'pointer',
              opacity: disabled || pusty ? 0.5 : 1,
            }}
          >
            {sendLabel}
            <IkonaWyslij color="#FFFFFF" />
          </button>
        </div>
      </div>
    </div>
  );
}

interface PrzelacznikProps {
  strona: Strona;
  sideBuyingLabel: string;
  sideSellingLabel: string;
  onSetStrona: (strona: Strona) => void;
}

function StronaPrzelacznik({ strona, sideBuyingLabel, sideSellingLabel, onSetStrona }: PrzelacznikProps) {
  const th = useTheme();
  const segmenty: Array<{ klucz: Strona; etykieta: string }> = [
    { klucz: 'kupujacy', etykieta: sideBuyingLabel },
    { klucz: 'sprzedajacy', etykieta: sideSellingLabel },
  ];
  const aktywnyIndeks = segmenty.findIndex((s) => s.klucz === strona);

  return (
    <div
      style={{
        position: 'relative',
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        padding: 3,
        borderRadius: 9,
        background: th.raised,
        border: `1px solid ${th.line}`,
      }}
    >
      <div
        aria-hidden
        style={{
          position: 'absolute',
          top: 3,
          bottom: 3,
          left: 3,
          width: 'calc((100% - 6px) / 2)',
          borderRadius: 6,
          background: AKCENT_SEGMENT,
          boxShadow: th.shadow,
          transform: `translateX(${aktywnyIndeks * 100}%)`,
          transition: 'transform 240ms cubic-bezier(0.4, 0, 0.2, 1), background 200ms ease',
        }}
      />
      {segmenty.map((s) => (
        <button
          key={s.klucz}
          type="button"
          onClick={() => onSetStrona(s.klucz)}
          style={segBtn(th, strona === s.klucz, strona === s.klucz)}
        >
          {s.etykieta}
        </button>
      ))}
    </div>
  );
}

function segBtn(th: ReturnType<typeof useTheme>, active: boolean, akcent: boolean): CSSProperties {
  return {
    position: 'relative',
    zIndex: 1,
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '6px 11px',
    border: 'none',
    background: 'transparent',
    borderRadius: 6,
    fontFamily: BODY,
    fontSize: 11.5,
    fontWeight: akcent ? 700 : 600,
    lineHeight: 1,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    color: akcent ? '#FFFFFF' : active ? th.ink : th.ink3,
    transition: 'color 200ms ease',
  };
}
