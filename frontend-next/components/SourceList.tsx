interface Props {
  zrodla: string[];
  etykieta: string;
}

export default function SourceList({ zrodla, etykieta }: Props) {
  if (zrodla.length === 0) return null;
  return (
    <div className="mt-2 text-sm">
      <p className="text-gray-500">{etykieta}</p>
      <ul className="list-inside list-disc">
        {zrodla.map((url) => (
          <li key={url}>
            <a href={url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
              {url}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
