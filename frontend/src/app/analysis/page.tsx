'use client';

import React from 'react';
import AppShell from '@/components/ui/AppShell';
import Link from 'next/link';
import { useTranslation } from '@/stores/languageStore';
import { BarChart3, ArrowRight, LayoutDashboard, Sparkles, Plus, TrendingUp, ShieldCheck } from 'lucide-react';

export default function AnalysisPage() {
  const { t } = useTranslation();

  return (
    <AppShell>
      <main className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col gap-8">
        {/* Banner */}
        <div className="relative overflow-hidden rounded-[28px] bg-gradient-to-br from-primary via-primary-600 to-[#0C4E36] p-8 sm:p-10 text-white shadow-fintech-card">
          <div className="absolute top-0 right-0 w-96 h-96 bg-white/10 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            <div className="max-w-2xl">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-white/15 backdrop-blur-md text-white border border-white/20 rounded-full text-xs font-semibold mb-4">
                <BarChart3 className="h-3.5 w-3.5 text-mint" /> AI Strategic Intelligence
              </span>
              <h1 className="text-3xl sm:text-4xl font-black tracking-tight leading-tight">{t('module.analysisTitle')}</h1>
              <p className="text-white/80 text-sm sm:text-base mt-2 font-normal">
                {t('module.analysisDesc')}
              </p>
            </div>
            <Link
              href="/onboarding"
              className="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-full bg-white text-primary font-bold text-sm shadow-fintech-btn hover:bg-neutral-50 transition-all active:scale-95 shrink-0 self-start sm:self-auto"
            >
              <Plus className="h-4 w-4" /> {t('module.startNew')}
            </Link>
          </div>
        </div>

        {/* Feature Hub */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-surface-dark rounded-3xl border border-border dark:border-border-dark p-8 shadow-subtle flex flex-col justify-between transition-colors">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-primary-50 dark:bg-primary/10 text-primary dark:text-emerald-400 flex items-center justify-center mb-6">
                <Sparkles className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-foreground dark:text-foreground-dark">Run New Business Viability Evaluation</h3>
              <p className="text-sm text-foreground-muted mt-2 leading-relaxed">
                Analyze local market demand, capital expenditure requirements, subsidy eligibility, and risk factors for any district across India.
              </p>
            </div>
            <div className="pt-6 mt-6 border-t border-border dark:border-border-dark">
              <Link
                href="/onboarding"
                className="inline-flex items-center justify-center gap-2 w-full py-3.5 px-6 rounded-full bg-primary text-white font-semibold text-sm hover:bg-primary-600 transition shadow-fintech-btn"
              >
                {t('module.startNew')} <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>

          <div className="bg-white dark:bg-surface-dark rounded-3xl border border-border dark:border-border-dark p-8 shadow-subtle flex flex-col justify-between transition-colors">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-primary-50 dark:bg-primary/10 text-primary dark:text-emerald-400 flex items-center justify-center mb-6">
                <LayoutDashboard className="h-6 w-6" />
              </div>
              <div className="flex items-center justify-between gap-2 flex-wrap mb-2">
                <h3 className="text-xl font-bold text-foreground dark:text-foreground-dark">Executive Dashboard & RAG Guidance</h3>
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30 shadow-xs">
                  <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" /> Verified by RAG
                </span>
              </div>
              <p className="text-sm text-foreground-muted mt-2 leading-relaxed">
                Review existing feasibility index scores, competitive spatial mandis, scheme matching, and AI recommendations.
              </p>
            </div>
            <div className="pt-6 mt-6 border-t border-border dark:border-border-dark">
              <Link
                href="/dashboard"
                className="inline-flex items-center justify-center gap-2 w-full py-3.5 px-6 rounded-full border border-border dark:border-border-dark text-foreground dark:text-foreground-dark font-semibold text-sm hover:bg-neutral-50 dark:hover:bg-surface-dark-elevated transition"
              >
                {t('module.goDashboard')} <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </main>
    </AppShell>
  );
}
