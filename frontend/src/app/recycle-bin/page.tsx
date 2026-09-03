'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/ui/AppShell';
import { getRecycleBin, restoreFromRecycleBin, permanentDeleteRecycleBin } from '@/lib/api';
import { Trash2, RotateCcw, AlertTriangle, Loader2, Inbox } from 'lucide-react';

export default function RecycleBinPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string[]>([]);
  const profileId = typeof window !== 'undefined' ? localStorage.getItem('udyam_profile_id') || '00000000-0000-0000-0000-000000000001' : '00000000-0000-0000-0000-000000000001';

  async function loadData() { try { setLoading(true); const data = await getRecycleBin(profileId); setItems(Array.isArray(data) ? data : []); } catch (err) { console.warn(err); } finally { setLoading(false); } }
  useEffect(() => { loadData(); }, []);

  async function handleRestore() {
    if (!selected.length) return;
    try { await restoreFromRecycleBin(selected); setSelected([]); loadData(); } catch (err) { console.error(err); }
  }

  async function handlePermanentDelete(id: string) {
    try { await permanentDeleteRecycleBin(id); loadData(); } catch (err) { console.error(err); }
  }

  function toggleSelect(id: string) {
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  }

  const itemTypeEmoji: Record<string, string> = { expense: '💸', cash_flow: '💰', savings_goal: '🎯', budget: '📋', debt: '💳', borrowing: '🏦', credit_score: '📊' };

  return (
    <AppShell>
      <main className="flex-1 max-w-5xl mx-auto p-6 w-full flex flex-col gap-6">
        <div className="rounded-2xl bg-gradient-to-r from-gray-800 via-slate-800 to-gray-700 text-white p-8 shadow-xl">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-gray-500/20 text-gray-300 border border-gray-400/30 rounded-full text-xs font-semibold mb-3"><Trash2 className="h-3.5 w-3.5" /> Recycle Bin</span>
          <h1 className="text-3xl font-extrabold tracking-tight">Recycle Bin</h1>
          <p className="text-gray-300 text-sm mt-2">Manage deleted items — restore or permanently delete them.</p>
        </div>

        {selected.length > 0 && (
          <div className="flex items-center gap-4 bg-blue-50 border border-blue-200 rounded-xl p-4">
            <span className="text-sm font-medium text-blue-700">{selected.length} item(s) selected</span>
            <button onClick={handleRestore} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700"><RotateCcw className="h-3.5 w-3.5" /> Restore Selected</button>
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center p-12 bg-white rounded-xl border border-slate-200"><Loader2 className="h-8 w-8 animate-spin text-gray-600 mb-3" /><p className="text-sm text-slate-600">Loading...</p></div>
        ) : items.length === 0 ? (
          <div className="rounded-xl border border-slate-200 bg-white p-12 text-center"><Inbox className="h-12 w-12 text-slate-300 mx-auto mb-3" /><p className="text-slate-500 font-medium">Recycle bin is empty.</p></div>
        ) : (
          <div className="flex flex-col gap-3">
            {items.map((item) => (
              <div key={item.id} className="rounded-xl border border-slate-200 bg-white p-4 flex items-center justify-between hover:shadow-sm transition">
                <div className="flex items-center gap-4">
                  <input type="checkbox" checked={selected.includes(item.id)} onChange={() => toggleSelect(item.id)} className="rounded" />
                  <span className="text-2xl">{itemTypeEmoji[item.item_type] || '📄'}</span>
                  <div>
                    <h4 className="font-semibold text-slate-900 capitalize">{item.item_type.replace(/_/g, ' ')}</h4>
                    <p className="text-xs text-slate-400">Deleted: {new Date(item.deleted_at).toLocaleDateString('en-IN')}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => restoreFromRecycleBin([item.id]).then(loadData)} className="p-2 text-blue-500 hover:bg-blue-50 rounded-lg transition" title="Restore"><RotateCcw className="h-4 w-4" /></button>
                  <button onClick={() => handlePermanentDelete(item.id)} className="p-2 text-red-400 hover:bg-red-50 rounded-lg transition" title="Delete permanently"><Trash2 className="h-4 w-4" /></button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-500 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-amber-800">Permanent deletion cannot be undone.</p>
            <p className="text-xs text-amber-600 mt-1">Items older than 30 days are automatically purged.</p>
          </div>
        </div>
      </main>
    </AppShell>
  );
}
