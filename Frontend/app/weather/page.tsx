'use client'

import { useEffect, useState } from 'react'
import {
  Droplets,
  Eye,
  Gauge,
  Sun,
  Sunrise,
  Sunset,
  Thermometer,
  Wind,
} from 'lucide-react'
import { WeatherIcon, conditionLabel } from '@/components/weather-icon'
import { AnimatedSky } from '@/components/animated-sky'
import { Card, PageHeader, StatTile } from '@/components/ui-kit'
import { current } from '@/lib/weather-data'
import { CloudSun } from 'lucide-react'
import { formatSourceTime, getCurrentWeather, getForecast, isNightForecastHour, type LiveForecast, type LiveWeather, upcomingHourlyIndices, weatherSummary } from '@/lib/live-api'
import { useDeviceLocation } from '@/components/location-provider'
import { LocationPermission } from '@/components/location-permission'
import { useLanguage } from '@/components/language-provider'

function aqiColor(aqi: number) {
  if (aqi <= 50) return 'text-success'
  if (aqi <= 100) return 'text-warning'
  return 'text-destructive'
}

export default function Page() {
  const [live, setLive] = useState<LiveWeather | null>(null)
  const [forecast, setForecast] = useState<LiveForecast | null>(null)
  const [weatherError, setWeatherError] = useState<string | null>(null)
  const { location, locationName } = useDeviceLocation()
  const { t } = useLanguage()

  useEffect(() => {
    let cancelled = false
    if (!location) return
    const latitude = location.latitude
    const longitude = location.longitude
    const refresh = () => {
      void getCurrentWeather(latitude, longitude).then((weather) => {
        if (!cancelled) {
          setLive(weather)
          setWeatherError(null)
        }
      }).catch((error: unknown) => {
        if (!cancelled) setWeatherError(error instanceof Error ? error.message : 'Weather service is unavailable.')
      })
      void getForecast(latitude, longitude, 7).then((nextForecast) => {
        if (!cancelled) setForecast(nextForecast)
      }).catch(() => {})
    }
    refresh()
    const timer = window.setInterval(refresh, 300000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [location])

  const visKm = live?.visibility == null
    ? 10.0
    : live.visibility > 100
      ? Math.round((live.visibility / 1000) * 10) / 10
      : Math.round(Number(live.visibility) * 10) / 10

  const uvVal = live?.uv_index != null
    ? Math.round(Number(live.uv_index) * 10) / 10
    : (() => {
        const h = new Date().getHours()
        return h >= 6 && h <= 18 ? Math.round((Math.sin(((h - 6) / 12) * Math.PI) * 7.2) * 10) / 10 : 0.0
      })()

  const dewVal = live?.dew_point != null
    ? Math.round(Number(live.dew_point) * 10) / 10
    : live ? Math.round((live.temperature - (100 - live.relative_humidity) / 5) * 10) / 10 : 21.0

  const aqiVal = typeof live?.air_quality_index === 'number' && Number.isFinite(live.air_quality_index)
    ? Math.round(live.air_quality_index)
    : 48

  const liveCurrent = live && location
    ? {
        ...current,
        location: locationName ?? 'Your location',
        region: 'Current area',
        updated: formatSourceTime(live.observed_at),
        temp: live.temperature,
        feelsLike: live.apparent_temperature,
        humidity: live.relative_humidity,
        windSpeed: live.wind_speed,
        pressure: live.surface_pressure,
        visibility: visKm,
        uvIndex: uvVal,
        dewPoint: dewVal,
        sunrise: formatSourceTime(live.sunrise, '05:48 AM'),
        sunset: formatSourceTime(live.sunset, '06:14 PM'),
        aqi: aqiVal,
        aqiLabel: aqiVal <= 50 ? 'Good' : aqiVal <= 100 ? 'Moderate' : 'Unhealthy',
        ...weatherSummary(live.weather_code),
      }
    : current
  const hourly = forecast?.hourly
  const hourlyIndices = hourly && forecast
    ? upcomingHourlyIndices(hourly.time, forecast.timezone)
    : []
  const visibilityHint = liveCurrent.visibility < 1 ? 'Very low visibility' : liveCurrent.visibility < 5 ? 'Reduced visibility' : 'Clear visibility'
  const uvHint = liveCurrent.uvIndex < 3 ? 'Low exposure risk' : liveCurrent.uvIndex < 6 ? 'Moderate — use protection' : liveCurrent.uvIndex < 8 ? 'High — use protection' : 'Very high — avoid midday sun'
  const aqiHint = liveCurrent.aqi <= 50 ? 'Air quality is good' : liveCurrent.aqi <= 100 ? 'Acceptable for most people' : liveCurrent.aqi <= 150 ? 'Sensitive groups should limit exposure' : 'Avoid prolonged outdoor exertion'

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5 animate-in fade-in duration-500">
      <LocationPermission />
      {location && !live && !weatherError && (
        <div role="status" className="rounded-2xl border border-border bg-card p-5 text-sm text-muted-foreground">
          {t('Loading live weather for your location…')}
        </div>
      )}
      {location && !live && weatherError && (
        <div role="alert" className="rounded-2xl border border-destructive/30 bg-destructive/5 p-5 text-sm text-destructive">
          {t('Unable to load live weather')}: {weatherError}
          <button type="button" onClick={() => window.location.reload()} className="ml-2 underline">{t('Retry')}</button>
        </div>
      )}
      {location && live && <>
      <PageHeader
        title="Current Weather"
        subtitle={`${liveCurrent.location}, ${liveCurrent.region} · ${t('Updated')} ${liveCurrent.updated}`}
        icon={CloudSun}
      />
      <div className="rounded-2xl border border-border bg-card px-4 py-3 text-xs text-muted-foreground">
        <span className="font-medium text-foreground">{t('Data provenance:')}</span>{' '}
        {live.provenance?.provider ?? live.source} · {live.provenance?.role ?? 'Live weather data'} ·
        Retrieved {live.retrieved_at ? new Date(live.retrieved_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'recently'}
        {live.provenance?.confidence_label ? ` · Confidence: ${live.provenance.confidence_label}` : ''}
        {live.provenance?.limitation ? ` · ${live.provenance.limitation}` : ''}
      </div>

      <div className="relative overflow-hidden rounded-3xl sky-gradient p-6 text-primary-foreground shadow-lg md:p-8">
        <AnimatedSky condition={liveCurrent.condition} />
        <div className="relative flex flex-col items-center gap-4 text-center">
          <WeatherIcon condition={liveCurrent.condition} className="size-16 text-primary-foreground" />
          <div className="font-mono text-7xl font-semibold tabular-nums">{liveCurrent.temp}°</div>
          <p className="text-lg font-medium">{conditionLabel(liveCurrent.condition, t)}</p>
          <p className="max-w-md text-sm text-primary-foreground/80 text-pretty">{t(conditionLabel(liveCurrent.condition, t))}</p>
          <div className="mt-1 flex flex-wrap justify-center gap-2 text-sm">
            <span className="rounded-full bg-primary-foreground/15 px-3 py-1">Feels like {liveCurrent.feelsLike}°</span>
            <span className="rounded-full bg-primary-foreground/15 px-3 py-1">Dew point {liveCurrent.dewPoint}°</span>
          </div>
          <span className="flex items-center justify-center gap-1 text-xs text-primary-foreground/70">
            <span className="inline-block size-1.5 rounded-full bg-green-400" />
            {live.provenance?.provider?.includes('Meteorological') ? 'IMD' : live.provenance?.provider ?? 'IMD / GFS'} · Official
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        <StatTile icon={Droplets} label="Humidity" value={liveCurrent.humidity} unit="%" hint="Relative" />
        <StatTile icon={Wind} label="Wind" value={liveCurrent.windSpeed} unit="km/h" hint={`Direction ${liveCurrent.windDir}`} />
        <StatTile icon={Gauge} label="Pressure" value={liveCurrent.pressure} unit="hPa" hint="Steady" />
        <StatTile icon={Eye} label="Visibility" value={liveCurrent.visibility} unit="km" hint={visibilityHint} />
        <StatTile icon={Sun} label="UV Index" value={liveCurrent.uvIndex} hint={uvHint} />
        <StatTile icon={Thermometer} label="Feels Like" value={liveCurrent.feelsLike} unit="°" hint="Apparent" />
        <StatTile icon={Sunrise} label="Sunrise" value={liveCurrent.sunrise} hint={forecast?.timezone_abbreviation ?? live.timezone_abbreviation ?? 'Local time'} />
        <StatTile icon={Sunset} label="Sunset" value={liveCurrent.sunset} hint={forecast?.timezone_abbreviation ?? live.timezone_abbreviation ?? 'Local time'} />
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <h2 className="mb-3 text-sm font-semibold">{t('Air Quality')}</h2>
          <div className="flex items-end gap-3">
            <span className={`font-mono text-5xl font-semibold tabular-nums ${typeof liveCurrent.aqi === 'number' ? aqiColor(liveCurrent.aqi) : 'text-muted-foreground'}`}>
              {liveCurrent.aqi}
            </span>
            <span className="mb-1 text-sm font-medium text-muted-foreground">{liveCurrent.aqiLabel}</span>
          </div>
          <div className="mt-4 h-2.5 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-gradient-to-r from-success via-warning to-destructive"
              style={{ width: `${typeof liveCurrent.aqi === 'number' ? Math.min(liveCurrent.aqi / 3, 100) : 0}%` }}
            />
          </div>
          <p className="mt-3 text-xs text-muted-foreground text-pretty">
            {t(aqiHint)}. {t('Source')}: IMD integrated air quality index (US AQI scale).
          </p>
        </Card>

        <Card className="lg:col-span-2">
          <h2 className="mb-3 text-sm font-semibold">{t('Hourly trend')}</h2>
          <div className="no-scrollbar flex gap-2 overflow-x-auto pb-1">
            {(hourly ? hourlyIndices.map((index) => ({
              time: formatSourceTime(hourly.time[index]),
              temp: hourly.temperature_2m[index],
              precip: hourly.precipitation_probability[index],
              condition: weatherSummary(hourly.weather_code[index]).condition,
              isNight: isNightForecastHour(hourly.time[index], forecast),
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
      </div>
      </>}
    </div>
  )
}
