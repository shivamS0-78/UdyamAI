"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Sparkles, CheckCircle2 } from "lucide-react";

import LocationSelector from "./LocationSelector";
import BusinessSelector from "./BusinessSelector";
import FinancialForm from "./FinancialForm";
import ReviewScreen from "./ReviewScreen";
import WhatYouNeed from "./WhatYouNeed";
import AppShell from "@/components/ui/AppShell";
import Card from "@/components/ui/Card";
import DemoBadge, { DemoScenarioButton } from "@/components/ui/DemoBadge";

import { startAnalysis, waitForAnalysisCompletion } from "@/lib/api";
import { type Language } from "@/lib/i18n";
import { useLanguageStore } from "@/stores/languageStore";

export default function OnboardingPage() {
  const router = useRouter();
  const t = useLanguageStore((s) => s.t);
  const globalLanguage = useLanguageStore((s) => s.language);

  // Location
  const [stateCode, setStateCode] = useState("Maharashtra");
  const [stateName, setStateName] = useState("Maharashtra");
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

  // Demo sample scenario button using verified seeded data from Maharashtra database
  const handleDemo = () => {
    setStateCode("Maharashtra");
    setStateName("Maharashtra");
    setDistrictId("624a9c93-78e1-4f68-b79b-0b865a45c1bf");
    setDistrictName("Pune");
    setTalukaId("3158caf9-f1f2-446f-8dc4-27e0be20170c");
    setTalukaName("Baramati");
    setVillageId("30c4436a-813c-4455-847e-5ec17e386d67");
    setVillageName("Malegaon Bk");
    setBusinessCategoryId("02f4c8bc-d8ca-4e80-9ef8-76dcd49547cd");
    setBusinessCategoryName("Agro-Processing & Food Manufacturing");
    setCapital("500000");
    setDesiredProjectCost("800000");
    setError("");
    setShowReview(true);
  };

  // Start Analysis via Backend API
  const handleStartAnalysis = async () => {
    setIsSubmitting(true);
    setError("");

    const analysisData = {
      stateCode,
      stateName,
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

    // Save inputs to session/local storage
    if (typeof window !== "undefined") {
      sessionStorage.setItem("udyam_analysis_inputs", JSON.stringify(analysisData));
      localStorage.setItem("udyam_analysis_inputs", JSON.stringify(analysisData));
      localStorage.setItem("udyam_draft_analysis", JSON.stringify(analysisData));
    }

    if (typeof navigator !== "undefined" && !navigator.onLine) {
      setError(
        "You are currently offline. Your business inputs have been saved as a draft. Please reconnect to the internet to generate fresh AI feasibility assessments."
      );
      setIsSubmitting(false);
      return;
    }

    try {
      // Call backend POST /api/v1/analysis
      const res = await startAnalysis({
        village_id: villageId,
        business_category_id: businessCategoryId,
        available_capital: Number(capital),
        desired_project_cost: Number(desiredProjectCost || capital),
        language,
      });

      const analysisId = res.id || res.analysis_id;
      if (analysisId) {
        if (typeof window !== "undefined") {
          localStorage.setItem("udyam_active_analysis_id", String(analysisId));
          localStorage.removeItem("udyam_draft_analysis");
        }
        await waitForAnalysisCompletion(String(analysisId));
        router.push(`/dashboard?analysis_id=${analysisId}`);
      } else {
        router.push('/dashboard');
      }
    } catch (e: any) {
      console.error("Analysis submission error:", e);
      if (typeof navigator !== "undefined" && !navigator.onLine) {
        setError(
          "Network disconnected. Your inputs were preserved as a draft. Reconnect to calculate feasibility."
        );
      } else {
        setError(e.message || t('onboard.submitFail'));
      }
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
          stateName={stateName}
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
          <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-foreground/70 backdrop-blur-sm text-white">
            <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
            <h3 className="text-xl font-bold">{t('onboard.runningTitle')}</h3>
            <p className="mt-2 text-sm text-white/80">{t('onboard.runningDesc')}</p>
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
      <section className="w-full max-w-6xl mx-auto py-2">
        <div className="grid gap-8 lg:grid-cols-12">
          {/* Left Column */}
          <div className="lg:col-span-5 space-y-6">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-primary">
                {t('onboard.eyebrow')}
              </p>

              <h1 className="mt-2 text-3xl sm:text-4xl font-black text-foreground tracking-tight leading-tight">
                {t('onboard.title')}
              </h1>

              <p className="mt-3 text-sm sm:text-base leading-relaxed text-foreground-muted">
                {t('onboard.desc')}
              </p>
            </div>

            <WhatYouNeed />
          </div>

          {/* Right Column Form Card */}
          <div className="lg:col-span-7">
            <Card padding="lg" className="border-primary/20">
              <div className="flex items-center justify-between gap-2 border-b border-primary/10 pb-4 mb-6">
                <h2 className="text-lg sm:text-xl font-black text-foreground tracking-tight">
                  {t('onboard.startTitle')}
                </h2>
                <DemoBadge label="Simulation Ready" />
              </div>

              <div className="space-y-6">
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
                  stateCode={stateCode}
                  setStateCode={(code, name) => {
                    setStateCode(code);
                    if (name) setStateName(name);
                  }}
                />

                <div className="h-px bg-primary/10" />

                {/* Business */}
                <BusinessSelector
                  businessCategoryId={businessCategoryId}
                  setBusinessCategoryId={(id, name) => {
                    setBusinessCategoryId(id);
                    setBusinessCategoryName(name || "");
                  }}
                />

                <div className="h-px bg-primary/10" />

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

              {/* Error Alert */}
              {error && (
                <div className="mt-6 rounded-xl border border-danger-200 bg-danger-50 p-4 text-xs sm:text-sm text-danger-700 font-medium">
                  {error}
                </div>
              )}

              {/* Actions */}
              <div className="mt-8 space-y-3">
                <button
                  type="button"
                  onClick={handleDemo}
                  className="w-full flex items-center justify-between gap-3 p-3.5 rounded-xl bg-gradient-to-r from-accent-50/70 to-accent-100/50 border border-dashed border-accent-400 hover:border-accent-600 hover:bg-accent-100 transition-all text-left group"
                >
                  <div className="flex items-center gap-2.5">
                    <Sparkles className="h-4 w-4 text-accent-700 animate-demo-pulse shrink-0" />
                    <span className="text-xs sm:text-sm font-bold text-foreground">
                      Pre-fill Sample Financial Scenario
                    </span>
                  </div>
                  <span className="text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-md bg-accent text-foreground">
                    Try Demo
                  </span>
                </button>

                <button
                  type="button"
                  onClick={handleReview}
                  className="w-full rounded-xl bg-primary px-6 py-3.5 font-bold text-white shadow-lg shadow-primary/25 transition-all hover:bg-primary-600 hover:shadow-primary/35 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                >
                  {t('onboard.reviewCta')}
                </button>
              </div>
            </Card>
          </div>
        </div>
      </section>
    </AppShell>
  );
}