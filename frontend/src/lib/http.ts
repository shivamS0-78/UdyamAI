// Shared HTTP helpers for talking to the UdyamAI backend.
//
// The Supabase access token is kept in memory (not localStorage) and is
// refreshed by AuthProvider whenever the session changes, so browser-side
// API calls can attach it synchronously.

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

/**
 * fetch() wrapper that adds the Authorization header for the current
 * Supabase session when one exists. Keeps the rest of the signature
 * identical to the native fetch so it can be swapped in transparently.
 */
export async function apiFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  const headers = new Headers(init?.headers);
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }
  return fetch(input, { ...init, headers });
}
