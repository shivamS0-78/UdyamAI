'use client';

import React, { useEffect } from 'react';
import { Circle, MapContainer as LeafletMap, Popup, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';

export type MapPointKind = 'village' | 'market' | 'business' | 'facility';

export interface MapPoint {
  id: string;
  lat: number;
  lng: number;
  label: string;
  kind: MapPointKind;
  subtitle?: string;
  distanceKm?: number;
}

export interface SpatialMapViewProps {
  center: { lat: number; lng: number; label: string };
  points: MapPoint[];
  analysisRadiusKm?: number;
  marketRadiusKm?: number;
}

const KIND_STYLES: Record<MapPointKind, { color: string; fill: string; radius: number }> = {
  village: { color: '#1d4ed8', fill: '#3b82f6', radius: 10 },
  market: { color: '#15803d', fill: '#22c55e', radius: 8 },
  business: { color: '#c2410c', fill: '#f97316', radius: 7 },
  facility: { color: '#7e22ce', fill: '#a855f7', radius: 7 },
};

function FitBounds({ center, points }: { center: { lat: number; lng: number }; points: MapPoint[] }) {
  const map = useMap();

  useEffect(() => {
    const coords: L.LatLngExpression[] = [[center.lat, center.lng]];
    for (const point of points) {
      coords.push([point.lat, point.lng]);
    }
    if (coords.length === 1) {
      map.setView([center.lat, center.lng], 11);
      return;
    }
    map.fitBounds(L.latLngBounds(coords), { padding: [36, 36], maxZoom: 13 });
  }, [map, center.lat, center.lng, points]);

  return null;
}

function formatDistance(km?: number) {
  if (km == null) return null;
  return km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(1)} km`;
}

export default function SpatialMapView({
  center,
  points,
  analysisRadiusKm = 10,
  marketRadiusKm = 25,
}: SpatialMapViewProps) {
  const markers = points.filter((p) => p.kind !== 'village');

  return (
    <LeafletMap
      center={[center.lat, center.lng]}
      zoom={11}
      scrollWheelZoom
      className="h-full w-full z-0"
      style={{ minHeight: '22rem' }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds center={center} points={markers} />

      <Circle
        center={[center.lat, center.lng]}
        radius={analysisRadiusKm * 1000}
        pathOptions={{ color: '#3b82f6', fillColor: '#3b82f6', fillOpacity: 0.06, weight: 1.5 }}
      />
      <Circle
        center={[center.lat, center.lng]}
        radius={marketRadiusKm * 1000}
        pathOptions={{ color: '#22c55e', fillColor: '#22c55e', fillOpacity: 0.03, weight: 1, dashArray: '6 4' }}
      />

      {points.map((point) => {
        const style = KIND_STYLES[point.kind];
        return (
          <Circle
            key={point.id}
            center={[point.lat, point.lng]}
            radius={style.radius * 120}
            pathOptions={{
              color: style.color,
              fillColor: style.fill,
              fillOpacity: 0.9,
              weight: 2,
            }}
          >
            <Popup>
              <div className="text-sm">
                <p className="font-semibold text-slate-900">{point.label}</p>
                {point.subtitle && <p className="text-slate-600 mt-0.5">{point.subtitle}</p>}
                {point.distanceKm != null && (
                  <p className="text-slate-500 mt-1">{formatDistance(point.distanceKm)} from village</p>
                )}
              </div>
            </Popup>
          </Circle>
        );
      })}
    </LeafletMap>
  );
}
