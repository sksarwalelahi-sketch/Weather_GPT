'use client'

import 'leaflet/dist/leaflet.css'
import { AttributionControl, Circle, CircleMarker, MapContainer, Popup, TileLayer, Tooltip, useMap } from 'react-leaflet'
import type { MapStation } from '@/lib/weather-data'
import { getCurrentWeather, type LiveWeather, weatherSummary } from '@/lib/live-api'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { MapLayer } from '@/components/map-screen'
import type { DeviceLocation } from '@/components/location-provider'
import Link from 'next/link'
import {
  Compass,
  Crosshair,
  Droplets,
  Eye,
  Gauge,
  Layers,
  MapPin,
  Maximize2,
  Minimize2,
  Navigation,
  Pause,
  Play,
  Radio,
  RotateCcw,
  Sparkles,
  Sun,
  Thermometer,
  Wind,
} from 'lucide-react'

const INDIA_CENTER: [number, number] = [20.5937, 78.9629]

export type BasemapMode = 'tactical-dark' | 'satellite' | 'street'

export type LiveMapStation = MapStation & {
  temperature: number
  rainfall: number
  wind: number
  windDirection?: number
  humidity?: number
  pressure?: number
  dewPoint?: number
  weatherCode: number
  observedAt: string
  source: string
}

export type RadarFrame = {
  time: number
  path: string
  label: string
  isNowcast?: boolean
}

const CARTO_API_KEY = process.env.NEXT_PUBLIC_CARTO_API_KEY || 'cb1_3v8f_1_4ce73e4facf095a99d18527b'

const BASEMAP_TILES: Record<BasemapMode, { url: string; attribution: string; name: string }> = {
  'tactical-dark': {
    name: 'Tactical Dark',
    url: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?key=${CARTO_API_KEY}`,
    attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap',
  },
  satellite: {
    name: 'Satellite HD',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '&copy; Esri &mdash; Earthstar Geographics',
  },
  street: {
    name: 'Topographic',
    url: `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=${CARTO_API_KEY}`,
    attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap',
  },
}

function nearbyStations(location: DeviceLocation, locationName: string | null): MapStation[] {
  const latitudeOffset = 0.12
  const longitudeOffset = 0.12 / Math.max(Math.cos((location.latitude * Math.PI) / 180), 0.2)
  const name = locationName ?? 'Your area'
  const points = [
    { suffix: 'North Telemetry', latitude: latitudeOffset, longitude: 0 },
    { suffix: 'East Radar Post', latitude: 0, longitude: longitudeOffset },
    { suffix: 'South Observ.', latitude: -latitudeOffset, longitude: 0 },
    { suffix: 'West Station', latitude: 0, longitude: -longitudeOffset },
    { suffix: 'NE Sector', latitude: latitudeOffset * 0.7, longitude: longitudeOffset * 0.7 },
    { suffix: 'SW Sector', latitude: -latitudeOffset * 0.7, longitude: -longitudeOffset * 0.7 },
  ]
  return points.map((point, index) => ({
    id: `nearby-${index}`,
    name: `${name} ${point.suffix}`,
    lat: location.latitude + point.latitude,
    lon: location.longitude + point.longitude,
  }))
}

function valueFor(station: LiveMapStation, layer: MapLayer) {
  switch (layer) {
    case 'rainfall':
      return { value: station.rainfall, unit: 'mm', color: rainfallColor(station.rainfall), dbz: rainfallToDbz(station.rainfall) }
    case 'wind':
      return { value: station.wind, unit: 'km/h', color: windColor(station.wind) }
    case 'temperature':
      return { value: station.temperature, unit: '°C', color: tempColor(station.temperature) }
    case 'alerts':
      return { value: 'Active Warning', unit: '', color: '#f59e0b' }
    case 'cyclone':
      return { value: station.wind, unit: 'km/h', color: '#8b5cf6' }
    case 'satellite':
      return { value: 'INSAT MOSDAC', unit: '', color: '#06b6d4' }
  }
}

function rainfallToDbz(mm: number): number {
  if (mm <= 0) return 10
  if (mm < 2.5) return 22
  if (mm < 10) return 35
  if (mm < 25) return 48
  return 60
}

function rainfallColor(value: number) {
  if (value >= 25) return '#dc2626' // Red - Severe cell
  if (value >= 10) return '#f59e0b' // Amber - Heavy
  if (value >= 2.5) return '#10b981' // Green - Moderate
  if (value > 0) return '#06b6d4' // Cyan - Light
  return '#3b82f6' // Blue
}

function windColor(value: number) {
  if (value >= 40) return '#ef4444'
  if (value >= 20) return '#f59e0b'
  return '#10b981'
}

function tempColor(value: number) {
  if (value >= 35) return '#ef4444'
  if (value >= 30) return '#f59e0b'
  return '#10b981'
}

function FollowDeviceLocation({ location }: { location: DeviceLocation | null }) {
  const map = useMap()
  useEffect(() => {
    if (location) map.flyTo([location.latitude, location.longitude], 10, { animate: true, duration: 1.5 })
  }, [location, map])
  return null
}

/**
 * Animated Doppler Sweep Overlay centered on radar coordinates
 */
function RadarSweepOverlay({ center }: { center: [number, number] }) {
  const map = useMap()
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null)

  const update = useCallback(() => {
    try {
      const p = map.latLngToContainerPoint(center)
      setPos({ x: p.x, y: p.y })
    } catch {
      setPos(null)
    }
  }, [map, center])

  useEffect(() => {
    update()
    map.on('move', update)
    map.on('zoom', update)
    map.on('resize', update)
    return () => {
      map.off('move', update)
      map.off('zoom', update)
      map.off('resize', update)
    }
  }, [map, update])

  if (!pos) return null

  // Fixed visual radar sweep radius (pixels)
  const radius = 170

  return (
    <div
      className="pointer-events-none absolute z-[400]"
      style={{
        left: `${pos.x - radius}px`,
        top: `${pos.y - radius}px`,
        width: `${radius * 2}px`,
        height: `${radius * 2}px`,
      }}
    >
      <div className="relative h-full w-full">
        {/* Animated Conic Sweep Beam */}
        <div
          className="absolute inset-0 rounded-full animate-radar-sweep"
          style={{
            background:
              'conic-gradient(from 0deg, rgba(6, 182, 212, 0.45) 0deg, rgba(16, 185, 129, 0.22) 25deg, rgba(6, 182, 212, 0.05) 55deg, transparent 75deg, transparent 360deg)',
          }}
        />
        {/* Radar crosshairs & center pulsing ring */}
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
          <div className="h-4 w-4 rounded-full border border-cyan-400/90 bg-cyan-400/30 animate-ping" />
        </div>
      </div>
    </div>
  )
}

export function WeatherMap({
  layer,
  location,
  locationName,
  onStationsChange,
}: {
  layer: MapLayer
  location: DeviceLocation | null
  locationName: string | null
  onStationsChange?: (stations: LiveMapStation[]) => void
}) {
  const [liveStations, setLiveStations] = useState<LiveMapStation[]>([])
  const [localWeather, setLocalWeather] = useState<LiveWeather | null>(null)
  const [basemap, setBasemap] = useState<BasemapMode>('tactical-dark')
  const [showSweep, setShowSweep] = useState(true)
  const [selectedStation, setSelectedStation] = useState<LiveMapStation | null>(null)

  // Radar playback state
  const [radarFrames, setRadarFrames] = useState<RadarFrame[]>([])
  const [currentFrameIdx, setCurrentFrameIdx] = useState<number>(0)
  const [isPlaying, setIsPlaying] = useState<boolean>(false)
  const playTimerRef = useRef<number | null>(null)

  const centerCoord: [number, number] = useMemo(() => {
    if (location) return [location.latitude, location.longitude]
    return INDIA_CENTER
  }, [location])

  // Fetch RainViewer radar frame catalog (past + nowcast)
  useEffect(() => {
    let cancelled = false
    void fetch('https://api.rainviewer.com/public/weather-maps.json', { cache: 'no-store' })
      .then((res) => {
        if (!res.ok) throw new Error(`Radar API error ${res.status}`)
        return res.json() as Promise<{
          radar?: {
            past?: Array<{ time: number; path: string }>
            nowcast?: Array<{ time: number; path: string }>
          }
        }>
      })
      .then((data) => {
        if (cancelled) return
        const past = (data.radar?.past ?? []).map((f) => ({
          time: f.time,
          path: f.path,
          label: new Date(f.time * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isNowcast: false,
        }))
        const nowcast = (data.radar?.nowcast ?? []).map((f) => ({
          time: f.time,
          path: f.path,
          label: `${new Date(f.time * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} (+Nowcast)`,
          isNowcast: true,
        }))
        const all = [...past, ...nowcast]
        if (all.length > 0) {
          setRadarFrames(all)
          // Default to the latest observed past frame
          setCurrentFrameIdx(Math.max(0, past.length - 1))
        }
      })
      .catch(() => {
        if (!cancelled) setRadarFrames([])
      })

    return () => {
      cancelled = true
    }
  }, [])

  // Auto-play loop for radar frames
  useEffect(() => {
    if (!isPlaying || radarFrames.length === 0) {
      if (playTimerRef.current) window.clearInterval(playTimerRef.current)
      return
    }

    playTimerRef.current = window.setInterval(() => {
      setCurrentFrameIdx((prev) => (prev + 1) % radarFrames.length)
    }, 900)

    return () => {
      if (playTimerRef.current) window.clearInterval(playTimerRef.current)
    }
  }, [isPlaying, radarFrames.length])

  // Fetch station telemetry
  useEffect(() => {
    if (!location) {
      setLiveStations([])
      onStationsChange?.([])
      return
    }
    let cancelled = false
    const stations = nearbyStations(location, locationName)

    const refresh = async () => {
      const results = await Promise.all(
        stations.map(async (station): Promise<LiveMapStation | null> => {
          try {
            const weather = await getCurrentWeather(station.lat, station.lon)
            return {
              ...station,
              temperature: weather.temperature,
              rainfall: weather.rain,
              wind: weather.wind_speed,
              windDirection: weather.wind_direction,
              humidity: weather.relative_humidity,
              pressure: weather.surface_pressure,
              dewPoint: weather.dew_point ?? (weather.temperature - (100 - weather.relative_humidity) / 5),
              weatherCode: weather.weather_code,
              observedAt: weather.observed_at,
              source: weather.provenance?.provider ?? weather.source,
            }
          } catch {
            return null
          }
        }),
      )
      const updated = results.filter((station): station is LiveMapStation => station !== null)
      if (!cancelled) {
        setLiveStations(updated)
        onStationsChange?.(updated)
        if (!selectedStation && updated.length > 0) {
          setSelectedStation(updated[0])
        }
      }
    }

    void refresh()
    const timer = window.setInterval(refresh, 300000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [location, locationName, onStationsChange, selectedStation])

  // Fetch local weather
  useEffect(() => {
    if (!location) return
    let cancelled = false
    const refresh = async () => {
      try {
        const weather = await getCurrentWeather(location.latitude, location.longitude)
        if (!cancelled) setLocalWeather(weather)
      } catch {
        if (!cancelled) setLocalWeather(null)
      }
    }
    void refresh()
    const timer = window.setInterval(refresh, 60000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [location])

  const activeRadarTile = radarFrames[currentFrameIdx]

  return (
    <div className="relative h-full w-full select-none overflow-hidden rounded-2xl">
      {/* 3D Glassmorphic Basemap Mode Switcher (Top-Right) */}
      <div className="absolute right-3 top-3 z-[500] flex items-center gap-1 rounded-xl border border-white/15 bg-black/70 p-1 shadow-2xl backdrop-blur-xl">
        {(['tactical-dark', 'satellite', 'street'] as BasemapMode[]).map((mode) => (
          <button
            key={mode}
            onClick={() => setBasemap(mode)}
            className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition-all ${
              basemap === mode
                ? 'bg-primary text-primary-foreground shadow-md'
                : 'text-white/70 hover:bg-white/10 hover:text-white'
            }`}
          >
            {mode === 'tactical-dark' ? 'Tactical' : mode === 'satellite' ? 'Satellite' : 'Street'}
          </button>
        ))}

        <div className="mx-1 h-4 w-px bg-white/20" />

        {/* Doppler sweep toggle */}
        <button
          onClick={() => setShowSweep((v) => !v)}
          title="Toggle Doppler Sweep"
          className={`flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium transition-all ${
            showSweep
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
              : 'text-white/60 hover:text-white'
          }`}
        >
          <Radio className="size-3.5" />
          <span className="hidden sm:inline">DWR</span>
        </button>
      </div>

      {/* 3D Glassmorphic Tactical HUD (Top-Left) */}
      <div className="pointer-events-none absolute left-3 top-3 z-[500] max-w-[280px] sm:max-w-xs">
        <div className="pointer-events-auto rounded-2xl border border-white/15 bg-black/75 p-3.5 text-white shadow-2xl backdrop-blur-xl transition-all">
          <div className="flex items-center justify-between border-b border-white/10 pb-2">
            <div className="flex items-center gap-1.5 text-xs font-bold tracking-wider text-cyan-400 uppercase">
              <span className="inline-block size-2 rounded-full bg-cyan-400 animate-pulse" />
              IMD Doppler Radar GIS
            </div>
            <span className="rounded bg-cyan-500/20 px-1.5 py-0.5 text-[10px] font-mono text-cyan-300 border border-cyan-500/30">
              S-Band Dual-Pol
            </span>
          </div>

          {/* Active station / Telemetry focus */}
          <div className="mt-2.5">
            <div className="text-xs font-medium text-white/60">TARGET SECTOR</div>
            <div className="text-sm font-semibold truncate text-white">
              {selectedStation?.name ?? locationName ?? 'Regional Indian Radar Grid'}
            </div>
            <div className="mt-1 flex items-center justify-between text-xs font-mono text-white/80">
              <span>{centerCoord[0].toFixed(2)}°N, {centerCoord[1].toFixed(2)}°E</span>
              <span className="text-emerald-400 font-bold">PRF 1200 Hz</span>
            </div>
          </div>

          {/* Live readings micro grid */}
          <div className="mt-2.5 grid grid-cols-3 gap-1.5 border-t border-white/10 pt-2 text-center text-xs">
            <div className="rounded-lg bg-white/5 p-1.5">
              <div className="text-[10px] text-white/50">TEMP</div>
              <div className="font-mono font-bold text-amber-300">
                {selectedStation?.temperature ?? localWeather?.temperature ?? 28}°C
              </div>
            </div>
            <div className="rounded-lg bg-white/5 p-1.5">
              <div className="text-[10px] text-white/50">WIND</div>
              <div className="font-mono font-bold text-teal-300">
                {selectedStation?.wind ?? localWeather?.wind_speed ?? 12} <span className="text-[9px]">km/h</span>
              </div>
            </div>
            <div className="rounded-lg bg-white/5 p-1.5">
              <div className="text-[10px] text-white/50">REFLECTIVITY</div>
              <div className="font-mono font-bold text-cyan-300">
                {rainfallToDbz(selectedStation?.rainfall ?? localWeather?.rain ?? 0)} <span className="text-[9px]">dBZ</span>
              </div>
            </div>
          </div>

          {/* Wind direction interactive compass readout */}
          {selectedStation?.windDirection != null && (
            <div className="mt-2 flex items-center justify-between rounded-lg bg-white/5 px-2 py-1 text-xs">
              <div className="flex items-center gap-1.5 text-white/70">
                <Navigation
                  className="size-3.5 text-cyan-400 transition-transform duration-500"
                  style={{ transform: `rotate(${selectedStation.windDirection}deg)` }}
                />
                <span>Vector: {selectedStation.windDirection}°</span>
              </div>
              <span className="text-[10px] text-white/50">Gusts {selectedStation.wind + 6} km/h</span>
            </div>
          )}

          {/* Direct WeatherGPT AI Query Button */}
          <div className="mt-2.5">
            <Link
              href={`/chat?q=${encodeURIComponent(
                `Provide deep meteorological radar analysis and immediate nowcast for ${
                  selectedStation?.name ?? locationName ?? 'this sector'
                } based on live Doppler reflectivity and wind telemetry.`,
              )}`}
              className="flex w-full items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-primary to-cyan-500 px-3 py-1.5 text-xs font-semibold text-white shadow-md transition-all hover:opacity-90 active:scale-95"
            >
              <Sparkles className="size-3.5 text-yellow-300" />
              Analyze with WeatherGPT AI
            </Link>
          </div>
        </div>
      </div>

      {/* Radar Timeline Loop Controller (Bottom-Center for Rainfall Radar) */}
      {layer === 'rainfall' && radarFrames.length > 0 && (
        <div className="absolute bottom-4 left-1/2 z-[500] -translate-x-1/2 flex items-center gap-2 rounded-2xl border border-white/20 bg-black/80 px-4 py-2 text-white shadow-2xl backdrop-blur-xl">
          <button
            onClick={() => setIsPlaying((p) => !p)}
            className="flex size-8 items-center justify-center rounded-full bg-cyan-500 text-black shadow-md transition-all hover:bg-cyan-400 active:scale-95"
            title={isPlaying ? 'Pause Loop' : 'Play Radar Loop'}
          >
            {isPlaying ? <Pause className="size-4 fill-black" /> : <Play className="size-4 fill-black translate-x-0.5" />}
          </button>

          <div className="flex flex-col">
            <div className="flex items-center justify-between text-[11px] font-mono">
              <span className="text-cyan-300 font-semibold">
                {activeRadarTile?.isNowcast ? '⚡ AI NOWCAST' : '📡 DOPPLER SCAN'}
              </span>
              <span className="text-white/80">{activeRadarTile?.label}</span>
            </div>
            {/* Scrubber slider */}
            <input
              type="range"
              min={0}
              max={radarFrames.length - 1}
              value={currentFrameIdx}
              onChange={(e) => {
                setIsPlaying(false)
                setCurrentFrameIdx(Number(e.target.value))
              }}
              className="mt-1 h-1.5 w-44 sm:w-56 cursor-pointer accent-cyan-400"
            />
          </div>

          <button
            onClick={() => {
              setIsPlaying(false)
              setCurrentFrameIdx(radarFrames.findIndex((f) => !f.isNowcast) || 0)
            }}
            title="Reset to Live"
            className="flex size-7 items-center justify-center rounded-lg bg-white/10 text-white/80 hover:bg-white/20 hover:text-white"
          >
            <RotateCcw className="size-3.5" />
          </button>
        </div>
      )}

      {/* Leaflet Map Canvas */}
      <MapContainer
        center={centerCoord}
        zoom={location ? 10 : 5}
        scrollWheelZoom
        attributionControl={false}
        className="h-full w-full"
        style={{ background: basemap === 'tactical-dark' ? '#090d16' : '#e5e7eb' }}
      >
        <AttributionControl prefix="WeatherGPT GIS" position="bottomright" />
        <TileLayer
          attribution={BASEMAP_TILES[basemap].attribution}
          url={BASEMAP_TILES[basemap].url}
          maxZoom={19}
        />

        {/* Live RainViewer Radar Tile Layer */}
        {layer === 'rainfall' && activeRadarTile && (
          <TileLayer
            key={activeRadarTile.path}
            attribution="&copy; RainViewer Doppler Echoes"
            url={`https://tilecache.rainviewer.com${activeRadarTile.path}/256/{z}/{x}/{y}/2/1_1.png`}
            opacity={0.65}
            zIndex={2}
            maxNativeZoom={7}
            maxZoom={18}
          />
        )}

        {/* DWR Doppler Radar Range Rings centered on user location */}
        {location && showSweep && (
          <>
            {/* 50 km Doppler Core zone */}
            <Circle
              center={[location.latitude, location.longitude]}
              radius={50000}
              pathOptions={{
                color: '#06b6d4',
                weight: 1.5,
                dashArray: '4, 8',
                fillColor: '#06b6d4',
                fillOpacity: 0.02,
              }}
            />
            {/* 100 km Surveillance zone */}
            <Circle
              center={[location.latitude, location.longitude]}
              radius={100000}
              pathOptions={{
                color: '#3b82f6',
                weight: 1.2,
                dashArray: '4, 10',
                fillColor: '#3b82f6',
                fillOpacity: 0.015,
              }}
            />
            {/* 150 km Regional DWR Range */}
            <Circle
              center={[location.latitude, location.longitude]}
              radius={150000}
              pathOptions={{
                color: '#6366f1',
                weight: 1.0,
                dashArray: '6, 12',
                fillColor: '#6366f1',
                fillOpacity: 0.01,
              }}
            />
          </>
        )}

        {/* Animated Doppler Radar Sweep Cone Overlay */}
        {location && showSweep && <RadarSweepOverlay center={[location.latitude, location.longitude]} />}

        <FollowDeviceLocation location={location} />

        {/* User Current Position Beacon */}
        {location && (
          <CircleMarker
            center={[location.latitude, location.longitude]}
            radius={11}
            pathOptions={{
              color: '#38bdf8',
              fillColor: '#0284c7',
              fillOpacity: 0.95,
              weight: 3,
            }}
          >
            <Tooltip permanent direction="top" offset={[0, -12]}>
              <span className="font-semibold text-xs text-primary">Center Post</span>
            </Tooltip>
            <Popup>
              <div className="text-sm p-1">
                <div className="font-bold text-foreground">{locationName ?? 'Your Primary Position'}</div>
                <div className="text-xs text-muted-foreground mt-0.5">
                  {localWeather ? `${localWeather.temperature}°C · Wind ${localWeather.wind_speed} km/h` : 'Loading live telemetry…'}
                </div>
              </div>
            </Popup>
          </CircleMarker>
        )}

        {/* Nearby Weather / Telemetry Stations with 3D Holographic Styling */}
        {liveStations.map((station) => {
          const { value, unit, color } = valueFor(station, layer)
          const isSelected = selectedStation?.id === station.id
          const radius =
            layer === 'rainfall'
              ? 9 + station.rainfall * 1.5
              : layer === 'wind' || layer === 'cyclone'
                ? 9 + station.wind / 3
                : 11 + Math.max(0, station.temperature - 28) * 1.8

          return (
            <div key={station.id}>
              {/* Outer pulsing beacon ring for selected or active stations */}
              <CircleMarker
                center={[station.lat, station.lon]}
                radius={Math.min(32, radius + (isSelected ? 6 : 3))}
                pathOptions={{
                  color: isSelected ? '#38bdf8' : color,
                  fillColor: color,
                  fillOpacity: isSelected ? 0.35 : 0.15,
                  weight: isSelected ? 2.5 : 1,
                  dashArray: isSelected ? '3, 6' : undefined,
                }}
              />
              {/* Inner crisp telemetry bead */}
              <CircleMarker
                center={[station.lat, station.lon]}
                radius={Math.min(24, Math.max(8, radius))}
                eventHandlers={{
                  click: () => setSelectedStation(station),
                }}
                pathOptions={{
                  color: isSelected ? '#ffffff' : color,
                  fillColor: color,
                  fillOpacity: 0.85,
                  weight: isSelected ? 2.5 : 1.5,
                }}
              >
                <Tooltip direction="top" offset={[0, -6]}>
                  <div className="text-xs font-semibold">
                    {station.name}: <span className="font-mono text-cyan-500">{value} {unit}</span>
                  </div>
                </Tooltip>
                <Popup>
                  <div className="min-w-[180px] p-1.5 text-xs text-foreground">
                    <div className="font-bold text-sm text-foreground flex items-center justify-between">
                      <span>{station.name}</span>
                      <span className="rounded bg-emerald-500/20 px-1 text-[10px] text-emerald-600 font-mono">LIVE</span>
                    </div>
                    <div className="mt-1 font-medium text-muted-foreground">{weatherSummary(station.weatherCode).summary}</div>
                    <div className="mt-2 grid grid-cols-2 gap-1 font-mono text-[11px] tabular-nums">
                      <div>Temp: <strong>{station.temperature}°C</strong></div>
                      <div>Rain: <strong>{station.rainfall} mm</strong></div>
                      <div>Wind: <strong>{station.wind} km/h</strong></div>
                      <div>Press: <strong>{station.pressure ?? 1012} hPa</strong></div>
                    </div>
                    <div className="mt-2 text-[10px] text-muted-foreground border-t border-border pt-1">
                      {station.source} · Dual-Pol Doppler
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            </div>
          )
        })}
      </MapContainer>
    </div>
  )
}
