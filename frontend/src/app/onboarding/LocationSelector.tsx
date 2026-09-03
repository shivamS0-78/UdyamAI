'use client';

import { useEffect, useState } from 'react';
import { MapPin, Loader2 } from 'lucide-react';
import { getDistricts, getTalukas, getVillages, District, Taluka, Village } from '@/lib/api';
import { useLanguageStore } from '@/stores/languageStore';

interface LocationSelectorProps {
  districtId: string;
  talukaId: string;
  villageId: string;
  setDistrictId: (id: string, name?: string) => void;
  setTalukaId: (id: string, name?: string) => void;
  setVillageId: (id: string, name?: string) => void;
}

export default function LocationSelector({
  districtId,
  talukaId,
  villageId,
  setDistrictId,
  setTalukaId,
  setVillageId,
}: LocationSelectorProps) {
  const [districts, setDistricts] = useState<District[]>([]);
  const [talukas, setTalukas] = useState<Taluka[]>([]);
  const [villages, setVillages] = useState<Village[]>([]);
  const [loadingDistricts, setLoadingDistricts] = useState(true);
  const [loadingTalukas, setLoadingTalukas] = useState(false);
  const [loadingVillages, setLoadingVillages] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const t = useLanguageStore((s) => s.t);

  // Load Districts on mount
  useEffect(() => {
    async function loadDistricts() {
      setLoadingDistricts(true);
      setLoadError(null);
      try {
        const apiDistricts = await getDistricts();
        setDistricts(apiDistricts);
        if (apiDistricts.length === 0) {
          setLoadError(t('onboard.noDistricts'));
        }
      } catch {
        setLoadError(t('onboard.failDistricts'));
      } finally {
        setLoadingDistricts(false);
      }
    }
    loadDistricts();
  }, []);

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
        setTalukas(apiTalukas);
      } catch {
        setTalukas([]);
      } finally {
        setLoadingTalukas(false);
      }
    }
    loadTalukas();
  }, [districtId]);

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
        setVillages(apiVillages);
      } catch {
        setVillages([]);
      } finally {
        setLoadingVillages(false);
      }
    }
    loadVillages();
  }, [talukaId]);

  return (
    <div className="flex gap-4">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
        <MapPin size={21} aria-hidden="true" />
      </div>

      <div className="w-full">
        <h4 className="font-semibold text-slate-900">
          {t('onboard.locTitle')}
        </h4>

        <p className="mt-1 text-sm text-slate-500">
          {t('onboard.locDesc')}
        </p>
        {loadError && <p className="mt-2 text-sm text-red-600">{loadError}</p>}

        <div className="mt-4 space-y-3">
          {/* District Selector */}
          <div className="relative">
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
              className="w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-500 disabled:bg-slate-100"
            >
              <option value="">
                {loadingDistricts ? t('onboard.loadingDistricts') : t('onboard.selectDistrict')}
              </option>
              {districts.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            {loadingDistricts && (
              <Loader2 className="absolute right-3 top-3.5 h-4 w-4 animate-spin text-slate-400" />
            )}
          </div>

          {/* Taluka Selector */}
          <div className="relative">
            <select
              value={talukaId}
              onChange={(e) => {
                const id = e.target.value;
                const found = talukas.find((t) => t.id === id);
                setTalukaId(id, found?.name || '');
                setVillageId('', '');
              }}
              disabled={!districtId || loadingTalukas}
              className="w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-500 disabled:bg-slate-100"
            >
              <option value="">
                {loadingTalukas ? t('onboard.loadingTalukas') : t('onboard.selectTaluka')}
              </option>
              {talukas.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            {loadingTalukas && (
              <Loader2 className="absolute right-3 top-3.5 h-4 w-4 animate-spin text-slate-400" />
            )}
          </div>

          {/* Village Selector */}
          <div className="relative">
            <select
              value={villageId}
              onChange={(e) => {
                const id = e.target.value;
                const found = villages.find((v) => v.id === id);
                setVillageId(id, found?.name || '');
              }}
              disabled={!talukaId || loadingVillages}
              className="w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-500 disabled:bg-slate-100"
            >
              <option value="">
                {loadingVillages ? t('onboard.loadingVillages') : t('onboard.selectVillage')}
              </option>
              {villages.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            {loadingVillages && (
              <Loader2 className="absolute right-3 top-3.5 h-4 w-4 animate-spin text-slate-400" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}