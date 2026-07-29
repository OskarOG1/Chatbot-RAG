import { useTheme } from '@/lib/theme';

interface Props {
  tekst: string | null;
}

export default function Toast({ tekst }: Props) {
  const th = useTheme();
  if (!tekst) return null;

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 24,
        left: '50%',
        transform: 'translateX(-50%)',
        background: th.toastBg,
        color: 'white',
        padding: '11px 20px',
        borderRadius: 10,
        fontSize: 13,
        fontWeight: 600,
        animation: 'dcFadeUp 0.25s ease both',
        boxShadow: '0 8px 24px oklch(0 0 0 / 0.25)',
      }}
    >
      {tekst}
    </div>
  );
}
