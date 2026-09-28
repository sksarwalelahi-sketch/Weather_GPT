'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import {
  CalendarDays,
  CloudSun,
  LayoutDashboard,
  Map,
  MapPin,
  Menu,
  MessageCircle,
  Moon,
  Search,
  Settings,
  Sprout,
  Sun,
  TrendingUp,
  TriangleAlert,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useTheme } from '@/components/theme-provider'
import { useDeviceLocation } from '@/components/location-provider'
import { useLanguage } from '@/components/language-provider'
import { LocationPicker } from '@/components/location-picker'

const nav = [
  { href: '/', key: 'Home', icon: LayoutDashboard },
  { href: '/chat', key: 'Chat', icon: MessageCircle },
  { href: '/weather', key: 'Current Weather', icon: CloudSun },
  { href: '/forecast', key: 'Forecast', icon: CalendarDays },
  { href: '/map', key: 'Weather Map', icon: Map },
  { href: '/alerts', key: 'Alerts', icon: TriangleAlert },
  { href: '/climate', key: 'Climate', icon: TrendingUp },
  { href: '/advisories', key: 'Advisories', icon: Sprout },
  { href: '/settings', key: 'Settings', icon: Settings },
]

const mobilePrimary = ['/', '/forecast', '/chat', '/map', '/alerts']

function Brand({ compact = false }: { compact?: boolean }) {
  const { t } = useLanguage()
  return (
    <Link href="/" className="flex items-center gap-2.5">
      <span className="grid size-9 place-items-center rounded-xl sky-gradient text-primary-foreground shadow-sm">
        <CloudSun className="size-5" />
      </span>
      {!compact && (
        <span className="flex flex-col leading-none">
          <span className="text-base font-semibold tracking-tight">WeatherGPT</span>
          <span className="text-[11px] text-muted-foreground">{t('Conversational Weather AI')}</span>
        </span>
      )}
    </Link>
  )
}

function ThemeToggle() {
  const { theme, toggle } = useTheme()
  return (
    <button
      onClick={toggle}
      aria-label="Toggle color theme"
      className="grid size-9 place-items-center rounded-lg border border-border bg-card text-muted-foreground transition-colors hover:text-foreground"
    >
      {theme === 'dark' ? <Sun className="size-4" /> : <Moon className="size-4" />}
    </button>
  )
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const { location, locationName, status, error, requestLocation } = useDeviceLocation()
  const { t } = useLanguage()
  const locationLabel = location
    ? (locationName ?? t('Finding your area…'))
    : status === 'requesting'
      ? t('Locating…')
      : t('Enable location')

  useEffect(() => {
    setDrawerOpen(false)
  }, [pathname])

  const isActive = (href: string) => (href === '/' ? pathname === '/' : pathname.startsWith(href))

  return (
    <div className="min-h-svh lg:grid lg:grid-cols-[260px_1fr]">
      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-svh flex-col border-r border-border bg-sidebar px-4 py-5 lg:flex">
        <div className="px-1">
          <Brand />
        </div>
        <nav className="mt-7 flex flex-1 flex-col gap-1">
          {nav.map((item) => {
            const active = isActive(item.href)
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  active
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                    : 'text-muted-foreground hover:bg-sidebar-accent/60 hover:text-foreground',
                )}
              >
                <item.icon className={cn('size-[18px]', active && 'text-primary')} />
                {t(item.key)}
              </Link>
            )
          })}
        </nav>
        <div className="rounded-xl border border-border bg-card p-3">
          <button onClick={requestLocation} className="flex items-center gap-2 text-left text-xs text-muted-foreground hover:text-foreground">
            <MapPin className="size-3.5 text-primary" />
            {location ? `${t('Your location')} · ${locationLabel}` : t('Location access needed')}
          </button>
          <p className="mt-1 text-sm font-medium">{t('Powered by IMD, GFS & WRF')}</p>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex min-h-svh flex-col">
        {/* Header */}
        <header className="glass sticky top-0 z-30 flex items-center gap-3 border-b border-border px-4 py-3 lg:px-8">
          <div className="lg:hidden">
            <Brand compact />
          </div>
          <button
            type="button"
            onClick={requestLocation}
            title={error ?? t('Use your current device location')}
            className="ml-auto flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-sm font-medium lg:ml-0"
          >
            <MapPin className="size-4 text-primary" />
            {locationLabel}
          </button>
          <LocationPicker />
          <Link
            href="/chat"
            className="hidden items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-sm text-muted-foreground transition-colors hover:text-foreground sm:flex md:ml-auto"
          >
            <Search className="size-4" />
            {t('Ask WeatherGPT anything…')}
          </Link>
          <div className="ml-auto flex items-center gap-2 sm:ml-0">
            <ThemeToggle />
          </div>
        </header>

        <main className="flex-1 px-4 pt-5 pb-28 lg:px-8 lg:pb-10">{children}</main>
      </div>

      {/* Mobile bottom nav */}
      <nav className="glass fixed inset-x-0 bottom-0 z-40 grid grid-cols-6 border-t border-border pb-[env(safe-area-inset-bottom)] lg:hidden">
        {nav
          .filter((n) => mobilePrimary.includes(n.href))
          .map((item) => {
            const active = isActive(item.href)
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex flex-col items-center gap-1 py-2.5 text-[10px] font-medium transition-colors',
                  active ? 'text-primary' : 'text-muted-foreground',
                )}
              >
                <item.icon className="size-5" />
                {t(item.key)}
              </Link>
            )
          })}
        <button
          onClick={() => setDrawerOpen(true)}
          className="flex flex-col items-center gap-1 py-2.5 text-[10px] font-medium text-muted-foreground"
        >
          <Menu className="size-5" />
          {t('More')}
        </button>
      </nav>

      {/* Mobile drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-foreground/40 backdrop-blur-sm animate-in fade-in"
            onClick={() => setDrawerOpen(false)}
          />
          <div className="absolute inset-x-0 bottom-0 rounded-t-3xl border-t border-border bg-card p-5 pb-8 animate-in slide-in-from-bottom">
            <div className="mb-4 flex items-center justify-between">
              <Brand />
              <button
                onClick={() => setDrawerOpen(false)}
                aria-label="Close menu"
                className="grid size-9 place-items-center rounded-lg border border-border text-muted-foreground"
              >
                <X className="size-4" />
              </button>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {nav.map((item) => {
                const active = isActive(item.href)
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'flex flex-col items-center gap-2 rounded-xl border p-4 text-xs font-medium transition-colors',
                      active
                        ? 'border-primary/40 bg-primary/10 text-primary'
                        : 'border-border bg-background text-muted-foreground',
                    )}
                  >
                    <item.icon className="size-5" />
                    {t(item.key)}
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
