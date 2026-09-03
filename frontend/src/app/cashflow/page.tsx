'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/ui/AppShell';
import { getCashFlow, createCashFlowEntry } from '@/lib/api';
import { ArrowDownLeft, ArrowUpRight, Banknote, TrendingUp, TrendingDown, Plus, X, Loader2 } from 'lucide-react';

const CATEGORIES = {
  income: ['sales', 'loan_disbursement', 'investment', 'refund', 'other_income'],
  expense: ['rent', 'salaries', 'inventory_purchase', 'utilities', 'transport', 'marketing', 'other_expense'],
};

export default function CashFlowPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ entry_type: 'income' as 'income' | 'expense', category: 'sales', description: '', amount: '', notes: '' });
  const [submitting, setSubmitting] = useState(false);
  const profileId = typeof window !== 'undefined' ? localStorage.getItem('udyam_profile_id') || '00000000-0000-0000-0000-000000000001' : '00000000-0000-0000-0000-000000000001';

  async function loadData() {
    try {
      setLoading(true);
      const result = await getCashFlow(profileId);
      setData(result);
    } catch (err) { console.warn('Failed to load cash flow:', err); }
    finally { setLoading(false); }
  }

  useEffect(() => { loadData(); }, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!form.amount) return;
    setSubmitting(true);
    try {
      await createCashFlowEntry(profileId, {
        entry_type: form.entry_type,
        category: form.category,
        description: form.description || undefined,
        amount: parseFloat(form.amount),
        notes: form.notes || undefined,
      });
      setForm({ entry_type: 'income', category: 'sales', description: '', amount: '', notes: '' });
      setShowAdd(false);
      loadData();
    } catch (err) { console.error(err); }
    finally { setSubmitting(false); }
  }

  function formatCurrency(amount: number) {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount);
  }

  const entries = data?.entries || [];

  return (
    <AppShell>
      <main className="flex-1 max-w-5xl mx-auto p-6 w-full flex flex-col gap-6">
        <div className="rounded-2xl bg-gradient-to-r from-emerald-950 via-teal-900 to-emerald-800 text-white p-8 shadow-xl">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 rounded-full text-xs font-semibold mb-3">
            <Banknote className="h-3.5 w-3.5" /> Cash Flow
          </span>
          <h1 className="text-3xl font-extrabold tracking-tight">Cash Flow Management</h1>
          <p className="text-emerald-200 text-sm mt-2">Monitor money entering and leaving your business in real-time.</p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between"><span className="text-sm font-medium text-slate-500">Total Income</span><TrendingUp className="h-5 w-5 text-emerald-500" /></div>
            <p className="mt-2 text-2xl font-bold text-emerald-600">{data ? formatCurrency(data.total_income) : '—'}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between"><span className="text-sm font-medium text-slate-500">Total Expenses</span><TrendingDown className="h-5 w-5 text-red-500" /></div>
            <p className="mt-2 text-2xl font-bold text-red-600">{data ? formatCurrency(data.total_expenses) : '—'}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between"><span className="text-sm font-medium text-slate-500">Net Cash Flow</span><Banknote className="h-5 w-5 text-blue-500" /></div>
            <p className={`mt-2 text-2xl font-bold ${(data?.net_cash_flow || 0) >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
              {data ? formatCurrency(data.net_cash_flow) : '—'}
            </p>
          </div>
        </div>

        <div className="flex justify-end">
          <button onClick={() => setShowAdd(!showAdd)} className="inline-flex items-center gap-2 px-4 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition">
            <Plus className="h-4 w-4" /> Add Entry
          </button>
        </div>

        {showAdd && (
          <form onSubmit={handleAdd} className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-slate-900">New Cash Flow Entry</h3>
              <button type="button" onClick={() => setShowAdd(false)} className="text-slate-400 hover:text-slate-600"><X className="h-5 w-5" /></button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1 block">Type</label>
                <select value={form.entry_type} onChange={e => { const v = e.target.value as 'income' | 'expense'; setForm({ ...form, entry_type: v, category: CATEGORIES[v][0] }); }} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
                  <option value="income">💰 Income</option>
                  <option value="expense">💸 Expense</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1 block">Category</label>
                <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
                  {CATEGORIES[form.entry_type].map(c => <option key={c} value={c}>{c.replace(/_/g, ' ')}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1 block">Amount (₹)</label>
                <input type="number" value={form.amount} onChange={e => setForm({ ...form, amount: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" placeholder="0" required />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1 block">Description</label>
                <input type="text" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" placeholder="Optional" />
              </div>
            </div>
            <button type="submit" disabled={submitting || !form.amount} className="self-end px-5 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition disabled:opacity-50 inline-flex items-center gap-2">
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />} Add Entry
            </button>
          </form>
        )}

        {/* Entries List */}
        {loading ? (
          <div className="flex flex-col items-center p-12 bg-white rounded-xl border border-slate-200">
            <Loader2 className="h-8 w-8 animate-spin text-emerald-600 mb-3" />
            <p className="text-sm text-slate-600">Loading cash flow data...</p>
          </div>
        ) : entries.length === 0 ? (
          <div className="rounded-xl border border-slate-200 bg-white p-12 text-center">
            <Banknote className="h-12 w-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 font-medium">No cash flow entries yet.</p>
            <p className="text-sm text-slate-400 mt-1">Add your first income or expense entry to start tracking.</p>
          </div>
        ) : (
          <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
            <div className="divide-y divide-slate-100">
              {entries.map((entry: any) => (
                <div key={entry.id} className="flex items-center justify-between p-4 hover:bg-slate-50 transition">
                  <div className="flex items-center gap-3">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${entry.entry_type === 'income' ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'}`}>
                      {entry.entry_type === 'income' ? <ArrowDownLeft className="h-5 w-5" /> : <ArrowUpRight className="h-5 w-5" />}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{entry.description || entry.category.replace(/_/g, ' ')}</p>
                      <p className="text-xs text-slate-400">{new Date(entry.date).toLocaleDateString('en-IN')} • {entry.category.replace(/_/g, ' ')}</p>
                    </div>
                  </div>
                  <span className={`text-lg font-bold ${entry.entry_type === 'income' ? 'text-emerald-600' : 'text-red-600'}`}>
                    {entry.entry_type === 'income' ? '+' : '-'}{formatCurrency(entry.amount)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </AppShell>
  );
}
