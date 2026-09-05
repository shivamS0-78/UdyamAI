import { getSupabaseClient, isSupabaseConfigured } from './supabase/client';

// Shared HTTP helpers for talking to the UdyamAI backend.
//
// The Supabase access token is kept in memory and is
// refreshed by AuthProvider whenever the session changes. If the token
// has not been populated yet, apiFetch resolves it from the active session.

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
  let token = accessToken;
  if (!token && typeof window !== 'undefined' && isSupabaseConfigured()) {
    try {
      const supabase = getSupabaseClient();
      const { data } = await supabase.auth.getSession();
      token = data?.session?.access_token ?? null;
      if (token) {
        accessToken = token;
      }
    } catch {
      // ignore
    }
  }

  const headers = new Headers(init?.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return fetch(input, { ...init, headers });
}
