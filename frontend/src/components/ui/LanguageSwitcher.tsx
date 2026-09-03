'use client';

import { LANGUAGE_OPTIONS, type Language } from '@/lib/i18n';
import { useLanguageStore } from '@/stores/languageStore';

export default function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const language = useLanguageStore((s) => s.language);
  const setLanguage = useLanguageStore((s) => s.setLanguage);
  const t = useLanguageStore((s) => s.t);

  return (
    <label className={`inline-flex items-center gap-1.5 ${compact ? '' : 'text-sm'}`}>
      <span className="sr-only">{t('lang.label')}</span>
      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value as Language)}
        className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs font-medium text-slate-700 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
        aria-label={t('lang.label')}
      >
        {LANGUAGE_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.nativeLabel}
          </option>
        ))}
      </select>
    </label>
  );
}
