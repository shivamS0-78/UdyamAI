'use client';

import { useEffect } from 'react';
import { useLanguageStore } from '@/stores/languageStore';

export default function LanguageProvider({ children }: { children: React.ReactNode }) {
  const hydrate = useLanguageStore((s) => s.hydrate);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  return <>{children}</>;
}
