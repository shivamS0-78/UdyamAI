import './globals.css';
import React from 'react';
import type { Metadata, Viewport } from 'next';
import AuthProvider from '@/components/auth/AuthProvider';
import ChatWidget from '@/components/chat/ChatWidget';
import LanguageProvider from '@/components/i18n/LanguageProvider';
import ThemeProvider from '@/components/theme/ThemeProvider';
import ServiceWorkerRegister from '@/components/pwa/ServiceWorkerRegister';
import OfflineBanner from '@/components/ui/OfflineBanner';

export const metadata: Metadata = {
  title: "UdyamAI — Rural FinTech & Business Feasibility Platform",
  description: "AI-Powered Business Feasibility, Rural Finance & Government Scheme Intelligence",
  manifest: "/manifest.json",
  applicationName: "UdyamAI",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "UdyamAI",
  },
  icons: {
    icon: "/logo-icon.svg",
    apple: "/icons/apple-touch-icon.svg",
    shortcut: "/logo-icon.svg",
  },
};

export const viewport: Viewport = {
  themeColor: "#0f172a",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

const pwaAndThemeScript = `
  (function() {
    try {
      var stored = localStorage.getItem('udyam_theme');
      var isDark = stored === 'dark' || (!stored && window.matchMedia('(prefers-color-scheme: dark)').matches);
      if (isDark) {
        document.documentElement.classList.add('dark');
        document.documentElement.style.colorScheme = 'dark';
      } else {
        document.documentElement.classList.remove('dark');
        document.documentElement.style.colorScheme = 'light';
      }
    } catch(e) {}

    window.__pwaPrompt = null;
    window.addEventListener('beforeinstallprompt', function(e) {
      e.preventDefault();
      window.__pwaPrompt = e;
      window.dispatchEvent(new CustomEvent('pwa-prompt-captured'));
    });
  })();
`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: pwaAndThemeScript }} />
      </head>
      <body>
        <ServiceWorkerRegister />
        <OfflineBanner />
        <ThemeProvider>
          <LanguageProvider>
            <AuthProvider>
              {children}
              <ChatWidget />
            </AuthProvider>
          </LanguageProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

