'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/ui/AppShell';
import { useLanguageStore } from '@/stores/languageStore';
import { getExpenses, createExpense, deleteExpense, getExpenseSummary } from '@/lib/api';
import {
  Plus, Trash2, Receipt, TrendingDown, RefreshCw, Filter,
  DollarSign, Tag, Calendar, Loader2, X, AlertCircle
} from 'lucide-react';

const EXPENSE_CATEGORIES = [
  { value: 'rent', label: 'Rent', emoji: '🏠' },
  { value: 'utilities', label: 'Utilities', emoji: '💡' },
  { value: 'inventory', label: 'Inventory', emoji: '📦' },
  { value: 'salaries', label: 'Salaries', emoji: '👥' },
  { value: 'marketing', label: 'Marketing', emoji: '📢' },
  { value: 'transport', label: 'Transport', emoji: '🚛' },
  { value: 'raw_materials', label: 'Raw Materials', emoji: '🏭' },
  { value: 'other', label: 'Other', emoji: '📋' },
];

export default function ExpensesPage() {
  const t = useLanguageStore((s) => s.t);
  const [expenses, setExpenses] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [filterCat, setFilterCat] = useState('');
  const [form, setForm] = useState({ category: 'rent', description: '', amount: '', is_recurring: false, recurring_frequency: 'monthly', notes: '' });
  const [submitting, setSubmitting] = useState(false);
  const profileId = typeof window !== 'undefined' ? localStorage.getItem('udyam_profile_id') || '00000000-0000-0000-0000-000000000001' : '00000000-0000-0000-0000-000000000001';

  async function loadData() {
    try {
      setLoading(true);
      const [exp, sum] = await Promise.all([
        getExpenses(profileId, filterCat || undefined),
        getExpenseSummary(profileId),
      ]);
      setExpenses(Array.isArray(exp) ? exp : []);
      setSummary(sum);
    } catch (err) {
      console.warn('Failed to load expenses:', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadData(); }, [filterCat]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!form.amount) return;
    setSubmitting(true);
    try {
      await createExpense(profileId, {
        category: form.category,
        description: form.description || undefined,
        amount: parseFloat(form.amount),
        is_recurring: form.is_recurring,
        recurring_frequency: form.is_recurring ? form.recurring_frequency : undefined,
        notes: form.notes || undefined,
      });
      setForm({ category: 'rent', description: '', amount: '', is_recurring: false, recurring_frequency: 'monthly', notes: '' });
      setShowAdd(false);
      loadData();
    } catch (err) {
      console.error('Failed to add expense:', err);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteExpense(id, profileId);
      loadData();
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  }

  function formatCurrency(amount: number) {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount);
  }

  const categoryColors: Record<string, string> = {
    rent: 'bg-blue-50 text-blue-700 border-blue-200',
    utilities: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    inventory: 'bg-purple-50 text-purple-700 border-purple-200',
    salaries: 'bg-green-50 text-green-700 border-green-200',
    marketing: 'bg-orange-50 text-orange-700 border-orange-200',
    transport: 'bg-cyan-50 text-cyan-700 border-cyan-200',
    raw_materials: 'bg-pink-50 text-pink-700 border-pink-200',
    other: 'bg-gray-50 text-gray-700 border-gray-200',
  };

  return (
    <AppShell>
      <main className="flex-1 max-w-5xl mx-auto p-6 w-full flex flex-col gap-6">
        {/* Banner */}
        <div className="rounded-2xl bg-gradient-to-r from-red-950 via-rose-900 to-red-800 text-white p-8 shadow-xl">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-red-500/20 text-red-300 border border-red-400/30 rounded-full text-xs font-semibold mb-3">
            <Receipt className="h-3.5 w-3.5" /> Expense Tracker
          </span>
          <h1 className="text-3xl font-extrabold tracking-tight">Business Expenses</h1>
          <p className="text-red-200 text-sm mt-2">Track and control your business spending to identify cost patterns.</p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Total Expenses</span>
              <TrendingDown className="h-5 w-5 text-red-500" />
            </div>
            <p className="mt-2 text-2xl font-bold text-slate-900">{summary ? formatCurrency(summary.total_expenses) : '—'}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Recurring Total</span>
              <RefreshCw className="h-5 w-5 text-orange-500" />
            </div>
            <p className="mt-2 text-2xl font-bold text-slate-900">{summary ? formatCurrency(summary.recurring_total) : '—'}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Total Entries</span>
              <Tag className="h-5 w-5 text-blue-500" />
            </div>
            <p className="mt-2 text-2xl font-bold text-slate-900">{summary?.count ?? 0}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Categories Used</span>
              <DollarSign className="h-5 w-5 text-emerald-500" />
            </div>
            <p className="mt-2 text-2xl font-bold text-slate-900">{summary ? Object.keys(summary.by_category).length : 0}</p>
          </div>
        </div>

        {/* Category Breakdown */}
        {summary && Object.keys(summary.by_category).length > 0 && (
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 mb-3">Spending by Category</h3>
            <div className="flex flex-col gap-3">
              {Object.entries(summary.by_category).sort((a, b) => (b[1] as number) - (a[1] as number)).map(([cat, amount]) => {
                const catInfo = EXPENSE_CATEGORIES.find(c => c.value === cat);
                const pct = summary.total_expenses > 0 ? ((amount as number) / summary.total_expenses * 100) : 0;
                return (
                  <div key={cat}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-slate-700">{catInfo?.emoji} {catInfo?.label || cat}</span>
                      <span className="text-sm font-bold text-slate-900">{formatCurrency(amount as number)}</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-slate-100">
                      <div className="h-full rounded-full bg-red-500 transition-all" style={{ width: `${Math.min(100, pct)}%` }} />
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">{pct.toFixed(1)}% of total</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Filter & Add */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Filter className="h-4 w-4 text-slate-400" />
            <select value={filterCat} onChange={e => setFilterCat(e.target.value)} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:ring-2 focus:ring-red-200">
              <option value="">All Categories</option>
              {EXPENSE_CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.emoji} {c.label}</option>)}
            </select>
          </div>
          <button onClick={() => setShowAdd(!showAdd)} className="inline-flex items-center gap-2 px-4 py-2.5 bg-red-600 text-white rounded-xl text-sm font-semibold hover:bg-red-700 transition">
            <Plus className="h-4 w-4" /> Add Expense
          </button>
        </div>

        {/* Add Form */}
        {showAdd && (
          <form onSubmit={handleAdd} className="rounded-xl border border-red-200 bg-red-50/50 p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-slate-900">New Expense</h3>
              <button type="button" onClick={() => setShowAdd(false)} className="text-slate-400 hover:text-slate-600"><X className="h-5 w-5" /></button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1 block">Category</label>
                <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
                  {EXPENSE_CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.emoji} {c.label}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1 block">Amount (₹)</label>
                <input type="number" value={form.amount} onChange={e => setForm({ ...form, amount: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" placeholder="0" required />
              </div>
              <div className="sm:col-span-2">
                <label className="text-xs font-medium text-slate-600 mb-1 block">Description</label>
                <input type="text" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" placeholder="What was this expense for?" />
              </div>
              <div className="flex items-center gap-3">
                <input type="checkbox" checked={form.is_recurring} onChange={e => setForm({ ...form, is_recurring: e.target.checked })} className="rounded" id="recurring" />
                <label htmlFor="recurring" className="text-sm text-slate-700">Recurring expense</label>
              </div>
              {form.is_recurring && (
                <select value={form.recurring_frequency} onChange={e => setForm({ ...form, recurring_frequency: e.target.value })} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                </select>
              )}
              <div className="sm:col-span-2">
                <label className="text-xs font-medium text-slate-600 mb-1 block">Notes</label>
                <input type="text" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" placeholder="Optional notes" />
              </div>
            </div>
            <button type="submit" disabled={submitting || !form.amount} className="self-end px-5 py-2.5 bg-red-600 text-white rounded-xl text-sm font-semibold hover:bg-red-700 transition disabled:opacity-50 inline-flex items-center gap-2">
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              Add Expense
            </button>
          </form>
        )}

        {/* Expense List */}
        {loading ? (
          <div className="flex flex-col items-center p-12 bg-white rounded-xl border border-slate-200">
            <Loader2 className="h-8 w-8 animate-spin text-red-600 mb-3" />
            <p className="text-sm text-slate-600">Loading expenses...</p>
          </div>
        ) : expenses.length === 0 ? (
          <div className="rounded-xl border border-slate-200 bg-white p-12 text-center">
            <Receipt className="h-12 w-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 font-medium">No expenses recorded yet.</p>
            <p className="text-sm text-slate-400 mt-1">Click “Add Expense” to start tracking your business spending.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {expenses.map((exp) => {
              const catInfo = EXPENSE_CATEGORIES.find(c => c.value === exp.category);
              return (
                <div key={exp.id} className="rounded-xl border border-slate-200 bg-white p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:shadow-sm transition">
                  <div className="flex items-center gap-4">
                    <span className="text-2xl">{catInfo?.emoji || '📋'}</span>
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold text-slate-900">{exp.description || catInfo?.label || exp.category}</h4>
                        <span className={`px-2 py-0.5 text-xs font-bold rounded-full border ${categoryColors[exp.category] || 'bg-gray-50 text-gray-700 border-gray-200'}`}>
                          {catInfo?.label || exp.category}
                        </span>
                        {exp.is_recurring && <RefreshCw className="h-3.5 w-3.5 text-orange-400" />}
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {new Date(exp.date).toLocaleDateString('en-IN')} {exp.recurring_frequency ? `• ${exp.recurring_frequency}` : ''}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-lg font-bold text-red-600">-{formatCurrency(exp.amount)}</span>
                    <button onClick={() => handleDelete(exp.id)} className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition">
                      <Trash2 className="h-4 w-4" />
                    </button>
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
