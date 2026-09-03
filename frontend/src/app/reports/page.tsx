'use client';

import React from 'react';
import AppShell from '@/components/ui/AppShell';
import Link from 'next/link';
import { useLanguageStore } from '@/stores/languageStore';

export default function ReportsPage() {
  const t = useLanguageStore((s) => s.t);
  return (
    <AppShell>
      <main className="flex-1 flex flex-col items-center justify-center p-6 text-center">
        <div className="max-w-md w-full bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
          <h1 className="text-3xl font-bold text-slate-900 mb-3">{t('module.reportsTitle')}</h1>
          <p className="text-slate-600 mb-6">{t('module.reportsDesc')}</p>
          <div className="flex flex-col gap-3">
            <Link
              href="/dashboard"
              className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl transition"
            >
              {t('module.goDashboard')}
            </Link>
          </div>
        </div>
      </main>
    </AppShell>
  );
}
