'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowRight, Loader2, UserRound, Building2, Mail } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';
import LanguageSwitcher from '@/components/ui/LanguageSwitcher';
import Logo from '@/components/ui/Logo';
import { createProfile } from '@/lib/api';
import { storeProfile } from '@/lib/auth';
import { useLanguageStore } from '@/stores/languageStore';
import { LANGUAGE_OPTIONS, type Language } from '@/lib/i18n';

const BUSINESS_TYPES = [
  { value: '', label: 'Select business category' },
  { value: 'agriculture', label: 'Agriculture & Crops (Paddy/Wheat/Cotton)' },
  { value: 'dairy', label: 'Dairy & Cattle Farming' },
  { value: 'poultry', label: 'Poultry & Livestock' },
  { value: 'fisheries', label: 'Fisheries & Aquaculture' },
  { value: 'food_processing', label: 'Agro / Food Processing & Milling' },
  { value: 'retail', label: 'Rural Retail & Kirana Store' },
  { value: 'handloom', label: 'Handloom & Rural Handicrafts' },
  { value: 'manufacturing', label: 'Small Scale Manufacturing' },
  { value: 'services', label: 'Rural Services & Transport' },
  { value: 'other', label: 'Other Enterprise' },
];

function SetupContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const isEditing = searchParams.get('edit') === 'true';

  const t = useLanguageStore((s) => s.t);
  const language = useLanguageStore((s) => s.language);
  const setLanguage = useLanguageStore((s) => s.setLanguage);
  const { user, profile, refreshProfile } = useAuth();

  const [name, setName] = useState(profile?.name || '');
  const [businessName, setBusinessName] = useState(profile?.business_name || '');
  const [businessType, setBusinessType] = useState((profile as any)?.business_type || '');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const email = user?.email ?? profile?.email ?? '';

  // Pre-fill fields when profile is loaded
  useEffect(() => {
    if (profile) {
      if (profile.name) setName((prev: string) => prev || profile.name || '');
      if (profile.business_name) setBusinessName((prev: string) => prev || profile.business_name || '');
      if ((profile as any).business_type) setBusinessType((prev: string) => prev || (profile as any).business_type || '');
      if (profile.preferred_language) setLanguage(profile.preferred_language as Language);
    }
  }, [profile, setLanguage]);

  // If user already has a complete profile and isn't explicitly editing, redirect to dashboard
  useEffect(() => {
    if (!isEditing && profile?.name && profile?.business_name) {
      router.replace('/dashboard');
    }
  }, [profile, isEditing, router]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim() || !businessName.trim()) {
      setError(t('setup.error'));
      return;
    }

    setError('');
    setSaving(true);
    try {
      const savedProfile = await createProfile(profile?.id ?? null, {
        name: name.trim(),
        business_name: businessName.trim(),
        business_type: businessType || null,
        email: email || null,
        preferred_language: language,
      });
      storeProfile(savedProfile);
      await refreshProfile();
      router.push('/dashboard');
    } catch (err) {
      console.error('Profile setup failed:', err);
      setError(t('setup.fail'));
      setSaving(false);
    }
  };

  const handleSkip = () => {
    if (profile?.id) storeProfile(profile);
    router.push('/dashboard');
  };

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-6 py-12 glow-mesh-hero">
      {/* Background glow halos */}
      <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-blue-400/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-indigo-400/10 blur-3xl" />

      <div className="absolute right-6 top-6">
        <LanguageSwitcher />
      </div>

      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mb-4 flex justify-center">
            <Logo variant="icon" size="xl" href="/" />
          </div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-primary border border-blue-200 text-xs font-bold uppercase tracking-wider">
            {t('setup.eyebrow')}
          </span>
          <h1 className="mt-3 text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">{t('setup.title')}</h1>
          <p className="mt-2 text-xs sm:text-sm text-foreground-muted">{t('setup.subtitle')}</p>
        </div>

        <form
          onSubmit={handleSave}
          className="rounded-3xl border border-slate-200/80 bg-white p-8 sm:p-10 shadow-2xl"
        >
          {/* Email (read only) */}
          <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-foreground-muted">
            {t('login.email')}
          </label>
          <div className="mb-5 flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-foreground-muted font-medium">
            <Mail className="h-4 w-4 text-primary" />
            <span>{email || '—'}</span>
          </div>

          {/* Full name */}
          <label htmlFor="setup-name" className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-foreground-muted">
            {t('setup.nameLabel')}
          </label>
          <div className="relative mb-5">
            <UserRound className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted" />
            <input
              id="setup-name"
              type="text"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setError('');
              }}
              placeholder={t('setup.namePlaceholder')}
              className="w-full rounded-2xl border border-slate-200 bg-slate-50/50 py-3.5 pl-11 pr-4 text-sm outline-none transition focus:border-primary focus:bg-white focus:ring-2 focus:ring-primary/20 text-foreground"
            />
          </div>

          {/* Business name */}
          <label
            htmlFor="setup-business"
            className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-foreground-muted"
          >
            {t('setup.bizNameLabel')}
          </label>
          <div className="relative mb-5">
            <Building2 className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted" />
            <input
              id="setup-business"
              type="text"
              value={businessName}
              onChange={(e) => {
                setBusinessName(e.target.value);
                setError('');
              }}
              placeholder={t('setup.bizNamePlaceholder')}
              className="w-full rounded-2xl border border-slate-200 bg-slate-50/50 py-3.5 pl-11 pr-4 text-sm outline-none transition focus:border-primary focus:bg-white focus:ring-2 focus:ring-primary/20 text-foreground"
            />
          </div>

          {/* Business type */}
          <label
            htmlFor="setup-biztype"
            className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-foreground-muted"
          >
            {t('setup.bizTypeLabel')}
          </label>
          <select
            id="setup-biztype"
            value={businessType}
            onChange={(e) => setBusinessType(e.target.value)}
            className="mb-5 w-full rounded-2xl border border-slate-200 bg-slate-50/50 px-4 py-3.5 text-sm outline-none transition focus:border-primary focus:bg-white focus:ring-2 focus:ring-primary/20 text-foreground"
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
            className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-foreground-muted"
          >
            {t('setup.langLabel')}
          </label>
          <select
            id="setup-language"
            value={language}
            onChange={(e) => setLanguage(e.target.value as Language)}
            className="mb-6 w-full rounded-2xl border border-slate-200 bg-slate-50/50 px-4 py-3.5 text-sm outline-none transition focus:border-primary focus:bg-white focus:ring-2 focus:ring-primary/20 text-foreground"
          >
            {LANGUAGE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.nativeLabel} ({opt.englishLabel})
              </option>
            ))}
          </select>

          {error && (
            <p className="mb-4 rounded-2xl border border-rose-200 bg-rose-50 p-3.5 text-xs sm:text-sm font-semibold text-rose-700">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={saving}
            className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-primary px-6 py-4 font-bold text-white shadow-fintech-btn transition-all duration-200 hover:bg-primary-600 hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-60"
          >
            {saving ? (
              <Loader2 className="h-5 w-5 animate-spin" />
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
            className="mt-4 w-full text-center text-xs font-bold text-foreground-muted transition hover:text-primary"
          >
            {t('setup.skip')}
          </button>
        </form>
      </div>
    </main>
  );
}

export default function SetupPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-background">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      }
    >
      <SetupContent />
    </Suspense>
  );
}
