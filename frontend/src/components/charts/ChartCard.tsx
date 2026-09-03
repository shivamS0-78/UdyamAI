'use client';

import React from 'react';

interface ChartCardProps {
  title: string;
  subtitle?: string;
  /** When real chart content is ready, pass it as children. Until then, shows a skeleton. */
  children?: React.ReactNode;
}

export default function ChartCard({ title, subtitle, children }: ChartCardProps) {
  return (
    <div className="rounded-xl border border-gray-200 p-6 bg-white">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-gray-900">{title}</h3>
        {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
      </div>

      {children ? (
        children
      ) : (
        // ---- Skeleton placeholder (no data wired up yet) ----
        <div className="h-48 flex items-end gap-2 px-2">
          {[40, 65, 30, 80, 55, 45, 70].map((height, i) => (
            <div
              key={i}
              className="flex-1 bg-gray-100 rounded-t animate-pulse"
              style={{ height: `${height}%` }}
            />
          ))}
        </div>
      )}
    </div>
  );
}