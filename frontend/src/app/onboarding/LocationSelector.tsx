'use client';

import { useEffect, useState } from 'react';
import { MapPin, Loader2, Sparkles, Building } from 'lucide-react';
import { getDistricts, getTalukas, getVillages, District, Taluka, Village } from '@/lib/api';
import { INDIAN_STATES, StateInfo } from '@/lib/states';
import { useLanguageStore } from '@/stores/languageStore';

interface LocationSelectorProps {
  districtId: string;
  talukaId: string;
  villageId: string;
  setDistrictId: (id: string, name?: string) => void;
  setTalukaId: (id: string, name?: string) => void;
  setVillageId: (id: string, name?: string) => void;
  stateCode?: string;
  setStateCode?: (code: string, name?: string) => void;
}

export default function LocationSelector({
  districtId,
  talukaId,
  villageId,
  setDistrictId,
  setTalukaId,
  setVillageId,
  stateCode = 'MH',
  setStateCode,
}: LocationSelectorProps) {
  const [selectedStateCode, setSelectedStateCode] = useState<string>(stateCode || 'MH');
  const [districts, setDistricts] = useState<District[]>([]);
  const [talukas, setTalukas] = useState<Taluka[]>([]);
  const [villages, setVillages] = useState<Village[]>([]);
  const [loadingDistricts, setLoadingDistricts] = useState(true);
  const [loadingTalukas, setLoadingTalukas] = useState(false);
  const [loadingVillages, setLoadingVillages] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const t = useLanguageStore((s) => s.t);

  const currentState = INDIAN_STATES.find((s) => s.code === selectedStateCode) || INDIAN_STATES[0];

  // Load Districts on mount or when state changes
  useEffect(() => {
    async function loadDistricts() {
      setLoadingDistricts(true);
      setLoadError(null);
      try {
        const apiDistricts = await getDistricts();
        if (apiDistricts.length > 0) {
          // If districts have state metadata, filter by selected state
          const filtered = apiDistricts.filter(
            (d) => !d.state || d.state.toLowerCase() === currentState.name.toLowerCase() || d.state.toUpperCase() === selectedStateCode
          );
          setDistricts(filtered.length > 0 ? filtered : apiDistricts);
        } else {
          // Fallback to canonical state districts
          setDistricts(currentState.defaultDistricts.map((d) => ({ id: d.id, name: d.name, state: currentState.name })));
        }
      } catch {
        // Use fallback state districts
        setDistricts(currentState.defaultDistricts.map((d) => ({ id: d.id, name: d.name, state: currentState.name })));
      } finally {
        setLoadingDistricts(false);
      }
    }
    loadDistricts();
  }, [selectedStateCode, currentState]);

  // Load Talukas when districtId changes
  useEffect(() => {
    if (!districtId) {
      setTalukas([]);
      return;
    }
    async function loadTalukas() {
      setLoadingTalukas(true);
      try {
        const apiTalukas = await getTalukas(districtId);
        if (apiTalukas && apiTalukas.length > 0) {
          setTalukas(apiTalukas);
        } else {
          // Fallback taluka based on district name
          const distObj = districts.find((d) => d.id === districtId);
          const distName = distObj?.name || 'Central';
          setTalukas([
            { id: `tal-${districtId}-1`, name: `${distName} Rural`, district_id: districtId },
            { id: `tal-${districtId}-2`, name: `${distName} East`, district_id: districtId },
          ]);
        }
      } catch {
        setTalukas([
          { id: `tal-${districtId}-1`, name: `Taluka 1`, district_id: districtId },
        ]);
      } finally {
        setLoadingTalukas(false);
      }
    }
    loadTalukas();
  }, [districtId, districts]);

  // Load Villages when talukaId changes
  useEffect(() => {
    if (!talukaId) {
      setVillages([]);
      return;
    }
    async function loadVillages() {
      setLoadingVillages(true);
      try {
        const apiVillages = await getVillages(talukaId);
        if (apiVillages && apiVillages.length > 0) {
          setVillages(apiVillages);
        } else {
          // Fallback village based on taluka name
          const talObj = talukas.find((t) => t.id === talukaId);
          const talName = talObj?.name || 'Village';
          setVillages([
            { id: `vil-${talukaId}-1`, name: `${talName} Gram`, taluka_id: talukaId },
            { id: `vil-${talukaId}-2`, name: `${talName} Kalan`, taluka_id: talukaId },
          ]);
        }
      } catch {
        setVillages([
          { id: `vil-${talukaId}-1`, name: `Sample Village`, taluka_id: talukaId },
        ]);
      } finally {
        setLoadingVillages(false);
      }
    }
    loadVillages();
  }, [talukaId, talukas]);

  const handleStateChange = (newCode: string) => {
    setSelectedStateCode(newCode);
    const stateObj = INDIAN_STATES.find((s) => s.code === newCode);
    if (setStateCode) {
      setStateCode(newCode, stateObj?.name);
    }
    setDistrictId('', '');
    setTalukaId('', '');
    setVillageId('', '');
  };

  return (
    <div className="flex gap-4">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary border border-primary/20 shadow-sm">
        <MapPin size={20} aria-hidden="true" />
      </div>

      <div className="w-full">
        <div className="flex items-center justify-between">
          <h4 className="font-bold text-foreground text-sm sm:text-base">
            {t('onboard.locTitle') || 'Location & Geographic Feasibility'}
          </h4>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-semibold border border-emerald-200 dark:border-emerald-800">
            {currentState.name} ({currentState.code})
          </span>
        </div>

        <p className="mt-0.5 text-xs text-foreground-muted">
          {t('onboard.locDesc') || 'Select state, district, taluka, and village for localized market benchmarks.'}
        </p>
        {loadError && <p className="mt-2 text-xs font-semibold text-rose-600 dark:text-rose-400">{loadError}</p>}

        <div className="mt-4 space-y-3">
          {/* State Selector */}
          <div>
            <label className="block text-xs font-semibold text-foreground-muted mb-1 flex items-center gap-1.5">
              <Building className="h-3.5 w-3.5 text-primary" /> State / Union Territory
            </label>
            <select
              value={selectedStateCode}
              onChange={(e) => handleStateChange(e.target.value)}
              className="w-full rounded-2xl border border-slate-200 dark:border-[#2B313C] bg-slate-50/50 dark:bg-[#1C2128] px-4 py-3 text-sm outline-none transition focus:border-primary focus:bg-white dark:focus:bg-[#222731] focus:ring-2 focus:ring-primary/20 text-foreground font-medium"
            >
              {INDIAN_STATES.map((st) => (
                <option key={st.code} value={st.code} className="bg-white dark:bg-[#1C2128] text-foreground">
                  {st.name} ({st.code})
                </option>
              ))}
            </select>
          </div>

          {/* District Selector */}
          <div className="relative">
            <label className="block text-xs font-semibold text-foreground-muted mb-1">District</label>
            <select
              value={districtId}
              onChange={(e) => {
                const id = e.target.value;
                const found = districts.find((d) => d.id === id);
                setDistrictId(id, found?.name || '');
                setTalukaId('', '');
                setVillageId('', '');
              }}
              disabled={loadingDistricts}
              className="w-full rounded-2xl border border-slate-200 dark:border-[#2B313C] bg-slate-50/50 dark:bg-[#1C2128] px-4 py-3 text-sm outline-none transition focus:border-primary focus:bg-white dark:focus:bg-[#222731] focus:ring-2 focus:ring-primary/20 disabled:bg-slate-100 dark:disabled:bg-[#161B22] text-foreground font-medium"
            >
              <option value="">
                {loadingDistricts ? t('onboard.loadingDistricts') : (t('onboard.selectDistrict') || `Select District in ${currentState.name}`)}
              </option>
              {districts.map((item) => (
                <option key={item.id} value={item.id} className="bg-white dark:bg-[#1C2128] text-foreground">
                  {item.name}
                </option>
              ))}
            </select>
            {loadingDistricts && (
              <Loader2 className="absolute right-3.5 top-9 h-4 w-4 animate-spin text-primary" />
            )}
          </div>

          {/* Taluka Selector */}
          <div className="relative">
            <label className="block text-xs font-semibold text-foreground-muted mb-1">Taluka / Block</label>
            <select
              value={talukaId}
              onChange={(e) => {
                const id = e.target.value;
                const found = talukas.find((t) => t.id === id);
                setTalukaId(id, found?.name || '');
                setVillageId('', '');
              }}
              disabled={!districtId || loadingTalukas}
              className="w-full rounded-2xl border border-slate-200 dark:border-[#2B313C] bg-slate-50/50 dark:bg-[#1C2128] px-4 py-3 text-sm outline-none transition focus:border-primary focus:bg-white dark:focus:bg-[#222731] focus:ring-2 focus:ring-primary/20 disabled:bg-slate-100 dark:disabled:bg-[#161B22] text-foreground font-medium"
            >
              <option value="">
                {loadingTalukas ? t('onboard.loadingTalukas') : (t('onboard.selectTaluka') || 'Select Taluka / Block')}
              </option>
              {talukas.map((item) => (
                <option key={item.id} value={item.id} className="bg-white dark:bg-[#1C2128] text-foreground">
                  {item.name}
                </option>
              ))}
            </select>
            {loadingTalukas && (
              <Loader2 className="absolute right-3.5 top-9 h-4 w-4 animate-spin text-primary" />
            )}
          </div>

          {/* Village Selector */}
          <div className="relative">
            <label className="block text-xs font-semibold text-foreground-muted mb-1">Village / Gram Panchayat</label>
            <select
              value={villageId}
              onChange={(e) => {
                const id = e.target.value;
                const found = villages.find((v) => v.id === id);
                setVillageId(id, found?.name || '');
              }}
              disabled={!talukaId || loadingVillages}
              className="w-full rounded-2xl border border-slate-200 dark:border-[#2B313C] bg-slate-50/50 dark:bg-[#1C2128] px-4 py-3 text-sm outline-none transition focus:border-primary focus:bg-white dark:focus:bg-[#222731] focus:ring-2 focus:ring-primary/20 disabled:bg-slate-100 dark:disabled:bg-[#161B22] text-foreground font-medium"
            >
              <option value="">
                {loadingVillages ? t('onboard.loadingVillages') : (t('onboard.selectVillage') || 'Select Village / Town')}
              </option>
              {villages.map((item) => (
                <option key={item.id} value={item.id} className="bg-white dark:bg-[#1C2128] text-foreground">
                  {item.name}
                </option>
              ))}
            </select>
            {loadingVillages && (
              <Loader2 className="absolute right-3.5 top-9 h-4 w-4 animate-spin text-primary" />
            )}
          </div>

          {/* State Priority Sector Highlight */}
          {currentState.prioritySectors.length > 0 && (
            <div className="mt-3 p-3 rounded-2xl bg-slate-50 dark:bg-[#161B22] border border-slate-200 dark:border-[#2B313C]">
              <span className="text-[11px] font-bold text-foreground-muted flex items-center gap-1 mb-1.5">
                <Sparkles className="h-3 w-3 text-amber-500" /> High-Growth Priority Sectors in {currentState.name}:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {currentState.prioritySectors.map((sector, idx) => (
                  <span
                    key={idx}
                    className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-white dark:bg-[#1C2128] border border-slate-200 dark:border-[#2B313C] text-foreground-muted shadow-2xs"
                  >
                    {sector}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}