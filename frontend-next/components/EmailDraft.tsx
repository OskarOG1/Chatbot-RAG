interface Props {
  tresc: string;
}

export default function EmailDraft({ tresc }: Props) {
  return (
    <pre className="whitespace-pre-wrap rounded bg-gray-900 p-3 font-mono text-sm text-gray-100">
      {tresc}
    </pre>
  );
}
