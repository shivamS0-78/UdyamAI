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
  type LucideIcon,
} from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';
import LanguageSwitcher from '@/components/ui/LanguageSwitcher';
import { useLanguageStore } from '@/stores/languageStore';

interface NavItem {
  href: string;
  labelKey: string;
  icon: LucideIcon;
}

interface NavGroup {
  titleKey?: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    items: [
      { href: '/dashboard', labelKey: 'nav.dashboard', icon: LayoutDashboard },
      { href: '/onboarding', labelKey: 'nav.feasibility', icon: BarChart3 },
    ],
  },
  {
    titleKey: 'sidebar.finance',
    items: [
      { href: '/expenses', labelKey: 'nav.expenses', icon: Receipt },
      { href: '/cashflow', labelKey: 'nav.cashflow', icon: Wallet },
      { href: '/savings', labelKey: 'nav.savings', icon: PiggyBank },
      { href: '/budget', labelKey: 'nav.budget', icon: Target },
      { href: '/debts', labelKey: 'nav.debts', icon: Landmark },
      { href: '/borrowing', labelKey: 'nav.borrowing', icon: HandCoins },
      { href: '/credit', labelKey: 'nav.credit', icon: CreditCard },
    ],
  },
  {
    titleKey: 'sidebar.insights',
    items: [
      { href: '/schemes', labelKey: 'nav.schemes', icon: BadgeCheck },
      { href: '/chat', labelKey: 'nav.chat', icon: MessageSquare },
      { href: '/reports', labelKey: 'nav.reports', icon: FileText },
      { href: '/businesses', labelKey: 'nav.businesses', icon: Store },
    ],
  },
  {
    titleKey: 'sidebar.account',
    items: [
      { href: '/profile', labelKey: 'nav.profile', icon: User },
      { href: '/settings', labelKey: 'nav.settings', icon: Settings },
      { href: '/privacy', labelKey: 'nav.privacy', icon: Shield },
      { href: '/recycle-bin', labelKey: 'nav.recyclebin', icon: Trash2 },
    ],
  },
];

function NavList({
  pathname,
  onNavigate,
}: {
  pathname: string;
  onNavigate?: () => void;
}) {
  const t = useLanguageStore((s) => s.t);

  return (
    <nav className="flex flex-col gap-6" aria-label="Main navigation">
      {NAV_GROUPS.map((group, groupIdx) => (
        <div key={group.titleKey || `group-${groupIdx}`}>
          {group.titleKey && (
            <p className="mb-2 px-3 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              {t(group.titleKey)}
            </p>
          )}
          <div className="flex flex-col gap-0.5">
            {group.items.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onNavigate}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <Icon
                    className={`h-[18px] w-[18px] shrink-0 ${
                      isActive ? 'text-indigo-600' : 'text-slate-400'
                    }`}
                  />
                  <span className="truncate">{t(item.labelKey)}</span>
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const t = useLanguageStore((s) => s.t);
  const { signOut } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  // Close the mobile drawer whenever the route changes
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  const handleSignOut = async () => {
    await signOut();
    router.push('/login');
    router.refresh();
  };

  const sidebarContent = (
    <div className="flex h-full flex-col">
      <div className="flex h-16 shrink-0 items-center gap-2 border-b border-slate-200 px-5">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50">
            <Sparkles className="h-4 w-4 text-indigo-600" />
          </div>
          <span className="text-lg font-bold tracking-tight text-slate-900">
            Udyam<span className="text-indigo-600">AI</span>
          </span>
        </Link>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-5">
        <NavList pathname={pathname} />
      </div>

      <div className="shrink-0 border-t border-slate-200 p-3">
        <button
          type="button"
          onClick={handleSignOut}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-red-50 hover:text-red-600"
        >
          <LogOut className="h-[18px] w-[18px] shrink-0 text-slate-400" />
          {t('app.signOut')}
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 border-r border-slate-200 bg-white lg:block">
        {sidebarContent}
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true">
          <div
            className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="absolute inset-y-0 left-0 w-72 bg-white shadow-xl">
            <button
              type="button"
              onClick={() => setMobileOpen(false)}
              className="absolute right-3 top-4 rounded-lg p-2 text-slate-400 hover:bg-slate-50 hover:text-slate-600"
              aria-label="Close menu"
            >
              <X className="h-5 w-5" />
            </button>
            {sidebarContent}
          </aside>
        </div>
      )}

      {/* Content column */}
      <div className="flex min-h-screen flex-col lg:pl-64">
        {/* Top utility bar */}
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur lg:justify-end lg:px-8">
          <div className="flex items-center gap-3 lg:hidden">
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
              className="rounded-lg p-2 text-slate-600 hover:bg-slate-100"
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <Link href="/" className="flex items-center gap-1.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-50">
                <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
              </div>
              <span className="text-base font-bold tracking-tight text-slate-900">
                Udyam<span className="text-indigo-600">AI</span>
              </span>
            </Link>
          </div>
          <LanguageSwitcher compact />
        </header>

        {/* Page content */}
        {children}
      </div>
    </div>
  );
}
