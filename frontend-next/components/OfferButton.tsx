interface Props {
  tekst: string;
  onClick: (tekst: string) => void;
}

export default function OfferButton({ tekst, onClick }: Props) {
  return (
    <button
      type="button"
      onClick={() => onClick(tekst)}
      className="rounded border border-blue-300 bg-blue-50 px-3 py-2 text-sm text-blue-700 hover:bg-blue-100"
    >
      {tekst}
    </button>
  );
}
