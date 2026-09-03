'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { Loader2, MapPin } from 'lucide-react';
import {
  ConsolidatedAnalysisData,
  getNearbyBusinesses,
  getNearbyFacilities,
  getNearbyMarkets,
  getNearbyVillages,
  NearbyBusiness,
  NearbyFacility,
  NearbyMarket,
  NearbyVillage,
} from '@/lib/api';
import type { MapLayers } from './LocationMap';

const LocationMap = dynamic(() => import('./LocationMap'), {
  ssr: false,
  loading: () => (
    <div className="h-[420px] bg-gray-50 flex items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
    </div>
  ),
});

interface MapContainerProps {
  title?: string;
  data: ConsolidatedAnalysisData;
}

const DEFAULT_LAYERS: MapLayers = {
  markets: true,
  businesses: true,
  facilities: true,
  villages: false,
  radius5: true,
  radius10: true,
};

export default function MapContainer({
  title = 'Location Map',
  data,
}: MapContainerProps) {
  const [markets, setMarkets] = useState<NearbyMarket[]>([]);
  const [businesses, setBusinesses] = useState<NearbyBusiness[]>([]);
  const [facilities, setFacilities] = useState<NearbyFacility[]>([]);
  const [villages, setVillages] = useState<NearbyVillage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [layers, setLayers] = useState<MapLayers>(DEFAULT_LAYERS);

  const lat = data.location?.latitude;
  const lng = data.location?.longitude;
  const villageName =
    data.location?.village_name || data.location?.name || 'Selected Village';
  const categoryId = data.business?.category_id;
  const directCompetitors = categoryId
    ? businesses.filter((b) => b.business_category_id === categoryId)
    : businesses;

  useEffect(() => {
    if (lat == null || lng == null) {
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function loadMapData() {
      try {
        setLoading(true);
        setError(null);
        const [marketsRes, businessesRes, facilitiesRes, villagesRes] = await Promise.all([
          getNearbyMarkets(lat!, lng!, 25),
          getNearbyBusinesses(lat!, lng!, 25),
          getNearbyFacilities(lat!, lng!, 10),
          getNearbyVillages(lat!, lng!, 10),
        ]);
        if (!cancelled) {
          setMarkets(marketsRes);
          setBusinesses(businessesRes);
          setFacilities(facilitiesRes);
          setVillages(villagesRes);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load map data');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadMapData();
    return () => {
      cancelled = true;
    };
  }, [lat, lng]);

  function toggleLayer(key: keyof MapLayers) {
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  const locLabel = [
    villageName,
    data.location?.taluka_name,
    data.location?.district_name,
  ]
    .filter(Boolean)
    .join(', ');

  return (
    <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
      <div className="px-6 py-4 border-b border-gray-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 className="text-base font-semibold text-gray-900">{title}</h3>
          {locLabel && (
            <p className="text-sm text-gray-500 flex items-center gap-1 mt-0.5">
              <MapPin className="h-3.5 w-3.5" />
              {locLabel}
            </p>
          )}
        </div>
        {!loading && lat != null && lng != null && (
          <div className="flex flex-wrap gap-3 text-xs text-gray-600">
            <span className="flex items-center gap-1">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-green-500" />
              {markets.length} mandis
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-red-500" />
              {directCompetitors.length} direct / {businesses.length} MSME
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-blue-500" />
              {facilities.length} facilities
            </span>
          </div>
        )}
      </div>

      {lat == null || lng == null ? (
        <div className="h-[420px] bg-gray-50 flex flex-col items-center justify-center gap-2 text-gray-400 px-6 text-center">
          <MapPin className="h-10 w-10" />
          <p className="text-sm">No coordinates available for this location.</p>
          <p className="text-xs text-gray-400">
            Re-run analysis with a village that has latitude/longitude data.
          </p>
        </div>
      ) : loading ? (
        <div className="h-[420px] bg-gray-50 flex flex-col items-center justify-center gap-2 text-gray-500">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <p className="text-sm">Loading spatial data from API...</p>
        </div>
      ) : error ? (
        <div className="h-[420px] bg-red-50 flex flex-col items-center justify-center gap-2 text-red-600 px-6 text-center">
          <p className="text-sm font-medium">Could not load map data</p>
          <p className="text-xs">{error}</p>
        </div>
      ) : (
        <>
          <div className="px-4 py-3 border-b border-gray-100 bg-slate-50 flex flex-wrap gap-x-4 gap-y-2">
            {(
              [
                ['markets', 'APMC Mandis', 'bg-green-500'],
                ['businesses', 'Competitors', 'bg-red-500'],
                ['facilities', 'Infrastructure', 'bg-blue-500'],
                ['villages', 'Nearby Villages', 'bg-gray-400'],
                ['radius5', '5 km radius', 'border-2 border-blue-500 bg-transparent'],
                ['radius10', '10 km radius', 'border-2 border-dashed border-indigo-500 bg-transparent'],
              ] as const
            ).map(([key, label, colorClass]) => (
              <label key={key} className="flex items-center gap-1.5 text-xs text-gray-700 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={layers[key]}
                  onChange={() => toggleLayer(key)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className={`inline-block w-2.5 h-2.5 rounded-full ${colorClass}`} />
                {label}
              </label>
            ))}
          </div>
          <div className="h-[420px] relative">
            {businesses.length === 0 && (
              <div className="absolute top-3 left-3 right-3 z-[500] rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800 shadow-sm">
                No MSME competitor records found within 25 km. Import business data with{' '}
                <code className="font-mono">python scripts/data/import_businesses.py --file data/raw/businesses/maharashtra_msme_clusters.csv</code>
              </div>
            )}
            <LocationMap
              center={[lat, lng]}
              villageName={villageName}
              markets={markets}
              businesses={businesses}
              directCompetitorCategoryId={categoryId}
              facilities={facilities}
              villages={villages}
              layers={layers}
            />
          </div>
          <div className="px-4 py-2 border-t border-gray-100 bg-slate-50 text-xs text-gray-500">
            Data sourced from UdyamAI PostGIS — APMC mandis &amp; MSME clusters (25 km), infrastructure (10 km).
            Red markers are direct competitors in your business category.
          </div>
        </>
      )}
    </div>
  );
}
