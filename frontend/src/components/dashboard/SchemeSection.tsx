'use client';

import React from 'react';
import { Award, CheckCircle2, Building2, ExternalLink, ShieldAlert, Landmark, Sparkles } from 'lucide-react';

interface SchemeSectionProps {
  data?: any;
}

function SummaryCard({
  label,
  value,
  subtitle,
  icon: Icon,
}: {
  label: string;
  value: string;
  subtitle: string;
  icon?: any;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-slate-500">{label}</p>
        {Icon && <Icon className="h-5 w-5 text-blue-600" />}
      </div>
      <h3 className="mt-2 text-2xl font-extrabold text-slate-900">{value}</h3>
      <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
    </div>
  );
}

function getEligibilityBadge(status: string) {
  const s = String(status || '').toLowerCase();
  if (s.includes('high') || s.includes('eligible') || s === 'potential_match') {
    return 'bg-emerald-100 text-emerald-800 border-emerald-300';
  }
  if (s.includes('partial') || s.includes('moderate')) {
    return 'bg-blue-100 text-blue-800 border-blue-300';
  }
  return 'bg-amber-100 text-amber-800 border-amber-300';
}

function formatCurrency(amount: number) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
}

export default function SchemeSection({ data }: SchemeSectionProps) {
  const matchedSchemes = data?.schemes || [];
  const aiAdvice = data?.ai_advice || {};
  const schemeAdviceList: string[] = aiAdvice.scheme_advice || [];

  const totalSchemes = matchedSchemes.length;
  const bestMatchName = matchedSchemes[0]?.scheme_name || matchedSchemes[0]?.name || 'No match yet';
  const totalSubsidyEst = matchedSchemes.reduce(
    (acc: number, s: any) => acc + (s.estimated_subsidy_amount || 0),
    0
  );

  return (
    <div className="flex flex-col gap-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <SummaryCard
          label="Matched Schemes"
          value={String(totalSchemes)}
          subtitle="Evaluated against eligibility rules"
          icon={Award}
        />

        <SummaryCard
          label="Top Matched Scheme"
          value={bestMatchName}
          subtitle="Highest subsidy potential"
          icon={Sparkles}
        />

        <SummaryCard
          label="Est. Subsidy Support"
          value={totalSubsidyEst > 0 ? formatCurrency(totalSubsidyEst) : (totalSchemes > 0 ? 'Calculation pending' : '—')}
          subtitle="Government financial support"
          icon={Landmark}
        />
      </div>

      {/* Main Scheme List */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-lg font-bold text-slate-900">
              Government Welfare & Capital Subsidy Schemes
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Verified eligibility against state & national enterprise guidelines
            </p>
          </div>
          <span className="text-xs font-semibold px-3 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full flex items-center gap-1">
            <CheckCircle2 className="h-3.5 w-3.5" /> Direct Govt. Support
          </span>
        </div>

        <div className="flex flex-col gap-4">
          {matchedSchemes.length === 0 && schemeAdviceList.length === 0 && (
            <p className="text-sm text-slate-600">
              No government schemes matched this analysis. Import scheme data and rerun the analysis pipeline.
            </p>
          )}

          {/* AI Scheme Guidance (when no schemes matched but AI has advice) */}
          {matchedSchemes.length === 0 && schemeAdviceList.length > 0 && (
            <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-5">
              <p className="text-xs font-bold uppercase tracking-wider text-blue-600 mb-2">
                AI Scheme Guidance
              </p>
              <ul className="space-y-1.5">
                {schemeAdviceList.map((advice: string, i: number) => (
                  <li key={i} className="text-sm text-blue-900 flex items-start gap-1.5">
                    <span className="text-blue-500 font-bold mt-0.5">•</span>
                    <span>{advice}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {matchedSchemes.map((s: any, idx: number) => {
            const title = s.scheme_name || s.name || s.title || 'Government Subsidy Scheme';
            const statusLabel = (s.match_status || 'ELIGIBLE').replace(/_/g, ' ').toUpperCase();
            const subsidy = s.estimated_subsidy_amount || 0;
            const loan = s.estimated_loan_amount || 0;

            return (
              <div
                key={s.scheme_id || idx}
                className="rounded-xl border border-slate-200 bg-slate-50/50 p-5 hover:bg-slate-50 hover:border-slate-300 transition shadow-2xs flex flex-col gap-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200/60 pb-3">
                  <div className="flex items-center gap-2">
                    <Building2 className="h-5 w-5 text-blue-600 shrink-0" />
                    <h4 className="font-bold text-slate-900 text-base">{title}</h4>
                  </div>
                  <span
                    className={`inline-flex items-center px-3 py-1 text-xs font-bold rounded-full border ${getEligibilityBadge(
                      s.match_status
                    )}`}
                  >
                    {statusLabel}
                  </span>
                </div>

                {s.description && (
                  <p className="text-sm text-slate-600 leading-relaxed">
                    {s.description}
                  </p>
                )}

                <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                  <div className="flex flex-wrap items-center gap-3">
                    {subsidy > 0 && (
                      <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 text-xs font-bold border border-emerald-200">
                        Capital Subsidy: {formatCurrency(subsidy)}
                      </span>
                    )}
                    {loan > 0 && (
                      <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-50 text-blue-800 text-xs font-bold border border-blue-200">
                        Loan Coverage: {formatCurrency(loan)}
                      </span>
                    )}
                    {s.agency_name && (
                      <span className="text-xs text-slate-500 font-medium">
                        Nodal Agency: <strong className="text-slate-700">{s.agency_name}</strong>
                      </span>
                    )}
                  </div>

                  {s.official_url && (
                    <a
                      href={s.official_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs font-bold text-blue-600 hover:text-blue-800 hover:underline transition"
                    >
                      Official Portal <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}