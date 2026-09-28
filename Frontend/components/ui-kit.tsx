import type { LucideIcon } from 'lucide-react'
import type { AlertSeverity } from '@/lib/weather-data'
import { cn } from '@/lib/utils'
import { useLanguage } from '@/components/language-provider'

export function Card({
  className,
  children,
}: {
  className?: string
  children: React.ReactNode
}) {
  return (
    <div className={cn('rounded-2xl border border-border bg-card p-5 shadow-sm', className)}>
      {children}
    </div>
  )
}

export function PageHeader({
  title,
  subtitle,
  icon: Icon,
  action,
}: {
  title: string
  subtitle?: string
  icon?: LucideIcon
  action?: React.ReactNode
}) {
  const { t } = useLanguage()
  return (
    <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-3">
        {Icon && (
          <span className="grid size-10 place-items-center rounded-xl bg-primary/10 text-primary">
            <Icon className="size-5" />
          </span>
        )}
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-balance md:text-2xl">{t(title)}</h1>
          {subtitle && <p className="text-sm text-muted-foreground text-pretty">{t(subtitle)}</p>}
        </div>
      </div>
      {action}
    </div>
  )
}

export function StatTile({
  icon: Icon,
  label,
  value,
  unit,
  hint,
}: {
  icon: LucideIcon
  label: string
  value: string | number
  unit?: string
  hint?: string
}) {
  const { t } = useLanguage()
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-card/90 via-card/70 to-card/40 p-4 shadow-sm backdrop-blur-md transition-all duration-300 hover:-translate-y-1 hover:border-primary/40 hover:shadow-lg">
      <div className="pointer-events-none absolute -bottom-6 -right-6 h-16 w-16 rounded-full bg-primary/10 blur-xl transition-all duration-300 group-hover:bg-primary/20" />
      <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
        <Icon className="size-4 text-primary" />
        {t(label)}
      </div>
      <div className="mt-2 font-mono text-2xl font-bold tracking-tight tabular-nums text-foreground">
        {value}
        {unit && <span className="ml-1 text-sm font-normal text-muted-foreground">{unit}</span>}
      </div>
      {hint && <p className="mt-1 text-xs text-muted-foreground truncate">{t(hint)}</p>}
    </div>
  )
}

const severityStyles: Record<AlertSeverity, string> = {
  advisory: 'bg-primary/10 text-primary border-primary/20',
  watch: 'bg-warning/15 text-warning-foreground border-warning/30',
  warning: 'bg-warning/20 text-warning-foreground border-warning/40',
  severe: 'bg-destructive/12 text-destructive border-destructive/30',
}

export function SeverityBadge({ severity }: { severity: AlertSeverity }) {
  const { t } = useLanguage()
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide',
        severityStyles[severity],
      )}
    >
      {t(severity)}
    </span>
  )
}
