import { useTheme, DISPLAY, BODY } from '@/lib/theme';

interface Props {
  krok: string | null;
  thinking: string;
}

export default function TypingBubble({ krok, thinking }: Props) {
  const th = useTheme();

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <span
        style={{
          width: 22,
          height: 22,
          borderRadius: 6,
          background: th.accent,
          color: th.markInk,
          fontFamily: DISPLAY,
          fontSize: 14,
          fontWeight: 800,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          lineHeight: 1,
          flex: '0 0 auto',
        }}
      >
        a
      </span>
      <span style={{ fontFamily: BODY, fontSize: 12.5, color: th.ink3 }}>{krok ?? thinking}</span>
      <span style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
        <span style={dot(th.accent, '0s')} />
        <span style={dot(th.accent, '0.18s')} />
        <span style={dot(th.accent, '0.36s')} />
      </span>
    </div>
  );
}

function dot(color: string, delay: string) {
  return {
    width: 5,
    height: 5,
    borderRadius: '50%',
    background: color,
    display: 'inline-block',
    animation: `dcPulse 1.1s infinite ${delay}`,
  };
}
