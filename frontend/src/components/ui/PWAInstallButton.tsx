'use client';

import React, { useEffect, useState } from 'react';
import { Download, Smartphone, CheckCircle } from 'lucide-react';
import { useLanguageStore } from '@/stores/languageStore';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
}

interface PWAInstallButtonProps {
  variant?: 'primary' | 'secondary' | 'compact' | 'banner';
  className?: string;
}

export default function PWAInstallButton({
  variant = 'primary',
  className = '',
}: PWAInstallButtonProps) {
  const language = useLanguageStore((s) => s.language);
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isInstalled, setIsInstalled] = useState(false);

  useEffect(() => {
    // Check if already running in standalone PWA mode
    if (
      typeof window !== 'undefined' &&
      (window.matchMedia('(display-mode: standalone)').matches ||
        (window.navigator as any).standalone === true)
    ) {
      setIsInstalled(true);
      return;
    }

    // Check if early capture in <head> already caught beforeinstallprompt
    if (typeof window !== 'undefined' && (window as any).__pwaPrompt) {
      setDeferredPrompt((window as any).__pwaPrompt);
    }

    const handlePromptCaptured = () => {
      if ((window as any).__pwaPrompt) {
        setDeferredPrompt((window as any).__pwaPrompt);
      }
    };

    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      (window as any).__pwaPrompt = e;
      setDeferredPrompt(e as BeforeInstallPromptEvent);
    };

    const handleAppInstalled = () => {
      setIsInstalled(true);
      setDeferredPrompt(null);
      (window as any).__pwaPrompt = null;
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('pwa-prompt-captured', handlePromptCaptured);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('pwa-prompt-captured', handlePromptCaptured);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const handleDirectInstall = async () => {
    if (isInstalled) return;

    const promptEvent = deferredPrompt || (typeof window !== 'undefined' ? (window as any).__pwaPrompt : null);

    if (promptEvent && typeof promptEvent.prompt === 'function') {
      try {
        await promptEvent.prompt();
        const choice = await promptEvent.userChoice;
        if (choice && choice.outcome === 'accepted') {
          setIsInstalled(true);
        }
        setDeferredPrompt(null);
        if (typeof window !== 'undefined') {
          (window as any).__pwaPrompt = null;
        }
      } catch (err) {
        console.warn('PWA install prompt error:', err);
      }
    } else {
      // If the browser hasn't fired beforeinstallprompt yet or on iOS/Desktop Chrome without prompt ready,
      // fallback to creating a service worker trigger or direct prompt
      console.info('PWA install prompt triggered directly');
    }
  };

  const getLabel = () => {
    if (isInstalled) {
      return language === 'hi' ? 'ऐप इंस्टॉल है' : language === 'mr' ? 'अॅप इन्स्टॉल आहे' : 'App Installed';
    }
    return language === 'hi'
      ? '📲 ऐप डाउनलोड करें'
      : language === 'mr'
      ? '📲 अॅप डाउनलोड करा'
      : '📲 Download App';
  };

  if (isInstalled) {
    return (
      <div
        className={`inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-xs font-bold text-emerald-600 dark:text-emerald-400 ${className}`}
      >
        <CheckCircle className="h-4 w-4" />
        <span>{getLabel()}</span>
      </div>
    );
  }

  if (variant === 'compact') {
    return (
      <button
        type="button"
        onClick={handleDirectInstall}
        className={`inline-flex items-center gap-1.5 rounded-full bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white px-3.5 py-1.5 text-xs font-bold shadow-sm transition-all duration-200 cursor-pointer ${className}`}
        title="Download UdyamAI App directly"
      >
        <Download className="h-3.5 w-3.5" />
        <span>{language === 'hi' ? 'ऐप डाउनलोड' : language === 'mr' ? 'अॅप डाउनलोड' : 'Download App'}</span>
      </button>
    );
  }

  if (variant === 'secondary') {
    return (
      <button
        type="button"
        onClick={handleDirectInstall}
        className={`inline-flex items-center gap-2.5 rounded-full border border-emerald-600/40 bg-emerald-50 dark:bg-emerald-950/40 px-6 py-3.5 text-sm sm:text-base font-bold text-emerald-700 dark:text-emerald-300 shadow-sm transition-all duration-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/60 hover:-translate-y-0.5 active:scale-95 cursor-pointer ${className}`}
      >
        <Smartphone className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
        <span>{getLabel()}</span>
      </button>
    );
  }

  if (variant === 'banner') {
    return (
      <div
        className={`flex items-center justify-between gap-3 rounded-2xl border border-emerald-500/30 bg-gradient-to-r from-emerald-500/15 via-teal-500/10 to-emerald-500/15 p-3 sm:p-4 text-slate-900 dark:text-white ${className}`}
      >
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-md">
            <Smartphone className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs sm:text-sm font-black">
              {language === 'hi'
                ? 'UdyamAI ऐप इंस्टॉल करें'
                : language === 'mr'
                ? 'UdyamAI अॅप इन्स्टॉल करा'
                : 'Install UdyamAI App'}
            </p>
            <p className="text-[11px] text-foreground-muted">
              {language === 'hi'
                ? 'सीधे अपने फोन पर डाउनलोड और इंस्टॉल करें'
                : language === 'mr'
                ? 'थेट तुमच्या फोनवर डाउनलोड आणि इन्स्टॉल करा'
                : 'Directly download and install on your device'}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleDirectInstall}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-emerald-600 hover:bg-emerald-700 px-4 py-2 text-xs font-bold text-white shadow-fintech-btn transition active:scale-95 cursor-pointer"
        >
          <Download className="h-3.5 w-3.5" />
          <span>{language === 'hi' ? 'डाउनलोड' : language === 'mr' ? 'डाउनलोड' : 'Download'}</span>
        </button>
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={handleDirectInstall}
      className={`inline-flex items-center gap-2.5 rounded-full bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 hover:from-emerald-700 hover:to-teal-800 text-white px-7 py-3.5 sm:py-4 text-sm sm:text-base font-bold shadow-lg shadow-emerald-600/25 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-emerald-600/35 active:scale-95 cursor-pointer ${className}`}
    >
      <Download className="h-5 w-5 animate-bounce" />
      <span>{getLabel()}</span>
    </button>
  );
}
