import {
  Cloud,
  CloudDrizzle,
  CloudFog,
  CloudLightning,
  CloudMoon,
  CloudRain,
  CloudSnow,
  CloudSun,
  Moon,
  Sun,
  Wind,
} from 'lucide-react'
import type { Condition } from '@/lib/weather-data'
import { cn } from '@/lib/utils'
import { useLanguage } from '@/components/language-provider'

const map: Record<Condition, { Icon: typeof Sun; className: string; label: string }> = {
  clear: { Icon: Sun, className: 'text-warning', label: 'Clear sky' },
  'partly-cloudy': { Icon: CloudSun, className: 'text-warning', label: 'Partly cloudy' },
  cloudy: { Icon: Cloud, className: 'text-muted-foreground', label: 'Cloudy' },
  rain: { Icon: CloudRain, className: 'text-primary', label: 'Rain' },
  'heavy-rain': { Icon: CloudDrizzle, className: 'text-primary', label: 'Heavy rain' },
  thunderstorm: { Icon: CloudLightning, className: 'text-chart-4', label: 'Thunderstorm' },
  snow: { Icon: CloudSnow, className: 'text-primary', label: 'Snow' },
  fog: { Icon: CloudFog, className: 'text-muted-foreground', label: 'Fog' },
  wind: { Icon: Wind, className: 'text-chart-3', label: 'Windy' },
}

export function conditionLabel(condition: Condition, translate: (text: string) => string = (text) => text) {
  return translate(map[condition].label)
}

export function WeatherIcon({
  condition,
  className,
  isNight = false,
}: {
  condition: Condition
  className?: string
  isNight?: boolean
}) {
  const selected = map[condition]
  const Icon = isNight
    ? condition === 'clear'
      ? Moon
      : condition === 'partly-cloudy'
        ? CloudMoon
        : selected.Icon
    : selected.Icon
  const colorClass = selected.className
  const label = selected.label
  const { t } = useLanguage()
  return <Icon aria-label={t(label)} className={cn(colorClass, className)} />
}
