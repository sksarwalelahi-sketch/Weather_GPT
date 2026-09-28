'use client'

import { useEffect, useState } from 'react'
import { CalendarDays, Droplets, Wind } from 'lucide-react'
import { WeatherIcon, conditionLabel } from '@/components/weather-icon'
import { Card, PageHeader } from '@/components/ui-kit'
import { ForecastChart } from '@/components/forecast-chart'
import { blendForecast, formatSourceTime, getForecast, getGfsForecast, resolveSourceLabel, type GfsForecast, type LiveForecast, weatherSummary } from '@/lib/live-api'
import { useDeviceLocation } from '@/components/location-provider'
import { LocationPermission } from '@/components/location-permission'
import { useLanguage } from '@/components/language-provider'

export default function Page() {
  const { location, locationName } = useDeviceLocation()
  const { t } = useLanguage()
  const [forecast, setForecast] = useState<LiveForecast | null>(null)
  const [gfsForecast, setGfsForecast] = useState<GfsForecast | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!location) return
    let cancelled = false
    void Promise.all([
      getForecast(location.latitude, location.longitude, 7),
      getGfsForecast(location.latitude, location.longitude),
    ]).then(([result, gfsResult]) => {
        if (!cancelled) {
          setGfsForecast(gfsResult)
          setForecast(blendForecast(result, gfsResult))
          setError(null)
        }
      })
      .catch((reason: unknown) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : 'Forecast service is unavailable.')
      })
    return () => { cancelled = true }
  }, [location])

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5 animate-in fade-in duration-500">
      <LocationPermission />
      {!forecast && !error && location && (
        <div role="status" className="rounded-2xl border border-border bg-card p-5 text-sm text-muted-foreground">
          {t('Loading live forecast for')} {locationName ?? t('your location')}…
        </div>
      )}
      {error && (
        <div role="alert" className="rounded-2xl border border-destructive/30 bg-destructive/5 p-5 text-sm text-destructive">
          {t('Unable to load live forecast')}: {error}
        </div>
      )}
      {forecast && (
        <>
          <PageHeader
            title="Forecast"
            subtitle={`${locationName ?? 'Your location'} · Open-Meteo forecast · ${forecast.timezone}`}
            icon={CalendarDays}
          />
          <div className="rounded-2xl border border-border bg-card px-4 py-3 text-xs text-muted-foreground">
            <span className="font-medium text-foreground">Data provenance:</span>{' '}
            {forecast.provenance?.provider ?? 'Unknown provider'} · {forecast.provenance?.role ?? 'Forecast data'} ·
            Retrieved {forecast.retrieved_at ? new Date(forecast.retrieved_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'recently'}
            {forecast.provenance?.confidence_label ? ` · Confidence: ${forecast.provenance.confidence_label}` : ''}
            {forecast.provenance?.limitation ? ` · ${forecast.provenance.limitation}` : ''}
          </div>
          <Card>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h2 className="text-sm font-semibold">Numerical model comparison</h2>
                <p className="mt-1 text-xs text-muted-foreground">
                  {gfsForecast?.status === 'live'
                    ? `NOAA GFS has ${gfsForecast.records.length} real model points available.`
                    : gfsForecast?.message ?? 'NOAA GFS is configured, but no model points are available for this location yet.'}
                </p>
              </div>
              <span className="rounded-full border border-border px-2.5 py-1 text-xs text-muted-foreground">
                {gfsForecast?.status === 'live' ? 'NOAA GFS · live model data' : `NOAA GFS · ${gfsForecast?.status ?? 'waiting for ingestion'}`}
              </span>
            </div>
            {gfsForecast?.status === 'live' && (
              <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
                {gfsForecast.records.map((record, index) => (
                  <div
                    key={`${record.valid_at}-${record.latitude}-${record.longitude}-${index}`}
                    className="min-w-28 rounded-xl border border-border bg-background p-3 text-xs"
                  >
                    <div className="text-muted-foreground">{formatSourceTime(record.valid_at)}</div>
                    <div className="mt-1 font-mono font-semibold">{record.temperature.toFixed(1)}°C</div>
                    <div className="text-muted-foreground">{record.wind_speed?.toFixed(1) ?? '—'} km/h wind</div>
                  </div>
                ))}
              </div>
            )}
          </Card>
          <Card>
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-sm font-semibold">Next 12 hours</h2>
              <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                <span className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-chart-1" /> Temp</span>
                <span className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-chart-3" /> Precipitation probability</span>
                <span className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-chart-2" /> Wind</span>
              </div>
            </div>
            <ForecastChart forecast={forecast} />
          </Card>
          <div>
            <h2 className="mb-3 px-1 text-sm font-semibold">7-day outlook</h2>
            <div className="flex flex-col gap-2.5">
              {forecast.forecast.map((day) => (
                <Card key={day.date} className="flex items-center gap-4 p-4">
                  <div className="w-24 shrink-0">
                    <div className="text-sm font-semibold">{new Date(`${day.date}T12:00:00`).toLocaleDateString([], { weekday: 'short' })}</div>
                    <div className="text-xs text-muted-foreground">{day.date}</div>
                  </div>
                  <WeatherIcon condition={weatherSummary(day.weather_code).condition} className="size-8 shrink-0" />
                  <div className="hidden min-w-0 flex-1 sm:block">
                    <div className="truncate text-sm font-medium">{conditionLabel(weatherSummary(day.weather_code).condition, t)}</div>
                    <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1"><Droplets className="size-3 text-primary" /> {day.precipitation_probability ?? '—'}%</span>
                      <span className="flex items-center gap-1"><Wind className="size-3" /> {day.wind_speed_max} km/h</span>
                      <span>Humidity {day.humidity ?? '—'}%</span>
                    </div>
                  </div>
                  <div className="ml-auto font-mono text-sm tabular-nums">
                    <span className="font-semibold">{day.temperature_max}°</span>
                    <span className="text-muted-foreground"> / {day.temperature_min}°</span>
                  </div>
                </Card>
              ))}
            </div>
          </div>
          <p className="text-xs text-muted-foreground">Source: {resolveSourceLabel(forecast.provenance, 'Open-Meteo')} · Forecast timezone: {forecast.timezone}</p>
        </>
      )}
    </div>
  )
}
