'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/ui/AppShell';
import { getDebts, createDebt, addDebtPayment } from '@/lib/api';
import { CreditCard, Plus, Loader2, X, AlertTriangle, CheckCircle2, Clock } from 'lucide-react';

export default function DebtsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [payDebt, setPayDebt] = useState<string | null>(null);
  const [form, setForm] = useState({ lender_name: '', loan_type: 'term_loan', principal_amount: '', outstanding_amount: '', interest_rate: '', emi_amount: '', tenure_months: '', notes: '' });
  const [payForm, setPayForm] = useState({ amount: '', principal_portion: '', interest_portion: '', payment_mode: 'neft', notes: '' });
  const [submitting, setSubmitting] = useState(false);
  const profileId = typeof window !== 'undefined' ? localStorage.getItem('udyam_profile_id') || '00000000-0000-0000-0000-000000000001' : '00000000-0000-0000-0000-000000000001';

  async function loadData() { try { setLoading(true); setData(await getDebts(profileId)); } catch (err) { console.warn(err); } finally { setLoading(false); } }
  useEffect(() => { loadData(); }, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!form.lender_name || !form.principal_amount) return;
    setSubmitting(true);
    try {
      await createDebt(profileId, { ...form, principal_amount: parseFloat(form.principal_amount), outstanding_amount: parseFloat(form.outstanding_amount || form.principal_amount), interest_rate: parseFloat(form.interest_rate) || 10, emi_amount: form.emi_amount ? parseFloat(form.emi_amount) : undefined, tenure_months: form.tenure_months ? parseInt(form.tenure_months) : undefined });
      setForm({ lender_name: '', loan_type: 'term_loan', principal_amount: '', outstanding_amount: '', interest_rate: '', emi_amount: '', tenure_months: '', notes: '' });
      setShowAdd(false); loadData();
    } catch (err) { console.error(err); }
    finally { setSubmitting(false); }
  }

  async function handlePay(e: React.FormEvent) {
    e.preventDefault();
    if (!payDebt || !payForm.amount) return;
    setSubmitting(true);
    try {
      await addDebtPayment(payDebt, { amount: parseFloat(payForm.amount), principal_portion: parseFloat(payForm.principal_portion) || parseFloat(payForm.amount), interest_portion: parseFloat(payForm.interest_portion) || 0, payment_mode: payForm.payment_mode, notes: payForm.notes || undefined });
      setPayForm({ amount: '', principal_portion: '', interest_portion: '', payment_mode: 'neft', notes: '' });
      setPayDebt(null); loadData();
    } catch (err) { console.error(err); }
    finally { setSubmitting(false); }
  }

  function fmt(a: number) { return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(a); }
  const statusColors: Record<string, string> = { active: 'bg-amber-100 text-amber-700 border-amber-300', paid_off: 'bg-emerald-100 text-emerald-700 border-emerald-300', defaulted: 'bg-red-100 text-red-700 border-red-300', restructured: 'bg-blue-100 text-blue-700 border-blue-300' };

  return (
    <AppShell>
      <main className="flex-1 max-w-5xl mx-auto p-6 w-full flex flex-col gap-6">
        <div className="rounded-2xl bg-gradient-to-r from-rose-950 via-pink-900 to-rose-800 text-white p-8 shadow-xl">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-rose-500/20 text-rose-300 border border-rose-400/30 rounded-full text-xs font-semibold mb-3"><CreditCard className="h-3.5 w-3.5" /> Debt Tracking</span>
          <h1 className="text-3xl font-extrabold tracking-tight">Debt Management</h1>
          <p className="text-rose-200 text-sm mt-2">Monitor existing debts, track payments, and avoid defaults.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center justify-between"><span className="text-sm font-medium text-slate-500">Total Outstanding</span><AlertTriangle className="h-5 w-5 text-red-500" /></div><p className="mt-2 text-2xl font-bold text-red-600">{data ? fmt(data.total_outstanding) : '—'}</p></div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center justify-between"><span className="text-sm font-medium text-slate-500">Total Principal</span><CreditCard className="h-5 w-5 text-slate-500" /></div><p className="mt-2 text-2xl font-bold text-slate-900">{data ? fmt(data.total_principal) : '—'}</p></div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center justify-between"><span className="text-sm font-medium text-slate-500">Monthly EMI</span><Clock className="h-5 w-5 text-blue-500" /></div><p className="mt-2 text-2xl font-bold text-blue-600">{data ? fmt(data.total_monthly_emi) : '—'}</p></div>
        </div>

        <div className="flex justify-end"><button onClick={() => setShowAdd(!showAdd)} className="inline-flex items-center gap-2 px-4 py-2.5 bg-rose-600 text-white rounded-xl text-sm font-semibold hover:bg-rose-700 transition"><Plus className="h-4 w-4" /> Add Debt</button></div>

        {showAdd && (
          <form onSubmit={handleAdd} className="rounded-xl border border-rose-200 bg-rose-50/50 p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between"><h3 className="font-bold text-slate-900">Add Debt Record</h3><button type="button" onClick={() => setShowAdd(false)} className="text-slate-400 hover:text-slate-600"><X className="h-5 w-5" /></button></div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Lender Name</label><input type="text" value={form.lender_name} onChange={e => setForm({ ...form, lender_name: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" required /></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Loan Type</label><select value={form.loan_type} onChange={e => setForm({ ...form, loan_type: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"><option value="term_loan">Term Loan</option><option value="working_capital">Working Capital</option><option value="credit_card">Credit Card</option><option value="personal">Personal Loan</option><option value="government_scheme">Government Scheme</option></select></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Principal Amount (₹)</label><input type="number" value={form.principal_amount} onChange={e => setForm({ ...form, principal_amount: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" required /></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Outstanding Amount (₹)</label><input type="number" value={form.outstanding_amount} onChange={e => setForm({ ...form, outstanding_amount: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" placeholder="Same as principal" /></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Interest Rate (%)</label><input type="number" value={form.interest_rate} onChange={e => setForm({ ...form, interest_rate: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" placeholder="10" /></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">EMI Amount (₹)</label><input type="number" value={form.emi_amount} onChange={e => setForm({ ...form, emi_amount: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" /></div>
            </div>
            <button type="submit" disabled={submitting} className="self-end px-5 py-2.5 bg-rose-600 text-white rounded-xl text-sm font-semibold hover:bg-rose-700 transition disabled:opacity-50">{submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Add Debt'}</button>
          </form>
        )}

        {payDebt && (
          <form onSubmit={handlePay} className="rounded-xl border border-blue-200 bg-blue-50/50 p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between"><h3 className="font-bold text-slate-900">Record Payment</h3><button type="button" onClick={() => setPayDebt(null)} className="text-slate-400 hover:text-slate-600"><X className="h-5 w-5" /></button></div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Payment Amount (₹)</label><input type="number" value={payForm.amount} onChange={e => setPayForm({ ...payForm, amount: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" required /></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Principal Portion (₹)</label><input type="number" value={payForm.principal_portion} onChange={e => setPayForm({ ...payForm, principal_portion: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" placeholder="Amount goes to principal" /></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Payment Mode</label><select value={payForm.payment_mode} onChange={e => setPayForm({ ...payForm, payment_mode: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"><option value="neft">NEFT</option><option value="upi">UPI</option><option value="cheque">Cheque</option><option value="cash">Cash</option></select></div>
            </div>
            <button type="submit" disabled={submitting} className="self-end px-5 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 transition disabled:opacity-50">Record Payment</button>
          </form>
        )}

        {loading ? (
          <div className="flex flex-col items-center p-12 bg-white rounded-xl border border-slate-200"><Loader2 className="h-8 w-8 animate-spin text-rose-600 mb-3" /><p className="text-sm text-slate-600">Loading debts...</p></div>
        ) : !data?.debts?.length ? (
          <div className="rounded-xl border border-slate-200 bg-white p-12 text-center"><CreditCard className="h-12 w-12 text-slate-300 mx-auto mb-3" /><p className="text-slate-500 font-medium">No debts recorded yet.</p></div>
        ) : (
          <div className="flex flex-col gap-4">
            {data.debts.map((d: any) => (
              <div key={d.id} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2"><h3 className="text-lg font-bold text-slate-900">{d.lender_name}</h3><span className={`px-2 py-0.5 text-xs font-bold rounded-full border ${statusColors[d.status] || 'bg-gray-100 text-gray-600'}`}>{d.status}</span></div>
                    <p className="text-sm text-slate-500 mt-1">{d.loan_type.replace(/_/g, ' ')} {d.scheme_name ? `• ${d.scheme_name}` : ''}</p>
                  </div>
                  <button onClick={() => setPayDebt(d.id)} className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition">Pay EMI</button>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-3">
                  <div><p className="text-xs text-slate-500">Principal</p><p className="text-sm font-bold text-slate-900">{fmt(d.principal_amount)}</p></div>
                  <div><p className="text-xs text-slate-500">Outstanding</p><p className="text-sm font-bold text-red-600">{fmt(d.outstanding_amount)}</p></div>
                  <div><p className="text-xs text-slate-500">Rate</p><p className="text-sm font-bold text-slate-900">{d.interest_rate}% p.a.</p></div>
                  <div><p className="text-xs text-slate-500">EMI</p><p className="text-sm font-bold text-blue-600">{d.emi_amount ? fmt(d.emi_amount) : '—'}</p></div>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-100"><div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${Math.min(100, d.paid_percent)}%` }} /></div>
                <p className="text-xs text-slate-400 mt-1">{d.paid_percent}% paid off</p>
              </div>
            ))}
          </div>
        )}
      </main>
    </AppShell>
  );
}
