'use client';

import { useLanguageStore } from '@/stores/languageStore';

export default function WhatYouNeed() {
  const t = useLanguageStore((s) => s.t);

  return (
    <section className="border-t bg-white">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <h3 className="text-2xl font-bold">{t('onboard.needTitle')}</h3>
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border p-5">
            <p className="font-semibold">{t('onboard.needLocation')}</p>
            <p className="mt-2 text-sm text-slate-500">{t('onboard.needLocationDesc')}</p>
          </div>
          <div className="rounded-xl border p-5">
            <p className="font-semibold">{t('onboard.needBusiness')}</p>
            <p className="mt-2 text-sm text-slate-500">{t('onboard.needBusinessDesc')}</p>
          </div>
          <div className="rounded-xl border p-5">
            <p className="font-semibold">{t('onboard.needCapital')}</p>
            <p className="mt-2 text-sm text-slate-500">{t('onboard.needCapitalDesc')}</p>
          </div>
        </div>
      </div>
    </section>
  );
}
