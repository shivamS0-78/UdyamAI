'use client';

import { ArrowRight, MapPin, Store } from 'lucide-react';
import { useLanguageStore } from '@/stores/languageStore';

interface ReviewScreenProps {
  district: string;
  taluka: string;
  village: string;
  business: string;
  capital: string;
  desiredProjectCost: string;
  language: string;
  error?: string;
  onEdit: () => void;
  onStartAnalysis: () => void;
}

export default function ReviewScreen({
  district,
  taluka,
  village,
  business,
  capital,
  desiredProjectCost,
  language,
  error,
  onEdit,
  onStartAnalysis,
}: ReviewScreenProps) {
  const t = useLanguageStore((s) => s.t);
  const languageName = t(`lang.${language}`);

  return (
    <section className="border-t bg-slate-50">
      <div className="mx-auto max-w-4xl px-6 py-12">
        <div className="rounded-2xl border bg-white p-8 shadow-sm">
          <p className="text-sm font-medium text-blue-600">{t('onboard.reviewEyebrow')}</p>
          <h3 className="mt-2 text-3xl font-bold">{t('onboard.reviewTitle')}</h3>
          <p className="mt-2 text-slate-500">{t('onboard.reviewDesc')}</p>

          <div className="mt-8 rounded-xl border p-5">
            <div className="flex gap-4">
              <MapPin className="text-blue-600" />
              <div>
                <p className="font-semibold">{t('onboard.reviewLocation')}</p>
                <p className="mt-2 text-sm text-slate-600">
                  {district} → {taluka} → {village}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-4 rounded-xl border p-5">
            <div className="flex gap-4">
              <Store className="text-blue-600" />
              <div>
                <p className="font-semibold">{t('onboard.reviewBusiness')}</p>
                <p className="mt-2 text-sm text-slate-600">{business}</p>
              </div>
            </div>
          </div>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl border p-5">
              <p className="font-semibold">{t('onboard.reviewCapital')}</p>
              <p className="mt-2 text-sm text-slate-600">₹{Number(capital).toLocaleString('en-IN')}</p>
            </div>
            <div className="rounded-xl border p-5">
              <p className="font-semibold">{t('onboard.reviewCost')}</p>
              <p className="mt-2 text-sm text-slate-600">
                ₹{Number(desiredProjectCost).toLocaleString('en-IN')}
              </p>
            </div>
          </div>

          <div className="mt-4 rounded-xl border p-5">
            <p className="font-semibold">{t('lang.label')}</p>
            <p className="mt-2 text-sm text-slate-600">{languageName}</p>
          </div>

          {error && (
            <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              <p className="font-semibold">{t('onboard.unableStart')}</p>
              <p className="mt-1">{error}</p>
              {(error.includes('Unable to reach') || error.includes('Failed to fetch')) && (
                <p className="mt-2 text-xs text-red-500">
                  Tip: Make sure the backend server is running on port 8000 before starting the analysis.
                </p>
              )}
            </div>
          )}

          <div className="mt-8 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={onEdit}
              className="rounded-lg border border-slate-300 bg-white px-6 py-3 font-semibold text-slate-700 hover:bg-slate-50"
            >
              {t('onboard.edit')}
            </button>
            <button
              type="button"
              onClick={onStartAnalysis}
              className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-6 py-3 font-semibold text-white hover:bg-slate-700"
            >
              {t('onboard.start')}
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
