"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import LocationSelector from "./LocationSelector";
import BusinessSelector from "./BusinessSelector";
import FinancialForm from "./FinancialForm";
import ReviewScreen from "./ReviewScreen";
import WhatYouNeed from "./WhatYouNeed";
import AppShell from "@/components/ui/AppShell";

import { startAnalysis } from "@/lib/api";
import { type Language } from "@/lib/i18n";
import { useLanguageStore } from "@/stores/languageStore";

export default function OnboardingPage() {
  const router = useRouter();
  const t = useLanguageStore((s) => s.t);
  const globalLanguage = useLanguageStore((s) => s.language);

  // Location
  const [districtId, setDistrictId] = useState("");
  const [talukaId, setTalukaId] = useState("");
  const [villageId, setVillageId] = useState("");

  const [districtName, setDistrictName] = useState("");
  const [talukaName, setTalukaName] = useState("");
  const [villageName, setVillageName] = useState("");

  // Business
  const [businessCategoryId, setBusinessCategoryId] = useState("");
  const [businessCategoryName, setBusinessCategoryName] = useState("");

  // Financial inputs
  const [capital, setCapital] = useState("");
  const [desiredProjectCost, setDesiredProjectCost] = useState("");

  // Language
  const [language, setLanguage] = useState<Language>("en");

  // UI state
  const [showReview, setShowReview] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setLanguage(globalLanguage);
  }, [globalLanguage]);

  // Review button
  const handleReview = () => {
    setError("");

    if (
      !districtId ||
      !talukaId ||
      !villageId ||
      !businessCategoryId ||
      !capital ||
      Number(capital) < 0
    ) {
      setError(t('onboard.fillRequired'));
      return;
    }

    setShowReview(true);
  };

  // Edit button
  const handleEdit = () => {
    setShowReview(false);
    setError("");
  };

  // Start Analysis via Backend API
  const handleStartAnalysis = async () => {
    setIsSubmitting(true);
    setError("");

    const analysisData = {
      districtId,
      districtName,
      talukaId,
      talukaName,
      villageId,
      villageName,
      businessCategoryId,
      businessCategoryName,
      capital,
      desiredProjectCost,
      language,
      timestamp: new Date().toISOString(),
    };

    try {
      if (typeof window !== "undefined") {
        sessionStorage.setItem("udyam_analysis_inputs", JSON.stringify(analysisData));
        localStorage.setItem("udyam_analysis_inputs", JSON.stringify(analysisData));
      }

      // Call backend POST /api/v1/analysis
      const res = await startAnalysis({
        village_id: villageId,
        business_category_id: businessCategoryId,
        available_capital: Number(capital) || 0,
        desired_project_cost: Number(desiredProjectCost) || Number(capital) || 100000,
        language: language || 'en',
      });

      const analysisId = res.id || res.analysis_id;
      if (analysisId) {
        if (typeof window !== "undefined") {
          localStorage.setItem("udyam_active_analysis_id", String(analysisId));
        }
        router.push(`/dashboard?analysis_id=${analysisId}`);
      } else {
        router.push('/dashboard');
      }
    } catch (e: any) {
      console.error("Analysis submission error:", e);
      setError(e.message || t('onboard.submitFail'));
      setIsSubmitting(false);
    }
  };

  // -----------------------------
  // Review Screen
  // -----------------------------
  if (showReview) {
    return (
      <AppShell>
        <ReviewScreen
          district={districtName || districtId}
          taluka={talukaName || talukaId}
          village={villageName || villageId}
          business={businessCategoryName || businessCategoryId}
          capital={capital}
          desiredProjectCost={desiredProjectCost}
          language={language}
          error={error}
          onEdit={handleEdit}
          onStartAnalysis={handleStartAnalysis}
        />
        {isSubmitting && (
          <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-slate-900/60 backdrop-blur-sm text-white">
            <Loader2 className="h-12 w-12 animate-spin text-blue-400 mb-4" />
            <h3 className="text-xl font-bold">{t('onboard.runningTitle')}</h3>
            <p className="mt-2 text-sm text-slate-300">{t('onboard.runningDesc')}</p>
          </div>
        )}
      </AppShell>
    );
  }

  // -----------------------------
  // Main Onboarding
  // -----------------------------
  return (
    <AppShell>

      {/* Main content */}
      <section className="mx-auto max-w-6xl px-6 py-12">
        <div className="grid gap-10 lg:grid-cols-2">

          {/* Left side */}
          <div>
            <p className="font-medium text-blue-600">
              {t('onboard.eyebrow')}
            </p>

            <h1 className="mt-3 text-4xl font-bold leading-tight">
              {t('onboard.title')}
            </h1>

            <p className="mt-5 max-w-xl text-lg leading-8 text-slate-600">
              {t('onboard.desc')}
            </p>

            <div className="mt-8">
              <WhatYouNeed />
            </div>
          </div>

          {/* Right side */}
          <div className="rounded-2xl border bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold">
              {t('onboard.startTitle')}
            </h2>

            <div className="mt-6 space-y-8">
              {/* Location */}
              <LocationSelector
                districtId={districtId}
                talukaId={talukaId}
                villageId={villageId}
                setDistrictId={(id, name) => {
                  setDistrictId(id);
                  setDistrictName(name || "");
                }}
                setTalukaId={(id, name) => {
                  setTalukaId(id);
                  setTalukaName(name || "");
                }}
                setVillageId={(id, name) => {
                  setVillageId(id);
                  setVillageName(name || "");
                }}
              />

              {/* Business */}
              <BusinessSelector
                businessCategoryId={businessCategoryId}
                setBusinessCategoryId={(id, name) => {
                  setBusinessCategoryId(id);
                  setBusinessCategoryName(name || "");
                }}
              />

              {/* Financial */}
              <FinancialForm
                capital={capital}
                desiredProjectCost={desiredProjectCost}
                language={language}
                setCapital={setCapital}
                setDesiredProjectCost={setDesiredProjectCost}
                setLanguage={setLanguage}
              />
            </div>

            {/* Error */}
            {error && (
              <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* Review */}
            <button
              type="button"
              onClick={handleReview}
              className="mt-8 w-full rounded-xl bg-slate-900 px-6 py-3 font-semibold text-white transition hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
            >
              {t('onboard.reviewCta')}
            </button>
          </div>
        </div>
      </section>
    </AppShell>
  );
}