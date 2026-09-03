'use client';

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { Loader2 } from 'lucide-react';

import { clearAuthStorage, storeProfile, storeUserPhone } from '@/lib/auth';
import { apiFetch, setAccessToken } from '@/lib/http';
import { getSupabaseClient } from '@/lib/supabase/client';

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000'
).replace(/\/+$/, '');

export interface AuthUser {
  id: string;
  phone?: string | null;
  email?: string | null;
}

export interface AuthProfile {
  id: string;
  name?: string | null;
  phone?: string | null;
  email?: string | null;
  business_name?: string | null;
  preferred_language?: string | null;
}

interface AuthContextValue {
  user: AuthUser | null;
  profile: AuthProfile | null;
  loading: boolean;
  refreshProfile: () => Promise<AuthProfile | null>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  profile: null,
  loading: true,
  refreshProfile: async () => null,
  signOut: async () => undefined,
});

export function useAuth() {
  return useContext(AuthContext);
}

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [profile, setProfile] = useState<AuthProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshProfile = useCallback(async (): Promise<AuthProfile | null> => {
    try {
      const res = await apiFetch(`${API_BASE_URL}/api/v1/auth/me`, {
        headers: { Accept: 'application/json' },
      });
      if (!res.ok) return null;
      const data = await res.json();
      const authUser: AuthUser | null = data.user
        ? {
            id: data.user.id,
            phone: data.user.phone,
            email: data.user.email,
          }
        : null;
      const appProfile: AuthProfile | null = data.profile ? data.profile : null;

      setUser(authUser);
      setProfile(appProfile);
      if (authUser) storeUserPhone(authUser.phone);
      storeProfile(appProfile);
      return appProfile;
    } catch {
      // Backend may be offline; keep whatever session info we have.
      return null;
    }
  }, []);

  useEffect(() => {
    let active = true;

    async function init() {
      let supabase;
      try {
        supabase = getSupabaseClient();
      } catch {
        setLoading(false);
        return;
      }

      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!active) return;
      if (session?.access_token) {
        setAccessToken(session.access_token);
      }

      // getUser() refreshes an expired session when one is present and
      // resolves to null when the user is signed out.
      const {
        data: { user: supabaseUser },
      } = await supabase.auth.getUser();

      if (!active) return;

      if (supabaseUser) {
        const authUser: AuthUser = {
          id: supabaseUser.id,
          phone: supabaseUser.phone ?? null,
          email: supabaseUser.email ?? null,
        };
        setUser(authUser);
        storeUserPhone(authUser.phone);
        setLoading(false);
        void refreshProfile();
      } else {
        setAccessToken(null);
        clearAuthStorage();
        setProfile(null);
        setLoading(false);
      }

      const {
        data: { subscription },
      } = supabase.auth.onAuthStateChange((event, nextSession) => {
        if (!active) return;
        if (nextSession?.access_token) {
          setAccessToken(nextSession.access_token);
          setUser({
            id: nextSession.user.id,
            phone: nextSession.user.phone ?? null,
            email: nextSession.user.email ?? null,
          });
          storeUserPhone(nextSession.user.phone ?? null);
          if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED' || event === 'USER_UPDATED') {
            void refreshProfile();
          }
        } else if (event === 'SIGNED_OUT') {
          setAccessToken(null);
          clearAuthStorage();
          setUser(null);
          setProfile(null);
          setLoading(false);
        }
      });

      return () => {
        active = false;
        subscription.unsubscribe();
      };
    }

    void init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const signOut = useCallback(async () => {
    try {
      const supabase = getSupabaseClient();
      await supabase.auth.signOut();
    } catch {
      // ignore sign-out network failures; clear locally regardless
    }
    setAccessToken(null);
    clearAuthStorage();
    setUser(null);
    setProfile(null);
  }, []);

  const value = useMemo(
    () => ({ user, profile, loading, refreshProfile, signOut }),
    [user, profile, loading, refreshProfile, signOut],
  );

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" aria-label="Loading" />
      </div>
    );
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
