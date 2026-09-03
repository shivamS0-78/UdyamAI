'use client';

import React from 'react';
import { useLanguageStore } from '@/stores/languageStore';

export type DashboardSection =
  | 'overview'
  | 'financial'
  | 'market'
  | 'competition'
  | 'map'
  | 'schemes'
  | 'risks'
  | 'report';

const SECTION_KEYS: { id: DashboardSection; key: string }[] = [
  { id: 'overview', key: 'dash.nav.overview' },
  { id: 'financial', key: 'dash.nav.financial' },
  { id: 'market', key: 'dash.nav.market' },
  { id: 'competition', key: 'dash.nav.competition' },
  { id: 'map', key: 'dash.nav.map' },
  { id: 'schemes', key: 'dash.nav.schemes' },
  { id: 'risks', key: 'dash.nav.risks' },
  { id: 'report', key: 'dash.nav.report' },
];

interface DashboardNavProps {
  activeSection: DashboardSection;
  onSectionChange: (section: DashboardSection) => void;
}

export default function DashboardNav({ activeSection, onSectionChange }: DashboardNavProps) {
  const t = useLanguageStore((s) => s.t);

  return (
    <nav className="border-b border-gray-200 mb-6 overflow-x-auto">
      <div className="flex gap-1 min-w-max">
        {SECTION_KEYS.map((section) => {
          const isActive = section.id === activeSection;
          return (
            <button
              key={section.id}
              onClick={() => onSectionChange(section.id)}
              className={`px-4 py-2 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
                isActive
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {t(section.key)}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
