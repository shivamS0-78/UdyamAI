'use client';

import { createBrowserClient } from '@supabase/ssr';

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseAnonKey = process.env.SUPABASE_ANON_KEY;

export function isSupabaseConfigured(): boolean {
  return Boolean(supabaseUrl && supabaseAnonKey);
}

export function createClient() {
  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      'Supabase is not configured: set SUPABASE_URL and SUPABASE_ANON_KEY',
    );
  }
  return createBrowserClient(supabaseUrl, supabaseAnonKey);
}

let client: ReturnType<typeof createClient> | null = null;

/** Singleton browser Supabase client (session lives in cookies). */
export function getSupabaseClient() {
  if (!client) {
    client = createClient();
  }
  return client;
}
