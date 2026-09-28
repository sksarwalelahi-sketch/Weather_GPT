'use client'

import { useEffect, useMemo, useState } from 'react'
import { CloudRain, Droplets, Thermometer, TrendingUp } from 'lucide-react'
import { Card, PageHeader, StatTile } from '@/components/ui-kit'
import { MonthlyClimateChart, WarmingTrendChart } from '@/components/climate-charts'
import { getHistorical, type LiveHistorical } from '@/lib/live-api'
import { useDeviceLocation } from '@/components/location-provider'
import { LocationPermission } from '@/components/location-permission'
import { useLanguage } from '@/components/language-provider'

const languageLocale: Record<string, string> = {
  English: 'en-IN', Hindi: 'hi-IN', Bengali: 'bn-IN', Tamil: 'ta-IN',
  Telugu: 'te-IN', Marathi: 'mr-IN', Gujarati: 'gu-IN', Kannada: 'kn-IN', Odia: 'or-IN',
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function isoDate(date: Date) {
  return date.toISOString().slice(0, 10)
}

function buildMonthlyData(historical: LiveHistorical['historical'], locale: string) {
  const monthFormatter = new Intl.DateTimeFormat(locale, { month: 'short', timeZone: 'UTC' })
  return MONTHS.map((month, monthIndex) => {
    const values = historical.filter((day) => Number(day.date.slice(5, 7)) === monthIndex + 1)
    const count = Math.max(values.length, 1)
    return {
      month: monthFormatter.format(new Date(Date.UTC(2020, monthIndex, 1))),
      avgHigh: Number((values.reduce((sum, day) => sum + day.temperature_max, 0) / count).toFixed(1)),
      avgLow: Number((values.reduce((sum, day) => sum + day.temperature_min, 0) / count).toFixed(1)),
      rainfall: Number((values.reduce((sum, day) => sum + day.precipitation, 0) / Math.max(values.length / 30, 1)).toFixed(1)),
    }
  })
}

function buildTrendData(historical: LiveHistorical['historical']) {
  const byYear = new Map<string, number[]>()
  historical.forEach((day) => {
    const year = day.date.slice(0, 4)
    const values = byYear.get(year) ?? []
    values.push((day.temperature_max + day.temperature_min) / 2)
    byYear.set(year, values)
  })
  return [...byYear.entries()].map(([year, values]) => ({
    year,
    temp: Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(1)),
  }))
}

export default function Page() {
  const { location, locationName } = useDeviceLocation()
  const { language, t } = useLanguage()
  const [historical, setHistorical] = useState<LiveHistorical | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!location) return
    let cancelled = false
    const end = new Date()
    end.setUTCDate(end.getUTCDate() - 1)
    // Archive data is gridded; rounding avoids a new expensive request for
    // every small GPS movement and lets the backend reuse its cache.
    const latitude = Number(location.latitude.toFixed(2))
    const longitude = Number(location.longitude.toFixed(2))
    // Ten years is enough for a useful local trend and avoids oversized
    // historical archive requests. IMD historical data is fetched via Open-Meteo ERA5 archive.
    const start = new Date(end)
    start.setUTCFullYear(start.getUTCFullYear() - 10)
    void getHistorical(latitude, longitude, isoDate(start), isoDate(end))
      .then((result) => {
        if (!cancelled) {
          setHistorical(result)
          setError(null)
        }
      })
      .catch((reason: unknown) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : 'Historical climate service is unavailable.')
      })
    return () => { cancelled = true }
  }, [location])

  const locale = languageLocale[language] ?? 'en-IN'
  const monthly = useMemo(() => historical ? buildMonthlyData(historical.historical, locale) : [], [historical, locale])
  const trend = useMemo(() => historical ? buildTrendData(historical.historical) : [], [historical])
  const latest = trend.at(-1)
  const first = trend[0]
  const latestYearValues = historical?.historical.filter((day) => day.date.startsWith(`${latest?.year ?? ''}-`)) ?? []
  const annualRainfall = latestYearValues.reduce((sum, day) => sum + day.precipitation, 0)
  const wettest = monthly.reduce((max, point) => point.rainfall > max.rainfall ? point : max, monthly[0] ?? { month: '—', rainfall: 0 })
  const warmingRate = first && latest && Number(latest.year) > Number(first.year)
    ? ((latest.temp - first.temp) / ((Number(latest.year) - Number(first.year)) / 10)).toFixed(2)
    : '—'

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5 animate-in fade-in duration-500">
      <LocationPermission />
      {!location && <div className="rounded-2xl border border-border bg-card p-5 text-sm text-muted-foreground">{t('Enable location to load climate history for your area.')}</div>}
      {location && !historical && !error && <div role="status" className="rounded-2xl border border-border bg-card p-5 text-sm text-muted-foreground">{t('Loading live historical climate data for')} {locationName ?? t('your location')}…</div>}
      {error && <div role="alert" className="rounded-2xl border border-destructive/30 bg-destructive/5 p-5 text-sm text-destructive">{t('Unable to load climate history')}: {error}</div>}
      {historical && (
        <>
          <PageHeader title="Climate Analysis" subtitle={`${locationName ?? t('Your location')} · IMD / ERA5 climate archive · ${historical.start_date} to ${historical.end_date}`} icon={TrendingUp} />
          <div className="rounded-2xl border border-border bg-card px-4 py-3 text-xs text-muted-foreground">
            <span className="font-medium text-foreground">{t('Data provenance:')}</span> IMD-aligned ERA5 reanalysis {t('historical daily observations, aggregated locally into monthly and annual climate statistics.')}
          </div>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatTile icon={Thermometer} label={`Mean temp ${latest?.year ?? 'latest'}`} value={latest?.temp ?? '—'} unit="°C" hint={first && latest ? `${Number(latest.temp) >= Number(first.temp) ? '+' : ''}${(latest.temp - first.temp).toFixed(1)}° since ${first.year}` : 'Historical archive'} />
            <StatTile icon={TrendingUp} label="Warming rate" value={warmingRate} unit="°C/decade" hint="Calculated from archive" />
            <StatTile icon={CloudRain} label={`Annual rainfall ${latest?.year ?? ''}`} value={annualRainfall.toFixed(0)} unit="mm" hint="Historical total" />
            <StatTile icon={Droplets} label="Wettest month" value={wettest.month} hint={`${wettest.rainfall.toFixed(0)} mm average`} />
          </div>
          <Card>
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2"><h2 className="text-sm font-semibold">Monthly climate history</h2><span className="text-xs text-muted-foreground">Aggregated from daily data</span></div>
            <MonthlyClimateChart data={monthly} />
          </Card>
          <Card>
            <div className="mb-1 flex items-center justify-between"><h2 className="text-sm font-semibold">Historical warming trend</h2><span className="text-xs text-muted-foreground">{trend.length} annual points</span></div>
            <p className="mb-3 text-xs text-muted-foreground">Annual mean temperature calculated from daily maximum and minimum temperatures at your selected location.</p>
            <WarmingTrendChart data={trend} />
          </Card>
        </>
      )}
    </div>
  )
}
