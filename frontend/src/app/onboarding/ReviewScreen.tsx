'use client';

import { ArrowRight, MapPin, Store, Wallet, Globe } from 'lucide-react';
import { useLanguageStore } from '@/stores/languageStore';
import Card from '@/components/ui/Card';

interface ReviewScreenProps {
  stateName?: string;
  district: string;
  taluka: string;
  village: string;
  business: string;
  capital: string;
  desiredProjectCost: string;
  language: string;
  error?: string;
  onEdit: () => void;
  onStartAnalysis: () => void;
}

export default function ReviewScreen({
  stateName,
  district,
  taluka,
  village,
  business,
  capital,
  desiredProjectCost,
  language,
  error,
  onEdit,
  onStartAnalysis,
}: ReviewScreenProps) {
  const t = useLanguageStore((s) => s.t);
  const languageName = t(`lang.${language}`);

  return (
    <section className="min-h-screen py-10 px-4 sm:px-6">
      <div className="mx-auto max-w-3xl">
        <Card padding="xl" className="border-slate-200/80 dark:border-[#2B313C] shadow-2xl">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 dark:bg-blue-950/40 text-primary border border-blue-200 dark:border-blue-800 text-xs font-bold uppercase tracking-wider mb-2">
            {t('onboard.reviewEyebrow')}
          </span>
          <h3 className="text-2xl sm:text-3xl font-black text-foreground tracking-tight">{t('onboard.reviewTitle')}</h3>
          <p className="mt-1 text-xs sm:text-sm text-foreground-muted">{t('onboard.reviewDesc')}</p>

          <div className="mt-7 space-y-4">
            <div className="rounded-2xl border border-slate-200 dark:border-[#2B313C] bg-slate-50/60 dark:bg-[#1C2128] p-5">
              <div className="flex items-start gap-4">
                <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
                  <MapPin className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-foreground-muted">{t('onboard.reviewLocation')}</p>
                  <p className="mt-1 text-sm sm:text-base font-bold text-foreground">
                    {stateName ? `${stateName} → ` : ''}{district} → {taluka} → {village}
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 dark:border-[#2B313C] bg-slate-50/60 dark:bg-[#1C2128] p-5">
              <div className="flex items-start gap-4">
                <div className="h-10 w-10 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-400 flex items-center justify-center shrink-0">
                  <Store className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-foreground-muted">{t('onboard.reviewBusiness')}</p>
                  <p className="mt-1 text-sm sm:text-base font-bold text-foreground">{business}</p>
                </div>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 dark:border-[#2B313C] bg-slate-50/60 dark:bg-[#1C2128] p-5">
                <div className="flex items-start gap-4">
                  <div className="h-10 w-10 rounded-xl bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-400 flex items-center justify-center shrink-0">
                    <Wallet className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-foreground-muted">{t('onboard.reviewCapital')}</p>
                    <p className="mt-1 text-base sm:text-lg font-financial font-extrabold text-foreground">
                      ₹{Number(capital).toLocaleString('en-IN')}
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 dark:border-[#2B313C] bg-slate-50/60 dark:bg-[#1C2128] p-5">
                <div className="flex items-start gap-4">
                  <div className="h-10 w-10 rounded-xl bg-blue-50 dark:bg-blue-950/40 text-primary flex items-center justify-center shrink-0">
                    <Wallet className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-foreground-muted">{t('onboard.reviewCost')}</p>
                    <p className="mt-1 text-base sm:text-lg font-financial font-extrabold text-primary dark:text-[#34D399]">
                      ₹{Number(desiredProjectCost).toLocaleString('en-IN')}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 dark:border-[#2B313C] bg-slate-50/60 dark:bg-[#1C2128] p-5">
              <div className="flex items-start gap-4">
                <div className="h-10 w-10 rounded-xl bg-slate-100 dark:bg-[#252C37] text-foreground flex items-center justify-center shrink-0">
                  <Globe className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-foreground-muted">{t('lang.label')}</p>
                  <p className="mt-1 text-sm sm:text-base font-bold text-foreground">{languageName}</p>
                </div>
              </div>
            </div>
          </div>

          {error && (
            <div className="mt-5 rounded-2xl border border-rose-200 dark:border-rose-800 bg-rose-50 dark:bg-rose-950/40 p-4 text-xs sm:text-sm text-rose-700 dark:text-rose-400 font-semibold">
              <p className="font-bold">{t('onboard.unableStart')}</p>
              <p className="mt-1">{error}</p>
            </div>
          )}

          <div className="mt-8 flex flex-wrap gap-4">
            <button
              type="button"
              onClick={onEdit}
              className="rounded-full border border-slate-200 dark:border-[#2B313C] bg-white dark:bg-[#1C2128] px-7 py-3.5 text-sm font-bold text-foreground hover:bg-slate-50 dark:hover:bg-[#252C37] transition shadow-sm"
            >
              {t('onboard.edit')}
            </button>
            <button
              type="button"
              onClick={onStartAnalysis}
              className="inline-flex items-center gap-2 rounded-full bg-primary px-8 py-3.5 text-sm font-bold text-white shadow-fintech-btn hover:bg-primary-600 transition-all hover:-translate-y-0.5"
            >
              {t('onboard.start')}
              <ArrowRight size={18} />
            </button>
          </div>
        </Card>
      </div>
    </section>
  );
}
