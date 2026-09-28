'use client'

import {
  Area,
  AreaChart,
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useLanguage } from '@/components/language-provider'
type MonthlyClimatePoint = { month: string; avgHigh: number; avgLow: number; rainfall: number }
type ClimateTrendPoint = { year: string; temp: number }

function Box({ children }: { children: React.ReactNode }) {
  return <div className="rounded-lg border border-border bg-popover px-3 py-2 text-xs shadow-md">{children}</div>
}

export function MonthlyClimateChart({ data }: { data: MonthlyClimatePoint[] }) {
  const { t } = useLanguage()
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
          <XAxis dataKey="month" tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} tickLine={false} axisLine={false} width={40} />
          <Tooltip
            cursor={{ fill: 'var(--muted)', opacity: 0.4 }}
            content={({ active, payload, label }: any) =>
              active && payload?.length ? (
                <Box>
                  <div className="mb-1 font-semibold">{label}</div>
                  {payload.map((p: any) => (
                    <div key={p.dataKey} className="font-mono tabular-nums">
                      {t(String(p.name))}: {p.value}
                      {p.dataKey === 'rainfall' || p.dataKey === 'normal' ? ' mm' : '°'}
                    </div>
                  ))}
                </Box>
              ) : null
            }
          />
          <Bar dataKey="rainfall" name={t('Rainfall')} fill="var(--chart-3)" radius={[3, 3, 0, 0]} barSize={14} />
          <Line dataKey="avgHigh" name={t('Avg high')} stroke="var(--chart-5)" strokeWidth={2} dot={false} />
          <Line dataKey="avgLow" name={t('Avg low')} stroke="var(--chart-1)" strokeWidth={2} dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

export function WarmingTrendChart({ data }: { data: ClimateTrendPoint[] }) {
  const { t } = useLanguage()
  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
          <defs>
            <linearGradient id="warmFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--chart-5)" stopOpacity={0.35} />
              <stop offset="100%" stopColor="var(--chart-5)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
          <XAxis dataKey="year" tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} tickLine={false} axisLine={false} />
          <YAxis domain={[24, 28]} tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} tickLine={false} axisLine={false} width={40} />
          <Tooltip
            content={({ active, payload, label }: any) =>
              active && payload?.length ? (
                <Box>
                  <div className="font-semibold">{label}</div>
                  <div className="font-mono tabular-nums">{t('Mean temp')}: {payload[0].value}°C</div>
                </Box>
              ) : null
            }
          />
          <Area type="monotone" dataKey="temp" stroke="var(--chart-5)" strokeWidth={2.5} fill="url(#warmFill)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
