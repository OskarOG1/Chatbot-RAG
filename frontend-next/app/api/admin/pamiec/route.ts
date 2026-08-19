const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://127.0.0.1:8000';

export async function POST() {
  const upstream = await fetch(`${FASTAPI_URL}/admin/wyczysc-pamiec`, {
    method: 'POST',
    cache: 'no-store',
  });

  const body = await upstream.text();

  return new Response(body, {
    status: upstream.status,
    headers: {
      'content-type': 'application/json',
      'cache-control': 'no-store',
    },
  });
}
