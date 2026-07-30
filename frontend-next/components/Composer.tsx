'use client';

import { type KeyboardEvent } from 'react';
import { useTheme, BODY, MONO } from '@/lib/theme';

interface Props {
  value: string;
  placeholder: string;
  hint: string;
  sendLabel: string;
  disabled: boolean;
  onChange: (v: string) => void;
  onSend: () => void;
}

export default function Composer({ value, placeholder, hint, sendLabel, disabled, onChange, onSend }: Props) {
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
        <span style={{ fontFamily: MONO, fontSize: 10.5, color: th.ink3 }}>{hint}</span>
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
          <span style={{ fontFamily: MONO, fontSize: 12, opacity: 0.75 }}>↵</span>
        </button>
      </div>
    </div>
  );
}
