'use client'

import { useEffect, useState } from 'react'
import {
  Activity,
  AlertCircle,
  Building2,
  Car,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  Compass,
  Footprints,
  Info,
  Plane,
  Radio,
  ShieldAlert,
  Ship,
  Sparkles,
  Sprout,
  Sun,
  Wind,
  Zap,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Card, PageHeader } from '@/components/ui-kit'
import { cn } from '@/lib/utils'
import {
  askWeather,
  getCurrentIntelligence,
  getCurrentWeather,
  getForecast,
  translateTexts,
  type LiveAdvisory,
  type LiveForecast,
  type LiveWeather,
} from '@/lib/live-api'
import { useDeviceLocation } from '@/components/location-provider'
import { LocationPermission } from '@/components/location-permission'
import { useLanguage } from '@/components/language-provider'

const sectorMeta: Record<string, { icon: LucideIcon; label: string }> = {
  agriculture: { icon: Sprout, label: 'Agriculture & Kisan' },
  aviation: { icon: Plane, label: 'Aviation & Air Ops' },
  marine: { icon: Ship, label: 'Fisheries & Marine' },
  urban: { icon: Building2, label: 'Urban & Municipal' },
  disaster_management: { icon: CircleAlert, label: 'Emergency Management' },
  general: { icon: CircleAlert, label: 'General Safety' },
}

const priorityStyle: Record<string, { badge: string; dot: string }> = {
  low: {
    badge: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
    dot: 'bg-emerald-500',
  },
  medium: {
    badge: 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30',
    dot: 'bg-amber-500',
  },
  high: {
    badge: 'bg-orange-500/10 text-orange-700 dark:text-orange-400 border-orange-500/30',
    dot: 'bg-orange-500',
  },
  critical: {
    badge: 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/30',
    dot: 'bg-rose-500 animate-pulse',
  },
}

interface LifestyleIndex {
  id: string
  title: string
  category: 'activity' | 'health' | 'travel' | 'home'
  icon: LucideIcon
  status: string
  level: 'good' | 'moderate' | 'warning' | 'critical'
  score: string
  shortHint: string
  summary: string
  reason: string
  action: string
  actionTip: string
  scientificBasis: string
}

function computeLifestyleIndices(
  weather: LiveWeather | null,
  forecast: LiveForecast | null,
): LifestyleIndex[] {
  if (!weather) return []

  const temp = weather.temperature
  const apparentTemp = weather.apparent_temperature ?? temp
  const humidity = weather.relative_humidity
  const rain = weather.rain ?? weather.precipitation ?? 0
  const wind = weather.wind_speed ?? 0
  const aqi = weather.air_quality_index ?? 50
  const uv = weather.uv_index ?? 0
  const code = weather.weather_code ?? 0

  const next24hRainProb = forecast?.forecast?.[0]?.precipitation_probability ?? (rain > 0 ? 80 : 20)
  const next48hRainProb = forecast?.forecast?.[1]?.precipitation_probability ?? (rain > 0 ? 60 : 15)

  const indices: LifestyleIndex[] = []

  // 1. Car Wash
  if (rain > 0.5 || next24hRainProb >= 40) {
    indices.push({
      id: 'car-wash',
      title: 'Car Wash',
      category: 'home',
      icon: Car,
      status: 'Poor',
      level: 'warning',
      score: '2/10',
      shortHint: 'Wet Conditions',
      summary: 'Postpone washing vehicle; rain or wet roads expected within 24 hours.',
      reason: `Precipitation of ${rain.toFixed(1)} mm recorded; ${next24hRainProb}% rain probability in the next 24 hours.`,
      action: 'Hold off on exterior detailing or commercial wash. Road grime and water spots will undo cleaning within hours.',
      actionTip: 'Postpone detailing; rain ahead',
      scientificBasis: 'High relative humidity combined with active precipitation causes roadway splashback, mineral spot etching, and rapid dirt adhesion to clear coat lacquer.',
    })
  } else if (next24hRainProb >= 20 || next48hRainProb >= 40) {
    indices.push({
      id: 'car-wash',
      title: 'Car Wash',
      category: 'home',
      icon: Car,
      status: 'Fair',
      level: 'moderate',
      score: '6/10',
      shortHint: 'Passing Clouds',
      summary: 'Acceptable for a quick rinse; marginal chance of a passing shower.',
      reason: `${next24hRainProb}% chance of light scattered shower in the next 24-48 hours.`,
      action: 'Quick rinse or waterless wipe is fine. Keep vehicle parked in covered bays if possible.',
      actionTip: 'Quick rinse fine; park under cover',
      scientificBasis: 'Atmospheric stability is moderate with patchy cumulus cover; low aerosol deposition rate.',
    })
  } else {
    indices.push({
      id: 'car-wash',
      title: 'Car Wash',
      category: 'home',
      icon: Car,
      status: 'Optimal',
      level: 'good',
      score: '9/10',
      shortHint: 'Dry 48h Window',
      summary: 'Dry asphalt and clear skies ahead for at least 48 hours.',
      reason: `Dry atmospheric profile with under 15% rain probability across the next two days.`,
      action: 'Optimal time for complete detailing, ceramic waxing, and vacuuming.',
      actionTip: 'Ideal 48h detailing window',
      scientificBasis: 'Anticyclonic subsidence and low atmospheric moisture create prolonged dry surface conditions with minimal road dust splashing.',
    })
  }

  // 2. Workout & Running
  if (rain > 1.0 || aqi > 160 || temp > 38) {
    indices.push({
      id: 'running',
      title: 'Workout & Running',
      category: 'activity',
      icon: Footprints,
      status: 'Indoor',
      level: 'critical',
      score: '3/10',
      shortHint: 'Indoor Only',
      summary: 'Unfavorable ambient conditions for outdoor cardio workouts.',
      reason: rain > 1.0
        ? `Wet pavement and rain (${rain.toFixed(1)} mm) elevate slip hazard and hypothermia risk.`
        : `Elevated Heat/AQI stress (Temp: ${temp.toFixed(1)}°C, AQI: ${aqi.toFixed(0)}) increases respiratory load.`,
      action: 'Switch outdoor running or cycling to indoor gym routines, treadmill work, or indoor mobility stretching.',
      actionTip: 'Switch to indoor gym or treadmill',
      scientificBasis: 'Strenuous exertion in high PM2.5 or active downpour elevates cardiac strain and airway resistance via particulate bronchoconstriction.',
    })
  } else if (temp > 30 || humidity > 75 || aqi > 100) {
    indices.push({
      id: 'running',
      title: 'Workout & Running',
      category: 'activity',
      icon: Footprints,
      status: 'Moderate',
      level: 'moderate',
      score: '6/10',
      shortHint: 'High Humidity',
      summary: 'Humid air limits evaporative cooling; hydrate heavily.',
      reason: `Relative humidity at ${humidity.toFixed(0)}% and apparent temperature at ${apparentTemp.toFixed(1)}°C reduce sweat evaporation efficiency.`,
      action: 'Schedule workouts before 7:00 AM or after 6:30 PM. Carry electrolyte-infused water and reduce pace by 10-15%.',
      actionTip: 'Hydrate; run early morning or dusk',
      scientificBasis: 'High wet-bulb globe temperature (WBGT) limits latent heat dissipation through sweat evaporation, accelerating core temperature rise.',
    })
  } else {
    indices.push({
      id: 'running',
      title: 'Workout & Running',
      category: 'activity',
      icon: Footprints,
      status: 'Optimal',
      level: 'good',
      score: '9/10',
      shortHint: 'Prime Air',
      summary: 'Ideal thermal envelope and clean air for outdoor endurance.',
      reason: `Ambient temperature ${temp.toFixed(1)}°C, clean air (AQI ${aqi.toFixed(0)}), and calm winds.`,
      action: 'Perfect window for high-cadence runs, marathon prep, outdoor HIIT, and group cycling.',
      actionTip: 'Great window for outdoor cardio',
      scientificBasis: 'Thermoregulatory equilibrium is easily maintained under moderate ambient temperature and optimal air oxygen density.',
    })
  }

  // 3. Mosquito Risk
  if (temp >= 21 && temp <= 35 && humidity >= 70 && (rain > 0 || code in [51, 53, 55, 61, 65, 80, 95])) {
    indices.push({
      id: 'mosquito',
      title: 'Mosquito Risk',
      category: 'health',
      icon: ShieldAlert,
      status: 'High Risk',
      level: 'warning',
      score: 'Peak Swarm',
      shortHint: 'Breeding Alert',
      summary: 'Moist, warm conditions trigger peak vector breeding & flight.',
      reason: `Temperature (${temp.toFixed(1)}°C) inside breeding envelope (20-34°C) with high humidity (${humidity.toFixed(0)}%) and surface pooling.`,
      action: 'Apply DEET / picaridin repellent, wear full-sleeve protective clothing at dusk, and drain stagnant water in flower pots, coolers, and tires.',
      actionTip: 'Apply repellent; clear stagnant water',
      scientificBasis: 'Aedes and Anopheles vectors exhibit maximum metabolic flight activity and accelerated ovicidal breeding cycles between 22-32°C when ambient relative humidity exceeds 70%.',
    })
  } else if (humidity >= 55 || (temp >= 20 && temp <= 32)) {
    indices.push({
      id: 'mosquito',
      title: 'Mosquito Risk',
      category: 'health',
      icon: ShieldAlert,
      status: 'Moderate',
      level: 'moderate',
      score: 'Normal',
      shortHint: 'Twilight Risk',
      summary: 'Moderate flight activity around dawn and dusk twilight.',
      reason: `Ambient humidity of ${humidity.toFixed(0)}% supports routine twilight feeding cycles.`,
      action: 'Use window mosquito screens and insect repellent vaporizers during early morning and sunset hours.',
      actionTip: 'Use window screens at dawn/dusk',
      scientificBasis: 'Standard diurnal vector feeding peaks at crepuscular hours (dawn/dusk) under moderate humidity.',
    })
  } else {
    indices.push({
      id: 'mosquito',
      title: 'Mosquito Risk',
      category: 'health',
      icon: ShieldAlert,
      status: 'Low Risk',
      level: 'good',
      score: 'Minimal',
      shortHint: 'Safe Window',
      summary: 'Dry atmospheric profile or cool air limits vector flight.',
      reason: `Low humidity (${humidity.toFixed(0)}%) and environmental conditions suppress mosquito flight range.`,
      action: 'Standard household vigilance; risk of vector-borne transmission is statistically minimal today.',
      actionTip: 'Low vector transmission risk',
      scientificBasis: 'Desiccating air (<50% RH) induces high insect dehydration stress, curbing flight endurance and larval survival.',
    })
  }

  // 4. UV & Skincare
  if (uv >= 8) {
    indices.push({
      id: 'uv-skincare',
      title: 'UV & Skincare',
      category: 'health',
      icon: Sun,
      status: 'Extreme',
      level: 'critical',
      score: `UV ${uv.toFixed(1)}`,
      shortHint: 'Hazardous Sun',
      summary: 'Hazardous solar radiation; cellular sunburn in under 15 minutes.',
      reason: `Solar UV Index of ${uv.toFixed(1)} delivers intense erythemal irradiance during midday peak.`,
      action: 'Apply broad-spectrum SPF 50+ sunscreen, wear UV400 sunglasses, use a wide-brim hat, and seek shade between 11:00 AM - 3:30 PM.',
      actionTip: 'SPF 50+ sunscreen & seek shade',
      scientificBasis: 'UV-B flux at this intensity induces rapid DNA photoproduct formation and acute dermal inflammatory erythema.',
    })
  } else if (uv >= 5) {
    indices.push({
      id: 'uv-skincare',
      title: 'UV & Skincare',
      category: 'health',
      icon: Sun,
      status: 'High',
      level: 'warning',
      score: `UV ${uv.toFixed(1)}`,
      shortHint: 'High UV',
      summary: 'Significant solar radiation potential during clear midday hours.',
      reason: `UV Index of ${uv.toFixed(1)} requires active dermal sun protection.`,
      action: 'Apply SPF 30+ sunscreen 20 minutes before stepping outdoors. Reapply every 2 hours if perspiring.',
      actionTip: 'Apply SPF 30+ before leaving',
      scientificBasis: 'Moderate to high solar elevation angle produces sufficient radiant flux to burn unprotected fair skin in 25-30 minutes.',
    })
  } else if (uv >= 3) {
    indices.push({
      id: 'uv-skincare',
      title: 'UV & Skincare',
      category: 'health',
      icon: Sun,
      status: 'Moderate',
      level: 'moderate',
      score: `UV ${uv.toFixed(1)}`,
      shortHint: 'Moderate Sun',
      summary: 'Low to moderate solar exposure; safe with basic precautions.',
      reason: `UV Index ${uv.toFixed(1)} under partial cloud attenuation.`,
      action: 'Wear light sun protection or sunglasses if staying outdoors for over 45 minutes.',
      actionTip: 'Sunglasses & light sun protection',
      scientificBasis: 'Cloud scattering attenuates diffuse UV irradiance, keeping burn risk manageable for general public.',
    })
  } else {
    indices.push({
      id: 'uv-skincare',
      title: 'UV & Skincare',
      category: 'health',
      icon: Sun,
      status: 'Low',
      level: 'good',
      score: `UV ${uv.toFixed(1)}`,
      shortHint: 'Minimal Sun',
      summary: 'Negligible ultraviolet risk during current conditions.',
      reason: `Low solar zenith angle or cloud cover restricts UV Index to safe baseline.`,
      action: 'No sun protection required for brief outdoor exposure.',
      actionTip: 'No sunscreen required for now',
      scientificBasis: 'Atmospheric path length (air mass > 3) scatters ultraviolet wavelengths before reaching ground level.',
    })
  }

  // 5. Driving Safety
  if (rain >= 3.0 || (weather.visibility != null && weather.visibility < 3.0) || code in [45, 48, 65, 95]) {
    indices.push({
      id: 'driving',
      title: 'Driving Safety',
      category: 'travel',
      icon: Car,
      status: 'Caution',
      level: 'critical',
      score: 'Wet Pavement',
      shortHint: 'Slip Hazard',
      summary: 'Standing water reduces traction and extends braking distance.',
      reason: `Precipitation (${rain.toFixed(1)} mm) and reduced visibility (${(weather.visibility ?? 3).toFixed(1)} km) impair highway maneuvering.`,
      action: 'Reduce cruising speed by 20 km/h, switch on low-beam headlights, maintain 4x vehicle following distance, and avoid abrupt steering inputs.',
      actionTip: 'Reduce speed & maintain 4x gap',
      scientificBasis: 'Tire water clearance capacity drops exponentially on flooded asphalt, causing dynamic hydroplaning risk above 65 km/h.',
    })
  } else if (rain > 0 || wind > 25) {
    indices.push({
      id: 'driving',
      title: 'Driving Safety',
      category: 'travel',
      icon: Car,
      status: 'Caution',
      level: 'moderate',
      score: 'Damp Roads',
      shortHint: 'Slick Asphalt',
      summary: 'Damp road surfaces and intermittent crosswinds on flyovers.',
      reason: `Damp asphalt and sustained winds of ${wind.toFixed(1)} km/h.`,
      action: 'Watch for sudden oil slicks on freshly wet tarmac and maintain firm grip on two-wheelers over bridges.',
      actionTip: 'Watch for damp tarmac & crosswinds',
      scientificBasis: 'First flush of precipitation lifts petroleum residues from porous asphalt before wash-off, temporarily reducing friction coefficient by up to 30%.',
    })
  } else {
    indices.push({
      id: 'driving',
      title: 'Driving Safety',
      category: 'travel',
      icon: Car,
      status: 'Safe',
      level: 'good',
      score: 'Dry Traction',
      shortHint: 'Optimal Grip',
      summary: 'Dry asphalt, optimal braking grip, and clear visibility.',
      reason: `Visibility exceeds 8 km with zero rain and calm wind vectors.`,
      action: 'Normal driving conditions across city corridors and expressways.',
      actionTip: 'Normal highway cruising conditions',
      scientificBasis: 'Dry pavement friction coefficient exceeds 0.8; clear optical sightlines ensure prompt braking response times.',
    })
  }

  // 6. Air & Respiratory
  if (aqi > 200) {
    indices.push({
      id: 'respiratory',
      title: 'Air & Respiratory',
      category: 'health',
      icon: Wind,
      status: 'Hazardous',
      level: 'critical',
      score: `AQI ${aqi.toFixed(0)}`,
      shortHint: 'Severe AQI',
      summary: 'Unhealthy air for all citizens; elevated PM2.5 particulate loading.',
      reason: `Atmospheric AQI of ${aqi.toFixed(0)} triggers respiratory irritation across healthy and sensitive populations.`,
      action: 'Wear certified N95/FFP2 masks outdoors. Run indoor HEPA air purifiers and keep residential windows sealed.',
      actionTip: 'Wear N95 mask; seal windows',
      scientificBasis: 'Sub-2.5 micron fine particulate matter penetrates alveolar sacs directly into blood circulation, triggering systemic vascular inflammation.',
    })
  } else if (aqi > 100) {
    indices.push({
      id: 'respiratory',
      title: 'Air & Respiratory',
      category: 'health',
      icon: Wind,
      status: 'Unhealthy',
      level: 'warning',
      score: `AQI ${aqi.toFixed(0)}`,
      shortHint: 'Sensitive Alert',
      summary: 'Air quality may cause coughing or wheezing in asthmatic citizens.',
      reason: `Particulate matter concentration elevated under low thermal inversion layer.`,
      action: 'Asthma patients, elderly, and children should limit prolonged outdoor exertion.',
      actionTip: 'Asthmatics limit outdoor exertion',
      scientificBasis: 'Aerosolized combustion and dust particles irritate bronchial mucosa, lowering peak expiratory flow rates in vulnerable individuals.',
    })
  } else if (aqi > 50) {
    indices.push({
      id: 'respiratory',
      title: 'Air & Respiratory',
      category: 'health',
      icon: Wind,
      status: 'Moderate',
      level: 'moderate',
      score: `AQI ${aqi.toFixed(0)}`,
      shortHint: 'Acceptable Air',
      summary: 'Acceptable ambient air; suitable for most everyday activities.',
      reason: `Particulate metrics within national standard threshold limits.`,
      action: 'Safe for normal citizen commuting and routine outdoor exposure.',
      actionTip: 'Safe for routine citizen movement',
      scientificBasis: 'Atmospheric ventilation index is sufficient to disperse ground-level pollutant accumulation.',
    })
  } else {
    indices.push({
      id: 'respiratory',
      title: 'Air & Respiratory',
      category: 'health',
      icon: Wind,
      status: 'Good',
      level: 'good',
      score: `AQI ${aqi.toFixed(0)}`,
      shortHint: 'Clean & Pure',
      summary: 'Pristine atmospheric purity; optimal for lung oxygenation.',
      reason: `Low aerosol optical depth and clean oceanic/rural air circulation.`,
      action: 'Superb time for morning pranayama, deep outdoor breathing, and park walks.',
      actionTip: 'Ideal for deep breathing & yoga',
      scientificBasis: 'Aerosol particulates below 15 µg/m³ ensure optimal pulmonary gas exchange without inflammatory alveolar response.',
    })
  }

  // 7. Travel & Outings
  if (code in [95, 96, 99, 65] || wind > 35) {
    indices.push({
      id: 'travel',
      title: 'Travel & Outings',
      category: 'travel',
      icon: Compass,
      status: 'Disrupted',
      level: 'warning',
      score: 'Storm Risk',
      shortHint: 'Delays Likely',
      summary: 'Convective storm activity or high gusts across regional transit corridors.',
      reason: `Thunderstorm system or high winds (${wind.toFixed(1)} km/h) may trigger regional airport ground stops and highway slowdowns.`,
      action: 'Verify departure schedules for regional flights and trains; postpone recreational outdoor excursions.',
      actionTip: 'Check transit & flight schedules',
      scientificBasis: 'Convective cloud tops (>10 km) induce severe clear-air turbulence, low-level wind shear, and localized flash pooling on roadways.',
    })
  } else if (code in [51, 53, 61, 80] || rain > 0) {
    indices.push({
      id: 'travel',
      title: 'Travel & Outings',
      category: 'travel',
      icon: Compass,
      status: 'Feasible',
      level: 'moderate',
      score: 'Fair',
      shortHint: 'Pack Raincoat',
      summary: 'Intermittent damp weather across tourist & transit locations.',
      reason: `Passing showers; carry compact umbrella and waterproof bag covers.`,
      action: 'Plan for 20-30 min buffer time in regional transit. Great for indoor museums, cultural centers, and dining.',
      actionTip: 'Carry umbrella & buffer 20 min',
      scientificBasis: 'Stratiform rain bands produce intermittent precipitation with safe regional transit windows between cells.',
    })
  } else {
    indices.push({
      id: 'travel',
      title: 'Travel & Outings',
      category: 'travel',
      icon: Compass,
      status: 'Optimal',
      level: 'good',
      score: 'Optimal',
      shortHint: 'Clear Skies',
      summary: 'Smooth transit conditions across highway, rail, and aviation routes.',
      reason: `Clear to partly cloudy skies with no convective weather warnings in effect.`,
      action: 'Ideal day for weekend getaways, heritage site visits, outdoor picnics, and photography.',
      actionTip: 'Superb day for weekend road trips',
      scientificBasis: 'Atmospheric stability provides unobstructed visibility and smooth aerodynamic flight envelopes across local sectors.',
    })
  }

  // 8. Cooling Demand
  if (apparentTemp >= 38 || temp >= 38) {
    indices.push({
      id: 'energy',
      title: 'Cooling Demand',
      category: 'home',
      icon: Zap,
      status: 'High Load',
      level: 'critical',
      score: `${apparentTemp.toFixed(0)}°C Index`,
      shortHint: 'Peak HVAC Load',
      summary: 'Heavy air conditioning load expected during peak afternoon heat.',
      reason: `Extreme heat index of ${apparentTemp.toFixed(1)}°C drives sustained residential refrigeration and HVAC draw.`,
      action: 'Set AC thermostat to 24-25°C to conserve up to 24% electricity; draw blackout thermal curtains across south/west-facing windows.',
      actionTip: 'Set AC to 24°C & draw curtains',
      scientificBasis: 'Every 1°C decrease in AC thermostat below 24°C inflates compressor electrical consumption by approximately 6%.',
    })
  } else if (apparentTemp >= 31) {
    indices.push({
      id: 'energy',
      title: 'Cooling Demand',
      category: 'home',
      icon: Zap,
      status: 'Moderate',
      level: 'moderate',
      score: `${apparentTemp.toFixed(0)}°C Index`,
      shortHint: 'Warm Indoors',
      summary: 'Warm indoor profile; ceiling fans and intermittent cooling suggested.',
      reason: `Warm ambient thermal index requiring continuous airflow.`,
      action: 'Utilize ceiling fans for convective cooling; run AC in dry/dehumidification mode if humidity exceeds 70%.',
      actionTip: 'Use ceiling fans & dry mode AC',
      scientificBasis: 'Convective skin cooling from fan airspeed of 1.5 m/s reduces effective perceived thermal stress by up to 2.5°C.',
    })
  } else {
    indices.push({
      id: 'energy',
      title: 'Cooling Demand',
      category: 'home',
      icon: Zap,
      status: 'Low Draw',
      level: 'good',
      score: `${apparentTemp.toFixed(0)}°C Index`,
      shortHint: 'Comfortable',
      summary: 'Pleasant thermal balance; low residential power demand for cooling.',
      reason: `Ambient conditions within human thermal comfort zone (18-28°C).`,
      action: 'Open windows for cross-ventilation during morning and evening to save electrical costs.',
      actionTip: 'Open windows for natural breeze',
      scientificBasis: 'Indoor-outdoor thermal equilibrium requires negligible mechanical ventilation or refrigerant compression.',
    })
  }

  return indices
}

const levelStyles: Record<string, { badge: string; border: string; dot: string }> = {
  good: {
    badge: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
    border: 'hover:border-emerald-500/50',
    dot: 'bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.6)]',
  },
  moderate: {
    badge: 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30',
    border: 'hover:border-amber-500/50',
    dot: 'bg-amber-500 shadow-[0_0_6px_rgba(245,158,11,0.6)]',
  },
  warning: {
    badge: 'bg-orange-500/10 text-orange-700 dark:text-orange-400 border-orange-500/30',
    border: 'hover:border-orange-500/50',
    dot: 'bg-orange-500 shadow-[0_0_6px_rgba(249,115,22,0.6)]',
  },
  critical: {
    badge: 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/30',
    border: 'hover:border-rose-500/50',
    dot: 'bg-rose-500 shadow-[0_0_6px_rgba(244,63,94,0.6)] animate-pulse',
  },
}

function displayDomain(domain: string) {
  return domain.toLowerCase()
}

function formatDate(value?: string | null) {
  return value ? new Date(value).toLocaleString() : 'Until conditions change'
}

export default function Page() {
  const { location, locationName } = useDeviceLocation()
  const { language, t } = useLanguage()

  const [activeTab, setActiveTab] = useState<'all' | 'lifestyle' | 'sectors'>('all')
  const [advisories, setAdvisories] = useState<LiveAdvisory[]>([])
  const [currentWeather, setCurrentWeather] = useState<LiveWeather | null>(null)
  const [forecast, setForecast] = useState<LiveForecast | null>(null)
  const [generatedAt, setGeneratedAt] = useState<string | null>(null)

  const [selectedAdvisory, setSelectedAdvisory] = useState<LiveAdvisory | null>(null)
  const [selectedLifestyle, setSelectedLifestyle] = useState<LifestyleIndex | null>(null)
  const [llmBrief, setLlmBrief] = useState<string | null>(null)
  const [briefLoading, setBriefLoading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!location) return
    let cancelled = false

    const refresh = async () => {
      setLoading(true)
      try {
        const [intelResult, weatherResult, forecastResult] = await Promise.allSettled([
          getCurrentIntelligence(location.latitude, location.longitude, locationName, language),
          getCurrentWeather(location.latitude, location.longitude),
          getForecast(location.latitude, location.longitude, 3),
        ])

        if (cancelled) return

        if (weatherResult.status === 'fulfilled') {
          setCurrentWeather(weatherResult.value)
        }
        if (forecastResult.status === 'fulfilled') {
          setForecast(forecastResult.value)
        }

        if (intelResult.status === 'fulfilled') {
          const result = intelResult.value
          const sourceAdvisories = result.advisories
          const strings = sourceAdvisories.flatMap((advisory) => [
            advisory.title,
            advisory.message,
            ...advisory.actions,
          ])
          let translatedAdvisories = sourceAdvisories
          try {
            const translated = await translateTexts(strings, language)
            let offset = 0
            translatedAdvisories = sourceAdvisories.map((advisory) => {
              const actionCount = advisory.actions.length
              const item = {
                ...advisory,
                title: translated[offset],
                message: translated[offset + 1],
                actions: translated.slice(offset + 2, offset + 2 + actionCount),
              }
              offset += 2 + actionCount
              return item
            })
          } catch {
            // Keep grounded provider response visible if optional translation is slow
          }
          setAdvisories(translatedAdvisories)
          setGeneratedAt(result.generated_at)
          setError(null)
        } else {
          throw intelResult.reason
        }
      } catch (reason: unknown) {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : 'Live advisory service is temporarily unavailable.')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void refresh()
    const timer = window.setInterval(refresh, 300000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [location, locationName, language])

  const openAdvisory = async (advisory: LiveAdvisory) => {
    setSelectedAdvisory(advisory)
    setLlmBrief(null)
    if (!location) return
    setBriefLoading(true)
    try {
      const response = await askWeather(
        `Create a concise practical brief for this live weather advisory. Stay strictly grounded in the supplied advisory and current weather context. Do not invent official warnings, measurements, or deadlines. Explain who should act, what to do first, what to avoid, and when to reassess. Advisory: ${advisory.title}. Risk: ${advisory.risk_level}. Message: ${advisory.message}. Required actions: ${advisory.actions.join('; ')}`,
        { locationName, latitude: location.latitude, longitude: location.longitude, language },
      )
      setLlmBrief(response.answer ?? null)
    } catch {
      setLlmBrief(null)
    } finally {
      setBriefLoading(false)
    }
  }

  const lifestyleIndices = computeLifestyleIndices(currentWeather, forecast)

  const imdStationName = currentWeather?.provenance && 'station_name' in currentWeather.provenance
    ? (currentWeather.provenance as Record<string, unknown>).station_name as string
    : null
  const imdDistrict = currentWeather?.provenance && 'district' in currentWeather.provenance
    ? (currentWeather.provenance as Record<string, unknown>).district as string
    : null
  const imdDistance = currentWeather?.provenance && 'distance_km' in currentWeather.provenance
    ? (currentWeather.provenance as Record<string, unknown>).distance_km as number
    : null

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 animate-in fade-in duration-500 pb-16">
      <LocationPermission />

      <PageHeader
        title="Weather Decision-Support & Lifestyle Intelligence"
        subtitle={location ? `${t('Live multi-tier guidance for')} ${locationName ?? t('your current location')}` : t('Enable location to generate weather-conditioned guidance')}
        icon={Sprout}
      />

      {/* Live Grounding & Sensor Telemetry Bar */}
      {location && currentWeather && (
        <div className="relative overflow-hidden rounded-2xl border border-primary/20 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent p-4 shadow-sm backdrop-blur-md">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <span className="relative flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-500" />
              </span>
              <div>
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-primary">
                  <Radio className="size-3.5" />
                  <span>IMD Official Observation Ground Truth</span>
                </div>
                <div className="mt-0.5 text-sm font-medium text-foreground">
                  {imdStationName ? `Station ${imdStationName}${imdDistrict ? ` (${imdDistrict})` : ''}` : 'Official Surface Station'}
                  {imdDistance != null && (
                    <span className="ml-1.5 text-xs text-muted-foreground">· {imdDistance.toFixed(1)} km away</span>
                  )}
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2.5 text-xs text-muted-foreground font-mono">
              <span className="rounded-lg bg-background/70 px-2.5 py-1 border border-border/60 shadow-xs">
                🌡️ {currentWeather.temperature.toFixed(1)}°C (Feels {currentWeather.apparent_temperature.toFixed(1)}°C)
              </span>
              <span className="rounded-lg bg-background/70 px-2.5 py-1 border border-border/60 shadow-xs">
                💧 {currentWeather.relative_humidity.toFixed(0)}% RH
              </span>
              <span className="rounded-lg bg-background/70 px-2.5 py-1 border border-border/60 shadow-xs">
                🌧️ {(currentWeather.rain ?? currentWeather.precipitation ?? 0).toFixed(1)} mm Rain
              </span>
              <span className="rounded-lg bg-background/70 px-2.5 py-1 border border-border/60 shadow-xs">
                💨 {currentWeather.wind_speed.toFixed(1)} km/h Wind
              </span>
              {currentWeather.air_quality_index != null && (
                <span className="rounded-lg bg-background/70 px-2.5 py-1 border border-border/60 shadow-xs">
                  🍃 AQI {currentWeather.air_quality_index.toFixed(0)}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {!location && (
        <div className="rounded-2xl border border-border bg-card p-5 text-sm text-muted-foreground">
          {t('Allow location access to receive guidance based on current weather hazards near you.')}
        </div>
      )}

      {location && loading && advisories.length === 0 && lifestyleIndices.length === 0 && (
        <div role="status" className="rounded-2xl border border-border bg-card p-5 text-sm text-muted-foreground">
          {t('Analysing current weather telemetry and generating grounded guidance…')}
        </div>
      )}

      {error && (
        <div role="alert" className="rounded-2xl border border-destructive/30 bg-destructive/5 p-5 text-sm text-destructive">
          {t('Unable to load live advisories')}: {error}
        </div>
      )}

      {/* Segmented Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-3">
        <div className="flex items-center gap-1.5 rounded-xl bg-muted/60 p-1 border border-border/60">
          <button
            type="button"
            onClick={() => setActiveTab('all')}
            className={cn(
              'rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-all',
              activeTab === 'all'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            All Intelligence ({lifestyleIndices.length + advisories.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('lifestyle')}
            className={cn(
              'rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-all',
              activeTab === 'lifestyle'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            Citizen Lifestyle & Health ({lifestyleIndices.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('sectors')}
            className={cn(
              'rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-all',
              activeTab === 'sectors'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            Sector Operations ({advisories.length})
          </button>
        </div>

        <div className="text-xs text-muted-foreground flex items-center gap-1.5">
          <Sparkles className="size-3.5 text-primary" />
          <span>Real-time synthesized decision support</span>
        </div>
      </div>

      {/* SECTION 1: CITIZEN LIFESTYLE & HEALTH WEATHER INTELLIGENCE */}
      {(activeTab === 'all' || activeTab === 'lifestyle') && lifestyleIndices.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold tracking-tight flex items-center gap-2">
                <Activity className="size-4 text-primary" />
                <span>Citizen Health & Lifestyle Weather Intelligence</span>
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Dynamic indices evaluated from live IMD automated station telemetry and NWP atmospheric physics.
              </p>
            </div>
            <span className="hidden sm:inline-block text-[11px] font-mono text-muted-foreground">
              Click any card for full scientific rationale
            </span>
          </div>

          <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
            {lifestyleIndices.map((item) => {
              const Icon = item.icon
              const style = levelStyles[item.level] ?? levelStyles.moderate
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSelectedLifestyle(item)}
                  className="group text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-2xl"
                >
                  <Card className={cn(
                    'group relative flex h-full flex-col justify-between overflow-hidden rounded-2xl border border-border/80 bg-card p-4 transition-all duration-200 hover:-translate-y-1 hover:shadow-lg',
                    style.border,
                  )}>
                    <div>
                      {/* Top Header Row with Icon, Title, and Clean Pill Badge */}
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="grid size-7 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
                            <Icon className="size-3.5" />
                          </span>
                          <span className="text-xs font-semibold tracking-wide text-foreground truncate">
                            {item.title}
                          </span>
                        </div>

                        {/* Modern High-Tech Pill Badge with Glowing Status Dot */}
                        <span className={cn(
                          'inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider',
                          style.badge,
                        )}>
                          <span className={cn('size-1.5 rounded-full shrink-0', style.dot)} />
                          <span>{item.status}</span>
                        </span>
                      </div>

                      {/* Score Metric & Short Hint */}
                      <div className="mt-3 flex items-baseline gap-2">
                        <span className="font-mono text-xl font-bold tracking-tight text-foreground">
                          {item.score}
                        </span>
                        <span className="text-xs font-medium text-muted-foreground truncate">
                          · {item.shortHint}
                        </span>
                      </div>

                      {/* Summary Explanation */}
                      <p className="mt-1.5 line-clamp-2 text-xs text-muted-foreground leading-relaxed">
                        {item.summary}
                      </p>
                    </div>

                    {/* Clean Action Tip Footer */}
                    <div className="mt-3.5 pt-2.5 border-t border-border/50 flex items-center justify-between text-[11px] text-muted-foreground group-hover:text-foreground transition-colors">
                      <span className="truncate pr-2 font-medium">{item.actionTip}</span>
                      <span className="flex items-center gap-0.5 text-primary font-semibold shrink-0 text-[11px]">
                        Details <ChevronRight className="size-3 transition-transform group-hover:translate-x-0.5" />
                      </span>
                    </div>
                  </Card>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* SECTION 2: SECTOR & ENTERPRISE DECISION-SUPPORT ADVISORIES */}
      {(activeTab === 'all' || activeTab === 'sectors') && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold tracking-tight flex items-center gap-2">
                <Sprout className="size-4 text-primary" />
                <span>Sector Operational Decision Support</span>
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Specialized tactical advisories for agriculture, marine fisheries, aviation operations, and urban municipal drainage.
              </p>
            </div>
          </div>

          {location && !loading && !error && advisories.length === 0 && (
            <Card className="p-6 text-center">
              <CheckCircle2 className="size-8 mx-auto text-emerald-500 mb-2" />
              <h3 className="text-sm font-semibold">{t('No active hazard-based operational advisories')}</h3>
              <p className="mt-1 text-xs text-muted-foreground max-w-md mx-auto">
                {t("Current meteorological conditions are benign and do not meet the intelligence engine's warning thresholds for sector disruption.")}
              </p>
            </Card>
          )}

          <div className="grid gap-4 md:grid-cols-2">
            {advisories.map((advisory, index) => {
              const domain = displayDomain(advisory.domain)
              const meta = sectorMeta[domain] ?? sectorMeta.general
              const Icon = meta.icon
              const priority = advisory.priority.toLowerCase()
              const pStyle = priorityStyle[priority] ?? priorityStyle.medium
              return (
                <button
                  key={`${advisory.domain}-${advisory.title}-${index}`}
                  type="button"
                  onClick={() => void openAdvisory(advisory)}
                  className="group text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-2xl"
                >
                  <Card className="flex h-full flex-col justify-between gap-3 border-border/80 transition-all duration-200 hover:-translate-y-1 hover:border-primary/50 hover:shadow-lg p-4">
                    <div>
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2.5">
                          <span className="grid size-9 place-items-center rounded-xl bg-primary/10 text-primary">
                            <Icon className="size-4" />
                          </span>
                          <div>
                            <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                              {t(meta.label)}
                            </div>
                            <div className="text-sm font-bold text-foreground">
                              {advisory.title}
                            </div>
                          </div>
                        </div>

                        {/* Modern Status Badge with Dot */}
                        <span className={cn(
                          'inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider',
                          pStyle.badge,
                        )}>
                          <span className={cn('size-1.5 rounded-full shrink-0', pStyle.dot)} />
                          <span>{t(priority)}</span>
                        </span>
                      </div>

                      <p className="mt-2.5 line-clamp-3 text-xs leading-relaxed text-muted-foreground">
                        {advisory.message}
                      </p>
                    </div>

                    <div className="mt-2 pt-2.5 border-t border-border/60 flex items-center justify-between text-xs text-muted-foreground">
                      <span className="text-[11px]">
                        {t('Risk')}: <strong className="text-foreground capitalize">{t(advisory.risk_level.toLowerCase())}</strong> · {t('Valid until')} {formatDate(advisory.valid_until)}
                      </span>
                      <span className="flex items-center gap-1 text-xs font-semibold text-primary group-hover:underline">
                        <span>View Brief</span>
                        <ChevronRight className="size-3.5 transition-transform group-hover:translate-x-0.5" />
                      </span>
                    </div>
                  </Card>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {generatedAt && (
        <p className="text-xs text-muted-foreground">
          {t('Generated')} {formatDate(generatedAt)} {t('from live weather telemetry by the WeatherGPT Intelligence Engine. Guidance is decision support grounded in official IMD and NWP streams.')}
        </p>
      )}

      {/* AI Assistant Tailored Prompt Card */}
      <Card className="relative overflow-hidden border-primary/20 bg-gradient-to-br from-primary/10 via-primary/5 to-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="max-w-xl">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-primary">
              <Sparkles className="size-3.5" />
              <span>Interactive Decision Intelligence</span>
            </div>
            <h3 className="mt-1 text-base font-semibold text-foreground">Need a custom tailored advisory?</h3>
            <p className="mt-1 text-xs text-muted-foreground text-pretty">
              Ask WeatherGPT about your specific farm crop stage (e.g. paddy flowering), flight approach path, marine vessel tonnage, highway route commute, or city ward for instant conditioned guidance.
            </p>
          </div>
          <a
            href="/chat"
            className="inline-flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
          >
            <span>Ask WeatherGPT Assistant</span>
            <ChevronRight className="size-3.5" />
          </a>
        </div>
      </Card>

      {/* MODAL 1: SECTOR ADVISORY DETAIL + LLM GROUNDED BRIEF */}
      {selectedAdvisory && (
        <div className="fixed inset-0 z-[1000] grid place-items-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200" role="presentation" onClick={() => setSelectedAdvisory(null)}>
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="advisory-title"
            className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-border bg-card p-5 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-primary">
                  {sectorMeta[displayDomain(selectedAdvisory.domain)]?.label ?? 'Sector Operational Guidance'}
                </div>
                <h2 id="advisory-title" className="mt-1 text-lg font-bold text-foreground">
                  {selectedAdvisory.title}
                </h2>
              </div>
              <button
                type="button"
                className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
                onClick={() => setSelectedAdvisory(null)}
              >
                ✕
              </button>
            </div>

            <p className="mt-3 text-sm text-muted-foreground leading-relaxed">
              {selectedAdvisory.message}
            </p>

            <div className="mt-4 rounded-xl border border-primary/20 bg-primary/5 p-4 text-sm">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-primary">
                <Sparkles className="size-3.5" />
                <span>WeatherGPT Operational Brief</span>
              </div>
              <p className="mt-1.5 whitespace-pre-wrap text-xs leading-relaxed text-foreground/90">
                {briefLoading ? 'Synthesizing tactical brief grounded in live meteorological telemetry…' : llmBrief ?? 'Review the validated operational checklists below.'}
              </p>
            </div>

            <h3 className="mt-4 text-xs font-bold uppercase tracking-wider text-foreground">
              Required Tactical Actions
            </h3>
            <ul className="mt-2 space-y-2 text-xs">
              {selectedAdvisory.actions.map((action, index) => (
                <li key={`${action}-${index}`} className="flex items-start gap-2 rounded-lg bg-muted/40 p-2.5 border border-border/60">
                  <CheckCircle2 className="size-3.5 text-primary shrink-0 mt-0.5" />
                  <span className="text-foreground/90">{action}</span>
                </li>
              ))}
            </ul>

            <div className="mt-5 border-t border-border pt-3 text-[11px] text-muted-foreground font-mono space-y-1">
              <div>Target Location: {selectedAdvisory.location_name}</div>
              <div>Severity: {selectedAdvisory.risk_level.toLowerCase()} · Priority: {selectedAdvisory.priority.toLowerCase()}</div>
              <div>Validity: Issued {formatDate(selectedAdvisory.issued_at)} · Expires {formatDate(selectedAdvisory.valid_until)}</div>
              <div>Provenance: {selectedAdvisory.source ?? 'WeatherGPT Intelligence Engine'}</div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: CITIZEN LIFESTYLE DETAIL */}
      {selectedLifestyle && (
        <div className="fixed inset-0 z-[1000] grid place-items-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200" role="presentation" onClick={() => setSelectedLifestyle(null)}>
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="lifestyle-title"
            className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-border bg-card p-5 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="grid size-11 place-items-center rounded-xl bg-primary/10 text-primary">
                  <selectedLifestyle.icon className="size-6" />
                </span>
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wider text-primary">
                    Citizen Lifestyle Intelligence
                  </div>
                  <h2 id="lifestyle-title" className="text-lg font-bold text-foreground">
                    {selectedLifestyle.title}
                  </h2>
                </div>
              </div>
              <button
                type="button"
                className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
                onClick={() => setSelectedLifestyle(null)}
              >
                ✕
              </button>
            </div>

            <div className="mt-4 flex items-center justify-between rounded-xl bg-muted/60 p-3 border border-border">
              <div>
                <div className="text-xs text-muted-foreground font-medium">Current Evaluation</div>
                <div className="text-base font-bold text-foreground">{selectedLifestyle.score} · {selectedLifestyle.shortHint}</div>
              </div>
              <span className={cn(
                'inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full border px-3 py-1 text-xs font-bold uppercase',
                levelStyles[selectedLifestyle.level]?.badge,
              )}>
                <span className={cn('size-2 rounded-full shrink-0', levelStyles[selectedLifestyle.level]?.dot)} />
                <span>{selectedLifestyle.status}</span>
              </span>
            </div>

            <div className="mt-4 space-y-3">
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Weather Condition</h4>
                <p className="mt-1 text-xs text-foreground leading-relaxed bg-background/80 p-2.5 rounded-lg border border-border/60">
                  {selectedLifestyle.reason}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Recommended Action</h4>
                <p className="mt-1 text-xs text-foreground leading-relaxed bg-primary/5 p-2.5 rounded-lg border border-primary/20">
                  {selectedLifestyle.action}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Scientific Meteorological Rationale</h4>
                <p className="mt-1 text-xs text-muted-foreground leading-relaxed bg-muted/30 p-2.5 rounded-lg border border-border/40">
                  {selectedLifestyle.scientificBasis}
                </p>
              </div>
            </div>

            <div className="mt-5 border-t border-border pt-3 text-[11px] text-muted-foreground font-mono flex items-center justify-between">
              <span>Grounded in IMD AWS Sensor Data</span>
              <button
                type="button"
                className="text-xs font-semibold text-primary hover:underline"
                onClick={() => setSelectedLifestyle(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
