'use client'

import dynamic from 'next/dynamic'
import { useCallback, useEffect, useState } from 'react'
import { CloudRain, Layers, Thermometer, TriangleAlert, Tornado, Wind } from 'lucide-react'
import { cn } from '@/lib/utils'
import { PageHeader } from '@/components/ui-kit'
import { getSatelliteCatalog, type SatelliteCatalog } from '@/lib/live-api'
import { useDeviceLocation } from '@/components/location-provider'
import type { LiveMapStation } from '@/components/weather-map'
import { useLanguage } from '@/components/language-provider'

export type MapLayer = 'rainfall' | 'wind' | 'temperature' | 'alerts' | 'cyclone' | 'satellite'

const WeatherMap = dynamic(() => import('@/components/weather-map').then((m) => m.WeatherMap), {
  ssr: false,
  loading: () => (
    <div className="grid h-full w-full place-items-center bg-muted text-sm text-muted-foreground">
      Loading map…
    </div>
  ),
})

const layers: { id: MapLayer; label: string; icon: typeof CloudRain }[] = [
  { id: 'rainfall', label: 'Doppler Radar', icon: CloudRain },
  { id: 'wind', label: 'Wind Field', icon: Wind },
  { id: 'temperature', label: 'Isotherm Temp', icon: Thermometer },
  { id: 'alerts', label: 'Disaster Risks', icon: TriangleAlert },
  { id: 'cyclone', label: 'Vorticity / Cyclone', icon: Tornado },
  { id: 'satellite', label: 'INSAT-3DR', icon: Layers },
]

const layerPurpose: Record<MapLayer, string> = {
  rainfall: 'Real-time IMD S-Band Doppler weather radar reflectivity (dBZ) and convective precipitation nowcast.',
  wind: 'Surface wind velocity vectors and gust intensity points from automated meteorological telemetry.',
  temperature: 'Isothermal surface temperature distribution across regional observation stations.',
  alerts: 'Official IMD early warning color codes (Green / Yellow / Orange / Red) and severe risk sectors.',
  cyclone: 'Atmospheric circulation vorticity and pressure depression tracking for storm systems.',
  satellite: 'Live ISRO MOSDAC INSAT-3DR multispectral meteorological satellite granule telemetry.',
}

const legends: Record<MapLayer, { color: string; label: string }[]> = {
  rainfall: [
    { color: '#3b82f6', label: '10–20 dBZ (Light Drizzle)' },
    { color: '#10b981', label: '20–35 dBZ (Moderate Rain)' },
    { color: '#f59e0b', label: '35–50 dBZ (Heavy Downpour)' },
    { color: '#dc2626', label: '50+ dBZ (Severe Storm / Hail)' },
  ],
  wind: [
    { color: '#10b981', label: '< 20 km/h (Gentle)' },
    { color: '#f59e0b', label: '20–40 km/h (Breezy)' },
    { color: '#ef4444', label: '> 40 km/h (Gale / Gusts)' },
  ],
  temperature: [
    { color: '#10b981', label: '< 28°C (Mild)' },
    { color: '#f59e0b', label: '28–34°C (Warm)' },
    { color: '#ef4444', label: '> 34°C (Heat Stress)' },
  ],
  alerts: [
    { color: '#3b82f6', label: 'Green / Advisory' },
    { color: '#f59e0b', label: 'Yellow / Watch' },
    { color: '#f97316', label: 'Orange / Alert' },
    { color: '#ef4444', label: 'Red / Severe Warning' },
  ],
  cyclone: [{ color: '#8b5cf6', label: 'Circulation & Vorticity Zone' }],
  satellite: [{ color: '#06b6d4', label: 'INSAT-3DR MOSDAC Granule' }],
}

export function MapScreen() {
  const { t } = useLanguage()
  const [layer, setLayer] = useState<MapLayer>('rainfall')
  const [liveStations, setLiveStations] = useState<LiveMapStation[]>([])
  const { location, locationName, status, requestLocation } = useDeviceLocation()
  const [satelliteCatalog, setSatelliteCatalog] = useState<SatelliteCatalog | null>(null)
  const [satelliteError, setSatelliteError] = useState<string | null>(null)
  const [satelliteLoading, setSatelliteLoading] = useState(false)
  const handleStationsChange = useCallback((stations: LiveMapStation[]) => {
    setLiveStations(stations)
  }, [])

  useEffect(() => {
    if (layer !== 'satellite' || satelliteCatalog) return
    let cancelled = false
    setSatelliteLoading(true)
    void getSatelliteCatalog()
      .then((catalog) => {
        if (!cancelled) setSatelliteCatalog(catalog)
      })
      .catch((error) => {
        if (!cancelled) setSatelliteError(error instanceof Error ? error.message : 'Satellite catalog unavailable.')
      })
      .finally(() => {
        if (!cancelled) setSatelliteLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [layer, satelliteCatalog])

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-4 animate-in fade-in duration-500">
      <PageHeader
        title={t('Weather Map')}
        subtitle={location ? `${t('Live weather centered on')} ${locationName ?? t('your current area')}` : t('Enable location to center the live map on your current position')}
        icon={Layers}
      />

      <div className="no-scrollbar flex gap-2 overflow-x-auto">
        {layers.map((l) => {
          const active = layer === l.id
          return (
            <button
              key={l.id}
              onClick={() => setLayer(l.id)}
              className={cn(
                'flex shrink-0 items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-colors',
                active
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-border bg-card text-muted-foreground hover:text-foreground',
              )}
            >
              <l.icon className="size-4" />
              {t(l.label)}
            </button>
          )
        })}
      </div>
      <div className="rounded-xl border border-primary/20 bg-primary/5 px-4 py-3 text-sm">
        <div className="font-semibold">{t(layer === 'rainfall' ? 'Weather radar around you' : 'What this map shows')}</div>
        <p className="mt-1 text-muted-foreground">{t(layerPurpose[layer])}</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="relative h-[420px] overflow-hidden rounded-2xl border border-border lg:h-[560px]">
          <WeatherMap
            layer={layer}
            location={location}
            locationName={locationName}
            onStationsChange={handleStationsChange}
          />
          {layer === 'satellite' && (
            <div className="glass absolute right-3 top-3 z-[500] max-w-xs rounded-xl border border-border p-3 text-xs">
              <div className="font-semibold">{t('INSAT satellite data')}</div>
              <p className="mt-1 text-muted-foreground">
                {satelliteLoading
                  ? t('Loading live MOSDAC catalog metadata…')
                  : satelliteError ?? (satelliteCatalog
                    ? t('Live granule metadata available. Pixel imagery is not exposed by this catalog endpoint.')
                    : t('No satellite catalog metadata available.'))}
              </p>
            </div>
          )}
          <div className="absolute bottom-3 left-3 z-[500] hidden sm:block rounded-xl border border-white/15 bg-black/75 p-2.5 text-xs text-white shadow-2xl backdrop-blur-xl">
            <div className="mb-1.5 font-bold uppercase tracking-wider text-cyan-400 text-[10px]">{layer} scale</div>
            <div className="flex flex-col gap-1">
              {legends[layer].map((item) => (
                <div key={item.label} className="flex items-center gap-2">
                  <span className="size-2.5 rounded-full shadow-sm" style={{ background: item.color }} />
                  <span className="text-[11px] text-white/90">{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-2.5">
          {!location && (
            <button
              onClick={requestLocation}
              className="rounded-xl border border-primary/30 bg-primary/10 px-3 py-2.5 text-left text-sm font-medium text-primary shadow-sm hover:bg-primary/15 transition-all"
            >
              {status === 'requesting' ? t('Finding your location…') : t('Use my current location')}
            </button>
          )}
          <h2 className="px-1 text-sm font-semibold">
            {location ? `${t('Live points near')} ${locationName ?? t('your location')}` : t('Nearby live points')}
          </h2>
          {!location && (
            <div className="rounded-xl border border-border bg-card p-3 text-xs text-muted-foreground">
              {t('Allow location access to load weather points near you.')}
            </div>
          )}
          {liveStations.length === 0 && (
            <div className="rounded-xl border border-border bg-card p-3 text-xs text-muted-foreground">
              {t('Loading live observations…')}
            </div>
          )}
          {liveStations.map((s) => (
            <div
              key={s.id}
              className="group relative overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-card/90 via-card/70 to-card/40 p-3 shadow-sm backdrop-blur-md transition-all duration-300 hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md"
            >
              <div className="pointer-events-none absolute -bottom-6 -right-6 h-14 w-14 rounded-full bg-primary/10 blur-xl transition-all duration-300 group-hover:bg-primary/20" />
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold tracking-tight">{s.name}</span>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-mono font-bold text-emerald-500 border border-emerald-500/30">
                  <span className="size-1 rounded-full bg-emerald-500 animate-ping" />
                  LIVE
                </span>
              </div>
              <div className="mt-2 grid grid-cols-3 gap-1 rounded-xl bg-muted/40 p-1.5 text-center font-mono text-xs tabular-nums">
                <div>
                  <div className="text-[9px] text-muted-foreground uppercase">Temp</div>
                  <div className="font-bold text-foreground">{s.temperature}°C</div>
                </div>
                <div>
                  <div className="text-[9px] text-muted-foreground uppercase">Rain</div>
                  <div className="font-bold text-cyan-600 dark:text-cyan-400">{s.rainfall} mm</div>
                </div>
                <div>
                  <div className="text-[9px] text-muted-foreground uppercase">Wind</div>
                  <div className="font-bold text-teal-600 dark:text-teal-400">{s.wind} km/h</div>
                </div>
              </div>
              <div className="mt-1.5 flex items-center justify-between text-[10px] text-muted-foreground">
                <span className="truncate">{s.source}</span>
                {s.windDirection != null && <span>Vector {s.windDirection}°</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
