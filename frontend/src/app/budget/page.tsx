'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/ui/AppShell';
import { getBudgets, createBudget } from '@/lib/api';
import { ClipboardList, Plus, TrendingUp, TrendingDown, Loader2, X } from 'lucide-react';

export default function BudgetPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: '', period_type: 'monthly', start_date: '', end_date: '', total_income_target: '', total_expense_target: '' });
  const [submitting, setSubmitting] = useState(false);
  const profileId = typeof window !== 'undefined' ? localStorage.getItem('udyam_profile_id') || '00000000-0000-0000-0000-000000000001' : '00000000-0000-0000-0000-000000000001';

  async function loadData() {
    try { setLoading(true); setData(await getBudgets(profileId)); }
    catch (err) { console.warn(err); }
    finally { setLoading(false); }
  }
  useEffect(() => { loadData(); }, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name || !form.start_date || !form.end_date) return;
    setSubmitting(true);
    try {
      await createBudget(profileId, { name: form.name, period_type: form.period_type, start_date: form.start_date, end_date: form.end_date, total_income_target: parseFloat(form.total_income_target) || 0, total_expense_target: parseFloat(form.total_expense_target) || 0, items: [] });
      setForm({ name: '', period_type: 'monthly', start_date: '', end_date: '', total_income_target: '', total_expense_target: '' });
      setShowAdd(false); loadData();
    } catch (err) { console.error(err); }
    finally { setSubmitting(false); }
  }

  function fmt(a: number) { return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(a); }

  return (
    <AppShell>
      <main className="flex-1 max-w-5xl mx-auto p-6 w-full flex flex-col gap-6">
        <div className="rounded-2xl bg-gradient-to-r from-indigo-950 via-purple-900 to-indigo-800 text-white p-8 shadow-xl">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 rounded-full text-xs font-semibold mb-3"><ClipboardList className="h-3.5 w-3.5" /> Budget & Planning</span>
          <h1 className="text-3xl font-extrabold tracking-tight">Budget & Planning</h1>
          <p className="text-indigo-200 text-sm mt-2">Create financial plans and budgets for proactive management.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between"><span className="text-sm font-medium text-slate-500">Active Budgets</span><ClipboardList className="h-5 w-5 text-indigo-500" /></div>
            <p className="mt-2 text-2xl font-bold text-slate-900">{data?.active_count ?? 0}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between"><span className="text-sm font-medium text-slate-500">Budgeted Income</span><TrendingUp className="h-5 w-5 text-emerald-500" /></div>
            <p className="mt-2 text-2xl font-bold text-emerald-600">{data ? fmt(data.total_budgeted_income) : '—'}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between"><span className="text-sm font-medium text-slate-500">Budgeted Expenses</span><TrendingDown className="h-5 w-5 text-red-500" /></div>
            <p className="mt-2 text-2xl font-bold text-red-600">{data ? fmt(data.total_budgeted_expenses) : '—'}</p>
          </div>
        </div>

        <div className="flex justify-end">
          <button onClick={() => setShowAdd(!showAdd)} className="inline-flex items-center gap-2 px-4 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-700 transition"><Plus className="h-4 w-4" /> New Budget</button>
        </div>

        {showAdd && (
          <form onSubmit={handleAdd} className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between"><h3 className="font-bold text-slate-900">Create Budget</h3><button type="button" onClick={() => setShowAdd(false)} className="text-slate-400 hover:text-slate-600"><X className="h-5 w-5" /></button></div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Budget Name</label><input type="text" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" placeholder="e.g. Monthly Budget Q1" required /></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Period</label><select value={form.period_type} onChange={e => setForm({ ...form, period_type: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"><option value="weekly">Weekly</option><option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="yearly">Yearly</option></select></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Start Date</label><input type="date" value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" required /></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">End Date</label><input type="date" value={form.end_date} onChange={e => setForm({ ...form, end_date: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" required /></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Target Income (₹)</label><input type="number" value={form.total_income_target} onChange={e => setForm({ ...form, total_income_target: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" /></div>
              <div><label className="text-xs font-medium text-slate-600 mb-1 block">Target Expenses (₹)</label><input type="number" value={form.total_expense_target} onChange={e => setForm({ ...form, total_expense_target: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" /></div>
            </div>
            <button type="submit" disabled={submitting} className="self-end px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-700 transition disabled:opacity-50 inline-flex items-center gap-2">{submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />} Create Budget</button>
          </form>
        )}

        {loading ? (
          <div className="flex flex-col items-center p-12 bg-white rounded-xl border border-slate-200"><Loader2 className="h-8 w-8 animate-spin text-indigo-600 mb-3" /><p className="text-sm text-slate-600">Loading budgets...</p></div>
        ) : !data?.budgets?.length ? (
          <div className="rounded-xl border border-slate-200 bg-white p-12 text-center"><ClipboardList className="h-12 w-12 text-slate-300 mx-auto mb-3" /><p className="text-slate-500 font-medium">No budgets created yet.</p></div>
        ) : (
          <div className="flex flex-col gap-4">
            {data.budgets.map((b: any) => (
              <div key={b.id} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition">
                <div className="flex items-start justify-between mb-4">
                  <div><h3 className="text-lg font-bold text-slate-900">{b.name}</h3><p className="text-sm text-slate-500">{b.period_type} • {new Date(b.start_date).toLocaleDateString('en-IN')} - {new Date(b.end_date).toLocaleDateString('en-IN')}</p></div>
                  <span className={`px-2.5 py-1 text-xs font-bold rounded-full ${b.status === 'active' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>{b.status}</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div><p className="text-xs text-slate-500">Income Target</p><p className="text-sm font-bold text-emerald-600">{fmt(b.total_income_target)}</p></div>
                  <div><p className="text-xs text-slate-500">Expense Target</p><p className="text-sm font-bold text-red-600">{fmt(b.total_expense_target)}</p></div>
                  <div><p className="text-xs text-slate-500">Actual Income</p><p className="text-sm font-bold text-slate-900">{fmt(b.total_actual_income)}</p></div>
                  <div><p className="text-xs text-slate-500">Actual Expenses</p><p className="text-sm font-bold text-slate-900">{fmt(b.total_actual_expenses)}</p></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </AppShell>
  );
}
