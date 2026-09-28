'use client'

import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { LiveForecast } from '@/lib/live-api'
import { formatSourceTime, upcomingHourlyIndices } from '@/lib/live-api'
import { useLanguage } from '@/components/language-provider'

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-border bg-popover px-3 py-2 text-xs shadow-md">
      <div className="mb-1 font-semibold">{label}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-2 font-mono tabular-nums">
          <span className="size-2 rounded-full" style={{ background: p.color }} />
          {p.name}: {p.value}
          {p.dataKey === 'temp' ? '°' : p.dataKey === 'precip' ? '%' : ' km/h'}
        </div>
      ))}
    </div>
  )
}

export function ForecastChart({ forecast }: { forecast: LiveForecast }) {
  const { t } = useLanguage()
  const indices = forecast.hourly
    ? upcomingHourlyIndices(forecast.hourly.time, forecast.timezone)
    : []
  const data = indices.flatMap((index) => {
    const hourly = forecast.hourly
    const temp = hourly?.temperature_2m[index]
    const precip = hourly?.precipitation_probability[index]
    const wind = hourly?.wind_speed_10m[index]
    if (!hourly || !Number.isFinite(temp) || !Number.isFinite(precip) || !Number.isFinite(wind)) return []
    return [{
      time: formatSourceTime(hourly.time[index]),
      temp,
      precip,
      wind,
    }]
  })
  if (data.length === 0) {
    return (
      <div className="grid h-64 place-items-center rounded-xl border border-dashed border-border px-4 text-center text-sm text-muted-foreground">
        {t('Hourly forecast data is unavailable right now. Please try again later.')}
      </div>
    )
  }
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
          <defs>
            <linearGradient id="tempFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--chart-1)" stopOpacity={0.4} />
              <stop offset="100%" stopColor="var(--chart-1)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
          <XAxis dataKey="time" tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} tickLine={false} axisLine={false} width={40} />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: 'var(--muted)', opacity: 0.4 }} />
          <Bar dataKey="precip" name={t('Precipitation probability')} fill="var(--chart-3)" radius={[3, 3, 0, 0]} barSize={12} opacity={0.65} />
          <Area type="monotone" dataKey="temp" name={t('Temp')} stroke="var(--chart-1)" strokeWidth={2.5} fill="url(#tempFill)" />
          <Line type="monotone" dataKey="wind" name={t('Wind')} stroke="var(--chart-2)" strokeWidth={2} dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
