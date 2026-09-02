import type { SseEvent } from './chat';

export async function* czytajSse(body: ReadableStream<Uint8Array>): AsyncGenerator<SseEvent> {
  const reader = body.getReader();
  const dekoder = new TextDecoder();
  let bufor = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      bufor += dekoder.decode(value, { stream: true });

      const czesci = bufor.split('\n\n');
      bufor = czesci.pop() ?? '';

      for (const czesc of czesci) {
        const linia = czesc.split('\n').find((l) => l.startsWith('data:'));
        if (!linia) continue;
        const json = linia.slice(5).trim();
        if (!json) continue;
        try {
          yield JSON.parse(json) as SseEvent;
        } catch {
          continue;
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
