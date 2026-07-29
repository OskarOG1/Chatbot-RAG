import { useState, type KeyboardEvent } from 'react';
import { useTheme } from '@/lib/theme';

interface Props {
  placeholder: string;
  disabled: boolean;
  onSend: (tekst: string) => void;
}

export default function Composer({ placeholder, disabled, onSend }: Props) {
  const th = useTheme();
  const [wartosc, setWartosc] = useState('');

  function wyslijJesliMozna() {
    const tekst = wartosc.trim();
    if (!tekst || disabled) return;
    onSend(tekst);
    setWartosc('');
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      wyslijJesliMozna();
    }
  }

  return (
    <div
      style={{
        width: '100%',
        maxWidth: 680,
        display: 'flex',
        gap: 10,
        alignItems: 'flex-end',
        background: th.bgSurface,
        border: `1px solid ${th.border}`,
        borderRadius: 16,
        padding: '10px 10px 10px 18px',
      }}
    >
      <textarea
        value={wartosc}
        onChange={(e) => setWartosc(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={1}
        disabled={disabled}
        style={{
          flex: '1 1 auto',
          border: 'none',
          outline: 'none',
          resize: 'none',
          fontFamily: 'inherit',
          fontSize: 14.5,
          lineHeight: 1.5,
          padding: '8px 0',
          maxHeight: 120,
          background: 'transparent',
          color: th.textPrimary,
        }}
      />
      <button
        type="button"
        onClick={wyslijJesliMozna}
        disabled={disabled || !wartosc.trim()}
        style={{
          flex: '0 0 auto',
          background: th.accent,
          color: 'white',
          border: 'none',
          borderRadius: 11,
          width: 42,
          height: 42,
          cursor: disabled || !wartosc.trim() ? 'default' : 'pointer',
          fontSize: 16,
          fontWeight: 700,
          opacity: disabled || !wartosc.trim() ? 0.5 : 1,
        }}
      >
        ↑
      </button>
    </div>
  );
}
