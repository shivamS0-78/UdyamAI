'use client';

import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Circle, CircleMarker, Popup, useMap } from 'react-leaflet';
import type {
  NearbyBusiness,
  NearbyFacility,
  NearbyMarket,
  NearbyVillage,
} from '@/lib/api';
import { formatKm } from '@/lib/api';

export interface MapLayers {
  markets: boolean;
  businesses: boolean;
  facilities: boolean;
  villages: boolean;
  radius5: boolean;
  radius10: boolean;
}

interface LocationMapProps {
  center: [number, number];
  villageName: string;
  markets: NearbyMarket[];
  businesses: NearbyBusiness[];
  directCompetitorCategoryId?: string;
  facilities: NearbyFacility[];
  villages: NearbyVillage[];
  layers: MapLayers;
}

function MapViewController({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, map.getZoom());
  }, [center, map]);
  return null;
}

function hasCoords(lat?: number | null, lng?: number | null): lat is number {
  return lat != null && lng != null;
}

export default function LocationMap({
  center,
  villageName,
  markets,
  businesses,
  directCompetitorCategoryId,
  facilities,
  villages,
  layers,
}: LocationMapProps) {
  return (
    <MapContainer
      center={center}
      zoom={11}
      scrollWheelZoom
      className="h-full w-full z-0"
      style={{ minHeight: '420px' }}
    >
      <MapViewController center={center} />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {layers.radius5 && (
        <Circle
          center={center}
          radius={5000}
          pathOptions={{ color: '#3b82f6', fillColor: '#3b82f6', fillOpacity: 0.06, weight: 2 }}
        />
      )}
      {layers.radius10 && (
        <Circle
          center={center}
          radius={10000}
          pathOptions={{ color: '#6366f1', fillColor: '#6366f1', fillOpacity: 0.04, weight: 2, dashArray: '6 4' }}
        />
      )}

      <CircleMarker
        center={center}
        radius={10}
        pathOptions={{ color: '#1d4ed8', fillColor: '#2563eb', fillOpacity: 1, weight: 2 }}
      >
        <Popup>
          <strong>{villageName}</strong>
          <br />
          Selected business location
        </Popup>
      </CircleMarker>

      {layers.markets &&
        markets
          .filter((m) => hasCoords(m.latitude, m.longitude))
          .map((m) => (
            <CircleMarker
              key={`market-${m.id}`}
              center={[m.latitude!, m.longitude!]}
              radius={7}
              pathOptions={{ color: '#15803d', fillColor: '#22c55e', fillOpacity: 0.9, weight: 2 }}
            >
              <Popup>
                <strong>{m.name || 'APMC Mandi'}</strong>
                <br />
                Type: {m.market_type || 'Market'}
                <br />
                Distance: {formatKm(m.distance_meters)}
              </Popup>
            </CircleMarker>
          ))}

      {layers.businesses &&
        businesses
          .filter((b) => hasCoords(b.latitude, b.longitude))
          .map((b) => {
            const isDirect =
              !directCompetitorCategoryId ||
              b.business_category_id === directCompetitorCategoryId;
            return (
            <CircleMarker
              key={`business-${b.id}`}
              center={[b.latitude!, b.longitude!]}
              radius={isDirect ? 7 : 5}
              pathOptions={
                isDirect
                  ? { color: '#b91c1c', fillColor: '#ef4444', fillOpacity: 0.95, weight: 2 }
                  : { color: '#c2410c', fillColor: '#f97316', fillOpacity: 0.85, weight: 2 }
              }
            >
              <Popup>
                <strong>{b.name || 'MSME Cluster'}</strong>
                <br />
                {b.category && <>Category: {b.category}<br /></>}
                {isDirect ? 'Direct competitor' : 'Other MSME cluster'}
                <br />
                Distance: {formatKm(b.distance_meters)}
              </Popup>
            </CircleMarker>
            );
          })}

      {layers.facilities &&
        facilities
          .filter((f) => hasCoords(f.latitude, f.longitude))
          .map((f) => (
            <CircleMarker
              key={`facility-${f.id}`}
              center={[f.latitude!, f.longitude!]}
              radius={6}
              pathOptions={{ color: '#1e40af', fillColor: '#3b82f6', fillOpacity: 0.9, weight: 2 }}
            >
              <Popup>
                <strong>{f.name || 'Infrastructure'}</strong>
                <br />
                Type: {f.facility_type || 'Facility'}
                <br />
                Distance: {formatKm(f.distance_meters)}
              </Popup>
            </CircleMarker>
          ))}

      {layers.villages &&
        villages
          .filter((v) => hasCoords(v.latitude, v.longitude))
          .map((v) => (
            <CircleMarker
              key={`village-${v.id}`}
              center={[v.latitude!, v.longitude!]}
              radius={4}
              pathOptions={{ color: '#6b7280', fillColor: '#9ca3af', fillOpacity: 0.8, weight: 1 }}
            >
              <Popup>
                <strong>{v.name}</strong>
                <br />
                {v.pin_code && <>PIN: {v.pin_code}<br /></>}
                Distance: {formatKm(v.distance_meters)}
              </Popup>
            </CircleMarker>
          ))}
    </MapContainer>
  );
}
