'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/ui/AppShell';
import { getSettings, updateSettings } from '@/lib/api';
import { Settings as SettingsIcon, Loader2, Save, Bell, Globe, Palette, Database } from 'lucide-react';

export default function SettingsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState({ language: 'en', theme: 'light', date_format: 'DD/MM/YYYY', notification_email: true, notification_sms: false, notification_push: true, auto_backup: true, default_view: 'dashboard' });
  const profileId = typeof window !== 'undefined' ? localStorage.getItem('udyam_profile_id') || '00000000-0000-0000-0000-000000000001' : '00000000-0000-0000-0000-000000000001';

  async function loadData() {
    try {
      setLoading(true);
      const s = await getSettings(profileId);
      setData(s);
      setForm({
        language: s.language || 'en',
        theme: s.theme || 'light',
        date_format: s.date_format || 'DD/MM/YYYY',
        notification_email: s.notification_email ?? true,
        notification_sms: s.notification_sms ?? false,
        notification_push: s.notification_push ?? true,
        auto_backup: s.auto_backup ?? true,
        default_view: s.default_view || 'dashboard',
      });
    } catch (err) { console.warn(err); }
    finally { setLoading(false); }
  }
  useEffect(() => { loadData(); }, []);

  async function handleSave() {
    setSaving(true);
    try {
      await updateSettings(profileId, form);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) { console.error(err); }
    finally { setSaving(false); }
  }

  function Toggle({ checked, onChange, disabled }: { checked: boolean; onChange: () => void; disabled?: boolean }) {
    return (
      <button type="button" onClick={onChange} disabled={disabled} className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${checked ? 'bg-indigo-500' : 'bg-slate-300'} ${disabled ? 'opacity-50' : ''}`}>
        <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-6' : 'translate-x-1'}`} />
      </button>
    );
  }

  return (
    <AppShell>
      <main className="flex-1 max-w-3xl mx-auto p-6 w-full flex flex-col gap-6">
        <div className="rounded-2xl bg-gradient-to-r from-slate-800 via-gray-800 to-slate-700 text-white p-8 shadow-xl">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-500/20 text-slate-300 border border-slate-400/30 rounded-full text-xs font-semibold mb-3"><SettingsIcon className="h-3.5 w-3.5" /> Settings</span>
          <h1 className="text-3xl font-extrabold tracking-tight">Application Settings</h1>
          <p className="text-slate-300 text-sm mt-2">Customize your UdyamAI experience.</p>
        </div>

        {loading ? (
          <div className="flex flex-col items-center p-12 bg-white rounded-xl border border-slate-200"><Loader2 className="h-8 w-8 animate-spin text-slate-600 mb-3" /><p className="text-sm text-slate-600">Loading settings...</p></div>
        ) : (
          <div className="flex flex-col gap-6">
            {/* Language & Display */}
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-2 mb-4"><Globe className="h-5 w-5 text-indigo-600" /><h3 className="font-bold text-slate-900">Language & Display</h3></div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium text-slate-600 mb-1 block">Language</label>
                  <select value={form.language} onChange={e => setForm({ ...form, language: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
                    <option value="en">English</option><option value="hi">हिंदी</option><option value="mr">मराठी</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-600 mb-1 block">Theme</label>
                  <select value={form.theme} onChange={e => setForm({ ...form, theme: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
                    <option value="light">Light</option><option value="dark">Dark</option><option value="system">System</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-600 mb-1 block">Date Format</label>
                  <select value={form.date_format} onChange={e => setForm({ ...form, date_format: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
                    <option value="DD/MM/YYYY">DD/MM/YYYY</option><option value="MM/DD/YYYY">MM/DD/YYYY</option><option value="YYYY-MM-DD">YYYY-MM-DD</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-600 mb-1 block">Default View</label>
                  <select value={form.default_view} onChange={e => setForm({ ...form, default_view: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
                    <option value="dashboard">Dashboard</option><option value="expenses">Expenses</option><option value="cashflow">Cash Flow</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Notifications */}
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-2 mb-4"><Bell className="h-5 w-5 text-indigo-600" /><h3 className="font-bold text-slate-900">Notifications</h3></div>
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between"><div><p className="text-sm font-medium text-slate-900">Email Notifications</p><p className="text-xs text-slate-500">Receive alerts via email</p></div><Toggle checked={form.notification_email} onChange={() => setForm({ ...form, notification_email: !form.notification_email })} /></div>
                <div className="flex items-center justify-between"><div><p className="text-sm font-medium text-slate-900">SMS Notifications</p><p className="text-xs text-slate-500">Receive alerts via SMS</p></div><Toggle checked={form.notification_sms} onChange={() => setForm({ ...form, notification_sms: !form.notification_sms })} /></div>
                <div className="flex items-center justify-between"><div><p className="text-sm font-medium text-slate-900">Push Notifications</p><p className="text-xs text-slate-500">Receive browser push alerts</p></div><Toggle checked={form.notification_push} onChange={() => setForm({ ...form, notification_push: !form.notification_push })} /></div>
              </div>
            </div>

            {/* Data & Backup */}
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-2 mb-4"><Database className="h-5 w-5 text-indigo-600" /><h3 className="font-bold text-slate-900">Data & Backup</h3></div>
              <div className="flex items-center justify-between">
                <div><p className="text-sm font-medium text-slate-900">Auto Backup</p><p className="text-xs text-slate-500">Automatically backup your data weekly</p></div>
                <Toggle checked={form.auto_backup} onChange={() => setForm({ ...form, auto_backup: !form.auto_backup })} />
              </div>
            </div>

            <button onClick={handleSave} disabled={saving} className="self-end inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-700 transition disabled:opacity-50">
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              {saved ? '✓ Saved!' : 'Save Settings'}
            </button>
          </div>
        )}
      </main>
    </AppShell>
  );
}
