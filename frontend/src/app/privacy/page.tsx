'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/ui/AppShell';
import { getPrivacy, updatePrivacyConsent } from '@/lib/api';
import { Shield, Loader2, CheckCircle2, XCircle } from 'lucide-react';

const CONSENT_TYPES = [
  { type: 'data_sharing', title: 'Data Sharing', desc: 'Allow sharing your business data with government agencies for scheme matching.' },
  { type: 'analytics', title: 'Usage Analytics', desc: 'Help improve UdyamAI by sharing anonymous usage patterns.' },
  { type: 'marketing', title: 'Marketing Communications', desc: 'Receive updates about new features, schemes, and tips via email or SMS.' },
  { type: 'ai_processing', title: 'AI Data Processing', desc: 'Allow AI to process your financial data to generate personalized recommendations.' },
  { type: 'third_party_sharing', title: 'Third-Party Sharing', desc: 'Share data with trusted financial partners for borrowing assistance.' },
];

export default function PrivacyPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);
  const profileId = typeof window !== 'undefined' ? localStorage.getItem('udyam_profile_id') || '00000000-0000-0000-0000-000000000001' : '00000000-0000-0000-0000-000000000001';

  async function loadData() { try { setLoading(true); setData(await getPrivacy(profileId)); } catch (err) { console.warn(err); } finally { setLoading(false); } }
  useEffect(() => { loadData(); }, []);

  async function handleToggle(type: string, current: boolean) {
    setUpdating(type);
    try { await updatePrivacyConsent(profileId, type, !current); loadData(); }
    catch (err) { console.error(err); }
    finally { setUpdating(null); }
  }

  function isGranted(type: string): boolean {
    return data?.consents?.find((c: any) => c.consent_type === type)?.granted || false;
  }

  return (
    <AppShell>
      <main className="flex-1 max-w-3xl mx-auto p-6 w-full flex flex-col gap-6">
        <div className="rounded-2xl bg-gradient-to-r from-slate-800 via-gray-800 to-slate-700 text-white p-8 shadow-xl">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-500/20 text-slate-300 border border-slate-400/30 rounded-full text-xs font-semibold mb-3"><Shield className="h-3.5 w-3.5" /> Privacy & Consent</span>
          <h1 className="text-3xl font-extrabold tracking-tight">Privacy & Data Consent</h1>
          <p className="text-slate-300 text-sm mt-2">Control how your data is used and shared across UdyamAI services.</p>
        </div>

        {loading ? (
          <div className="flex flex-col items-center p-12 bg-white rounded-xl border border-slate-200"><Loader2 className="h-8 w-8 animate-spin text-slate-600 mb-3" /><p className="text-sm text-slate-600">Loading settings...</p></div>
        ) : (
          <div className="flex flex-col gap-4">
            {CONSENT_TYPES.map(ct => {
              const granted = isGranted(ct.type);
              const isUpdating = updating === ct.type;
              return (
                <div key={ct.type} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-bold text-slate-900">{ct.title}</h3>
                      <p className="text-sm text-slate-500 mt-1">{ct.desc}</p>
                    </div>
                    <button
                      onClick={() => handleToggle(ct.type, granted)}
                      disabled={isUpdating}
                      className={`shrink-0 relative inline-flex h-7 w-12 items-center rounded-full transition-colors ${granted ? 'bg-emerald-500' : 'bg-slate-300'} ${isUpdating ? 'opacity-50' : ''}`}
                    >
                      <span className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${granted ? 'translate-x-6' : 'translate-x-1'}`} />
                    </button>
                  </div>
                  <div className="mt-3 flex items-center gap-2">
                    {granted ? <CheckCircle2 className="h-4 w-4 text-emerald-500" /> : <XCircle className="h-4 w-4 text-slate-400" />}
                    <span className={`text-xs font-semibold ${granted ? 'text-emerald-600' : 'text-slate-400'}`}>{granted ? 'Enabled' : 'Disabled'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-5">
          <p className="text-sm font-medium text-blue-800">🔒 Your data is encrypted and stored securely.</p>
          <p className="text-xs text-blue-600 mt-1">You can change these settings at any time. Revoking consent will stop data processing for that category immediately.</p>
        </div>
      </main>
    </AppShell>
  );
}
