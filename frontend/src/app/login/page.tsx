'use client';

import LoginForm from '@/components/auth/LoginForm';
import LanguageSwitcher from '@/components/ui/LanguageSwitcher';
import { useLanguageStore } from '@/stores/languageStore';

export default function LoginPage() {
  const t = useLanguageStore((s) => s.t);

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-br from-blue-50 via-white to-blue-100 px-6">
      <div className="pointer-events-none absolute -left-32 -top-32 h-72 w-72 rounded-full bg-blue-200/40 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-32 -right-32 h-80 w-80 rounded-full bg-blue-300/30 blur-3xl" />
      <div className="absolute right-6 top-6">
        <LanguageSwitcher />
      </div>
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-slate-900">UdyamAI</h1>
          <p className="mt-2 text-sm text-slate-500">{t('login.tagline')}</p>
        </div>
        <LoginForm />
      </div>
    </main>
  );
}
