'use client';

import React, { useEffect, useState, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2, Sparkles, ArrowLeft, Download, FileText, CheckCircle2, Volume2, VolumeX } from 'lucide-react';
import AppShell from '@/components/ui/AppShell';
import DashboardNav, { DashboardSection } from '@/components/dashboard/DashboardNav';
import FinancialSection from '@/components/dashboard/FinancialSection';
import MarketSection from '@/components/dashboard/MarketSection';
import CompetitionSection from '@/components/dashboard/CompetitionSection';
import SchemeSection from '@/components/dashboard/SchemeSection';
import RiskSection from '@/components/dashboard/RiskSection';
import MapContainer from '@/components/maps/MapContainer';
import UserOverview from '@/components/dashboard/UserOverview';
import { getConsolidatedAnalysis, downloadAnalysisPdf, ConsolidatedAnalysisData } from '@/lib/api';
import { useTranslation } from '@/stores/languageStore';
import Card from '@/components/ui/Card';
import StatusBadge from '@/components/ui/StatusBadge';
import { useSpeech } from '@/hooks/useSpeech';

const VALID_SECTIONS: DashboardSection[] = [
  'overview',
  'financial',
  'market',
  'competition',
  'map',
  'schemes',
  'risks',
  'report',
];

function isDashboardSection(value: string | null): value is DashboardSection {
  return value != null && (VALID_SECTIONS as string[]).includes(value);
}

function isValidAnalysisData(obj: any): obj is ConsolidatedAnalysisData {
  return !!(
    obj &&
    typeof obj === 'object' &&
    (obj.feasibility || obj.analysis_id || obj.business)
  );
}

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [activeSection, setActiveSection] = useState<DashboardSection>('overview');
  const [data, setData] = useState<ConsolidatedAnalysisData | null>(null);
  const [resolvedAnalysisId, setResolvedAnalysisId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const { t } = useTranslation();
  const { isSpeaking, speakingId, toggleSpeak } = useSpeech();

  const analysisId = searchParams.get('analysis_id');

  useEffect(() => {
    const raw = searchParams.get('section');
    setActiveSection(isDashboardSection(raw) ? raw : 'overview');
  }, [analysisId, data?.analysis_id, searchParams]);

  useEffect(() => {
    async function loadAnalysis() {
      const targetId =
        analysisId ||
        (typeof window !== 'undefined' ? localStorage.getItem('udyam_active_analysis_id') : null);

      if (!targetId) {
        // Try fallback to last cached analysis if available
        if (typeof window !== 'undefined') {
          const lastSaved = localStorage.getItem('udyam_latest_cached_analysis');
          if (lastSaved) {
            try {
              const parsed = JSON.parse(lastSaved);
              if (isValidAnalysisData(parsed)) {
                setData(parsed);
                setResolvedAnalysisId(parsed.analysis_id || null);
              }
            } catch (e) {
              console.warn('Could not parse cached analysis:', e);
            }
          }
        }
        setLoading(false);
        return;
      }

      setResolvedAnalysisId(targetId);

      try {
        setLoading(true);
        const res = await getConsolidatedAnalysis(targetId);
        if (isValidAnalysisData(res)) {
          setData(res);
          if (typeof window !== 'undefined') {
            localStorage.setItem(`udyam_cached_analysis_${targetId}`, JSON.stringify(res));
            localStorage.setItem('udyam_latest_cached_analysis', JSON.stringify(res));
            localStorage.setItem('udyam_active_analysis_id', targetId);
          }
        }
      } catch (err) {
        console.warn('Failed to fetch fresh consolidated analysis, attempting offline cache fallback:', err);
        if (typeof window !== 'undefined') {
          const cached =
            localStorage.getItem(`udyam_cached_analysis_${targetId}`) ||
            localStorage.getItem('udyam_latest_cached_analysis');
          if (cached) {
            try {
              const parsed = JSON.parse(cached);
              if (isValidAnalysisData(parsed)) {
                setData(parsed);
              }
            } catch (e) {
              console.warn('Could not parse offline cached analysis:', e);
            }
          }
        }
      } finally {
        setLoading(false);
      }
    }
    loadAnalysis();
  }, [analysisId]);

  const feas = data?.feasibility || {};
  const overallScore = feas.overall_score != null ? Math.round(feas.overall_score) : null;
  const marketScore = feas.market_score != null ? Math.round(feas.market_score) : null;
  const financialScore = feas.financial_score != null ? Math.round(feas.financial_score) : null;
  const competitionScore = feas.competition_score != null ? Math.round(feas.competition_score) : null;
  const riskScore = feas.risk_score != null ? Math.round(feas.risk_score) : null;

  const riskLevelKey =
    riskScore == null ? 'unknown' : riskScore >= 70 ? 'low' : riskScore >= 40 ? 'medium' : 'high';
  const riskLevelLabel =
    riskLevelKey === 'unknown'
      ? t('dash.riskUnknown')
      : riskLevelKey === 'low'
        ? t('dash.riskLow')
        : riskLevelKey === 'medium'
          ? t('dash.riskMedium')
          : t('dash.riskHigh');
  const label =
    overallScore == null
      ? t('dash.awaiting')
      : overallScore >= 75
        ? t('dash.highly')
        : overallScore >= 50
          ? t('dash.moderately')
          : t('dash.highRisk');

  const locName = data?.location
    ? `${data.location.village_name || data.location.name || ''}${data.location.district_name ? `, ${data.location.district_name}` : ''}`.trim()
    : '';
  const bizName = data?.business?.category_name || '';

  const advisorSummary = data?.ai_advice?.summary || feas.recommendation || '';
  const advisorRecommendations =
    data?.ai_advice?.recommendations ||
    data?.ai_advice?.financial_advice ||
    (data?.ai_advice?.recommendation ? [data.ai_advice.recommendation] : []);

  const effectiveAnalysisId = analysisId || resolvedAnalysisId || data?.analysis_id;

  async function handleDownloadPdf() {
    if (!effectiveAnalysisId) return;
    try {
      setPdfLoading(true);
      setPdfError(null);
      await downloadAnalysisPdf(effectiveAnalysisId);
    } catch (err: any) {
      setPdfError(err?.message || 'Failed to download PDF report.');
    } finally {
      setPdfLoading(false);
    }
  }

  function getScoreStatus(score: number): 'verified' | 'warning' | 'risk' {
    if (score >= 75) return 'verified';
    if (score >= 50) return 'warning';
    return 'risk';
  }

  function ScoreCard({ label, score }: { label: string; score: number }) {
    return (
      <Card padding="md" className="border-border bg-white dark:bg-[#161B22] rounded-2xl flex flex-col justify-between shadow-subtle hover:border-primary/30 transition-all">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{label}</span>
        <div className="flex items-baseline justify-between mt-3">
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-extrabold font-financial text-foreground tracking-tight">
              {score}
            </span>
            <span className="text-xs font-medium text-muted-foreground">/ 100</span>
          </div>
          <StatusBadge status={getScoreStatus(score)} label={score >= 75 ? 'Strong' : score >= 50 ? 'Moderate' : 'Risk'} size="sm" />
        </div>
      </Card>
    );
  }

  if (loading) {
    return (
      <AppShell>
        <div className="flex flex-1 flex-col items-center justify-center p-12">
          <Loader2 className="h-10 w-10 animate-spin text-primary mb-4" />
          <p className="text-muted-foreground font-medium text-sm">{t('dash.loading')}</p>
        </div>
      </AppShell>
    );
  }

  if (!data) {
    return (
      <AppShell>
        <UserOverview />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <main className="p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto flex flex-col gap-6 w-full flex-1">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-border pb-5 gap-3">
          <div>
            <button
              type="button"
              onClick={() => router.push('/dashboard')}
              className="mb-3 inline-flex items-center gap-1.5 rounded-full bg-slate-100 dark:bg-[#1F242C] hover:bg-slate-200 dark:hover:bg-[#272D37] border border-slate-200 dark:border-[#2B313C] px-3.5 py-1 text-xs font-semibold text-foreground transition"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to Overview
            </button>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">{t('dash.title')}</h1>
            <p className="text-muted-foreground text-xs sm:text-sm mt-1 font-medium">
              {bizName || t('dash.pendingBiz')} •{' '}
              <span className="text-primary font-semibold">{locName || t('dash.pendingLoc')}</span>
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <Link
              href="/onboarding"
              className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 hover:bg-primary/20 border border-primary/20 px-3.5 py-1.5 text-xs font-semibold text-primary transition"
            >
              <Sparkles className="h-3.5 w-3.5" />
              Switch State / New Feasibility
            </Link>
            {effectiveAnalysisId && (
              <div className="text-xs font-mono font-medium bg-slate-100 dark:bg-[#1F242C] text-foreground-muted px-3.5 py-1.5 rounded-full border border-border">
                Run #{String(effectiveAnalysisId).slice(0, 8)}
              </div>
            )}
          </div>
        </div>

        <DashboardNav activeSection={activeSection} onSectionChange={setActiveSection} />

        {activeSection === 'overview' && (
          <div className="flex flex-col gap-6">
            {/* Overall feasibility banner */}
            <div className="relative overflow-hidden rounded-[24px] border border-border bg-white dark:bg-[#161B22] p-6 sm:p-8 shadow-subtle">
              <div className="absolute top-0 right-0 w-96 h-96 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
              <div className="relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">{t('dash.overall')}</span>
                  <div className="text-4xl sm:text-5xl font-extrabold font-financial text-foreground mt-2 tracking-tight">
                    {overallScore != null ? `${overallScore}/100` : (data?.ai_advice?.confidence ? `AI: ${data.ai_advice.confidence}` : '—')}
                  </div>
                  <span className="text-primary font-semibold text-sm sm:text-base block mt-2">{label}</span>
                </div>
                <div className="shrink-0">
                  <StatusBadge
                    status={riskLevelKey === 'low' ? 'verified' : riskLevelKey === 'medium' ? 'warning' : 'risk'}
                    label={`${riskLevelLabel} ${t('dash.riskProfile')}`}
                    size="lg"
                  />
                </div>
              </div>
            </div>

            {/* Score breakdown */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {marketScore != null && <ScoreCard label={t('dash.marketScore')} score={marketScore} />}
              {financialScore != null && <ScoreCard label={t('dash.financialScore')} score={financialScore} />}
              {competitionScore != null && <ScoreCard label={t('dash.competitionScore')} score={competitionScore} />}
              {riskScore != null && <ScoreCard label="Risk Profile Index" score={riskScore} />}
            </div>

            {/* Analysis Data Status */}
            {overallScore == null && (
              <div className="rounded-2xl border border-border bg-slate-50/70 dark:bg-[#1C2128]/70 p-5">
                <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3">Analysis Data Readiness</p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-semibold">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${data?.financial ? 'bg-primary' : 'bg-slate-300 dark:bg-slate-700'}`} />
                    <span className="text-foreground">Financial Model</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${data?.market ? 'bg-primary' : 'bg-slate-300 dark:bg-slate-700'}`} />
                    <span className="text-foreground">Market Demand</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${data?.competition ? 'bg-primary' : 'bg-slate-300 dark:bg-slate-700'}`} />
                    <span className="text-foreground">Competition Density</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${data?.ai_advice?.model_name && data.ai_advice.model_name !== 'unavailable' ? 'bg-primary' : 'bg-slate-300 dark:bg-slate-700'}`} />
                    <span className="text-foreground">AI Intelligence</span>
                  </div>
                </div>
              </div>
            )}

            {/* AI Advisor Strategic Summary */}
            {advisorSummary && (
              <Card padding="lg" className="border-border bg-white dark:bg-[#161B22] rounded-[24px] shadow-subtle">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-primary" />
                    <h3 className="text-base font-bold text-foreground">{t('dash.aiAdvisor')}</h3>
                  </div>

                  {/* Read Aloud Button */}
                  <button
                    type="button"
                    onClick={() => {
                      const fullAdviceText = `${advisorSummary}. Next steps: ${advisorRecommendations.join('. ')}`;
                      toggleSpeak(fullAdviceText, 'dashboard-advice');
                    }}
                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold transition ${
                      isSpeaking && speakingId === 'dashboard-advice'
                        ? 'bg-primary text-white animate-pulse'
                        : 'bg-slate-100 dark:bg-slate-800 text-foreground hover:bg-slate-200 dark:hover:bg-slate-700'
                    }`}
                    title={isSpeaking && speakingId === 'dashboard-advice' ? 'Stop audio' : 'Listen to AI summary'}
                  >
                    {isSpeaking && speakingId === 'dashboard-advice' ? (
                      <>
                        <VolumeX className="h-3.5 w-3.5 text-white" />
                        <span>Stop Audio</span>
                      </>
                    ) : (
                      <>
                        <Volume2 className="h-3.5 w-3.5 text-primary" />
                        <span>Read Aloud</span>
                      </>
                    )}
                  </button>
                </div>
                <p className="text-foreground-muted text-sm leading-relaxed whitespace-pre-line">{advisorSummary}</p>
              </Card>
            )}

            {/* Recommendations / Next Steps */}
            {advisorRecommendations.length > 0 && (
              <Card padding="lg" className="border-border bg-white dark:bg-[#161B22] rounded-[24px] shadow-subtle">
                <h3 className="text-base font-bold text-foreground mb-4">{t('dash.nextSteps')}</h3>
                <ul className="space-y-3">
                  {advisorRecommendations.map((rec: string, i: number) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-foreground-muted">
                      <CheckCircle2 className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            )}
          </div>
        )}

        {activeSection === 'financial' && <FinancialSection data={data} />}
        {activeSection === 'market' && <MarketSection data={data} />}
        {activeSection === 'competition' && <CompetitionSection data={data} />}
        {activeSection === 'map' && (
          <MapContainer title={t('dash.mapTitle')} data={data} />
        )}
        {activeSection === 'schemes' && <SchemeSection data={data} />}
        {activeSection === 'risks' && <RiskSection data={data} />}
        {activeSection === 'report' && (
          <div className="rounded-[28px] border border-border bg-white dark:bg-[#161B22] p-8 sm:p-12 text-center shadow-subtle">
            <div className="h-16 w-16 rounded-2xl bg-primary/10 text-primary border border-primary/20 mx-auto flex items-center justify-center mb-5">
              <FileText className="h-8 w-8" />
            </div>
            <h3 className="text-2xl font-extrabold text-foreground mb-2">{t('dash.pdfTitle')}</h3>
            <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto leading-relaxed">{t('dash.pdfDesc')}</p>
            {pdfError && (
              <p className="text-xs font-semibold text-rose-600 dark:text-rose-400 mb-4">{pdfError}</p>
            )}
            <button
              onClick={handleDownloadPdf}
              disabled={!effectiveAnalysisId || pdfLoading}
              className="px-8 py-3.5 bg-primary text-white rounded-full text-sm font-semibold shadow-fintech-btn hover:bg-primary-600 transition disabled:opacity-60 disabled:cursor-not-allowed inline-flex items-center gap-2"
            >
              {pdfLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {t('dash.pdfDownloading')}
                </>
              ) : (
                <>
                  <Download className="h-4 w-4" />
                  {t('dash.pdfButton')}
                </>
              )}
            </button>
          </div>
        )}
      </main>
    </AppShell>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background flex items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>}>
      <DashboardContent />
    </Suspense>
  );
}