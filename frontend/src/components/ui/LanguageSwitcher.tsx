'use client';

import React, { useState, useRef, useEffect } from 'react';
import { LANGUAGE_OPTIONS, type Language } from '@/lib/i18n';
import { useLanguageStore } from '@/stores/languageStore';
import { Globe, Check, ChevronDown } from 'lucide-react';

const SCRIPT_BADGES: Record<string, string> = {
  en: 'EN',
  hi: 'हिं',
  mr: 'म',
  ta: 'த',
  te: 'తె',
  kn: 'ಕ',
  gu: 'ગુ',
  bn: 'বা',
  pa: 'ਪੰ',
  ml: 'മ',
};

export default function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const language = useLanguageStore((s) => s.language);
  const setLanguage = useLanguageStore((s) => s.setLanguage);
  const t = useLanguageStore((s) => s.t);
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentOption = LANGUAGE_OPTIONS.find((opt) => opt.value === language) || LANGUAGE_OPTIONS[0];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpen(false);
      }
    };

    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open]);

  return (
    <div className="relative inline-flex items-center" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className={`inline-flex items-center gap-2 rounded-full border border-border bg-[#F6F7F9] dark:bg-[#1C2128] text-foreground font-semibold transition hover:bg-neutral-100 dark:hover:bg-[#272D37] hover:border-primary/40 focus:outline-none focus:ring-2 focus:ring-primary/20 shadow-sm ${
          compact ? 'px-3 py-1.5 text-xs' : 'px-4 py-2 text-sm'
        }`}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={t('lang.label')}
      >
        <Globe className="h-3.5 w-3.5 text-primary shrink-0" />
        <span className="truncate">
          {compact ? currentOption.nativeLabel : `${currentOption.nativeLabel} (${currentOption.englishLabel})`}
        </span>
        <ChevronDown className={`h-3 w-3 text-foreground-muted transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div
          role="listbox"
          className="absolute right-0 top-full mt-2 z-50 w-64 max-h-80 overflow-y-auto rounded-2xl border border-border bg-white dark:bg-[#1C2128] p-1.5 shadow-xl backdrop-blur-md animate-in fade-in zoom-in-95 duration-150"
        >
          <div className="sticky top-0 bg-white dark:bg-[#1C2128] px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-wider text-foreground-muted border-b border-border/70 mb-1 flex items-center justify-between z-10">
            <span>{t('lang.label')}</span>
            <span className="text-[10px] font-normal lowercase opacity-75">{LANGUAGE_OPTIONS.length} Available</span>
          </div>

          <div className="space-y-0.5">
            {LANGUAGE_OPTIONS.map((opt) => {
              const isSelected = opt.value === language;
              return (
                <button
                  key={opt.value}
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  onClick={() => {
                    setLanguage(opt.value as Language);
                    setOpen(false);
                  }}
                  className={`w-full flex items-center justify-between gap-2 px-3 py-2 rounded-xl text-xs font-medium transition ${
                    isSelected
                      ? 'bg-primary/10 text-primary dark:bg-primary/20 dark:text-emerald-400 font-bold'
                      : 'text-foreground hover:bg-neutral-100 dark:hover:bg-[#272D37]'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`inline-flex items-center justify-center w-6 h-6 rounded-lg text-[11px] font-bold ${
                        isSelected
                          ? 'bg-primary text-white shadow-xs'
                          : 'bg-neutral-100 dark:bg-neutral-800 text-foreground-muted'
                      }`}
                    >
                      {SCRIPT_BADGES[opt.value] || opt.value.toUpperCase()}
                    </span>
                    <div className="text-left">
                      <p className="font-semibold">{opt.nativeLabel}</p>
                      <p className="text-[10px] text-foreground-muted">{opt.englishLabel}</p>
                    </div>
                  </div>

                  {isSelected && <Check className="h-4 w-4 text-primary shrink-0" />}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
