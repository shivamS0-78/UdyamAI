'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  BadgeCheck,
  BarChart3,
  CreditCard,
  FileText,
  HandCoins,
  Landmark,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquare,
  PiggyBank,
  Receipt,
  Settings,
  Shield,
  Sparkles,
  Store,
  Target,
  Trash2,
  User,
  Wallet,
  X,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  PanelLeftClose,
  PanelLeftOpen,
  Layers,
  type LucideIcon,
} from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';
import LanguageSwitcher from '@/components/ui/LanguageSwitcher';
import DarkModeToggle from '@/components/ui/DarkModeToggle';
import PWAInstallButton from '@/components/ui/PWAInstallButton';
import { useLanguageStore, useTranslation } from '@/stores/languageStore';
import Logo from '@/components/ui/Logo';

interface NavItem {
  href: string;
  labelKey: string;
  icon: LucideIcon;
  shortLabel: string;
}

interface NavModule {
  id: 'dashboard' | 'financial' | 'schemes' | 'reports';
  labelKey: string;
  defaultLabel: string;
  href: string;
  icon: LucideIcon;
  matchPrefixes: string[];
  items: NavItem[];
}

const NAV_MODULES: NavModule[] = [
  {
    id: 'dashboard',
    labelKey: 'nav.dashboardAndAnalytics',
    defaultLabel: 'Dashboard & Analytics',
    href: '/dashboard',
    icon: LayoutDashboard,
    matchPrefixes: ['/dashboard', '/onboarding', '/analysis', '/chat'],
    items: [
      { href: '/dashboard', labelKey: 'nav.dashboard', shortLabel: 'Overview', icon: LayoutDashboard },
      { href: '/onboarding', labelKey: 'nav.feasibility', shortLabel: 'Feasibility Engine', icon: BarChart3 },
      { href: '/reports', labelKey: 'nav.reports', shortLabel: 'Feasibility Reports', icon: FileText },
      { href: '/chat', labelKey: 'nav.chat', shortLabel: 'AI Business Advisor', icon: MessageSquare },
    ],
  },
  {
    id: 'financial',
    labelKey: 'nav.financialTools',
    defaultLabel: 'Financial Tools',
    href: '/cashflow',
    icon: Wallet,
    matchPrefixes: ['/cashflow', '/expenses', '/savings', '/budget', '/debts', '/borrowing', '/credit'],
    items: [
      { href: '/cashflow', labelKey: 'nav.cashflow', shortLabel: 'Cash Flow', icon: Wallet },
      { href: '/expenses', labelKey: 'nav.expenses', shortLabel: 'Expenses', icon: Receipt },
      { href: '/savings', labelKey: 'nav.savings', shortLabel: 'Savings', icon: PiggyBank },
      { href: '/budget', labelKey: 'nav.budget', shortLabel: 'Budgeting', icon: Target },
      { href: '/debts', labelKey: 'nav.debts', shortLabel: 'Debt Tracker', icon: Landmark },
      { href: '/borrowing', labelKey: 'nav.borrowing', shortLabel: 'Micro Borrowing', icon: HandCoins },
      { href: '/credit', labelKey: 'nav.credit', shortLabel: 'Credit Health', icon: CreditCard },
    ],
  },
  {
    id: 'schemes',
    labelKey: 'nav.schemesAndDirectory',
    defaultLabel: 'Schemes & Directory',
    href: '/schemes',
    icon: BadgeCheck,
    matchPrefixes: ['/schemes', '/businesses'],
    items: [
      { href: '/schemes', labelKey: 'nav.schemes', shortLabel: 'Gov Schemes', icon: BadgeCheck },
      { href: '/businesses', labelKey: 'nav.businesses', shortLabel: 'Business Ecosystem', icon: Store },
      { href: '/onboarding', labelKey: 'nav.feasibility', shortLabel: 'Eligibility Check', icon: Sparkles },
    ],
  },
  {
    id: 'reports',
    labelKey: 'nav.reportsAndInsights',
    defaultLabel: 'Reports',
    href: '/reports',
    icon: FileText,
    matchPrefixes: ['/reports'],
    items: [
      { href: '/reports', labelKey: 'nav.reports', shortLabel: 'Generated Reports', icon: FileText },
      { href: '/dashboard', labelKey: 'nav.dashboard', shortLabel: 'Feasibility Dossier', icon: LayoutDashboard },
      { href: '/schemes', labelKey: 'nav.schemes', shortLabel: 'Scheme Documents', icon: BadgeCheck },
    ],
  },
];

const MOBILE_NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', labelKey: 'nav.dashboard', shortLabel: 'Dashboard', icon: LayoutDashboard },
  { href: '/cashflow', labelKey: 'nav.cashflow', shortLabel: 'Finance', icon: Wallet },
  { href: '/schemes', labelKey: 'nav.schemes', shortLabel: 'Schemes', icon: BadgeCheck },
  { href: '/reports', labelKey: 'nav.reports', shortLabel: 'Reports', icon: FileText },
  { href: '/profile', labelKey: 'nav.profile', shortLabel: 'Profile', icon: User },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { t, language } = useTranslation();
  const { user, profile, signOut } = useAuth();
  const [profileOpen, setProfileOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sidebarExpanded, setSidebarExpanded] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem('udyam_sidebar_expanded');
      if (saved !== null) {
        setSidebarExpanded(saved === 'true');
      }
    } catch {}
  }, []);

  const toggleSidebar = () => {
    setSidebarExpanded((prev) => {
      const next = !prev;
      try {
        localStorage.setItem('udyam_sidebar_expanded', String(next));
      } catch {}
      return next;
    });
  };

  useEffect(() => {
    setMobileOpen(false);
    setProfileOpen(false);
  }, [pathname]);

  const handleSignOut = async () => {
    await signOut();
    router.push('/login');
    router.refresh();
  };

  const activeModule =
    NAV_MODULES.find((m) =>
      m.matchPrefixes.some((prefix) => pathname === prefix || pathname.startsWith(prefix + '/'))
    ) || NAV_MODULES[0];

  const userName = profile?.name || profile?.business_name || user?.email?.split('@')[0] || 'Entrepreneur';

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans transition-colors duration-200 w-full">
      {/* ========================================================================= */}
      {/* TOP NAVIGATION BAR (FULL WIDTH & DEAD-CENTERED MODULE PILL)               */}
      {/* ========================================================================= */}
      <header className="sticky top-0 z-30 w-full bg-white/95 dark:bg-[#161B22]/95 backdrop-blur-md border-b border-border px-4 sm:px-6 lg:px-8 py-3 transition-colors">
        <div className="relative flex items-center justify-between gap-4 w-full">
          {/* Brand Logo (Enlarged with hover micro-animation) */}
          <div className="flex items-center gap-3 shrink-0 z-10">
            <button
              type="button"
              onClick={() => setMobileOpen(!mobileOpen)}
              className="p-2 rounded-xl text-foreground-muted hover:bg-neutral-100 dark:hover:bg-neutral-800 lg:hidden transition-transform active:scale-95"
              aria-label="Toggle Navigation"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="transition-transform duration-200 hover:scale-[1.02] active:scale-[0.98]">
              <Logo href="/dashboard" size="md" />
            </div>
          </div>

          {/* Centered Floating Module Pill Navigation (Dead-Centered on Desktop) */}
          <nav className="hidden md:flex items-center bg-[#F6F7F9] dark:bg-[#1C2128] border border-border rounded-full p-1.5 shadow-sm gap-1 absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 pointer-events-auto">
            {NAV_MODULES.map((mod) => {
              const isModActive = activeModule.id === mod.id;
              const ModIcon = mod.icon;
              return (
                <Link
                  key={mod.id}
                  href={mod.href}
                  className={`flex items-center gap-2 px-4 sm:px-4.5 py-2 rounded-full text-[13px] sm:text-sm transition-all duration-200 ${
                    isModActive
                      ? 'bg-primary text-white shadow-pill-active font-bold scale-[1.02]'
                      : 'text-foreground-muted hover:text-foreground hover:bg-white/80 dark:hover:bg-white/10 font-semibold hover:scale-[1.02] active:scale-[0.98]'
                  }`}
                >
                  <ModIcon className={`h-4 w-4 shrink-0 transition-transform duration-200 ${isModActive ? 'scale-110' : 'group-hover:scale-105'}`} />
                  <span>{t(mod.labelKey, mod.defaultLabel)}</span>
                </Link>
              );
            })}
          </nav>

          {/* Right Controls: Language, Dark Mode, Profile */}
          <div className="flex items-center gap-2 sm:gap-2.5 shrink-0 z-10">
            {/* Language Switcher */}
            <div className="hidden sm:block transition-transform duration-200 hover:scale-105 active:scale-95">
              <LanguageSwitcher compact />
            </div>

            {/* Dark Mode Toggle */}
            <DarkModeToggle />

            {/* User Profile Avatar Dropdown */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setProfileOpen(!profileOpen)}
                className="flex items-center gap-2 p-1.5 sm:px-3 sm:py-1.5 rounded-full bg-[#F6F7F9] dark:bg-[#1C2128] border border-border hover:bg-neutral-100 dark:hover:bg-[#272D37] transition-all duration-200 hover:scale-105 active:scale-95"
              >
                <div className="w-7 h-7 rounded-full bg-primary/15 border border-primary/20 flex items-center justify-center text-primary font-bold text-xs uppercase shadow-xs">
                  {userName.charAt(0)}
                </div>
                <ChevronDown className={`h-4 w-4 text-foreground-muted hidden sm:block transition-transform duration-200 ${profileOpen ? 'rotate-180' : ''}`} />
              </button>

              {/* Profile Dropdown Modal */}
              {profileOpen && (
                <div className="absolute right-0 top-12 z-50 w-60 bg-white dark:bg-[#1C2128] rounded-2xl border border-border shadow-xl p-2 animate-scale-in">
                  <div className="px-3.5 py-2.5 border-b border-border">
                    <p className="text-sm font-bold text-foreground truncate">{userName}</p>
                    <p className="text-xs text-foreground-muted truncate mt-0.5">{user?.email || 'Active Entrepreneur'}</p>
                  </div>
                  <div className="py-1">
                    <Link
                      href="/profile"
                      className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13px] sm:text-sm font-semibold text-foreground-muted hover:bg-neutral-50 dark:hover:bg-neutral-800 hover:text-foreground transition-all duration-150 hover:translate-x-0.5"
                    >
                      <User className="h-4 w-4 text-foreground-muted" /> {t('nav.profile')}
                    </Link>
                    <Link
                      href="/settings"
                      className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13px] sm:text-sm font-semibold text-foreground-muted hover:bg-neutral-50 dark:hover:bg-neutral-800 hover:text-foreground transition-all duration-150 hover:translate-x-0.5"
                    >
                      <Settings className="h-4 w-4 text-foreground-muted" /> {t('nav.settings')}
                    </Link>
                    <Link
                      href="/privacy"
                      className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13px] sm:text-sm font-semibold text-foreground-muted hover:bg-neutral-50 dark:hover:bg-neutral-800 hover:text-foreground transition-all duration-150 hover:translate-x-0.5"
                    >
                      <Shield className="h-4 w-4 text-foreground-muted" /> {t('nav.privacy')}
                    </Link>
                    <Link
                      href="/recycle-bin"
                      className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13px] sm:text-sm font-semibold text-foreground-muted hover:bg-neutral-50 dark:hover:bg-neutral-800 hover:text-foreground transition-all duration-150 hover:translate-x-0.5"
                    >
                      <Trash2 className="h-4 w-4 text-foreground-muted" /> {t('nav.recyclebin')}
                    </Link>
                  </div>
                  <div className="pt-1 border-t border-border">
                    <button
                      type="button"
                      onClick={handleSignOut}
                      className="flex w-full items-center gap-2.5 px-3 py-2 rounded-xl text-[13px] sm:text-sm font-semibold text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-all duration-150 hover:translate-x-0.5 active:scale-95"
                    >
                      <LogOut className="h-4 w-4 text-rose-600" /> {t('app.signOut')}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* ========================================================================= */}
      {/* MAIN WORKSPACE BODY (SIDEBAR + MAIN SCREEN)                               */}
      {/* ========================================================================= */}
      <div className="flex flex-col lg:flex-row gap-5 lg:gap-6 flex-1 w-full px-4 sm:px-6 lg:px-8 py-6">
        
        {/* Left Expandable Floating Contextual Sidebar (Desktop) */}
        <aside
          className={`hidden lg:flex flex-col justify-between bg-white dark:bg-[#161B22] border border-border rounded-2xl shadow-subtle shrink-0 sticky top-20 self-start transition-all duration-300 ease-in-out ${
            sidebarExpanded ? 'w-64 p-4' : 'w-[64px] p-2.5 py-4 items-center'
          }`}
        >
          <div className="flex flex-col gap-2 w-full">
            {/* Header / Module Indicator & Toggle Button */}
            <div className={`flex items-center pb-3 border-b border-border/80 ${sidebarExpanded ? 'justify-between px-1' : 'justify-center'}`}>
              {sidebarExpanded ? (
                <div className="flex items-center gap-2 min-w-0">
                  <span className="w-2 h-2 rounded-full bg-primary shrink-0" />
                  <span className="text-xs font-bold uppercase tracking-wider text-foreground truncate">
                    {t(activeModule.labelKey, activeModule.defaultLabel)}
                  </span>
                </div>
              ) : null}
              <button
                type="button"
                onClick={toggleSidebar}
                className="p-1.5 rounded-lg text-foreground-muted hover:text-foreground hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
                title={sidebarExpanded ? 'Collapse sidebar' : 'Expand sidebar'}
                aria-label={sidebarExpanded ? 'Collapse sidebar' : 'Expand sidebar'}
              >
                {sidebarExpanded ? (
                  <PanelLeftClose className="h-4.5 w-4.5" />
                ) : (
                  <PanelLeftOpen className="h-4.5 w-4.5" />
                )}
              </button>
            </div>

            {/* Contextual Navigation Links for Active Module */}
            <div className="flex flex-col gap-1 mt-1">
              {activeModule.items.map((item) => {
                const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    title={!sidebarExpanded ? t(item.labelKey, item.shortLabel) : undefined}
                    className={`relative flex items-center transition-all duration-150 group ${
                      sidebarExpanded
                        ? `gap-3 px-3.5 py-2.5 rounded-xl text-sm ${
                            isActive
                              ? 'bg-primary text-white shadow-pill-active font-bold'
                              : 'text-neutral-600 dark:text-neutral-300 hover:text-foreground hover:bg-neutral-50 dark:hover:bg-neutral-800/80 font-medium'
                          }`
                        : `justify-center w-11 h-11 rounded-xl ${
                            isActive
                              ? 'bg-primary text-white shadow-pill-active scale-105'
                              : 'text-neutral-500 dark:text-neutral-400 hover:text-foreground hover:bg-neutral-100 dark:hover:bg-neutral-800'
                          }`
                    }`}
                  >
                    <Icon className="h-5 w-5 shrink-0" />
                    {sidebarExpanded ? (
                      <span className="truncate">{t(item.labelKey, item.shortLabel)}</span>
                    ) : (
                      <span className="absolute left-14 z-50 bg-neutral-900 dark:bg-neutral-800 text-white text-xs font-semibold px-3 py-1.5 rounded-lg opacity-0 pointer-events-none group-hover:opacity-100 transition whitespace-nowrap shadow-lg">
                        {t(item.labelKey, item.shortLabel)}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>

            {/* Quick Switch to Other Suites */}
            {sidebarExpanded ? (
              <div className="pt-3.5 mt-2 border-t border-border/80 w-full">
                <div className="px-1 mb-2 flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-foreground-muted">
                  <span>Switch Suite</span>
                  <Layers className="h-3.5 w-3.5" />
                </div>
                <div className="grid grid-cols-4 gap-1.5">
                  {NAV_MODULES.map((mod) => {
                    const isModActive = activeModule.id === mod.id;
                    const MIcon = mod.icon;
                    return (
                      <Link
                        key={mod.id}
                        href={mod.href}
                        title={t(mod.labelKey, mod.defaultLabel)}
                        className={`flex items-center justify-center h-9 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 ${
                          isModActive
                            ? 'bg-primary text-white shadow-xs'
                            : 'text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:text-foreground'
                        }`}
                      >
                        <MIcon className="h-4 w-4" />
                      </Link>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="pt-3 mt-2 border-t border-border/80 w-full flex flex-col items-center gap-1.5">
                {NAV_MODULES.filter((m) => m.id !== activeModule.id).map((mod) => {
                  const MIcon = mod.icon;
                  return (
                    <Link
                      key={mod.id}
                      href={mod.href}
                      title={`Go to ${t(mod.labelKey, mod.defaultLabel)}`}
                      className="flex items-center justify-center w-9 h-9 rounded-xl text-neutral-400 hover:text-foreground hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:scale-105 active:scale-95 transition-all duration-200"
                    >
                      <MIcon className="h-4 w-4" />
                    </Link>
                  );
                })}
              </div>
            )}
          </div>

          {/* Bottom Actions */}
          <div className={`flex flex-col gap-1 pt-3.5 border-t border-border w-full mt-4 ${sidebarExpanded ? 'px-0' : 'items-center'}`}>
            <Link
              href="/settings"
              title={!sidebarExpanded ? t('nav.settings') : undefined}
              className={`flex items-center transition-all duration-150 group ${
                sidebarExpanded
                  ? `gap-3 px-3.5 py-2.5 rounded-xl text-sm ${
                      pathname === '/settings'
                        ? 'bg-primary text-white shadow-pill-active font-bold'
                        : 'text-neutral-600 dark:text-neutral-300 hover:text-foreground hover:bg-neutral-50 dark:hover:bg-neutral-800/80 font-medium'
                    }`
                  : `justify-center w-11 h-11 rounded-xl text-neutral-500 dark:text-neutral-400 hover:text-foreground hover:bg-neutral-100 dark:hover:bg-neutral-800 ${
                      pathname === '/settings' ? 'bg-primary text-white shadow-pill-active' : ''
                    }`
              }`}
            >
              <Settings className="h-5 w-5 shrink-0" />
              {sidebarExpanded ? (
                <span className="truncate">{t('nav.settings')}</span>
              ) : (
                <span className="absolute left-14 z-50 bg-neutral-900 dark:bg-neutral-800 text-white text-xs font-semibold px-3 py-1.5 rounded-lg opacity-0 pointer-events-none group-hover:opacity-100 transition whitespace-nowrap shadow-lg">
                  {t('nav.settings')}
                </span>
              )}
            </Link>
            <button
              type="button"
              onClick={handleSignOut}
              title={!sidebarExpanded ? t('app.signOut') : undefined}
              className={`flex items-center transition-all duration-150 text-neutral-500 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 group ${
                sidebarExpanded
                  ? 'gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium w-full'
                  : 'justify-center w-11 h-11 rounded-xl'
              }`}
            >
              <LogOut className="h-5 w-5 shrink-0" />
              {sidebarExpanded ? (
                <span className="truncate">{t('app.signOut')}</span>
              ) : (
                <span className="absolute left-14 z-50 bg-neutral-900 dark:bg-neutral-800 text-white text-xs font-semibold px-3 py-1.5 rounded-lg opacity-0 pointer-events-none group-hover:opacity-100 transition whitespace-nowrap shadow-lg">
                  {t('app.signOut')}
                </span>
              )}
            </button>
          </div>
        </aside>

        {/* Main Content Workspace */}
        <main className="flex-1 min-w-0 flex flex-col pb-20 lg:pb-0">
          {children}
        </main>
      </div>

      {/* ========================================================================= */}
      {/* MOBILE SIDE NAVIGATION DRAWER (Slide-over)                                */}
      {/* ========================================================================= */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity duration-200"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />

          {/* Drawer Panel */}
          <div className="fixed inset-y-0 left-0 flex max-w-full">
            <div className="w-screen max-w-xs sm:max-w-sm bg-white dark:bg-[#161B22] border-r border-border shadow-2xl flex flex-col justify-between overflow-y-auto p-5 transition-transform duration-300">
              <div className="space-y-5">
                {/* Header: Brand + Close */}
                <div className="flex items-center justify-between pb-3 border-b border-border">
                  <Logo href="/dashboard" size="md" />
                  <button
                    type="button"
                    onClick={() => setMobileOpen(false)}
                    className="p-2 rounded-xl text-foreground-muted hover:text-foreground hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
                    aria-label="Close Navigation"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>

                {/* PWA Download Banner */}
                <PWAInstallButton variant="banner" className="w-full shadow-xs" />

                {/* User Profile Card */}
                {user && (
                  <Link
                    href="/profile"
                    onClick={() => setMobileOpen(false)}
                    className="flex items-center gap-3 p-3 rounded-2xl bg-slate-50 dark:bg-[#1C2128] border border-border hover:border-primary/40 transition"
                  >
                    <div className="h-10 w-10 rounded-full bg-primary/15 text-primary flex items-center justify-center font-black text-sm uppercase shrink-0 border border-primary/20">
                      {userName.slice(0, 2)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-bold text-foreground truncate">{userName}</p>
                      <p className="text-xs text-foreground-muted truncate">
                        {profile?.business_name || user?.email || 'Active Member'}
                      </p>
                    </div>
                    <ChevronRight className="h-4 w-4 text-foreground-muted shrink-0" />
                  </Link>
                )}

                {/* Navigation Modules & Links */}
                <div className="space-y-4 pt-1">
                  {NAV_MODULES.map((mod) => {
                    const ModIcon = mod.icon;
                    const isModActive = activeModule.id === mod.id;

                    return (
                      <div key={mod.id} className="space-y-1">
                        <div className="flex items-center gap-2 px-2 py-1 text-xs font-bold uppercase tracking-wider text-foreground-muted">
                          <ModIcon className="h-3.5 w-3.5 text-primary" />
                          <span>{t(mod.labelKey, mod.defaultLabel)}</span>
                        </div>
                        <div className="space-y-0.5 pl-2">
                          {mod.items.map((item) => {
                            const isItemActive = pathname === item.href;
                            const ItemIcon = item.icon;
                            return (
                              <Link
                                key={item.href}
                                href={item.href}
                                onClick={() => setMobileOpen(false)}
                                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                                  isItemActive
                                    ? 'bg-primary text-white shadow-xs font-bold'
                                    : 'text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:text-foreground'
                                }`}
                              >
                                <ItemIcon className="h-4 w-4 shrink-0" />
                                <span className="truncate">{t(item.labelKey, item.shortLabel)}</span>
                              </Link>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Bottom Drawer Actions */}
              <div className="pt-4 mt-6 border-t border-border space-y-3">
                <div className="flex items-center justify-between px-2">
                  <span className="text-xs font-bold text-foreground-muted uppercase tracking-wider">Preferences</span>
                  <div className="flex items-center gap-2">
                    <LanguageSwitcher compact />
                    <DarkModeToggle />
                  </div>
                </div>

                <div className="flex flex-col gap-1 pt-1">
                  <Link
                    href="/settings"
                    onClick={() => setMobileOpen(false)}
                    className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
                  >
                    <Settings className="h-4 w-4 text-foreground-muted" />
                    <span>{t('nav.settings')}</span>
                  </Link>
                  <button
                    type="button"
                    onClick={() => {
                      setMobileOpen(false);
                      void handleSignOut();
                    }}
                    className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition text-left"
                  >
                    <LogOut className="h-4 w-4" />
                    <span>{t('app.signOut')}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MOBILE BOTTOM NAVIGATION BAR                                              */}
      {/* ========================================================================= */}
      <nav
        className="fixed inset-x-0 bottom-0 z-40 border-t border-[#E7E7E7] dark:border-[#2B313C] bg-white/95 dark:bg-[#161B22]/95 backdrop-blur-md px-4 py-2 pb-[env(safe-area-inset-bottom)] lg:hidden shadow-lg transition-colors"
        aria-label="Mobile navigation"
      >
        <div className="mx-auto flex max-w-md items-center justify-around">
          {MOBILE_NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex min-w-0 flex-1 flex-col items-center justify-center gap-1 py-1 text-xs font-semibold transition-colors ${
                  isActive
                    ? 'text-primary font-bold'
                    : 'text-foreground-muted hover:text-foreground'
                }`}
              >
                <div className={`p-1 rounded-xl transition ${isActive ? 'bg-primary-50 dark:bg-primary-950/50 text-primary' : ''}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <span className="truncate">{t(item.labelKey, item.shortLabel)}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
