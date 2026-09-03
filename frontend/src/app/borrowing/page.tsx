'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/ui/AppShell';
import { getBorrowings, createBorrowing } from '@/lib/api';
import { Landmark, Plus, Loader2, X, Search, FileCheck, Clock, CheckCircle2, XCircle } from 'lucide-react';

export default function BorrowingPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ lender_name: '', loan_type: 'mudra', requested_amount: '', interest_rate: '', tenure_months: '', notes: '' });
  const [submitting, setSubmitting] = useState(false);
  const profileId = typeof window !== 'undefined' ? localStorage.getItem('udyam_profile_id') || '00000000-0000-0000-0000-000000000001' : '00000000-0000-0000-0000-000000000001';

  async function loadData() { try { setLoading(true); setData(await getBorrowings(profileId)); } catch (err) { console.warn(err); } finally { setLoading(false); } }
  useEffect(() => { loadData(); }, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!form.lender_name || !form.requested_amount) return;
    setSubmitting(true);
    try {
      await createBorrowing(profileId, { ...form, requested_amount: parseFloat(form.requested_amount), interest_rate: form.interest_rate ? parseFloat(form.interest_rate) : undefined, tenure_months: form.tenure_months ? parseInt(form.tenure_months) : undefined });
      setForm({ lender_name: '', loan_type: 'mudra', requested_amount: '', interest_rate: '', tenure_months: '', notes: '' });
      setShowAdd(false); loadData();
    } catch (err) { console.error(err); }
    finally { setSubmitting(false); }
  }

  function fmt(a: number) { return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(a); }
  const statusConfig: Record<string, { icon: any; color: string; bg: string }> = {
    exploring: { icon: Search, color: 'text-blue-700', bg: 'bg-blue-100 border-blue-300' },
    applied: { icon: Clock, color: 'text-amber-700', bg: 'bg-amber-100 border-amber-300' },
    under_review: { icon: Clock, color: 'text-purple-700', bg: 'bg-purple-100 border-purple-300' },
    approved: { icon: CheckCircle2, color: 'text-emerald-700', bg: 'bg-emerald-100 border-emerald-300' },
    disbursed: { icon: CheckCircle2, color: 'text-emerald-700', bg: 'bg-emerald-100 border-emerald-300' },
    rejected: { icon: XCircle, color: 'text-red-700', bg: 'bg-red-100 border-red-300' },
  };

  return (
    <AppShell>
      <main className="flex-1 max-w-5xl mx-auto p-6 w-full flex flex-col gap-6">
        <div className="rounded-2xl bg-gradient-to-r from-violet-950 via-purple-900 to-violet-800 text-white p-8 shadow-xl">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-violet-500/20 text-violet-300 border border-violet-400/30 rounded-full text-xs font-semibold mb-3"><Landmark className="h-3.5 w-3.5" /> Borrowing Assistance</span>
          <h1 className="text-3xl font-extrabold tracking-tight">Borrowing Assistance</h1>
          <p className="text-violet-200 text-sm mt-2">Find and track loan options tailored to your business situation.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><span className="text-sm font-medium text-slate-500">Exploring</span><p className="mt-2 text-2xl font-bold text-blue-600">{data?.exploring_count ?? 0}</p></div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><span className="text-sm font-medium text-slate-500">Applied</span><p className="mt-2 text-2xl font-bold text-amber-600">{data?.applied_count ?? 0}</p></div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><span className="text-sm font-medium text-slate-500">Approved</span><p className="mt-2 text-2xl font-bold text-emerald-600">{data?.approved_count ?? 0}</p></div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><span className="text-sm font-medium text-slate-500">Total Requested</span><p className="mt-2 text-2xl font-bold text-slate-900">{data ? fmt(data.total_requested) : '—'}</p></div>
        </div>

        <div className="rounded-xl border border-violet-200 bg-violet-50/50 p-5">
          <h3 className="text-sm font-bold text-violet-900 mb-2">💡 Borrowing Tips</h3>
          <ul className="text-sm text-violet-800 space-y-1">
            <li>• Check scheme-linked loans (PMEGP, MUDRA) for lower interest rates</li>
            <li>• Compare interest rates across multiple lenders before applying</li>
            <li>• Ensure your credit score is above 650 for better loan terms</li>
            <li>• Keep all required documents ready before application</li>
          </ul>
        </div>

        <div className="flex justify-end"><button onClick={() => setShowAdd(!showAdd)} className="inline-flex items-center gap-2 px-4 py-2.5 bg-violet-600 text-white rounded-xl text-sm font-semibold hover:bg-violet-700 transition"><Plus className="h-4 w-4" /> Add Borrowing</button></div>

        {showAdd && (
          <form onSubmit={handleAdd} className="rounded-xl border border-violet-200 bg-violet-50/50 p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between"><h3 className="font-bold text-slate-900">Add Borrowing Record</h3><button type="button" onClick={() => setShowAdd(false)} className="text-slate-400 hover:text-slate-600"><X className="h-5 w-5" /></button></div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Lender / Bank</label><input type="text" value={form.lender_name} onChange={e => setForm({ ...form, lender_name: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" required /></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Loan Type</label><select value={form.loan_type} onChange={e => setForm({ ...form, loan_type: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"><option value="mudra">MUDRA</option><option value="pmegp">PMEGP</option><option value="term_loan">Term Loan</option><option value="working_capital">Working Capital</option><option value="gold_loan">Gold Loan</option></select></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Requested Amount (₹)</label><input type="number" value={form.requested_amount} onChange={e => setForm({ ...form, requested_amount: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" required /></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Interest Rate (%)</label><input type="number" value={form.interest_rate} onChange={e => setForm({ ...form, interest_rate: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" /></div>
            </div>
            <button type="submit" disabled={submitting} className="self-end px-5 py-2.5 bg-violet-600 text-white rounded-xl text-sm font-semibold hover:bg-violet-700 transition disabled:opacity-50">{submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Add Borrowing'}</button>
          </form>
        )}

        {loading ? (
          <div className="flex flex-col items-center p-12 bg-white rounded-xl border border-slate-200"><Loader2 className="h-8 w-8 animate-spin text-violet-600 mb-3" /><p className="text-sm text-slate-600">Loading...</p></div>
        ) : !data?.borrowings?.length ? (
          <div className="rounded-xl border border-slate-200 bg-white p-12 text-center"><Landmark className="h-12 w-12 text-slate-300 mx-auto mb-3" /><p className="text-slate-500 font-medium">No borrowing records yet.</p></div>
        ) : (
          <div className="flex flex-col gap-4">
            {data.borrowings.map((b: any) => {
              const sc = statusConfig[b.status] || statusConfig.exploring;
              const Icon = sc.icon;
              return (
                <div key={b.id} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2"><h3 className="font-bold text-slate-900">{b.lender_name}</h3><span className={`px-2 py-0.5 text-xs font-bold rounded-full border ${sc.bg} ${sc.color}`}><Icon className="h-3 w-3 inline mr-1" />{b.status.replace(/_/g, ' ')}</span></div>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                    <div><p className="text-xs text-slate-500">Type</p><p className="font-semibold">{b.loan_type.replace(/_/g, ' ')}</p></div>
                    <div><p className="text-xs text-slate-500">Requested</p><p className="font-semibold">{fmt(b.requested_amount)}</p></div>
                    <div><p className="text-xs text-slate-500">Approved</p><p className="font-semibold">{b.approved_amount ? fmt(b.approved_amount) : '—'}</p></div>
                    <div><p className="text-xs text-slate-500">Rate</p><p className="font-semibold">{b.interest_rate ? `${b.interest_rate}%` : '—'}</p></div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </AppShell>
  );
}
