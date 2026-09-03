'use client';

import React from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  ShieldAlert,
  HelpCircle,
  Sparkles,
} from 'lucide-react';

interface RiskSectionProps {
  data?: any;
}

function getRiskLevelBadge(level: string) {
  const l = String(level || '').toLowerCase();
  if (l.includes('low')) {
    return 'bg-emerald-100 text-emerald-800 border-emerald-300';
  }
  if (l.includes('high') || l.includes('critical')) {
    return 'bg-red-100 text-red-800 border-red-300';
  }
  return 'bg-amber-100 text-amber-800 border-amber-300';
}

const DEFAULT_RISKS: never[] = [];

export default function RiskSection({ data }: RiskSectionProps) {
  const feas = data?.feasibility || {};
  const aiAdvice = data?.ai_advice || {};
  const riskScore = feas.risk_score != null ? Math.round(feas.risk_score) : null;
  const riskLevel =
    riskScore == null ? 'Not assessed' : riskScore >= 70 ? 'Low Risk' : riskScore >= 40 ? 'Medium Risk' : 'High Risk';

  const rawRisks = data?.risks || [];
  const riskList = Array.isArray(rawRisks) ? rawRisks : [];

  // AI-derived risk indicators when backend risk_score is missing
  const aiRisks: string[] = aiAdvice.risks || [];
  const aiWeaknesses: string[] = aiAdvice.weaknesses || [];
  const aiConfidence = aiAdvice.confidence || null;
  const aiModelName = aiAdvice.model_name || null;

  // Derive a risk level from AI data when feasibility score is missing
  const derivedRiskLevel =
    riskScore != null ? riskLevel
    : aiRisks.length > 3 ? 'High Risk'
    : aiRisks.length > 0 ? 'Medium Risk'
    : aiWeaknesses.length > 2 ? 'Medium Risk'
    : null;

  // Calculate mitigation coverage: only count risks that actually have mitigation text
  const risksWithMitigation = riskList.filter((r: any) => {
    const mitigation = r.mitigation || r.mitigation_strategy || r.action_plan;
    return mitigation && String(mitigation).trim().length > 0;
  });
  const mitigationCoverage = riskList.length > 0
    ? Math.round((risksWithMitigation.length / riskList.length) * 100)
    : 0;

  const swot = feas.swot || data?.ai_advice?.swot || {};
  const strengths = data?.ai_advice?.reasoning || swot.strengths || (swot as any).strength_indicators || [];
  const opportunities =
    data?.ai_advice?.opportunities || swot.opportunities || (swot as any).opportunity_indicators || [];
  const threats = data?.ai_advice?.threats || swot.threats || (swot as any).threat_indicators || [];

  return (
    <div className="flex flex-col gap-6">
      {/* Risk Profile Header & Score Summary */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-500">Risk Profile Index</span>
            <ShieldCheck className="h-5 w-5 text-emerald-600" />
          </div>
          <div className="mt-2 flex items-baseline gap-1">
            <span className="text-3xl font-extrabold text-slate-900">
              {riskScore ?? (aiRisks.length > 0 ? `~${Math.max(20, 60 - aiRisks.length * 5)}` : '—')}
            </span>
            {(riskScore != null || aiRisks.length > 0) && <span className="text-sm font-medium text-slate-400">/100</span>}
          </div>
          <p className="mt-1 text-xs text-slate-500">Higher score indicates lower operational risk</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-500">Risk Rating</span>
            <AlertTriangle className="h-5 w-5 text-amber-500" />
          </div>
          <h3 className="mt-2 text-2xl font-extrabold text-slate-900">
            {derivedRiskLevel || riskLevel}
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            {riskScore != null
              ? 'Evaluated against 12 risk metrics'
              : derivedRiskLevel
                ? `Derived from ${aiRisks.length} AI-identified risk factors`
                : 'Awaiting feasibility analysis'}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-500">Mitigation Coverage</span>
            <CheckCircle2 className="h-5 w-5 text-blue-600" />
          </div>
          <h3 className="mt-2 text-2xl font-extrabold text-slate-900">
            {riskList.length > 0 ? `${mitigationCoverage}% Covered` : 'Pending'}
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            {riskList.length > 0
              ? `${risksWithMitigation.length} of ${riskList.length} risks have mitigation plans`
              : 'Risk factors pending analysis'}
          </p>
        </div>
      </div>

      {/* SWOT Analysis Matrix */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-3">
          <Sparkles className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-bold text-slate-900">Enterprise SWOT Matrix</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Strengths */}
          <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-700" />
              <h4 className="font-bold text-emerald-900 text-sm">Key Strengths</h4>
            </div>
            <ul className="space-y-1.5 text-xs text-emerald-950">
              {strengths.map((item: string, i: number) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-emerald-600 font-bold">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Opportunities */}
          <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-blue-700" />
              <h4 className="font-bold text-blue-900 text-sm">Growth Opportunities</h4>
            </div>
            <ul className="space-y-1.5 text-xs text-blue-950">
              {opportunities.map((item: string, i: number) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-blue-600 font-bold">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Threats */}
          <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4 md:col-span-2">
            <div className="flex items-center gap-2 mb-2">
              <ShieldAlert className="h-4 w-4 text-amber-700" />
              <h4 className="font-bold text-amber-900 text-sm">External Threats & Vulnerabilities</h4>
            </div>
            <ul className="space-y-1.5 text-xs text-amber-950">
              {threats.map((item: string, i: number) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-amber-600 font-bold">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Actionable Risk Assessment & Mitigation Plan */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-amber-600" />
            <h3 className="text-lg font-bold text-slate-900">
              Risk Factors & Actionable Mitigation Plan
            </h3>
          </div>
          <span className="text-xs font-semibold px-3 py-1 bg-amber-50 text-amber-800 border border-amber-200 rounded-full">
            {riskList.length > 0 ? `${riskList.length} Risk Factors Identified` : aiRisks.length > 0 ? `${aiRisks.length} AI-Identified Risks` : '0 Risks Identified'}
          </span>
        </div>

        <div className="flex flex-col gap-4">
          {riskList.length === 0 && aiRisks.length === 0 && (
            <p className="text-sm text-slate-600">No risk factors were identified for this analysis run.</p>
          )}
          {riskList.map((r: any, idx: number) => {
            const factorName = r.risk_factor || r.factor || r.risk_type || `Operational Risk ${idx + 1}`;
            const category = r.category || 'Enterprise Risk';
            const level = r.level || 'Medium';
            const mitigation = r.mitigation || r.mitigation_strategy || r.action_plan || null;

            return (
              <div
                key={idx}
                className="rounded-xl border border-slate-200 bg-slate-50/50 p-5 hover:bg-slate-50 transition shadow-2xs flex flex-col gap-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200/60 pb-2.5">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4.5 w-4.5 text-amber-600 shrink-0" />
                    <h4 className="font-bold text-slate-900 text-sm sm:text-base">{factorName}</h4>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-slate-500 bg-white px-2.5 py-0.5 rounded border border-slate-200">
                      {category}
                    </span>
                    <span
                      className={`px-2.5 py-0.5 text-xs font-bold rounded-full border ${getRiskLevelBadge(
                        level
                      )}`}
                    >
                      {String(level).toUpperCase()}
                    </span>
                  </div>
                </div>

                <div className="bg-white rounded-lg border border-slate-200/80 p-3.5 mt-1">
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
                    Mitigation Strategy & Action Plan
                  </p>
                  {mitigation ? (
                    <p className="text-sm text-slate-700 leading-relaxed font-normal">
                      {mitigation}
                    </p>
                  ) : (
                    <p className="text-sm text-slate-400 italic">
                      Mitigation plan pending — review risk factors with financial advisor
                    </p>
                  )}
                </div>
              </div>
            );
          })}

          {/* AI-derived risk items when backend risk list is empty */}
          {riskList.length === 0 && aiRisks.length > 0 && aiRisks.map((riskText: string, idx: number) => {
            const isHighSeverity = idx < 2;
            const aiLevel = isHighSeverity ? 'Medium' : 'Low';
            return (
              <div
                key={`ai-risk-${idx}`}
                className="rounded-xl border border-blue-200 bg-blue-50/30 p-5 flex flex-col gap-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-blue-200/60 pb-2.5">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-blue-500 shrink-0" />
                    <h4 className="font-bold text-slate-900 text-sm sm:text-base">{riskText}</h4>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-blue-500 bg-white px-2.5 py-0.5 rounded border border-blue-200">
                      AI-Identified
                    </span>
                    <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full border ${getRiskLevelBadge(aiLevel)}`}>
                      {aiLevel.toUpperCase()}
                    </span>
                  </div>
                </div>
                <div className="bg-white rounded-lg border border-blue-100 p-3.5 mt-1">
                  <p className="text-xs font-bold uppercase tracking-wider text-blue-400 mb-1">
                    AI-Generated Mitigation Guidance
                  </p>
                  <p className="text-sm text-slate-500 italic">
                    Consult the matched scheme documents and financial plan to build a specific mitigation action.
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* AI Confidence Badge */}
        {aiConfidence && (
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2">
            <span className="text-xs font-medium text-slate-400">AI Confidence:</span>
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
              aiConfidence === 'high' ? 'bg-emerald-100 text-emerald-700'
              : aiConfidence === 'medium' ? 'bg-amber-100 text-amber-700'
              : 'bg-slate-100 text-slate-600'
            }`}>
              {aiConfidence.toUpperCase()}
            </span>
            {aiModelName && aiModelName !== 'unavailable' && (
              <span className="text-xs text-slate-400">via {aiModelName}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
