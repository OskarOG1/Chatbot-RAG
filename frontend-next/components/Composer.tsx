'use client';

import { type CSSProperties, type KeyboardEvent } from 'react';
import { useTheme, BODY, MONO } from '@/lib/theme';
import { type Strona } from '@/lib/chat';
import { IkonaWyslij } from './Ikony';

interface Props {
  value: string;
  placeholder: string;
  hint: string;
  sendLabel: string;
  disabled: boolean;
  strona: Strona;
  sideAutoLabel: string;
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
  sideAutoLabel,
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
          <span style={{ fontFamily: MONO, fontSize: 10.5, color: th.ink3 }}>{hint}</span>
          <div style={{ display: 'flex', padding: 2, borderRadius: 8, background: th.raised, border: `1px solid ${th.line}` }}>
            <button type="button" onClick={() => onSetStrona('kupujacy')} style={segBtn(th, strona === 'kupujacy')}>
              {sideBuyingLabel}
            </button>
            <button type="button" onClick={() => onSetStrona('auto')} style={segBtn(th, strona === 'auto')}>
              {sideAutoLabel}
            </button>
            <button type="button" onClick={() => onSetStrona('sprzedajacy')} style={segBtn(th, strona === 'sprzedajacy')}>
              {sideSellingLabel}
            </button>
          </div>
        </div>
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
            background: th.accent,
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
  );
}

function segBtn(th: ReturnType<typeof useTheme>, active: boolean): CSSProperties {
  return {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '5px 9px',
    border: 'none',
    borderRadius: 6,
    fontFamily: MONO,
    fontSize: 10.5,
    fontWeight: 500,
    lineHeight: 1,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    background: active ? th.surface : 'transparent',
    color: active ? th.ink : th.ink3,
    boxShadow: active ? th.shadow : 'none',
  };
}
