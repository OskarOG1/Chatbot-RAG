interface Props {
  tekst: string;
}

export default function InfoBanner({ tekst }: Props) {
  return (
    <div className="rounded border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-800">
      {tekst}
    </div>
  );
}
