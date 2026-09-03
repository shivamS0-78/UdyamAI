"use client";

import React from "react";
import Link from "next/link";
import {
  ArrowRight,
  Bot,
  Building2,
  Check,
  CircleDollarSign,
  LineChart,
  MapPin,
  Rocket,
  ShieldCheck,
  Sparkles,
  Store,
} from "lucide-react";
import LanguageSwitcher from "@/components/ui/LanguageSwitcher";
import { useLanguageStore } from "@/stores/languageStore";

export default function HomePage() {
  const t = useLanguageStore((s) => s.t);

  return (
    <main className="min-h-screen bg-white text-slate-900">
      {/* ================= NAVBAR ================= */}
      <nav className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-[76px] max-w-[1280px] items-center justify-between px-6 lg:px-10">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50">
              <Sparkles className="h-5 w-5 text-indigo-600" />
            </div>

            <span className="text-2xl font-bold tracking-tight">
              Udyam<span className="text-indigo-500">AI</span>
            </span>
          </Link>

          {/* Links */}
          <div className="hidden items-center gap-10 md:flex">
            <a
              href="#how-it-works"
              className="text-sm font-medium text-slate-700 transition hover:text-indigo-600"
            >
              {t('nav.howItWorks')}
            </a>

            <a
              href="#features"
              className="text-sm font-medium text-slate-700 transition hover:text-indigo-600"
            >
              {t('nav.features')}
            </a>

            <a
              href="#why"
              className="text-sm font-medium text-slate-700 transition hover:text-indigo-600"
            >
              {t('nav.why')}
            </a>

            <LanguageSwitcher compact />

            <Link
              href="/login"
              className="rounded-xl bg-slate-950 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-slate-950/10 transition hover:bg-indigo-700"
            >
              {t('nav.getStarted')}
              <ArrowRight className="ml-2 inline h-4 w-4" />
            </Link>
          </div>
        </div>
      </nav>

      {/* ================= HERO ================= */}
      <section className="relative overflow-hidden">
        {/* Background decoration */}
        <div className="pointer-events-none absolute -right-40 top-20 h-[500px] w-[500px] rounded-full bg-indigo-100/60 blur-3xl" />
        <div className="pointer-events-none absolute left-[35%] top-[40%] h-[350px] w-[350px] rounded-full bg-blue-100/50 blur-3xl" />

        <div className="relative mx-auto grid min-h-[600px] max-w-[1280px] items-center gap-16 px-6 py-20 lg:grid-cols-2 lg:px-10 lg:py-24">
          {/* LEFT */}
          <div>
            {/* Badge */}
            <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-indigo-50/70 px-4 py-2 text-sm font-medium text-indigo-600">
              <Sparkles className="h-4 w-4" />
              {t('home.badge')}
            </div>

            {/* Heading */}
            <h1 className="max-w-[650px] text-5xl font-extrabold leading-[1.05] tracking-[-0.035em] text-slate-950 sm:text-6xl lg:text-[68px]">
              {t('home.heroLine1')}
              <br />
              {t('home.heroLine2')}{" "}
              <span className="bg-gradient-to-r from-indigo-500 to-blue-500 bg-clip-text text-transparent">
                {t('home.heroSmarter')}
              </span>
              <br />
              <span className="bg-gradient-to-r from-indigo-500 to-blue-500 bg-clip-text text-transparent">
                {t('home.heroDecision')}
              </span>
            </h1>

            {/* Description */}
            <p className="mt-7 max-w-[650px] text-lg leading-8 text-slate-600">
              {t('home.heroDesc')}
            </p>

            {/* Buttons */}
          <div className="mt-9">
  <Link
    href="/login"
    className="inline-flex items-center rounded-xl bg-slate-950 px-7 py-4 font-semibold text-white shadow-xl shadow-indigo-900/10 transition hover:-translate-y-0.5 hover:bg-indigo-700"
  >
    {t('home.startAnalysis')}
    <ArrowRight className="ml-2 h-5 w-5" />
  </Link>
</div>

            {/* Benefits */}
            <div className="mt-8 flex flex-wrap gap-x-7 gap-y-3 text-sm text-slate-600">
              <span className="flex items-center gap-2">
                <Check className="h-4 w-4 text-indigo-500" />
                {t('home.locationAware')}
              </span>

              <span className="flex items-center gap-2">
                <Check className="h-4 w-4 text-emerald-500" />
                {t('home.aiAssisted')}
              </span>

              <span className="flex items-center gap-2">
                <Check className="h-4 w-4 text-orange-500" />
                {t('home.schemeDiscovery')}
              </span>
            </div>
          </div>

          {/* RIGHT ANALYSIS CARD */}
          <div className="relative">
            <div className="absolute -inset-5 rounded-[32px] bg-gradient-to-br from-indigo-100/70 via-blue-50/40 to-purple-100/70 blur-2xl" />

            <div className="relative rounded-[22px] border border-slate-200 bg-slate-50/95 p-7 shadow-2xl shadow-slate-300/40">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-500">
                    {t('home.cardFeasibility')}
                  </p>

                  <h2 className="mt-2 text-2xl font-bold text-slate-950">
                    {t('home.cardAnalysis')}
                  </h2>
                </div>

                {/* Score */}
                <div className="flex h-20 w-20 items-center justify-center rounded-full border-[6px] border-indigo-200 border-t-indigo-600 border-r-indigo-500 bg-white">
                  <span className="text-xl font-bold">82%</span>
                </div>
              </div>

              <div className="my-5 h-px bg-slate-200" />

              {/* Location */}
              <div className="mb-4 rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-indigo-50">
                    <MapPin className="h-6 w-6 text-indigo-600" />
                  </div>

                  <div>
                    <p className="text-sm text-slate-500">{t('home.cardLocation')}</p>
                    <p className="mt-1 font-semibold text-slate-900">
                      {t('home.cardSelectedArea')}
                    </p>
                  </div>
                </div>
              </div>

              {/* Investment */}
              <div className="mb-4 rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-emerald-50">
                    <CircleDollarSign className="h-6 w-6 text-emerald-600" />
                  </div>

                  <div>
                    <p className="text-sm text-slate-500">{t('home.cardInvestment')}</p>
                    <p className="mt-1 font-semibold text-slate-900">
                      ₹5,00,000
                    </p>
                  </div>
                </div>
              </div>

              {/* Recommendation */}
              <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-orange-50">
                    <LineChart className="h-6 w-6 text-orange-500" />
                  </div>

                  <div>
                    <p className="text-sm text-slate-500">
                      {t('home.cardRecommendation')}
                    </p>
                    <p className="mt-1 font-semibold text-emerald-600">
                      {t('home.cardPotential')}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ================= HOW IT WORKS ================= */}
      <section
        id="how-it-works"
        className="border-t border-slate-100 bg-white px-6 py-24 lg:px-10"
      >
        <div className="mx-auto max-w-[1150px]">
          <div className="text-center">
            <span className="rounded-full bg-blue-50 px-4 py-2 text-sm font-semibold text-blue-600">
              {t('home.processBadge')}
            </span>

            <h2 className="mt-5 text-4xl font-bold tracking-tight text-slate-950">
              {t('home.howTitle')}
            </h2>

            <p className="mx-auto mt-4 max-w-2xl text-slate-600">
              {t('home.howDesc')}
            </p>
          </div>

          <div className="mt-16 grid gap-12 md:grid-cols-4">
            <Step
              number="01"
              icon={<MapPin className="h-8 w-8" />}
              title={t('home.step1Title')}
              description={t('home.step1Desc')}
              iconClass="bg-indigo-50 text-indigo-600"
              numberClass="text-indigo-600"
            />

            <Step
              number="02"
              icon={<Store className="h-8 w-8" />}
              title={t('home.step2Title')}
              description={t('home.step2Desc')}
              iconClass="bg-emerald-50 text-emerald-600"
              numberClass="text-emerald-600"
            />

            <Step
              number="03"
              icon={<CircleDollarSign className="h-8 w-8" />}
              title={t('home.step3Title')}
              description={t('home.step3Desc')}
              iconClass="bg-orange-50 text-orange-500"
              numberClass="text-orange-500"
            />

            <Step
              number="04"
              icon={<Bot className="h-8 w-8" />}
              title={t('home.step4Title')}
              description={t('home.step4Desc')}
              iconClass="bg-blue-50 text-blue-600"
              numberClass="text-blue-600"
            />
          </div>
        </div>
      </section>

      {/* ================= FEATURES ================= */}
      <section
        id="features"
        className="border-t border-slate-100 bg-slate-50/40 px-6 py-24 lg:px-10"
      >
        <div className="mx-auto max-w-[1150px]">
          <div className="text-center">
            <span className="rounded-full bg-blue-50 px-4 py-2 text-sm font-semibold text-blue-600">
              {t('home.featuresBadge')}
            </span>

            <h2 className="mt-5 text-4xl font-bold tracking-tight text-slate-950">
              {t('home.featuresTitle')}
            </h2>
          </div>

          <div className="mt-12 grid gap-6 md:grid-cols-3">
            <FeatureCard
              icon={<LineChart className="h-7 w-7" />}
              iconClass="bg-indigo-50 text-indigo-600"
              title={t('home.feat1Title')}
              description={t('home.feat1Desc')}
            />

            <FeatureCard
              icon={<CircleDollarSign className="h-7 w-7" />}
              iconClass="bg-emerald-50 text-emerald-600"
              title={t('home.feat2Title')}
              description={t('home.feat2Desc')}
            />

            <FeatureCard
              icon={<Building2 className="h-7 w-7" />}
              iconClass="bg-orange-50 text-orange-500"
              title={t('home.feat3Title')}
              description={t('home.feat3Desc')}
            />
          </div>
        </div>
      </section>

      {/* ================= WHY UDYAMAI ================= */}
      <section id="why" className="bg-white px-6 py-20 lg:px-10">
        <div className="mx-auto grid max-w-[1150px] gap-10 md:grid-cols-3">
          <WhyCard
            icon={<MapPin className="h-6 w-6" />}
            title={t('home.why1Title')}
            description={t('home.why1Desc')}
          />

          <WhyCard
            icon={<Bot className="h-6 w-6" />}
            title={t('home.why2Title')}
            description={t('home.why2Desc')}
          />

          <WhyCard
            icon={<ShieldCheck className="h-6 w-6" />}
            title={t('home.why3Title')}
            description={t('home.why3Desc')}
          />
        </div>
      </section>

      {/* ================= CTA ================= */}
      <section id="start" className="px-6 pb-10 lg:px-10">
        <div className="relative mx-auto max-w-[1150px] overflow-hidden rounded-[24px] bg-gradient-to-r from-slate-950 via-indigo-950 to-indigo-800 px-8 py-12 text-white shadow-2xl lg:px-16">
          {/* Decorative glow */}
          <div className="absolute -right-20 -top-20 h-72 w-72 rounded-full bg-indigo-500/30 blur-3xl" />

          <div className="relative flex flex-col items-center justify-between gap-10 md:flex-row">
            {/* Rocket */}
            <div className="hidden md:block">
              <div className="flex h-28 w-28 rotate-[-15deg] items-center justify-center rounded-full bg-white/10">
                <Rocket className="h-16 w-16 text-white" />
              </div>
            </div>

            <div className="max-w-xl">
              <p className="mb-2 text-sm font-medium text-indigo-200">
                {t('home.ctaEyebrow')}
              </p>

              <h2 className="text-3xl font-bold">
                {t('home.ctaTitle')}
              </h2>

              <p className="mt-3 leading-7 text-slate-300">
                {t('home.ctaDesc')}
              </p>
            </div>

            <Link
              href="/login"
              className="shrink-0 rounded-xl bg-white px-8 py-4 font-semibold text-slate-900 shadow-xl transition hover:-translate-y-0.5 hover:bg-indigo-50"
            >
              {t('home.ctaButton')}
              <ArrowRight className="ml-2 inline h-5 w-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* ================= FOOTER ================= */}
      <footer className="border-t border-slate-100 bg-white px-6 py-8 lg:px-10">
        <div className="mx-auto flex max-w-[1280px] flex-col items-center justify-between gap-4 text-sm text-slate-500 md:flex-row">
          <div className="text-xl font-bold text-slate-900">
            Udyam<span className="text-indigo-500">AI</span>
          </div>

          <p>{t('home.footerTagline')}</p>

          <p>{t('home.footerCopy')}</p>
        </div>
      </footer>
    </main>
  );
}

/* ================= COMPONENTS ================= */

function Step({
  number,
  icon,
  title,
  description,
  iconClass,
  numberClass,
}: {
  number: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  iconClass: string;
  numberClass: string;
}) {
  return (
    <div className="relative text-center">
      <div
        className={`mx-auto flex h-20 w-20 items-center justify-center rounded-full ${iconClass} shadow-sm`}
      >
        {icon}
      </div>

      <p className={`mt-5 text-sm font-bold ${numberClass}`}>{number}</p>

      <h3 className="mt-2 font-bold text-slate-900">{title}</h3>

      <p className="mx-auto mt-2 max-w-[220px] text-sm leading-6 text-slate-500">
        {description}
      </p>
    </div>
  );
}

function FeatureCard({
  icon,
  iconClass,
  title,
  description,
}: {
  icon: React.ReactNode;
  iconClass: string;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-slate-200/60">
      <div
        className={`flex h-12 w-12 items-center justify-center rounded-xl ${iconClass}`}
      >
        {icon}
      </div>

      <h3 className="mt-5 text-lg font-bold text-slate-900">{title}</h3>

      <p className="mt-3 text-sm leading-6 text-slate-600">{description}</p>
    </div>
  );
}

function WhyCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex gap-4 rounded-2xl border border-slate-100 bg-white p-5">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
        {icon}
      </div>

      <div>
        <h3 className="font-bold text-slate-900">{title}</h3>
        <p className="mt-1 text-sm leading-6 text-slate-500">{description}</p>
      </div>
    </div>
  );
}