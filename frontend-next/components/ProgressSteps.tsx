interface Props {
  kroki: string[];
  etykieta: string;
}

export default function ProgressSteps({ kroki, etykieta }: Props) {
  if (kroki.length === 0) return null;
  return (
    <div className="rounded border border-gray-200 bg-gray-50 p-3 text-sm text-gray-600">
      <p className="mb-1 font-medium">{etykieta}</p>
      <ul className="space-y-1">
        {kroki.map((krok, i) => (
          <li key={i}>{krok}</li>
        ))}
      </ul>
    </div>
  );
}
