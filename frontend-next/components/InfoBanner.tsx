import { useTheme } from '@/lib/theme';

interface Props {
  tekst: string;
}

export default function InfoBanner({ tekst }: Props) {
  const th = useTheme();

  return (
    <div
      style={{
        border: `1px solid ${th.accentSoftHover}`,
        background: th.accentSoft,
        color: th.accentText,
        padding: '8px 12px',
        borderRadius: 10,
        fontSize: 13,
      }}
    >
      {tekst}
    </div>
  );
}
