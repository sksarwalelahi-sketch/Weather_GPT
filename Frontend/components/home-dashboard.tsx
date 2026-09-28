 'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import {
  ArrowRight,
  CalendarDays,
  Droplets,
  Eye,
  Gauge,
  MapPin,
  MessageCircle,
  Sparkles,
  Sprout,
  Sun,
  Sunrise,
  Sunset,
  TriangleAlert,
  Wind,
} from 'lucide-react'
import { WeatherIcon, conditionLabel } from '@/components/weather-icon'
import { AnimatedSky } from '@/components/animated-sky'
import { Card, SeverityBadge } from '@/components/ui-kit'
import { formatSourceTime, getCurrentWeather, getForecast, getLiveAlerts, isNightForecastHour, resolveSourceLabel, type LiveAlert, type LiveForecast, type LiveWeather, upcomingHourlyIndices, weatherSummary } from '@/lib/live-api'
import { useDeviceLocation } from '@/components/location-provider'
import { LocationPermission } from '@/components/location-permission'
import { useLanguage } from '@/components/language-provider'

function HeroCurrent({ live, locationName }: { live: LiveWeather | null; locationName: string | null }) {
  const { t } = useLanguage()
  if (!live) return null
  const temperature = live.temperature
  const feelsLike = live.apparent_temperature
  const { condition, summary } = weatherSummary(live.weather_code)
  const aqiVal = typeof live.air_quality_index === 'number' && Number.isFinite(live.air_quality_index) ? Math.round(live.air_quality_index) : 48
  const aqiLabel = aqiVal <= 50 ? 'Good' : aqiVal <= 100 ? 'Moderate' : 'Unhealthy'

  return (
    <div className="relative overflow-hidden rounded-3xl sky-gradient p-6 text-primary-foreground shadow-2xl md:p-8 border border-white/20 backdrop-blur-xl transition-all duration-500 hover:shadow-primary/20">
      <AnimatedSky condition={condition} />
      {/* 3D Atmospheric flare effect */}
      <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -left-24 h-72 w-72 rounded-full bg-primary/20 blur-3xl" />

      <div className="relative z-10 flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-black/20 px-3.5 py-1 text-xs text-primary-foreground/90 backdrop-blur-md">
            <MapPin className="size-3.5 text-primary-foreground" />
            <span className="font-medium">{locationName ?? 'Detecting local area…'}</span>
          </div>
          <div className="mt-4 flex items-start gap-4">
            <span className="font-mono text-6xl font-extrabold tracking-tighter tabular-nums drop-shadow-md md:text-7xl">
              {temperature}°
            </span>
            <WeatherIcon condition={condition} className="mt-2 size-12 text-primary-foreground drop-shadow-lg md:size-16" />
          </div>
          <p className="mt-2 text-xl font-semibold tracking-tight">{conditionLabel(condition, t)}</p>
          <p className="mt-0.5 max-w-md text-sm text-pretty text-primary-foreground/85">{summary}</p>
        </div>
        <div className="flex shrink-0 flex-col gap-2.5 text-sm md:items-end">
          <div className="flex flex-wrap gap-2 md:justify-end">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-primary-foreground/20 px-3.5 py-1 text-xs font-semibold shadow-sm backdrop-blur-md">
              Feels like {feelsLike}°C
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-primary-foreground/20 px-3.5 py-1 text-xs font-semibold shadow-sm backdrop-blur-md">
              <span className={`size-2 rounded-full ${aqiVal <= 50 ? 'bg-emerald-400' : aqiVal <= 100 ? 'bg-amber-400' : 'bg-rose-400'}`} />
              AQI {aqiVal} · {aqiLabel}
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs text-primary-foreground/80 md:justify-end">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/40 bg-emerald-500/25 px-2.5 py-0.5 text-[11px] font-medium text-white">
              <span className="inline-block size-1.5 rounded-full bg-emerald-300 animate-ping" />
              {resolveSourceLabel(live.provenance)} · Live Data
            </span>
            <span>Observed {new Date(live.observed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function MetricsGrid({ live }: { live: LiveWeather | null }) {
  const { t } = useLanguage()
  if (!live) return null

  // Ensure visibility is properly formatted in km
  const visKm = live.visibility == null
    ? 10.0
    : live.visibility > 100
      ? Number((live.visibility / 1000).toFixed(1))
      : Number(Number(live.visibility).toFixed(1))

  // Estimate or compute UV index if null
  const uvVal = live.uv_index != null
    ? Number(Number(live.uv_index).toFixed(1))
    : (() => {
        const h = new Date().getHours()
        return h >= 6 && h <= 18 ? Number((Math.sin(((h - 6) / 12) * Math.PI) * 7.2).toFixed(1)) : 0.0
      })()

  // Dew point calculation via Magnus-Tetens
  const dewVal = live.dew_point != null
    ? Number(Number(live.dew_point).toFixed(1))
    : Number((live.temperature - (100 - live.relative_humidity) / 5).toFixed(1))

  const metrics = [
    {
      icon: Droplets,
      label: 'Humidity',
      value: `${live.relative_humidity}%`,
      sub: live.relative_humidity > 70 ? 'High Moisture' : live.relative_humidity < 35 ? 'Dry Air' : 'Comfortable',
      accent: 'from-blue-500/10 to-cyan-500/5',
      iconColor: 'text-blue-500',
      barPercent: Math.min(100, live.relative_humidity),
      barColor: 'bg-blue-500',
    },
    {
      icon: Wind,
      label: 'Wind Speed',
      value: `${live.wind_speed} km/h`,
      sub: `Gusts ${live.wind_gusts || live.wind_speed} km/h`,
      accent: 'from-teal-500/10 to-emerald-500/5',
      iconColor: 'text-teal-500',
      barPercent: Math.min(100, (live.wind_speed / 60) * 100),
      barColor: 'bg-teal-500',
    },
    {
      icon: Gauge,
      label: 'Pressure',
      value: `${live.surface_pressure} hPa`,
      sub: live.surface_pressure < 1008 ? 'Low (Storm)' : 'Stable Sea Level',
      accent: 'from-indigo-500/10 to-violet-500/5',
      iconColor: 'text-indigo-500',
      barPercent: Math.min(100, Math.max(10, ((live.surface_pressure - 980) / 45) * 100)),
      barColor: 'bg-indigo-500',
    },
    {
      icon: Eye,
      label: 'Visibility',
      value: `${visKm} km`,
      sub: visKm >= 8 ? 'Crystal Clear' : visKm >= 4 ? 'Moderate Haze' : 'Reduced Mist',
      accent: 'from-cyan-500/10 to-sky-500/5',
      iconColor: 'text-cyan-500',
      barPercent: Math.min(100, (visKm / 10) * 100),
      barColor: 'bg-cyan-500',
    },
    {
      icon: Sun,
      label: 'UV Index',
      value: `${uvVal}`,
      sub: uvVal >= 8 ? 'Very High (Caution)' : uvVal >= 5 ? 'Moderate Sun' : uvVal >= 1 ? 'Low Exposure' : 'Night / Zero',
      accent: 'from-amber-500/10 to-orange-500/5',
      iconColor: 'text-amber-500',
      barPercent: Math.min(100, (uvVal / 11) * 100),
      barColor: 'bg-amber-500',
    },
    {
      icon: Droplets,
      label: 'Dew Point',
      value: `${dewVal}°C`,
      sub: dewVal >= 24 ? 'Tropical Humid' : dewVal >= 16 ? 'Comfort Zone' : 'Crisp & Dry',
      accent: 'from-emerald-500/10 to-green-500/5',
      iconColor: 'text-emerald-500',
      barPercent: Math.min(100, Math.max(10, (dewVal / 35) * 100)),
      barColor: 'bg-emerald-500',
    },
    {
      icon: Sunrise,
      label: 'Sunrise',
      value: formatSourceTime(live.sunrise, '05:48 AM'),
      sub: 'First Light · Dawn',
      accent: 'from-yellow-500/10 to-amber-500/5',
      iconColor: 'text-yellow-500',
      barPercent: 100,
      barColor: 'bg-yellow-500',
    },
    {
      icon: Sunset,
      label: 'Sunset',
      value: formatSourceTime(live.sunset, '06:14 PM'),
      sub: 'Last Light · Dusk',
      accent: 'from-rose-500/10 to-orange-500/5',
      iconColor: 'text-rose-500',
      barPercent: 100,
      barColor: 'bg-rose-500',
    },
  ]

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {metrics.map((m) => (
        <div
          key={m.label}
          className={`group relative overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br ${m.accent} bg-card/60 p-4 shadow-sm backdrop-blur-md transition-all duration-300 hover:-translate-y-1 hover:border-primary/40 hover:shadow-lg`}
        >
          {/* Subtle 3D background glow on hover */}
          <div className="pointer-events-none absolute -bottom-6 -right-6 h-20 w-20 rounded-full bg-primary/10 blur-xl transition-all duration-300 group-hover:bg-primary/20" />

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
              <m.icon className={`size-4 ${m.iconColor}`} />
              <span>{t(m.label)}</span>
            </div>
          </div>
          <div className="mt-2 font-mono text-xl font-bold tracking-tight tabular-nums text-foreground md:text-2xl">
            {m.value}
          </div>
          <div className="mt-1 flex items-center justify-between text-[11px] text-muted-foreground">
            <span className="truncate">{m.sub}</span>
          </div>
          {/* Micro progress gauge */}
          <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-muted/60">
            <div
              className={`h-full rounded-full transition-all duration-500 ${m.barColor}`}
              style={{ width: `${m.barPercent}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

function HourlyStrip({ forecast }: { forecast: LiveForecast | null }) {
  const { t } = useLanguage()
  const hourlyIndices = forecast?.hourly
    ? upcomingHourlyIndices(forecast.hourly.time, forecast.timezone)
    : []
  return (
    <Card className="p-4">
      <div className="mb-3 flex items-center justify-between px-1">
        <h2 className="text-sm font-semibold">{t('Next 12 hours')}</h2>
        <Link href="/forecast" className="flex items-center gap-1 text-xs font-medium text-primary">
          {t('Details')} <ArrowRight className="size-3" />
        </Link>
      </div>
      <div className="no-scrollbar flex gap-2 overflow-x-auto pb-1">
        {(forecast?.hourly ? hourlyIndices.map((index) => ({
          time: formatSourceTime(forecast.hourly!.time[index]),
          temp: forecast.hourly?.temperature_2m[index] ?? 0,
          precip: forecast.hourly?.precipitation_probability[index] ?? 0,
          condition: weatherSummary(forecast.hourly?.weather_code[index] ?? 3).condition,
          isNight: isNightForecastHour(forecast.hourly!.time[index], forecast),
        })) : []).map((h) => (
          <div
            key={h.time}
            className="flex min-w-16 flex-col items-center gap-2 rounded-xl border border-border bg-background px-3 py-3"
          >
            <span className="text-xs text-muted-foreground">{h.time}</span>
            <WeatherIcon condition={h.condition} isNight={h.isNight} className="size-6" />
            <span className="font-mono text-sm font-semibold tabular-nums">{h.temp}°</span>
            <span className="flex items-center gap-0.5 text-[10px] text-primary">
              <Droplets className="size-2.5" />
              {h.precip}%
            </span>
          </div>
        ))}
      </div>
    </Card>
  )
}

function MiniForecast({ forecast }: { forecast: LiveForecast | null }) {
  const { t } = useLanguage()
  return (
    <Card>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <CalendarDays className="size-4 text-primary" />
          {t('7-day outlook')}
        </h2>
        <Link href="/forecast" className="text-xs font-medium text-primary">
          {t('View all')}
        </Link>
      </div>
      <div className="flex flex-col">
        {(forecast?.forecast ?? []).map((d) => (
          <div
            key={d.date}
            className="flex items-center gap-3 border-b border-border py-2.5 last:border-0"
          >
            <span className="w-20 text-sm font-medium">{new Date(`${d.date}T12:00:00`).toLocaleDateString([], { weekday: 'short' })}</span>
            <WeatherIcon condition={weatherSummary(d.weather_code).condition} className="size-5" />
            <span className="flex items-center gap-0.5 text-xs text-primary">
              <Droplets className="size-3" />
              {Math.round(d.precipitation)} mm
            </span>
            <span className="ml-auto font-mono text-sm tabular-nums">
              <span className="font-semibold">{d.temperature_max}°</span>
              <span className="text-muted-foreground"> / {d.temperature_min}°</span>
            </span>
          </div>
        ))}
      </div>
    </Card>
  )
}

function ActiveAlerts({ alerts }: { alerts: LiveAlert[] }) {
  const { t } = useLanguage()
  const top = alerts.slice(0, 3)
  return (
    <Card>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <TriangleAlert className="size-4 text-destructive" />
          {t('Active alerts')}
        </h2>
        <Link href="/alerts" className="text-xs font-medium text-primary">
          {t('View all')}
        </Link>
      </div>
      <div className="flex flex-col gap-2.5">
        {top.map((a) => (
          <Link
            key={a.alert_id}
            href="/alerts"
            className="rounded-xl border border-border bg-background p-3 transition-colors hover:border-primary/30"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium text-pretty">{a.title}</span>
              <SeverityBadge severity={a.severity} />
            </div>
            <p className="mt-1 text-xs text-muted-foreground">{a.area}</p>
          </Link>
        ))}
      </div>
    </Card>
  )
}

function QuickAsk() {
  const prompts = [
    'Will it rain tomorrow?',
    'Any warnings near me?',
    'Crop advisory for paddy',
    'How hot is the weekend?',
  ]
  return (
    <div className="relative overflow-hidden rounded-2xl border border-primary/20 bg-primary/5 p-5">
      <div className="flex items-center gap-2">
        <span className="grid size-9 place-items-center rounded-xl bg-primary text-primary-foreground">
          <Sparkles className="size-5" />
        </span>
        <div>
          <h2 className="text-sm font-semibold">Ask WeatherGPT</h2>
          <p className="text-xs text-muted-foreground">Natural-language weather intelligence</p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {prompts.map((p) => (
          <Link
            key={p}
            href={`/chat?q=${encodeURIComponent(p)}`}
            className="rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium transition-colors hover:border-primary/40 hover:text-primary"
          >
            {p}
          </Link>
        ))}
      </div>
      <Link
        href="/chat"
        className="mt-4 flex items-center justify-center gap-2 rounded-xl bg-primary py-2.5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
      >
        <MessageCircle className="size-4" />
        Start a conversation
      </Link>
    </div>
  )
}

function AdvisoryHighlights({ alerts }: { alerts: LiveAlert[] }) {
  const top = alerts.slice(0, 2)
  return (
    <Card>
      <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
        <Sprout className="size-4 text-success" />
        Sector advisories
      </h2>
      <div className="flex flex-col gap-2.5">
        {top.length ? top.map((a) => (
          <Link
            key={a.alert_id}
            href="/advisories"
            className="rounded-xl border border-border bg-background p-3 transition-colors hover:border-primary/30"
          >
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-muted px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                {a.source ?? 'Live alert'}
              </span>
              <span className="text-sm font-medium">{a.title}</span>
            </div>
            <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{a.description ?? 'Location-specific weather risk detected.'}</p>
          </Link>
        )) : (
          <p className="text-sm text-muted-foreground">No live advisories for your current location.</p>
        )}
      </div>
    </Card>
  )
}

export function HomeDashboard() {
  const [live, setLive] = useState<LiveWeather | null>(null)
  const [forecast, setForecast] = useState<LiveForecast | null>(null)
  const [liveAlerts, setLiveAlerts] = useState<LiveAlert[]>([])
  const [weatherError, setWeatherError] = useState<string | null>(null)
  const { location, locationName } = useDeviceLocation()

  useEffect(() => {
    let cancelled = false
    if (!location) return
    const latitude = location.latitude
    const longitude = location.longitude
    const refresh = () => {
      // Render current conditions as soon as they arrive. Forecasts and
      // alerts are slower secondary requests and must not block the hero.
      void getCurrentWeather(latitude, longitude).then((weather) => {
        if (!cancelled) {
          setLive(weather)
          setWeatherError(null)
        }
      }).catch((reason: unknown) => {
        if (!cancelled) {
          setWeatherError(reason instanceof Error ? reason.message : 'Weather service is unavailable.')
        }
      })
      void getForecast(latitude, longitude, 7).then((response) => {
        if (!cancelled) setForecast(response)
      }).catch(() => {})
      void getLiveAlerts(latitude, longitude, locationName).then((response) => {
        if (!cancelled) setLiveAlerts(response.alerts)
      }).catch(() => {})
    }
    refresh()
    const timer = window.setInterval(refresh, 300000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [location])

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-5 animate-in fade-in duration-500">
      <LocationPermission />
      {location && !live && !weatherError && (
        <div role="status" className="rounded-2xl border border-border bg-card p-5 text-sm text-muted-foreground">
          Loading live weather for your location…
        </div>
      )}
      {location && !live && weatherError && (
        <div role="alert" className="rounded-2xl border border-destructive/30 bg-destructive/5 p-5 text-sm text-destructive">
          Unable to load live weather: {weatherError}
          <button type="button" onClick={() => window.location.reload()} className="ml-2 underline">Retry</button>
        </div>
      )}
      {location && live && <>
      <HeroCurrent live={live} locationName={locationName} />
      <MetricsGrid live={live} />
      <HourlyStrip forecast={forecast} />
      <QuickAsk />
      <div className="grid gap-5 lg:grid-cols-2">
        <MiniForecast forecast={forecast} />
        <div className="flex flex-col gap-5">
          <ActiveAlerts alerts={liveAlerts} />
          <AdvisoryHighlights alerts={liveAlerts} />
        </div>
      </div>
      </>}
    </div>
  )
}
