'use client'

import { useEffect, useState, useMemo } from 'react'
import {
  AlertCircle, CheckCircle2, Clock, Filter, MapPin, Radio,
  ShieldAlert, Sparkles, TriangleAlert, Wind, Zap, CloudRain,
  ExternalLink, Siren,
} from 'lucide-react'
import { Card, PageHeader, SeverityBadge } from '@/components/ui-kit'
import { cn } from '@/lib/utils'
import { getActiveAlerts, getLiveAlerts, translateTexts, type LiveAlert } from '@/lib/live-api'
import { useDeviceLocation } from '@/components/location-provider'
import { useLanguage } from '@/components/language-provider'

// ── IMD colour-code map ───────────────────────────────────────────────────────
const IMD_COLOR_LABELS: Record<string, { label: string; cls: string }> = {
  '#FF0000': { label: 'RED ALERT',    cls: 'bg-red-600 text-white' },
  '#FFA500': { label: 'ORANGE WARN',  cls: 'bg-orange-500 text-white' },
  '#FFFF00': { label: 'YELLOW WATCH', cls: 'bg-yellow-400 text-black' },
  '#00FF00': { label: 'GREEN — SAFE', cls: 'bg-green-500 text-white' },
}

const accent: Record<string, string> = {
  advisory: 'border-l-primary',
  watch:    'border-l-amber-500',
  warning:  'border-l-orange-500',
  severe:   'border-l-red-600',
}

// Sources treated as "official IMD" for filtering/labelling
function isOfficialSource(src?: string | null) {
  const s = (src ?? '').toLowerCase()
  return s.includes('imd') || s.includes('gdacs') || s.includes('ndma')
}

function isCycloneAlert(a: LiveAlert) {
  const text = ((a.title ?? '') + ' ' + (a.description ?? '') + ' ' + (a.event ?? '')).toLowerCase()
  return (
    text.includes('cyclone') ||
    text.includes('depression') ||
    text.includes('cyclone_depression') ||
    text.includes('arnav') ||
    text.includes('arnab') ||
    a.event === 'cyclone_depression' ||
    a.event === 'cyclone_track'
  )
}

export default function Page() {
  const [liveAlerts, setLiveAlerts] = useState<LiveAlert[] | null>(null)
  const [filterSource, setFilterSource] = useState<'all' | 'imd' | 'ai'>('all')
  const { location, locationName } = useDeviceLocation()
  const { language, t } = useLanguage()

  useEffect(() => {
    let cancelled = false
    const refresh = async () => {
      try {
        const response = location
          ? await getLiveAlerts(location.latitude, location.longitude, locationName)
          : await getActiveAlerts()
        let alerts = response.alerts
        try {
          const strings = alerts.flatMap((alert) => [alert.title, alert.description ?? ''])
          const translated = await translateTexts(strings, language)
          alerts = alerts.map((alert, index) => ({
            ...alert,
            title:       translated[index * 2],
            description: alert.description ? translated[index * 2 + 1] : alert.description,
          }))
        } catch {
          // Keep official provider text if translation is unavailable
        }
        if (!cancelled) setLiveAlerts(alerts)
      } catch {
        if (!cancelled) setLiveAlerts([])
      }
    }
    void refresh()
    const timer = window.setInterval(refresh, 60_000)
    return () => { cancelled = true; window.clearInterval(timer) }
  }, [location, locationName, language])

  const displayAlerts = liveAlerts ?? []

  const filteredAlerts = useMemo(() => {
    if (filterSource === 'imd') return displayAlerts.filter((a) => isOfficialSource(a.source))
    if (filterSource === 'ai')  return displayAlerts.filter((a) => !isOfficialSource(a.source))
    return displayAlerts
  }, [displayAlerts, filterSource])

  const severe     = displayAlerts.filter((a) => a.severity === 'severe').length
  const warning    = displayAlerts.filter((a) => a.severity === 'warning').length
  const imdCount   = displayAlerts.filter((a) => isOfficialSource(a.source)).length
  const aiCount    = displayAlerts.filter((a) => !isOfficialSource(a.source)).length
  const cycloneAlerts = displayAlerts.filter(isCycloneAlert)

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-5 animate-in fade-in duration-500">
      <PageHeader
        title={t('Extreme Weather Alerts')}
        subtitle={`${locationName ?? t('Your region')} · ${t('Official IMD Warning Feeds & AI Risk Intelligence')}`}
        icon={TriangleAlert}
      />

      {/* ── Cyclone / Deep-Depression Emergency Banner ─────────────────────── */}
      {cycloneAlerts.length > 0 && (
        <div className="relative overflow-hidden rounded-2xl border border-red-500/40 bg-gradient-to-br from-red-950/80 via-red-900/60 to-orange-950/70 p-5 shadow-lg shadow-red-900/30">
          {/* animated pulse ring */}
          <span className="absolute right-4 top-4 flex size-10 items-center justify-center">
            <span className="absolute inline-flex size-full animate-ping rounded-full bg-red-400 opacity-40" />
            <Siren className="relative size-5 text-red-300" />
          </span>
          <div className="flex items-start gap-3">
            <div className="rounded-xl bg-red-500/20 p-2.5">
              <Wind className="size-6 text-red-300" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="rounded-md bg-red-600 px-2 py-0.5 text-[11px] font-bold text-white tracking-wide">
                  IMD CYCLONIC SYSTEM ALERT
                </span>
                <span className="rounded-md bg-orange-500/20 px-2 py-0.5 text-[11px] font-semibold text-orange-300">
                  Bay of Bengal
                </span>
              </div>
              <h2 className="mt-2 text-base font-bold text-red-100">
                Deep Depression / Cyclonic System Active
              </h2>
              <p className="mt-1 text-xs leading-relaxed text-red-200/80">
                IMD and GDACS data indicate a cyclonic system in the Bay of Bengal affecting your region.
                Heavy to very heavy rainfall, strong gusty winds and rough seas are expected.
                Follow NDMA / State DEOC evacuation advisories.
              </p>
              <div className="mt-3 flex flex-wrap gap-2 text-[11px]">
                <a
                  href="https://rsmcnewdelhi.imd.gov.in/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 rounded-md border border-red-500/30 bg-red-900/40 px-2.5 py-1.5 font-medium text-red-200 hover:bg-red-800/60 transition-colors"
                >
                  <ExternalLink className="size-3" /> IMD RSMC Cyclone
                </a>
                <a
                  href="https://www.gdacs.org/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 rounded-md border border-orange-500/30 bg-orange-900/40 px-2.5 py-1.5 font-medium text-orange-200 hover:bg-orange-800/60 transition-colors"
                >
                  <ExternalLink className="size-3" /> GDACS Live Track
                </a>
                <a
                  href="https://sachet.ndma.gov.in/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 rounded-md border border-yellow-500/30 bg-yellow-900/40 px-2.5 py-1.5 font-medium text-yellow-200 hover:bg-yellow-800/60 transition-colors"
                >
                  <ExternalLink className="size-3" /> NDMA SACHET
                </a>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Official IMD Integration Banner ─────────────────────────────────── */}
      <Card className="border-primary/25 bg-gradient-to-r from-primary/10 via-background to-primary/5 p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5 text-primary">
              <ShieldAlert className="size-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-semibold">{t('Official IMD & GDACS Alert Center')}</h2>
                <span className="flex items-center gap-1 rounded-full bg-green-500/15 px-2 py-0.5 text-[11px] font-medium text-green-600 dark:text-green-400">
                  <span className="size-1.5 rounded-full bg-green-500 animate-pulse" />
                  Live Feed
                </span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {t('Warnings from IMD forecast models, GDACS cyclone tracker, NDMA SACHET feeds and WeatherGPT AI risk detection.')}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-lg border border-border bg-card px-2.5 py-1.5 font-medium text-muted-foreground">
              {imdCount} {t('Official')}
            </span>
            <span className="rounded-lg border border-border bg-card px-2.5 py-1.5 font-medium text-muted-foreground">
              {aiCount} {t('AI Derived')}
            </span>
          </div>
        </div>
      </Card>

      {/* ── Severity Counters ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-3">
        <Card className="p-4 text-center border-destructive/20 bg-destructive/5">
          <div className="font-mono text-3xl font-semibold text-destructive">{severe}</div>
          <div className="text-xs font-medium text-muted-foreground">{t('Severe (Red)')}</div>
        </Card>
        <Card className="p-4 text-center border-orange-500/20 bg-orange-500/5">
          <div className="font-mono text-3xl font-semibold text-orange-600 dark:text-orange-400">{warning}</div>
          <div className="text-xs font-medium text-muted-foreground">{t('Warnings (Orange)')}</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="font-mono text-3xl font-semibold text-primary">{displayAlerts.length}</div>
          <div className="text-xs font-medium text-muted-foreground">{t('Total Active')}</div>
        </Card>
      </div>

      {/* ── IMD Colour-Code Legend ────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-2 text-[11px] font-medium">
        <span className="text-muted-foreground mr-1">{t('IMD Color Code:')}</span>
        {Object.entries(IMD_COLOR_LABELS).map(([hex, { label, cls }]) => (
          <span key={hex} className={cn('flex items-center gap-1.5 rounded-md px-2 py-1', cls)}>
            <span className="size-2 rounded-full border border-white/30" style={{ backgroundColor: hex }} />
            {label}
          </span>
        ))}
      </div>

      {/* ── Filter Tabs ───────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-2 border-b border-border pb-2 text-xs font-medium">
        <Filter className="size-3.5 text-muted-foreground" />
        <span className="text-muted-foreground">{t('Filter:')}</span>
        {(['all', 'imd', 'ai'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setFilterSource(tab)}
            className={cn(
              'rounded-full px-3 py-1 transition-colors',
              filterSource === tab
                ? 'bg-primary text-primary-foreground font-semibold'
                : 'text-muted-foreground hover:bg-muted',
            )}
          >
            {tab === 'all' ? `${t('All Alerts')} (${displayAlerts.length})`
              : tab === 'imd' ? `${t('Official IMD/GDACS')} (${imdCount})`
              : `${t('AI Intelligence')} (${aiCount})`}
          </button>
        ))}
      </div>

      {/* ── Alerts Stream ─────────────────────────────────────────────────────── */}
      {liveAlerts === null ? (
        <Card className="p-8 text-center">
          <div className="mx-auto size-10 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="mt-4 text-sm text-muted-foreground">{t('Fetching live alerts…')}</p>
        </Card>
      ) : filteredAlerts.length === 0 ? (
        <Card className="p-8 text-center">
          <CheckCircle2 className="mx-auto size-10 text-green-500/80" />
          <h3 className="mt-3 text-base font-semibold">{t('No Active Extreme Weather Warnings')}</h3>
          <p className="mt-1 text-xs text-muted-foreground max-w-md mx-auto">
            {t('No severe warnings or hazards are currently active for this area in official IMD bulletins or AI detection models.')}
          </p>
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          {filteredAlerts.map((a) => {
            const official = isOfficialSource(a.source)
            const isGdacs  = (a.source ?? '').toLowerCase().includes('gdacs')
            const cyclone  = isCycloneAlert(a)
            const colorHex = String(a.metadata?.color_code ?? '')
            const colorMeta = IMD_COLOR_LABELS[colorHex.toUpperCase()]
            const precip   = a.metadata?.precipitation_mm as number | undefined
            const wcode    = a.metadata?.weather_code as number | undefined
            const action   = a.metadata?.recommended_action as string | undefined

            return (
              <div
                key={a.alert_id}
                className={cn(
                  'rounded-2xl border border-l-4 border-border bg-card p-5 shadow-sm transition-all hover:shadow-md',
                  accent[a.severity] ?? 'border-l-primary',
                  cyclone && 'ring-1 ring-red-500/30',
                )}
              >
                {/* ── Header row ── */}
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="flex flex-col gap-1.5">
                    {/* Source badges */}
                    <div className="flex flex-wrap items-center gap-1.5">
                      {official ? (
                        isGdacs ? (
                          <span className="flex items-center gap-1 rounded-md bg-blue-500/10 px-2 py-0.5 text-[10px] font-semibold text-blue-600 dark:text-blue-400">
                            <Radio className="size-3" /> GDACS OFFICIAL
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 rounded-md bg-green-500/10 px-2 py-0.5 text-[10px] font-semibold text-green-600 dark:text-green-400">
                            <Radio className="size-3" /> IMD OFFICIAL
                          </span>
                        )
                      ) : (
                        <span className="flex items-center gap-1 rounded-md bg-purple-500/10 px-2 py-0.5 text-[10px] font-semibold text-purple-600 dark:text-purple-400">
                          <Sparkles className="size-3" /> AI INTELLIGENCE
                        </span>
                      )}
                      {cyclone && (
                        <span className="flex items-center gap-1 rounded-md bg-red-600/15 px-2 py-0.5 text-[10px] font-bold text-red-500">
                          <Wind className="size-3" /> CYCLONIC SYSTEM
                        </span>
                      )}
                      {/* IMD color code pill */}
                      {colorMeta && (
                        <span className={cn('rounded-md px-2 py-0.5 text-[10px] font-bold', colorMeta.cls)}>
                          {colorMeta.label}
                        </span>
                      )}
                    </div>
                    <h2 className="text-base font-semibold text-pretty">{a.title}</h2>
                  </div>
                  <SeverityBadge severity={a.severity} />
                </div>

                {/* ── Description ── */}
                <p className="mt-2.5 text-sm text-muted-foreground leading-relaxed text-pretty">
                  {a.description ?? t('Live alert from the weather data service.')}
                </p>

                {/* ── Telemetry row ── */}
                {(precip !== undefined || wcode !== undefined) && (
                  <div className="mt-3 flex flex-wrap gap-3 text-xs">
                    {precip !== undefined && (
                      <span className="flex items-center gap-1.5 rounded-lg border border-blue-500/20 bg-blue-500/10 px-2.5 py-1.5 text-blue-600 dark:text-blue-400 font-medium">
                        <CloudRain className="size-3.5" /> {precip} mm forecast
                      </span>
                    )}
                    {wcode !== undefined && wcode >= 95 && (
                      <span className="flex items-center gap-1.5 rounded-lg border border-yellow-500/20 bg-yellow-500/10 px-2.5 py-1.5 text-yellow-600 dark:text-yellow-400 font-medium">
                        <Zap className="size-3.5" /> WMO code {wcode} — Thunderstorm
                      </span>
                    )}
                  </div>
                )}

                {/* ── Advisory Action ── */}
                {action && (
                  <div className="mt-3 rounded-xl border border-border/60 bg-muted/30 p-3 text-xs">
                    <span className="font-semibold text-foreground flex items-center gap-1.5">
                      <AlertCircle className="size-3.5 text-primary" /> {t('Advisory Action:')}
                    </span>
                    <p className="mt-1 text-muted-foreground">{action}</p>
                  </div>
                )}

                {/* ── Footer ── */}
                <div className="mt-4 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2 pt-2 border-t border-border/40">
                  <span className="flex items-center gap-1.5">
                    <MapPin className="size-3.5 text-primary" />
                    {a.area ?? 'Area not specified'}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Clock className="size-3.5 text-primary" />
                    Issued {a.created_at
                      ? new Date(a.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })
                      : 'recently'}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
