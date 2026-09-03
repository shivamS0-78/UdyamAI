'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/ui/AppShell';
import { getProfile, updateProfile } from '@/lib/api';
import { User, Loader2, Save, Mail, Phone, Building2, Globe } from 'lucide-react';

export default function ProfilePage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', phone: '', business_name: '', business_type: '', preferred_language: 'en' });
  const profileId = typeof window !== 'undefined' ? localStorage.getItem('udyam_profile_id') || '00000000-0000-0000-0000-000000000001' : '00000000-0000-0000-0000-000000000001';

  async function loadData() {
    try {
      setLoading(true);
      const p = await getProfile(profileId);
      setData(p);
      setForm({
        name: p.name || '',
        email: p.email || '',
        phone: p.phone || '',
        business_name: p.business_name || '',
        business_type: p.business_type || '',
        preferred_language: p.preferred_language || 'en',
      });
    } catch (err) { console.warn(err); }
    finally { setLoading(false); }
  }
  useEffect(() => { loadData(); }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await updateProfile(profileId, form);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) { console.error(err); }
    finally { setSaving(false); }
  }

  return (
    <AppShell>
      <main className="flex-1 max-w-3xl mx-auto p-6 w-full flex flex-col gap-6">
        <div className="rounded-2xl bg-gradient-to-r from-indigo-950 via-blue-900 to-indigo-800 text-white p-8 shadow-xl">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 rounded-full text-xs font-semibold mb-3"><User className="h-3.5 w-3.5" /> Profile</span>
          <h1 className="text-3xl font-extrabold tracking-tight">Profile Management</h1>
          <p className="text-indigo-200 text-sm mt-2">Update your personal and business account information.</p>
        </div>

        {loading ? (
          <div className="flex flex-col items-center p-12 bg-white rounded-xl border border-slate-200"><Loader2 className="h-8 w-8 animate-spin text-indigo-600 mb-3" /><p className="text-sm text-slate-600">Loading profile...</p></div>
        ) : (
          <form onSubmit={handleSave} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col gap-5">
            {/* Avatar */}
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-indigo-100">
                <User className="h-8 w-8 text-indigo-600" />
              </div>
              <div>
                <p className="font-bold text-slate-900">{form.name || 'Your Name'}</p>
                <p className="text-sm text-slate-500">{form.email || 'No email set'}</p>
                {data?.created_at && <p className="text-xs text-slate-400">Member since {new Date(data.created_at).toLocaleDateString('en-IN')}</p>}
              </div>
            </div>

            <div className="h-px bg-slate-100" />

            {/* Personal Info */}
            <h3 className="font-bold text-slate-900 flex items-center gap-2"><User className="h-4 w-4" /> Personal Information</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1 block">Full Name</label>
                <input type="text" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm" placeholder="Your full name" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1 block">Email</label>
                <input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm" placeholder="you@example.com" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1 block">Phone</label>
                <input type="tel" value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm" placeholder="10-digit mobile number" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1 block">Preferred Language</label>
                <select value={form.preferred_language} onChange={e => setForm({ ...form, preferred_language: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm">
                  <option value="en">English</option><option value="hi">हिंदी</option><option value="mr">मराठी</option>
                </select>
              </div>
            </div>

            <div className="h-px bg-slate-100" />

            {/* Business Info */}
            <h3 className="font-bold text-slate-900 flex items-center gap-2"><Building2 className="h-4 w-4" /> Business Information</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1 block">Business Name</label>
                <input type="text" value={form.business_name} onChange={e => setForm({ ...form, business_name: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm" placeholder="Your business name" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1 block">Business Type</label>
                <select value={form.business_type} onChange={e => setForm({ ...form, business_type: e.target.value })} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm">
                  <option value="">Select type</option>
                  <option value="manufacturing">Manufacturing</option>
                  <option value="services">Services</option>
                  <option value="trading">Trading</option>
                  <option value="agriculture">Agriculture</option>
                  <option value="dairy">Dairy</option>
                  <option value="food_processing">Food Processing</option>
                  <option value="retail">Retail</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            <button type="submit" disabled={saving} className="self-end inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-700 transition disabled:opacity-50">
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              {saved ? '✓ Profile Updated!' : 'Save Profile'}
            </button>
          </form>
        )}
      </main>
    </AppShell>
  );
}
