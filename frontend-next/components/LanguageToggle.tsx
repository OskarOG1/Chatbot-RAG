import type { Lang } from '@/lib/chat';

interface Props {
  lang: Lang;
  onChange: (lang: Lang) => void;
}

export default function LanguageToggle({ lang, onChange }: Props) {
  return (
    <select
      value={lang}
      onChange={(e) => onChange(e.target.value as Lang)}
      className="rounded border border-gray-300 bg-white px-2 py-1 text-sm text-gray-800"
    >
      <option value="pl">Polski</option>
      <option value="en">English</option>
    </select>
  );
}
