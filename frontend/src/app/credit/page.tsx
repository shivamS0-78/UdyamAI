'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/ui/AppShell';
import { getCreditScore, createCreditScore } from '@/lib/api';
import { Shield, TrendingUp, TrendingDown, Minus, Plus, Loader2, X, AlertCircle } from 'lucide-react';

export default function CreditPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ score: '', provider: 'estimated', notes: '' });
  const [submitting, setSubmitting] = useState(false);
  const profileId = typeof window !== 'undefined' ? localStorage.getItem('udyam_profile_id') || '00000000-0000-0000-0000-000000000001' : '00000000-0000-0000-0000-000000000001';

  async function loadData() { try { setLoading(true); setData(await getCreditScore(profileId)); } catch (err) { console.warn(err); } finally { setLoading(false); } }
  useEffect(() => { loadData(); }, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!form.score) return;
    setSubmitting(true);
    try {
      await createCreditScore(profileId, { score: parseInt(form.score), provider: form.provider, suggestions: form.notes || undefined });
      setForm({ score: '', provider: 'estimated', notes: '' });
      setShowAdd(false); loadData();
    } catch (err) { console.error(err); }
    finally { setSubmitting(false); }
  }

  function getScoreColor(score: number) {
    if (score >= 800) return 'from-emerald-400 to-emerald-600';
    if (score >= 700) return 'from-blue-400 to-blue-600';
    if (score >= 600) return 'from-amber-400 to-amber-600';
    if (score >= 500) return 'from-orange-400 to-orange-600';
    return 'from-red-400 to-red-600';
  }

  function getRatingLabel(rating: string) {
    const labels: Record<string, string> = { excellent: 'Excellent', very_good: 'Very Good', good: 'Good', fair: 'Fair', poor: 'Poor', not_rated: 'Not Rated' };
    return labels[rating] || rating;
  }

  function getTrendIcon(trend: string) {
    if (trend === 'improving') return <TrendingUp className="h-5 w-5 text-emerald-500" />;
    if (trend === 'declining') return <TrendingDown className="h-5 w-5 text-red-500" />;
    return <Minus className="h-5 w-5 text-slate-400" />;
  }

  const defaultSuggestions = [
    'Pay all bills and EMIs on time consistently',
    'Keep credit utilization below 30% of your limit',
    'Maintain a healthy mix of secured and unsecured loans',
    'Avoid applying for multiple loans simultaneously',
    'Monitor your credit report regularly for errors',
    'Keep old credit accounts active to build credit history',
  ];

  return (
    <AppShell>
      <main className="flex-1 max-w-5xl mx-auto p-6 w-full flex flex-col gap-6">
        <div className="rounded-2xl bg-gradient-to-r from-cyan-950 via-sky-900 to-cyan-800 text-white p-8 shadow-xl">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-cyan-500/20 text-cyan-300 border border-cyan-400/30 rounded-full text-xs font-semibold mb-3"><Shield className="h-3.5 w-3.5" /> Business Credit</span>
          <h1 className="text-3xl font-extrabold tracking-tight">Business Credit Monitoring</h1>
          <p className="text-cyan-200 text-sm mt-2">Track your business credit score and get improvement suggestions.</p>
        </div>

        {/* Credit Score Display */}
        {data?.latest_score ? (
          <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm flex flex-col sm:flex-row items-center gap-8">
            <div className={`relative flex h-36 w-36 items-center justify-center rounded-full bg-gradient-to-br ${getScoreColor(data.latest_score.score)}`}>
              <div className="text-center">
                <p className="text-4xl font-extrabold text-white">{data.latest_score.score}</p>
                <p className="text-xs text-white/80 font-medium">/ 1000</p>
              </div>
            </div>
            <div className="flex-1 text-center sm:text-left">
              <div className="flex items-center gap-3 justify-center sm:justify-start">
                <h2 className="text-2xl font-bold text-slate-900">{getRatingLabel(data.rating)}</h2>
                {getTrendIcon(data.trend)}
                <span className={`text-sm font-semibold ${data.trend === 'improving' ? 'text-emerald-600' : data.trend === 'declining' ? 'text-red-600' : 'text-slate-500'}`}>{data.trend}</span>
              </div>
              <p className="text-sm text-slate-500 mt-1">Provider: {data.latest_score.provider} • Recorded: {new Date(data.latest_score.recorded_date).toLocaleDateString('en-IN')}</p>
              <div className="flex gap-2 mt-3 justify-center sm:justify-start flex-wrap">
                <span className="px-3 py-1 text-xs font-bold rounded-full bg-slate-100 text-slate-700">Score: {data.latest_score.score}</span>
                <span className="px-3 py-1 text-xs font-bold rounded-full bg-blue-100 text-blue-700">History: {data.history.length} records</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-slate-200 bg-white p-12 text-center">
            <Shield className="h-12 w-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 font-medium">No credit score recorded yet.</p>
            <p className="text-sm text-slate-400 mt-1">Add your first credit score to start monitoring.</p>
          </div>
        )}

        {/* Score History */}
        {data?.history?.length > 1 && (
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 mb-3">Score History</h3>
            <div className="flex items-end gap-3 overflow-x-auto pb-2">
              {data.history.slice(0, 12).reverse().map((s: any, i: number) => (
                <div key={i} className="flex flex-col items-center gap-1 min-w-[60px]">
                  <div className={`w-8 rounded-t bg-gradient-to-t ${getScoreColor(s.score)}`} style={{ height: `${Math.max(20, (s.score / 1000) * 100)}px` }} />
                  <span className="text-xs font-bold text-slate-700">{s.score}</span>
                  <span className="text-[10px] text-slate-400">{new Date(s.recorded_date).toLocaleDateString('en-IN', { month: 'short' })}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Improvement Suggestions */}
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-5">
          <h3 className="text-sm font-bold text-emerald-900 mb-2">💡 Tips to Improve Your Score</h3>
          <ul className="text-sm text-emerald-800 space-y-1">
            {(data?.suggestions?.length ? data.suggestions : defaultSuggestions).map((s: string, i: number) => (
              <li key={i}>• {s}</li>
            ))}
          </ul>
        </div>

        <div className="flex justify-end">
          <button onClick={() => setShowAdd(!showAdd)} className="inline-flex items-center gap-2 px-4 py-2.5 bg-cyan-600 text-white rounded-xl text-sm font-semibold hover:bg-cyan-700 transition"><Plus className="h-4 w-4" /> Record Score</button>
        </div>

        {showAdd && (
          <form onSubmit={handleAdd} className="rounded-xl border border-cyan-200 bg-cyan-50/50 p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between"><h3 className="font-bold text-slate-900">Record Credit Score</h3><button type="button" onClick={() => setShowAdd(false)} className="text-slate-400 hover:text-slate-600"><X className="h-5 w-5" /></button></div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Score (0-1000)</label><input type="number" value={form.score} onChange={e => setForm({ ...form, score: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" min={0} max={1000} required /></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Provider</label><select value={form.provider} onChange={e => setForm({ ...form, provider: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"><option value="estimated">Estimated</option><option value="cibil">CIBIL</option><option value="equifax">Equifax</option><option value="crif">CRIF</option><option value="experian">Experian</option></select></div>
            </div>
            <button type="submit" disabled={submitting} className="self-end px-5 py-2.5 bg-cyan-600 text-white rounded-xl text-sm font-semibold hover:bg-cyan-700 transition disabled:opacity-50">{submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save Score'}</button>
          </form>
        )}
      </main>
    </AppShell>
  );
}
