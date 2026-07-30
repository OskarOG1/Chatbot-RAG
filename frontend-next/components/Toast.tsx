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
        color: th.toastInk,
        padding: '11px 20px',
        borderRadius: 10,
        fontSize: 13,
        fontWeight: 600,
        animation: 'dcFadeUp 0.25s ease both',
        boxShadow: th.shadowLift,
        zIndex: 50,
      }}
    >
      {tekst}
    </div>
  );
}
