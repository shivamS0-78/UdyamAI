'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/ui/AppShell';
import Link from 'next/link';
import { getSchemes } from '@/lib/api';
import { Building2, ExternalLink, Search, Sparkles, Award, ShieldCheck, Loader2 } from 'lucide-react';
import { useLanguageStore } from '@/stores/languageStore';

interface SchemeItem {
  id: string;
  name: string;
  description?: string;
  agency_name?: string;
  state?: string;
  official_url?: string;
  active?: boolean;
}

const FEATURED_SCHEMES: SchemeItem[] = [
  {
    id: 'pmegp',
    name: 'Prime Minister’s Employment Generation Programme (PMEGP)',
    description: 'Credit-linked subsidy scheme offering 15% to 35% margin money subsidy for rural micro-enterprises across manufacturing and service sectors. Maximum project cost ₹50 Lakhs.',
    agency_name: 'KVIC / DIC Maharashtra',
    state: 'Maharashtra / All India',
    official_url: 'https://kviconline.gov.in/pmegpeportal',
    active: true,
  },
  {
    id: 'pmfme',
    name: 'PM Formalisation of Micro Food Processing Enterprises (PMFME)',
    description: '35% credit-linked capital subsidy up to ₹10 Lakhs for individual micro food processing, dairy, agro-processing, and livestock units.',
    agency_name: 'Ministry of Food Processing Industries (MoFPI)',
    state: 'Maharashtra / All India',
    official_url: 'https://pmfme.mofpi.gov.in',
    active: true,
  },
  {
    id: 'mudra',
    name: 'Pradhan Mantri MUDRA Yojana (Shishu, Kishor & Tarun)',
    description: 'Collateral-free institutional bank credit up to ₹10 Lakhs (Kishor category up to ₹5 Lakhs) for non-farm micro enterprises and rural business setups.',
    agency_name: 'MUDRA Ltd / PSU Commercial Banks',
    state: 'All India',
    official_url: 'https://www.mudra.org.in',
    active: true,
  },
  {
    id: 'didf',
    name: 'Dairy Processing & Infrastructure Development Fund (DIDF)',
    description: 'Concessional interest subvention (up to 2.5% p.a.) for milk processing plants, chilling centers, and livestock product processing units.',
    agency_name: 'NABARD / DAHD Government of India',
    state: 'All India',
    official_url: 'https://www.nabard.org',
    active: true,
  },
];

export default function SchemesPage() {
  const [schemes, setSchemes] = useState<SchemeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const t = useLanguageStore((s) => s.t);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const apiSchemes = await getSchemes();
        if (Array.isArray(apiSchemes) && apiSchemes.length > 0) {
          setSchemes(apiSchemes);
        } else {
          setSchemes(FEATURED_SCHEMES);
        }
      } catch (err) {
        console.warn('Using default featured schemes:', err);
        setSchemes(FEATURED_SCHEMES);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filteredSchemes = schemes.filter((s) => {
    const searchStr = `${s.name} ${s.description || ''} ${s.agency_name || ''}`.toLowerCase();
    return searchStr.includes(query.toLowerCase());
  });

  return (
    <AppShell>
      <main className="flex-1 max-w-5xl w-full mx-auto p-6 flex flex-col gap-6">
        {/* Banner */}
        <div className="rounded-2xl bg-gradient-to-r from-blue-950 via-slate-900 to-indigo-950 text-white p-8 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-500/20 text-blue-300 border border-blue-400/30 rounded-full text-xs font-semibold mb-3">
              <Sparkles className="h-3.5 w-3.5 text-blue-400" /> {t('schemes.badge')}
            </span>
            <h1 className="text-3xl font-extrabold tracking-tight">{t('schemes.title')}</h1>
            <p className="text-slate-300 text-sm mt-2 leading-relaxed">
              {t('schemes.desc')}
            </p>
          </div>
          <Link
            href="/onboarding"
            className="shrink-0 px-5 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm rounded-xl transition shadow-md"
          >
            {t('schemes.check')}
          </Link>
        </div>

        {/* Search & Filter Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="relative w-full sm:w-96">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t('schemes.search')}
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white text-slate-900"
            />
          </div>
          <div className="text-xs text-slate-500 font-semibold">
            Showing <span className="text-slate-900">{filteredSchemes.length}</span> verified scheme policies
          </div>
        </div>

        {/* Scheme List */}
        {loading ? (
          <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-slate-200">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-3" />
            <p className="text-sm font-medium text-slate-600">Loading government schemes directory...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredSchemes.map((s, idx) => (
              <div
                key={s.id || idx}
                className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col justify-between shadow-xs hover:shadow-md hover:border-slate-300 transition"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-2">
                      <Building2 className="h-5 w-5 text-blue-600 shrink-0" />
                      <h3 className="font-bold text-slate-900 text-base leading-snug">{s.name}</h3>
                    </div>
                    <span className="shrink-0 px-2.5 py-1 text-2xs font-bold rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                      ACTIVE
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed mb-4">
                    {s.description || 'Verified government credit assistance & subsidy scheme.'}
                  </p>
                </div>

                <div className="border-t border-slate-100 pt-3 flex items-center justify-between gap-2 text-xs">
                  {s.agency_name && (
                    <span className="text-slate-500 font-medium truncate">
                      Nodal: <strong className="text-slate-700">{s.agency_name}</strong>
                    </span>
                  )}
                  {s.official_url && (
                    <a
                      href={s.official_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 font-bold text-blue-600 hover:text-blue-800 transition"
                    >
                      Portal <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </AppShell>
  );
}
