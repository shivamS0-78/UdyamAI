"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Bot,
  Building2,
  CircleDollarSign,
  LineChart,
  MapPin,
  Rocket,
  ShieldCheck,
  Sparkles,
  Store,
  TrendingUp,
  Award,
  Zap,
  FileSpreadsheet,
  Globe2,
  Menu,
  X,
} from "lucide-react";
import LanguageSwitcher from "@/components/ui/LanguageSwitcher";
import DarkModeToggle from "@/components/ui/DarkModeToggle";
import PWAInstallButton from "@/components/ui/PWAInstallButton";
import { useTranslation } from "@/stores/languageStore";
import StatusBadge from "@/components/ui/StatusBadge";
import Logo from "@/components/ui/Logo";

export default function HomePage() {
  const { t } = useTranslation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <main className="min-h-screen bg-background text-foreground selection:bg-primary/20 selection:text-primary transition-colors duration-200">
      {/* ================= FLOATING NAVBAR ================= */}
      <header className="sticky top-4 z-50 mx-auto max-w-[1240px] px-4 sm:px-6">
        <nav className="flex h-[68px] items-center justify-between rounded-full border border-slate-200/80 dark:border-[#2B313C] bg-white/90 dark:bg-[#161B22]/90 px-4 sm:px-6 backdrop-blur-xl shadow-lg shadow-slate-900/5 transition-all">
          {/* Logo */}
          <Logo href="/" size="md" />

          {/* Desktop Navigation Links */}
          <div className="hidden items-center gap-6 lg:gap-8 md:flex">
            <a
              href="#how-it-works"
              className="text-sm font-semibold text-foreground-muted transition hover:text-primary"
            >
              {t('nav.howItWorks')}
            </a>

            <a
              href="#features"
              className="text-sm font-semibold text-foreground-muted transition hover:text-primary"
            >
              {t('nav.features')}
            </a>

            <a
              href="#why"
              className="text-sm font-semibold text-foreground-muted transition hover:text-primary"
            >
              {t('nav.why')}
            </a>

            <PWAInstallButton variant="compact" />

            <LanguageSwitcher compact />

            <DarkModeToggle />

            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-2.5 text-sm font-bold text-white shadow-fintech-btn transition-all duration-200 hover:bg-primary-600 hover:-translate-y-0.5"
            >
              {t('nav.getStarted')}
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          {/* Mobile Navigation Controls */}
          <div className="flex items-center gap-2 md:hidden">
            <PWAInstallButton variant="compact" />
            <LanguageSwitcher compact />
            <DarkModeToggle />
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl text-foreground-muted hover:bg-neutral-100 dark:hover:bg-neutral-800 transition active:scale-95"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </nav>

        {/* Mobile Dropdown Menu Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden mt-2 p-4 rounded-3xl border border-border bg-white/95 dark:bg-[#161B22]/95 backdrop-blur-xl shadow-2xl space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
            <div className="flex flex-col space-y-2">
              <a
                href="#how-it-works"
                onClick={() => setMobileMenuOpen(false)}
                className="px-4 py-2.5 rounded-xl text-sm font-semibold text-neutral-700 dark:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
              >
                {t('nav.howItWorks')}
              </a>
              <a
                href="#features"
                onClick={() => setMobileMenuOpen(false)}
                className="px-4 py-2.5 rounded-xl text-sm font-semibold text-neutral-700 dark:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
              >
                {t('nav.features')}
              </a>
              <a
                href="#why"
                onClick={() => setMobileMenuOpen(false)}
                className="px-4 py-2.5 rounded-xl text-sm font-semibold text-neutral-700 dark:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
              >
                {t('nav.why')}
              </a>
            </div>

            <div className="pt-2 border-t border-border">
              <PWAInstallButton variant="banner" className="w-full" />
            </div>

            <div className="pt-2">
              <Link
                href="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center justify-center gap-2 w-full rounded-2xl bg-primary py-3.5 text-sm font-bold text-white shadow-fintech-btn"
              >
                {t('nav.getStarted')}
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        )}
      </header>

      {/* ================= HERO SECTION ================= */}
      <section className="relative overflow-hidden pt-12 pb-24 lg:pt-20 lg:pb-32 glow-mesh-hero">
        {/* Background glow halos */}
        <div className="pointer-events-none absolute -right-32 top-10 h-[550px] w-[550px] rounded-full bg-blue-400/10 dark:bg-emerald-500/10 blur-3xl" />
        <div className="pointer-events-none absolute left-[15%] top-[25%] h-[450px] w-[450px] rounded-full bg-indigo-400/10 dark:bg-primary/10 blur-3xl" />
        <div className="pointer-events-none absolute -left-20 bottom-10 h-[400px] w-[400px] rounded-full bg-purple-400/10 dark:bg-indigo-500/10 blur-3xl" />

        <div className="relative mx-auto max-w-[1280px] px-6 lg:px-10">
          <div className="grid min-h-[580px] items-center gap-16 lg:grid-cols-12">
            {/* LEFT COLUMN: Editorial Typography */}
            <div className="lg:col-span-7 space-y-7 text-center lg:text-left">
              {/* Pill Badge */}
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-blue-50 dark:bg-primary/10 px-4 py-1.5 text-xs sm:text-sm font-bold text-primary shadow-sm">
                <Zap className="h-4 w-4 text-accent" />
                <span>{t('home.badge')}</span>
                <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                <span className="text-foreground-muted font-normal">Modern Rural FinTech Intelligence</span>
              </div>

              {/* Headline */}
              <h1 className="text-4xl font-black leading-[1.08] tracking-tight text-slate-900 dark:text-white sm:text-6xl lg:text-[70px]">
                {t('home.heroLine1')}
                <br />
                {t('home.heroLine2')}{" "}
                <span className="bg-gradient-to-r from-primary via-emerald-500 to-teal-500 bg-clip-text text-transparent">
                  {t('home.heroSmarter')}
                </span>
                <br />
                <span className="bg-gradient-to-r from-teal-500 via-cyan-500 to-primary bg-clip-text text-transparent">
                  {t('home.heroDecision')}
                </span>
              </h1>

              {/* Description */}
              <p className="mx-auto lg:mx-0 max-w-[620px] text-base sm:text-xl leading-relaxed text-foreground-muted">
                {t('home.heroDesc')}
              </p>

              {/* CTA Group */}
              <div className="flex flex-wrap items-center justify-center lg:justify-start gap-4 pt-2">
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2.5 rounded-full bg-primary px-9 py-4 text-base font-bold text-white shadow-fintech-btn transition-all duration-300 hover:-translate-y-0.5 hover:bg-primary-600 hover:shadow-lg hover:shadow-primary/35"
                >
                  {t('home.startAnalysis')}
                  <ArrowRight className="h-5 w-5" />
                </Link>

                <PWAInstallButton variant="secondary" />

                <a
                  href="#features"
                  className="inline-flex items-center gap-2 rounded-full border border-slate-200 dark:border-[#2B313C] bg-white dark:bg-[#1C2128] px-8 py-4 text-base font-bold text-slate-800 dark:text-neutral-100 shadow-sm transition-all hover:bg-slate-50 dark:hover:bg-[#272D37] hover:border-slate-300 dark:hover:border-[#3D4450]"
                >
                  {t('nav.howItWorks')}
                </a>
              </div>

              {/* Mini Trust Metrics */}
              <div className="grid grid-cols-3 gap-6 pt-6 border-t border-slate-200/70 dark:border-[#2B313C] max-w-md mx-auto lg:mx-0">
                <div>
                  <p className="text-2xl sm:text-3xl font-financial font-black text-slate-900 dark:text-white">84%</p>
                  <p className="text-xs text-foreground-muted font-medium mt-0.5">Average Feasibility</p>
                </div>
                <div>
                  <p className="text-2xl sm:text-3xl font-financial font-black text-primary">₹2.5L+</p>
                  <p className="text-xs text-foreground-muted font-medium mt-0.5">Scheme Subsidies</p>
                </div>
                <div>
                  <p className="text-2xl sm:text-3xl font-financial font-black text-emerald-600 dark:text-emerald-400">100%</p>
                  <p className="text-xs text-foreground-muted font-medium mt-0.5">RAG Verified</p>
                </div>
              </div>
            </div>

            {/* RIGHT COLUMN: Layered Floating FinTech UI Preview */}
            <div className="lg:col-span-5 relative">
              <div className="relative mx-auto w-full max-w-[480px]">
                {/* Main Elevated Preview Card */}
                <div className="rounded-3xl border border-slate-200/80 dark:border-[#2B313C] bg-white dark:bg-[#161B22] p-7 shadow-2xl backdrop-blur-xl relative z-10 space-y-6 transition-colors">
                  {/* Card Header */}
                  <div className="flex items-center justify-between border-b border-slate-100 dark:border-[#2B313C] pb-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/10 text-primary border border-primary/20">
                        <LineChart className="h-5 w-5" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-slate-900 dark:text-white">Enterprise Health Score</h3>
                        <p className="text-xs text-foreground-muted">Live Pipeline Analysis</p>
                      </div>
                    </div>
                    <StatusBadge status="verified" label="92/100 Safe" size="sm" />
                  </div>

                  {/* High Impact Numbers */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="rounded-2xl bg-slate-50 dark:bg-[#1C2128] p-4 border border-slate-100 dark:border-[#2B313C]">
                      <p className="text-[11px] font-bold uppercase tracking-wider text-foreground-muted">Projected Revenue</p>
                      <p className="text-2xl font-financial font-black text-slate-900 dark:text-white mt-1">₹14.8 L</p>
                      <span className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400">↑ 18.4% YoY</span>
                    </div>

                    <div className="rounded-2xl bg-blue-50/60 dark:bg-primary/10 p-4 border border-blue-100 dark:border-primary/20">
                      <p className="text-[11px] font-bold uppercase tracking-wider text-primary">Break-Even Point</p>
                      <p className="text-2xl font-financial font-black text-primary mt-1">7.2 Mos</p>
                      <span className="text-[11px] font-semibold text-foreground-muted">Optimized Capex</span>
                    </div>
                  </div>

                  {/* Matched Scheme Pill Card */}
                  <div className="flex items-center justify-between rounded-2xl border border-emerald-200 dark:border-emerald-800 bg-emerald-50/70 dark:bg-emerald-950/40 p-4">
                    <div className="flex items-center gap-3">
                      <Award className="h-5 w-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                      <div>
                        <p className="text-xs font-bold text-emerald-950 dark:text-emerald-300">PMEGP Scheme Subvention</p>
                        <p className="text-[11px] text-emerald-800 dark:text-emerald-400">35% Capital Subsidy Pre-Approved</p>
                      </div>
                    </div>
                    <span className="text-xs font-financial font-extrabold text-emerald-700 dark:text-emerald-300">₹3.5L</span>
                  </div>
                </div>

                {/* Floating Micro-Badge Top-Right */}
                <div className="absolute -top-6 -right-6 hidden sm:flex items-center gap-2.5 rounded-full border border-slate-200/80 dark:border-[#2B313C] bg-white/95 dark:bg-[#1C2128]/95 px-4 py-2.5 shadow-xl backdrop-blur-md z-20 animate-bounce" style={{ animationDuration: '4s' }}>
                  <Sparkles className="h-4 w-4 text-accent" />
                  <span className="text-xs font-bold text-slate-800 dark:text-neutral-100">AI Dual-Model Verified</span>
                </div>

                {/* Floating Micro-Badge Bottom-Left */}
                <div className="absolute -bottom-6 -left-6 hidden sm:flex items-center gap-2.5 rounded-full border border-slate-200/80 dark:border-[#2B313C] bg-white/95 dark:bg-[#1C2128]/95 px-4 py-2.5 shadow-xl backdrop-blur-md z-20">
                  <MapPin className="h-4 w-4 text-primary" />
                  <span className="text-xs font-bold text-slate-800 dark:text-neutral-100">PostGIS Geospatial Engine</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ================= MEASURED IMPACT STAT STRIP ================= */}
      <section className="relative z-10 -mt-8 mx-auto max-w-[1240px] px-4 sm:px-6">
        <div className="rounded-3xl border border-slate-200/80 dark:border-[#2B313C] bg-white/95 dark:bg-[#161B22]/95 p-6 sm:p-8 shadow-fintech backdrop-blur-xl transition-colors">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8 divide-y lg:divide-y-0 lg:divide-x divide-slate-100 dark:divide-[#2B313C]">
            <div className="pt-2 lg:pt-0 lg:px-4 text-center sm:text-left">
              <div className="flex items-center justify-center sm:justify-start gap-2 text-primary font-bold text-xs uppercase tracking-wider mb-1">
                <FileSpreadsheet className="h-4 w-4" />
                <span>Indexed Schemes</span>
              </div>
              <p className="text-3xl sm:text-4xl font-extrabold font-financial tracking-tight text-foreground">31</p>
              <p className="text-xs text-foreground-muted mt-1">PMEGP, PMFME, MUDRA & State Rules</p>
            </div>

            <div className="pt-4 sm:pt-2 lg:pt-0 lg:px-4 text-center sm:text-left">
              <div className="flex items-center justify-center sm:justify-start gap-2 text-teal-600 dark:text-teal-400 font-bold text-xs uppercase tracking-wider mb-1">
                <Globe2 className="h-4 w-4" />
                <span>Districts Covered</span>
              </div>
              <p className="text-3xl sm:text-4xl font-extrabold font-financial tracking-tight text-foreground">35</p>
              <p className="text-xs text-foreground-muted mt-1">Across Maharashtra Agro-Climatic Zones</p>
            </div>

            <div className="pt-4 sm:pt-2 lg:pt-0 lg:px-4 text-center sm:text-left">
              <div className="flex items-center justify-center sm:justify-start gap-2 text-emerald-600 dark:text-emerald-400 font-bold text-xs uppercase tracking-wider mb-1">
                <MapPin className="h-4 w-4" />
                <span>Verified Villages</span>
              </div>
              <p className="text-3xl sm:text-4xl font-extrabold font-financial tracking-tight text-foreground">53</p>
              <p className="text-xs text-foreground-muted mt-1">With 2011 Census Demographic Catchments</p>
            </div>

            <div className="pt-4 sm:pt-2 lg:pt-0 lg:px-4 text-center sm:text-left">
              <div className="flex items-center justify-center sm:justify-start gap-2 text-amber-600 dark:text-amber-400 font-bold text-xs uppercase tracking-wider mb-1">
                <Building2 className="h-4 w-4" />
                <span>MSME Sectors</span>
              </div>
              <p className="text-3xl sm:text-4xl font-extrabold font-financial tracking-tight text-foreground">17</p>
              <p className="text-xs text-foreground-muted mt-1">Dairy, Agro, Retail, Manufacturing & Services</p>
            </div>
          </div>
        </div>
      </section>

      {/* ================= WHY UDYAMAI: PILLARS ================= */}
      <section id="why" className="py-20 lg:py-28 bg-white dark:bg-background border-y border-slate-100 dark:border-[#2B313C] transition-colors">
        <div className="mx-auto max-w-[1280px] px-6 lg:px-10">
          <div className="mx-auto max-w-2xl text-center">
            <span className="text-xs font-bold uppercase tracking-widest text-primary">
              Core Intelligence
            </span>
            <h2 className="mt-2 text-3xl sm:text-5xl font-black tracking-tight text-slate-900 dark:text-white">
              {t('home.whyTitle')}
            </h2>
            <p className="mt-4 text-base sm:text-lg leading-relaxed text-foreground-muted">
              {t('home.whySubtitle')}
            </p>
          </div>

          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <WhyCard
              icon={<LineChart className="h-6 w-6" />}
              title={t('home.why1Title')}
              description={t('home.why1Desc')}
            />

            <WhyCard
              icon={<MapPin className="h-6 w-6" />}
              title={t('home.why2Title')}
              description={t('home.why2Desc')}
            />

            <WhyCard
              icon={<Award className="h-6 w-6" />}
              title={t('home.why3Title')}
              description={t('home.why3Desc')}
            />
          </div>
        </div>
      </section>

      {/* ================= HOW IT WORKS ================= */}
      <section id="how-it-works" className="py-20 lg:py-28 bg-slate-50/50 dark:bg-[#101419]/70 transition-colors">
        <div className="mx-auto max-w-[1280px] px-6 lg:px-10">
          <div className="mx-auto max-w-2xl text-center">
            <span className="text-xs font-bold uppercase tracking-widest text-primary">
              Streamlined Workflow
            </span>
            <h2 className="mt-2 text-3xl sm:text-5xl font-black tracking-tight text-slate-900 dark:text-white">
              {t('home.howTitle')}
            </h2>
            <p className="mt-4 text-base sm:text-lg leading-relaxed text-foreground-muted">
              {t('home.howDesc')}
            </p>
          </div>

          <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <Step
              number="01"
              icon={<MapPin className="h-6 w-6 text-primary" />}
              title={t('home.step1Title')}
              description={t('home.step1Desc')}
            />

            <Step
              number="02"
              icon={<Store className="h-6 w-6 text-primary" />}
              title={t('home.step2Title')}
              description={t('home.step2Desc')}
            />

            <Step
              number="03"
              icon={<CircleDollarSign className="h-6 w-6 text-primary" />}
              title={t('home.step3Title')}
              description={t('home.step3Desc')}
            />

            <Step
              number="04"
              icon={<TrendingUp className="h-6 w-6 text-primary" />}
              title={t('home.step4Title')}
              description={t('home.step4Desc')}
            />
          </div>
        </div>
      </section>

      {/* ================= FEATURES ================= */}
      <section id="features" className="py-20 lg:py-28 bg-white dark:bg-background border-t border-slate-100 dark:border-[#2B313C] transition-colors">
        <div className="mx-auto max-w-[1280px] px-6 lg:px-10">
          <div className="mx-auto max-w-2xl text-center">
            <span className="text-xs font-bold uppercase tracking-widest text-primary">
              Platform Modules
            </span>
            <h2 className="mt-2 text-3xl sm:text-5xl font-black tracking-tight text-slate-900 dark:text-white">
              {t('home.featuresTitle')}
            </h2>
            <p className="mt-4 text-base sm:text-lg leading-relaxed text-foreground-muted">
              {t('home.featuresSubtitle')}
            </p>
          </div>

          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              icon={<LineChart className="h-6 w-6 text-primary" />}
              title={t('home.f1Title')}
              description={t('home.f1Desc')}
            />

            <FeatureCard
              icon={<Building2 className="h-6 w-6 text-primary" />}
              title={t('home.f2Title')}
              description={t('home.f2Desc')}
            />

            <FeatureCard
              icon={<Award className="h-6 w-6 text-primary" />}
              title={t('home.f3Title')}
              description={t('home.f3Desc')}
            />

            <FeatureCard
              icon={<ShieldCheck className="h-6 w-6 text-primary" />}
              title={t('home.f4Title')}
              description={t('home.f4Desc')}
            />

            <FeatureCard
              icon={<Bot className="h-6 w-6 text-primary" />}
              title={t('home.f5Title')}
              description={t('home.f5Desc')}
            />

            <FeatureCard
              icon={<Globe2 className="h-6 w-6 text-primary" />}
              title={t('home.f6Title')}
              description={t('home.f6Desc')}
            />
          </div>
        </div>
      </section>

      {/* ================= FULL-WIDTH FINTECH CTA BANNER ================= */}
      <section id="start" className="px-6 py-16 lg:py-24 max-w-[1280px] mx-auto">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-emerald-950 via-primary to-teal-900 dark:from-slate-900 dark:via-primary dark:to-emerald-950 px-8 py-14 sm:p-16 text-white shadow-2xl border border-white/10">
          {/* Decorative radial glows */}
          <div className="absolute -right-16 -top-16 h-80 w-80 rounded-full bg-cyan-400/20 blur-3xl" />
          <div className="absolute -left-16 -bottom-16 h-80 w-80 rounded-full bg-emerald-400/20 blur-3xl" />

          <div className="relative z-10 flex flex-col items-center justify-between gap-8 text-center lg:flex-row lg:text-left">
            <div className="max-w-2xl space-y-3">
              <span className="inline-flex items-center gap-2 rounded-full bg-white/15 px-4 py-1 text-xs font-bold uppercase tracking-widest text-emerald-300">
                <Rocket className="h-3.5 w-3.5" /> {t('home.ctaEyebrow')}
              </span>
              <h2 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
                {t('home.ctaTitle')}
              </h2>
              <p className="text-base sm:text-lg text-white/80 leading-relaxed max-w-xl">
                {t('home.ctaDesc')}
              </p>
            </div>

            <Link
              href="/login"
              className="inline-flex shrink-0 items-center gap-2.5 rounded-full bg-white dark:bg-[#161B22] px-9 py-4.5 text-base font-extrabold text-primary dark:text-emerald-400 shadow-2xl transition-all duration-300 hover:bg-slate-100 dark:hover:bg-[#1C2128] hover:scale-105"
            >
              {t('home.ctaButton')}
              <ArrowRight className="h-5 w-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* ================= FOOTER ================= */}
      <footer className="border-t border-slate-200 dark:border-[#2B313C] bg-white dark:bg-[#161B22] px-6 py-12 lg:px-10 transition-colors">
        <div className="mx-auto flex max-w-[1280px] flex-col items-center justify-between gap-6 text-xs sm:text-sm text-foreground-muted md:flex-row">
          <Logo href="/" size="sm" />

          <p className="text-center md:text-left">{t('home.footerTagline')}</p>

          <p>{t('home.footerCopy')}</p>
        </div>
      </footer>
    </main>
  );
}

/* ================= REUSABLE COMPONENTS ================= */

function Step({
  number,
  icon,
  title,
  description,
}: {
  number: string;
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="relative text-center rounded-3xl bg-white dark:bg-[#161B22] p-7 border border-slate-200/80 dark:border-[#2B313C] shadow-card hover:shadow-card-hover transition-all duration-300 hover:-translate-y-1">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 dark:bg-primary/10 border border-blue-100 dark:border-primary/20 text-primary shadow-sm">
        {icon}
      </div>

      <p className="mt-5 text-xs font-black uppercase tracking-widest text-primary">
        Step {number}
      </p>

      <h3 className="mt-1 font-bold text-slate-900 dark:text-white text-base">{title}</h3>

      <p className="mx-auto mt-2 text-xs leading-relaxed text-foreground-muted">
        {description}
      </p>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-3xl border border-slate-200/80 dark:border-[#2B313C] bg-white dark:bg-[#161B22] p-8 shadow-card transition-all duration-300 hover:-translate-y-1 hover:shadow-card-hover hover:border-primary/30">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 border border-primary/20 text-primary shadow-sm">
        {icon}
      </div>

      <h3 className="mt-6 text-lg font-bold text-slate-900 dark:text-white">{title}</h3>

      <p className="mt-2 text-sm leading-relaxed text-foreground-muted">{description}</p>
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
    <div className="flex gap-4 rounded-3xl border border-slate-200/80 dark:border-[#2B313C] bg-white dark:bg-[#161B22] p-7 shadow-card transition-all duration-300 hover:-translate-y-0.5 hover:shadow-card-hover">
      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary border border-primary/20">
        {icon}
      </div>

      <div>
        <h3 className="font-bold text-slate-900 dark:text-white text-base">{title}</h3>
        <p className="mt-1 text-xs sm:text-sm leading-relaxed text-foreground-muted">{description}</p>
      </div>
    </div>
  );
}