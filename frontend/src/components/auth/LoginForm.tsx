'use client';

import { useState } from 'react';
import { Loader2, Lock, Mail } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useLanguageStore } from '@/stores/languageStore';
import { getSupabaseClient, isSupabaseConfigured } from '@/lib/supabase/client';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LENGTH = 6;

type Mode = 'signin' | 'signup';

export default function LoginForm() {
  const router = useRouter();
  const t = useLanguageStore((s) => s.t);

  const [mode, setMode] = useState<Mode>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const switchMode = (next: Mode) => {
    setMode(next);
    setError('');
    setInfo('');
  };

  const handleSubmit = async (e?: React.SyntheticEvent) => {
    e?.preventDefault();
    setError('');
    setInfo('');

    if (!EMAIL_PATTERN.test(email)) {
      setError(t('login.invalidEmail'));
      return;
    }
    if (password.length < MIN_PASSWORD_LENGTH) {
      setError(t('login.passwordShort'));
      return;
    }
    if (!isSupabaseConfigured()) {
      setError(t('login.notConfigured'));
      return;
    }

    setSubmitting(true);
    try {
      const supabase = getSupabaseClient();

      if (mode === 'signin') {
        const { error: signInError } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (signInError) {
          // "Invalid login credentials" etc. -> friendly localized message
          console.error('Sign-in failed:', signInError);
          setError(t('login.authFailed'));
          return;
        }
        // Session cookies are set by supabase-js; middleware will let us in.
        router.push('/setup');
      } else {
        const { data, error: signUpError } = await supabase.auth.signUp({
          email,
          password,
        });
        if (signUpError) throw signUpError;

        if (data.session) {
          // Email confirmations are off: session is ready immediately.
          router.push('/setup');
        } else {
          // Supabase sent a confirmation email; ask the user to confirm first.
          switchMode('signin');
          setInfo(t('login.confirmEmail'));
        }
      }
    } catch (err: any) {
      console.error('Authentication failed:', err);
      setError(err?.message || t('login.authFailed'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border bg-white p-8 shadow-sm"
    >
      <h2 className="text-2xl font-bold text-slate-900">
        {mode === 'signin' ? t('login.welcome') : t('login.createAccount')}
      </h2>
      <p className="mt-2 text-sm text-slate-500">{t('login.subtitle')}</p>

      <div className="mt-6 space-y-4">
        <div>
          <label htmlFor="email" className="mb-2 block text-sm font-medium text-slate-700">
            {t('login.email')}
          </label>
          <div className="relative">
            <Mail
              className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
              aria-hidden="true"
            />
            <input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value.trim());
                setError('');
              }}
              placeholder={t('login.placeholder')}
              className="w-full rounded-xl border border-slate-200 py-3 pl-10 pr-4 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>
        </div>

        <div>
          <label htmlFor="password" className="mb-2 block text-sm font-medium text-slate-700">
            {t('login.password')}
          </label>
          <div className="relative">
            <Lock
              className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
              aria-hidden="true"
            />
            <input
              id="password"
              type="password"
              autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setError('');
              }}
              placeholder={t('login.passwordPlaceholder')}
              className="w-full rounded-xl border border-slate-200 py-3 pl-10 pr-4 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>
        </div>

        {info && <p className="text-sm text-emerald-600">{info}</p>}
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-6 py-3 font-semibold text-white transition hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2 disabled:opacity-60"
      >
        {submitting ? (
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
        ) : mode === 'signin' ? (
          t('login.signIn')
        ) : (
          t('login.signUp')
        )}
      </button>

      <button
        type="button"
        onClick={() => switchMode(mode === 'signin' ? 'signup' : 'signin')}
        className="mt-4 w-full text-center text-sm font-medium text-slate-500 transition hover:text-slate-800"
      >
        {mode === 'signin' ? t('login.switchToSignUp') : t('login.switchToSignIn')}
      </button>

      <p className="mt-4 text-center text-xs text-slate-400">{t('login.authNote')}</p>
    </form>
  );
}
