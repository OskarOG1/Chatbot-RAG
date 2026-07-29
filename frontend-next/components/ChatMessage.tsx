import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import EmailDraft from './EmailDraft';

interface Props {
  role: 'user' | 'assistant';
  content: string;
  tryb?: 'rag' | 'email';
}

export default function ChatMessage({ role, content, tryb = 'rag' }: Props) {
  const wyrownanie = role === 'user' ? 'items-end' : 'items-start';
  const tlo = role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-900';

  return (
    <div className={`flex flex-col ${wyrownanie}`}>
      <div className={`max-w-2xl rounded-lg px-4 py-2 ${tlo}`}>
        {role === 'assistant' && tryb === 'email' ? (
          <EmailDraft tresc={content} />
        ) : role === 'assistant' ? (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          </div>
        ) : (
          <p className="whitespace-pre-wrap">{content}</p>
        )}
      </div>
    </div>
  );
}
