import { useTheme } from '@/lib/theme';

interface Props {
  krok: string | null;
}

export default function TypingBubble({ krok }: Props) {
  const th = useTheme();

  return (
    <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
      <div
        style={{
          background: th.bgBubbleBot,
          border: `1px solid ${th.border}`,
          borderRadius: '16px 16px 16px 4px',
          padding: '14px 16px',
          display: 'flex',
          gap: 10,
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
          <span style={dotStyle(th.textSecondary, '0s')} />
          <span style={dotStyle(th.textSecondary, '0.15s')} />
          <span style={dotStyle(th.textSecondary, '0.3s')} />
        </div>
        {krok && <span style={{ fontSize: 13, color: th.textSecondary }}>{krok}</span>}
      </div>
    </div>
  );
}

function dotStyle(color: string, delay: string) {
  return {
    width: 6,
    height: 6,
    borderRadius: '50%',
    background: color,
    animation: `dcDot 1.2s infinite ${delay}`,
  };
}
