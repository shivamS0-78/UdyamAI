'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/ui/AppShell';
import { getSavings, createSavingsGoal, addSavingsTransaction } from '@/lib/api';
import { Target, Plus, TrendingUp, Loader2, X, Coins, ArrowUpCircle, ArrowDownCircle } from 'lucide-react';

export default function SavingsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [showTxn, setShowTxn] = useState<string | null>(null);
  const [form, setForm] = useState({ name: '', target_amount: '', priority: 'medium', notes: '' });
  const [txnForm, setTxnForm] = useState({ amount: '', transaction_type: 'deposit' as 'deposit' | 'withdrawal', notes: '' });
  const [submitting, setSubmitting] = useState(false);
  const profileId = typeof window !== 'undefined' ? localStorage.getItem('udyam_profile_id') || '00000000-0000-0000-0000-000000000001' : '00000000-0000-0000-0000-000000000001';

  async function loadData() {
    try { setLoading(true); setData(await getSavings(profileId)); }
    catch (err) { console.warn('Failed:', err); }
    finally { setLoading(false); }
  }
  useEffect(() => { loadData(); }, []);

  async function handleAddGoal(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name || !form.target_amount) return;
    setSubmitting(true);
    try {
      await createSavingsGoal(profileId, { name: form.name, target_amount: parseFloat(form.target_amount), priority: form.priority, notes: form.notes || undefined });
      setForm({ name: '', target_amount: '', priority: 'medium', notes: '' });
      setShowAdd(false); loadData();
    } catch (err) { console.error(err); }
    finally { setSubmitting(false); }
  }

  async function handleTxn(e: React.FormEvent) {
    e.preventDefault();
    if (!showTxn || !txnForm.amount) return;
    setSubmitting(true);
    try {
      await addSavingsTransaction(showTxn, { amount: parseFloat(txnForm.amount), transaction_type: txnForm.transaction_type, notes: txnForm.notes || undefined });
      setTxnForm({ amount: '', transaction_type: 'deposit', notes: '' });
      setShowTxn(null); loadData();
    } catch (err) { console.error(err); }
    finally { setSubmitting(false); }
  }

  function fmt(amount: number) { return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount); }
  const priorityColors: Record<string, string> = { high: 'bg-red-100 text-red-700 border-red-300', medium: 'bg-amber-100 text-amber-700 border-amber-300', low: 'bg-green-100 text-green-700 border-green-300' };

  return (
    <AppShell>
      <main className="flex-1 max-w-5xl mx-auto p-6 w-full flex flex-col gap-6">
        <div className="rounded-2xl bg-gradient-to-r from-amber-950 via-yellow-900 to-amber-800 text-white p-8 shadow-xl">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-500/20 text-amber-300 border border-amber-400/30 rounded-full text-xs font-semibold mb-3"><Target className="h-3.5 w-3.5" /> Savings Goals</span>
          <h1 className="text-3xl font-extrabold tracking-tight">Financial Savings</h1>
          <p className="text-amber-200 text-sm mt-2">Set, monitor, and achieve your financial goals systematically.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between"><span className="text-sm font-medium text-slate-500">Total Saved</span><Coins className="h-5 w-5 text-amber-500" /></div>
            <p className="mt-2 text-2xl font-bold text-amber-600">{data ? fmt(data.total_saved) : '—'}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between"><span className="text-sm font-medium text-slate-500">Total Target</span><Target className="h-5 w-5 text-slate-500" /></div>
            <p className="mt-2 text-2xl font-bold text-slate-900">{data ? fmt(data.total_target) : '—'}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between"><span className="text-sm font-medium text-slate-500">Overall Progress</span><TrendingUp className="h-5 w-5 text-emerald-500" /></div>
            <p className="mt-2 text-2xl font-bold text-emerald-600">{data ? `${data.overall_progress}%` : '—'}</p>
          </div>
        </div>

        <div className="flex justify-end">
          <button onClick={() => setShowAdd(!showAdd)} className="inline-flex items-center gap-2 px-4 py-2.5 bg-amber-600 text-white rounded-xl text-sm font-semibold hover:bg-amber-700 transition"><Plus className="h-4 w-4" /> New Goal</button>
        </div>

        {showAdd && (
          <form onSubmit={handleAddGoal} className="rounded-xl border border-amber-200 bg-amber-50/50 p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between"><h3 className="font-bold text-slate-900">New Savings Goal</h3><button type="button" onClick={() => setShowAdd(false)} className="text-slate-400 hover:text-slate-600"><X className="h-5 w-5" /></button></div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Goal Name</label><input type="text" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" placeholder="e.g. Emergency Fund" required /></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Target Amount (₹)</label><input type="number" value={form.target_amount} onChange={e => setForm({ ...form, target_amount: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" required /></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Priority</label><select value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"><option value="high">🔴 High</option><option value="medium">🟡 Medium</option><option value="low">🟢 Low</option></select></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Notes</label><input type="text" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" placeholder="Optional" /></div>
            </div>
            <button type="submit" disabled={submitting} className="self-end px-5 py-2.5 bg-amber-600 text-white rounded-xl text-sm font-semibold hover:bg-amber-700 transition disabled:opacity-50 inline-flex items-center gap-2">{submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />} Create Goal</button>
          </form>
        )}

        {showTxn && (
          <form onSubmit={handleTxn} className="rounded-xl border border-blue-200 bg-blue-50/50 p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between"><h3 className="font-bold text-slate-900">Add Transaction</h3><button type="button" onClick={() => setShowTxn(null)} className="text-slate-400 hover:text-slate-600"><X className="h-5 w-5" /></button></div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Type</label><select value={txnForm.transaction_type} onChange={e => setTxnForm({ ...txnForm, transaction_type: e.target.value as any })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"><option value="deposit">Deposit</option><option value="withdrawal">Withdrawal</option></select></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Amount (₹)</label><input type="number" value={txnForm.amount} onChange={e => setTxnForm({ ...txnForm, amount: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" required /></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Notes</label><input type="text" value={txnForm.notes} onChange={e => setTxnForm({ ...txnForm, notes: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" /></div>
            </div>
            <button type="submit" disabled={submitting} className="self-end px-5 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 transition disabled:opacity-50">Add Transaction</button>
          </form>
        )}

        {loading ? (
          <div className="flex flex-col items-center p-12 bg-white rounded-xl border border-slate-200"><Loader2 className="h-8 w-8 animate-spin text-amber-600 mb-3" /><p className="text-sm text-slate-600">Loading savings data...</p></div>
        ) : !data?.goals?.length ? (
          <div className="rounded-xl border border-slate-200 bg-white p-12 text-center"><Target className="h-12 w-12 text-slate-300 mx-auto mb-3" /><p className="text-slate-500 font-medium">No savings goals yet.</p><p className="text-sm text-slate-400 mt-1">Create your first goal to start saving.</p></div>
        ) : (
          <div className="flex flex-col gap-4">
            {data.goals.map((goal: any) => (
              <div key={goal.id} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-2"><h3 className="text-lg font-bold text-slate-900">{goal.name}</h3><span className={`px-2 py-0.5 text-xs font-bold rounded-full border ${priorityColors[goal.priority] || 'bg-gray-100 text-gray-600'}`}>{goal.priority}</span></div>
                    <p className="text-sm text-slate-500 mt-1">{fmt(goal.current_amount)} of {fmt(goal.target_amount)}</p>
                  </div>
                  <span className="text-2xl font-bold text-amber-600">{goal.progress_percent}%</span>
                </div>
                <div className="h-3 w-full rounded-full bg-slate-100 mb-4"><div className="h-full rounded-full bg-amber-500 transition-all" style={{ width: `${Math.min(100, goal.progress_percent)}%` }} /></div>
                <div className="flex items-center justify-between">
                  <span className={`px-2 py-1 text-xs font-bold rounded-full ${goal.status === 'active' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>{goal.status}</span>
                  <button onClick={() => setShowTxn(goal.id)} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition"><Plus className="h-3.5 w-3.5" /> Add Transaction</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </AppShell>
  );
}
