import { useState, type FormEvent } from 'react';

interface Props {
  placeholder: string;
  wyslijEtykieta: string;
  disabled: boolean;
  onSend: (tekst: string) => void;
}

export default function Composer({ placeholder, wyslijEtykieta, disabled, onSend }: Props) {
  const [wartosc, setWartosc] = useState('');

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const tekst = wartosc.trim();
    if (!tekst || disabled) return;
    onSend(tekst);
    setWartosc('');
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={wartosc}
        onChange={(e) => setWartosc(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className="flex-1 rounded border border-gray-300 px-3 py-2 text-sm disabled:bg-gray-100"
      />
      <button
        type="submit"
        disabled={disabled || !wartosc.trim()}
        className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:bg-gray-300"
      >
        {wyslijEtykieta}
      </button>
    </form>
  );
}
