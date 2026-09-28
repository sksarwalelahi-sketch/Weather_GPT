import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import { ThemeProvider } from '@/components/theme-provider'
import { LocationProvider } from '@/components/location-provider'
import { AppShell } from '@/components/app-shell'
import { AlertNotificationProvider } from '@/components/alert-notification-provider'
import { LanguageProvider } from '@/components/language-provider'
import './globals.css'

const geistSans = Geist({ subsets: ['latin'], variable: '--font-geist-sans' })
const geistMono = Geist_Mono({ subsets: ['latin'], variable: '--font-geist-mono' })

export const metadata: Metadata = {
  title: 'WeatherGPT — Conversational AI for Weather Forecasting & Alerts',
  description:
    'WeatherGPT delivers real-time weather intelligence, forecasts, extreme-weather alerts, GIS maps, climate trends, and sector advisories through a conversational, multilingual interface.',
  generator: 'v0.app',
  keywords: ['weather', 'forecast', 'AI chatbot', 'IMD', 'alerts', 'climate', 'GIS', 'India'],
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'WeatherGPT',
  },
  other: {
    'mobile-web-app-capable': 'yes',
    'application-name': 'WeatherGPT',
    'msapplication-TileColor': '#1e40af',
    'msapplication-config': '/browserconfig.xml',
  },
}

export const viewport: Viewport = {
  colorScheme: 'light dark',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#eef4ff' },
    { media: '(prefers-color-scheme: dark)', color: '#141d2e' },
  ],
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning className={`${geistSans.variable} ${geistMono.variable} bg-background`}>
      <body className="font-sans antialiased">
        <ThemeProvider>
          <LanguageProvider>
            <LocationProvider>
              <AlertNotificationProvider>
                <AppShell>{children}</AppShell>
              </AlertNotificationProvider>
            </LocationProvider>
          </LanguageProvider>
        </ThemeProvider>
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
