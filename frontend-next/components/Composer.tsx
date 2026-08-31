'use client';

import { useState, type CSSProperties, type KeyboardEvent } from 'react';
import { useTheme, BODY, MONO } from '@/lib/theme';
import { type Strona } from '@/lib/chat';
import { IkonaWyslij } from './Ikony';

const AKCENT_GRADIENT = 'linear-gradient(180deg, #FF6A1F 0%, #D94600 100%)';
const WYSOKOSC = 36;
const PROMIEN = 100;

interface Props {
  value: string;
  placeholder: string;
  hint: string;
  enterHint: string;
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
  enterHint,
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
  const nieaktywny = disabled || pusty;

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && !pusty) onSend();
    }
  }

  return (
    <div
      style={{
        border: `1px solid ${th.line}`,
        borderRadius: 16,
        background: th.surface,
        boxShadow: th.shadow,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          flexWrap: 'wrap',
          padding: '10px 14px',
          background: th.raised,
          borderBottom: `1px solid ${th.line}`,
        }}
      >
        <span
          style={{
            fontFamily: BODY,
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: '.07em',
            textTransform: 'uppercase',
            color: th.ink3,
          }}
        >
          {hint}
        </span>
        <StronaPrzelacznik
          strona={strona}
          sideBuyingLabel={sideBuyingLabel}
          sideSellingLabel={sideSellingLabel}
          onSetStrona={onSetStrona}
        />
      </div>

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
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          padding: '6px 12px 12px 17px',
        }}
      >
        <span style={{ fontFamily: MONO, fontSize: 10.5, color: th.ink3, minWidth: 0 }}>
          {enterHint}
        </span>
        <button
          type="button"
          className="dc-akcja"
          onClick={onSend}
          disabled={disabled || pusty}
          aria-label={sendLabel}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            height: WYSOKOSC,
            padding: '0 20px',
            borderRadius: PROMIEN,
            border: 'none',
            background: nieaktywny ? th.raised : AKCENT_GRADIENT,
            boxShadow: nieaktywny
              ? `inset 0 0 0 1px ${th.line}`
              : '0 1px 2px rgba(160, 50, 0, 0.30), 0 6px 16px -8px rgba(160, 50, 0, 0.55)',
            color: nieaktywny ? th.ink3 : '#FFFFFF',
            fontFamily: BODY,
            fontSize: 13,
            fontWeight: 700,
            letterSpacing: '.01em',
            lineHeight: 1,
            cursor: nieaktywny ? 'default' : 'pointer',
          }}
        >
          {sendLabel}
          <IkonaWyslij color={nieaktywny ? th.ink3 : '#FFFFFF'} />
        </button>
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
  const [hover, setHover] = useState<Strona | null>(null);
  const segmenty: Array<{ klucz: Strona; etykieta: string }> = [
    { klucz: 'kupujacy', etykieta: sideBuyingLabel },
    { klucz: 'sprzedajacy', etykieta: sideSellingLabel },
  ];
  const aktywnyIndeks = segmenty.findIndex((s) => s.klucz === strona);

  return (
    <div
      role="group"
      style={{
        position: 'relative',
        display: 'grid',
        gridTemplateColumns: 'repeat(2, minmax(104px, 1fr))',
        height: WYSOKOSC,
        boxSizing: 'border-box',
        padding: 3,
        borderRadius: PROMIEN,
        background: th.surface,
        border: `1px solid ${th.line}`,
        boxShadow: `inset 0 1px 2px ${th.lineSoft}`,
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
          borderRadius: PROMIEN,
          background: AKCENT_GRADIENT,
          boxShadow: '0 1px 2px rgba(160, 50, 0, 0.30)',
          transform: `translateX(${aktywnyIndeks * 100}%)`,
          transition: 'transform 240ms cubic-bezier(0.4, 0, 0.2, 1), background 200ms ease',
        }}
      />
      {segmenty.map((s) => (
        <button
          key={s.klucz}
          type="button"
          className="dc-segment"
          aria-pressed={strona === s.klucz}
          onClick={() => onSetStrona(s.klucz)}
          onMouseEnter={() => setHover(s.klucz)}
          onMouseLeave={() => setHover(null)}
          style={segBtn(th, strona === s.klucz, hover === s.klucz)}
        >
          {s.etykieta}
        </button>
      ))}
    </div>
  );
}

function segBtn(th: ReturnType<typeof useTheme>, akcent: boolean, hover: boolean): CSSProperties {
  return {
    position: 'relative',
    zIndex: 1,
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    padding: '0 14px',
    border: 'none',
    background: 'transparent',
    borderRadius: PROMIEN,
    fontFamily: BODY,
    fontSize: 12.5,
    fontWeight: akcent ? 700 : 600,
    lineHeight: 1,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    color: akcent ? '#FFFFFF' : hover ? th.ink : th.ink2,
  };
}
