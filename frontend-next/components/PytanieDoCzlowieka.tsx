import { useState } from 'react';
import { useTheme, BODY } from '@/lib/theme';
import { TEKSTY, type Lang } from '@/lib/chat';

const EMAIL_WZORZEC = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export type WynikZgloszenia = 'ok' | 'konflikt' | 'limit' | 'blad';

interface Props {
  lang: Lang;
  numer?: string | null;
  onZglos: (email: string) => Promise<WynikZgloszenia>;
}

export default function PytanieDoCzlowieka({ lang, numer = null, onZglos }: Props) {
  const th = useTheme();
  const t = TEKSTY[lang];
  const [rozwiniete, setRozwiniete] = useState(false);
  const [email, setEmail] = useState('');
  const [wysylka, setWysylka] = useState(false);
  const [blad, setBlad] = useState<Exclude<WynikZgloszenia, 'ok'> | null>(null);

  if (numer) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 2 }}>
        <span style={{ fontFamily: BODY, fontSize: 13, fontWeight: 600, color: th.ink }}>
          {t.zgloszeniePotwierdzenie(numer)}
        </span>
        <span style={{ fontFamily: BODY, fontSize: 11.5, color: th.ink3 }}>
          {t.zgloszeniePrzechowywanieNota}
        </span>
      </div>
    );
  }

  const emailOk = EMAIL_WZORZEC.test(email.trim());

  async function wyslij() {
    if (!emailOk || wysylka) return;
    setWysylka(true);
    setBlad(null);
    const wynik = await onZglos(email.trim());
    setWysylka(false);
    if (wynik !== 'ok') {
      setBlad(wynik);
    }
  }

  if (!rozwiniete) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 9, marginTop: 2 }}>
        <span style={{ fontFamily: BODY, fontSize: 13, color: th.ink3 }}>{t.zgloszenieZacheta}</span>
        <div style={{ display: 'flex' }}>
          <button type="button" onClick={() => setRozwiniete(true)} style={przyciskGlowny(th)}>
            {t.zgloszeniePrzycisk}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 9, marginTop: 2 }}>
      <span style={{ fontFamily: BODY, fontSize: 13, color: th.ink3 }}>{t.zgloszenieZacheta}</span>
      <label style={{ fontFamily: BODY, fontSize: 11.5, fontWeight: 700, color: th.ink3, letterSpacing: '0.03em', textTransform: 'uppercase' }}>
        {t.zgloszenieEmailLabel}
      </label>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          type="email"
          value={email}
          placeholder={t.emailPlaceholder}
          onChange={(e) => setEmail(e.target.value)}
          style={{
            flex: '1 1 220px',
            border: `1px solid ${th.line}`,
            background: th.surface,
            color: th.ink,
            borderRadius: 9,
            padding: '10px 12px',
            fontFamily: BODY,
            fontSize: 13.5,
            outline: 'none',
          }}
        />
        <button
          type="button"
          onClick={wyslij}
          disabled={!emailOk || wysylka}
          style={przyciskGlowny(th, !emailOk || wysylka)}
        >
          {wysylka ? t.sending : t.zgloszeniePrzycisk}
        </button>
      </div>
      {blad && (
        <span style={{ fontFamily: BODY, fontSize: 12, color: th.accentInk }}>
          {blad === 'konflikt' ? t.zgloszenieBlad409 : blad === 'limit' ? t.zgloszenieBlad429 : t.zgloszenieBladOgolny}
        </span>
      )}
    </div>
  );
}

function przyciskGlowny(th: ReturnType<typeof useTheme>, disabled = false) {
  return {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 9,
    padding: '11px 17px',
    borderRadius: 9,
    border: 'none',
    background: disabled ? th.accentSoft : th.accent,
    color: disabled ? th.accentInk : '#FFFFFF',
    fontFamily: BODY,
    fontSize: 13,
    fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer',
    boxShadow: disabled ? 'none' : th.shadow,
  };
}
