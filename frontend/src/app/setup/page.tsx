'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, Loader2, Sparkles, UserRound, Building2, Mail } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';
import LanguageSwitcher from '@/components/ui/LanguageSwitcher';
import { createProfile } from '@/lib/api';
import { storeProfile } from '@/lib/auth';
import { useLanguageStore } from '@/stores/languageStore';

const BUSINESS_TYPES = [
  { value: '', label: 'Select type' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'services', label: 'Services' },
  { value: 'trading', label: 'Trading' },
  { value: 'agriculture', label: 'Agriculture' },
  { value: 'dairy', label: 'Dairy' },
  { value: 'food_processing', label: 'Food Processing' },
  { value: 'retail', label: 'Retail' },
  { value: 'other', label: 'Other' },
];

export default function SetupPage() {
  const router = useRouter();
  const t = useLanguageStore((s) => s.t);
  const language = useLanguageStore((s) => s.language);
  const setLanguage = useLanguageStore((s) => s.setLanguage);
  const { user, profile } = useAuth();

  const [name, setName] = useState('');
  const [businessName, setBusinessName] = useState('');
  const [businessType, setBusinessType] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const email = user?.email ?? '';


  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim() || !businessName.trim()) {
      setError(t('setup.error'));
      return;
    }

    setError('');
    setSaving(true);
    try {
      // Creates/updates the profile linked to the authenticated user.
      const savedProfile = await createProfile(profile?.id ?? null, {
        name: name.trim(),
        business_name: businessName.trim(),
        business_type: businessType || null,
        email: email || null,
        preferred_language: language,
      });
      storeProfile(savedProfile);
      router.push('/dashboard');
    } catch (err) {
      console.error('Profile setup failed:', err);
      setError(t('setup.fail'));
      setSaving(false);
    }
  };

  const handleSkip = () => {
    // Keep whatever profile id AuthProvider already resolved for the user.
    if (profile?.id) storeProfile(profile);
    router.push('/dashboard');
  };

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-br from-indigo-50 via-white to-blue-50 px-6">
      <div className="pointer-events-none absolute -left-32 -top-32 h-72 w-72 rounded-full bg-indigo-200/40 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-32 -right-32 h-80 w-80 rounded-full bg-blue-200/30 blur-3xl" />
      <div className="absolute right-6 top-6">
        <LanguageSwitcher />
      </div>

      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mb-3 flex items-center justify-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-100">
              <Sparkles className="h-5 w-5 text-indigo-600" />
            </div>
          </div>
          <p className="text-xs font-bold uppercase tracking-widest text-indigo-500">
            {t('setup.eyebrow')}
          </p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">{t('setup.title')}</h1>
          <p className="mt-2 text-sm text-slate-500">{t('setup.subtitle')}</p>
        </div>

        <form
          onSubmit={handleSave}
          className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm"
        >
          {/* Email (read only) */}
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            {t('login.email')}
          </label>
          <div className="mb-5 flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
            <Mail className="h-4 w-4 text-slate-400" />
            {email || '—'}
          </div>

          {/* Full name */}
          <label htmlFor="setup-name" className="mb-1.5 block text-sm font-medium text-slate-700">
            {t('setup.nameLabel')}
          </label>
          <div className="relative mb-5">
            <UserRound className="pointer-events-none absolute left-3.5 top-3.5 h-4 w-4 text-slate-400" />
            <input
              id="setup-name"
              type="text"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setError('');
              }}
              placeholder={t('setup.namePlaceholder')}
              className="w-full rounded-xl border border-slate-200 py-3 pl-10 pr-4 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            />
          </div>

          {/* Business name */}
          <label
            htmlFor="setup-business"
            className="mb-1.5 block text-sm font-medium text-slate-700"
          >
            {t('setup.bizNameLabel')}
          </label>
          <div className="relative mb-5">
            <Building2 className="pointer-events-none absolute left-3.5 top-3.5 h-4 w-4 text-slate-400" />
            <input
              id="setup-business"
              type="text"
              value={businessName}
              onChange={(e) => {
                setBusinessName(e.target.value);
                setError('');
              }}
              placeholder={t('setup.bizNamePlaceholder')}
              className="w-full rounded-xl border border-slate-200 py-3 pl-10 pr-4 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            />
          </div>

          {/* Business type */}
          <label
            htmlFor="setup-biztype"
            className="mb-1.5 block text-sm font-medium text-slate-700"
          >
            {t('setup.bizTypeLabel')}
          </label>
          <select
            id="setup-biztype"
            value={businessType}
            onChange={(e) => setBusinessType(e.target.value)}
            className="mb-5 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
          >
            {BUSINESS_TYPES.map((bt) => (
              <option key={bt.value} value={bt.value}>
                {bt.label}
              </option>
            ))}
          </select>

          {/* Preferred language */}
          <label
            htmlFor="setup-language"
            className="mb-1.5 block text-sm font-medium text-slate-700"
          >
            {t('setup.langLabel')}
          </label>
          <select
            id="setup-language"
            value={language}
            onChange={(e) => setLanguage(e.target.value as 'en' | 'hi' | 'mr')}
            className="mb-6 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
          >
            <option value="en">English</option>
            <option value="hi">हिंदी</option>
            <option value="mr">मराठी</option>
          </select>

          {error && (
            <p className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={saving}
            className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-6 py-3 font-semibold text-white transition hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 disabled:opacity-60"
          >
            {saving ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                {t('setup.save')}
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handleSkip}
            className="mt-4 w-full text-center text-sm font-medium text-slate-400 transition hover:text-slate-600"
          >
            {t('setup.skip')}
          </button>
        </form>
      </div>
    </main>
  );
}
