'use client';

import { create } from 'zustand';
import {
  isLanguage,
  LANGUAGE_STORAGE_KEY,
  translate,
  type Language,
} from '@/lib/i18n';

interface LanguageState {
  language: Language;
  hydrated: boolean;
  setLanguage: (language: Language) => void;
  hydrate: () => void;
  t: (key: string) => string;
}

export const useLanguageStore = create<LanguageState>((set) => ({
  language: 'en',
  hydrated: false,
  t: (key: string) => translate('en', key),
  setLanguage: (language) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
      document.documentElement.lang = language;
    }
    set({ language, t: (key: string) => translate(language, key) });
  },
  hydrate: () => {
    if (typeof window === 'undefined') return;
    const stored = localStorage.getItem(LANGUAGE_STORAGE_KEY);
    const language = isLanguage(stored) ? stored : 'en';
    document.documentElement.lang = language;
    set({ language, hydrated: true, t: (key: string) => translate(language, key) });
  },
}));
