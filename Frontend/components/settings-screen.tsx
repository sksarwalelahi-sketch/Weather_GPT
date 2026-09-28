'use client'

import { useEffect, useState } from 'react'
import {
  Bell,
  Globe,
  Mic,
  Moon,
  Ruler,
  Settings as SettingsIcon,
  Sun,
  TriangleAlert,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card, PageHeader } from '@/components/ui-kit'
import { useTheme } from '@/components/theme-provider'
import { alertNotificationsEnabled, setAlertNotifications } from '@/components/alert-notification-provider'
import { languages, useLanguage, type AppLanguage } from '@/components/language-provider'

function Toggle({ on, onChange, label }: { on: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button
      role="switch"
      aria-checked={on}
      aria-label={label}
      onClick={() => onChange(!on)}
      className={cn(
        'relative h-6 w-11 shrink-0 rounded-full transition-colors',
        on ? 'bg-primary' : 'bg-muted-foreground/30',
      )}
    >
      <span
        className={cn(
          'absolute top-0.5 size-5 rounded-full bg-background shadow transition-transform',
          on ? 'translate-x-5' : 'translate-x-0.5',
        )}
      />
    </button>
  )
}

function Row({
  icon: Icon,
  title,
  desc,
  children,
}: {
  icon: LucideIcon
  title: string
  desc: string
  children: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-border py-3.5 last:border-0">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 grid size-9 shrink-0 place-items-center rounded-lg bg-muted text-primary">
          <Icon className="size-4" />
        </span>
        <div>
          <div className="text-sm font-medium">{title}</div>
          <div className="text-xs text-muted-foreground text-pretty">{desc}</div>
        </div>
      </div>
      {children}
    </div>
  )
}

export function SettingsScreen() {
  const { theme, toggle } = useTheme()
  const { language, setLanguage, t, label } = useLanguage()
  const [unit, setUnit] = useState<'C' | 'F'>('C')
  const [voice, setVoice] = useState(true)
  const [autoRead, setAutoRead] = useState(false)
  const [severe, setSevere] = useState(false)
  const [daily, setDaily] = useState(true)

  const changeAlertNotifications = async (enabled: boolean) => {
    const result = await setAlertNotifications(enabled)
    if (result === 'enabled') {
      setSevere(enabled)
      return
    }
    setSevere(false)
    window.alert(result === 'unsupported'
      ? 'This browser does not support device notifications.'
      : 'Notification permission is blocked. Allow notifications in your browser settings, then try again.')
  }

  useEffect(() => {
    setSevere(alertNotificationsEnabled())
  }, [])

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-5 animate-in fade-in duration-500">
      <PageHeader title={t('Settings')} subtitle={t('Personalise WeatherGPT for accessibility and your region')} icon={SettingsIcon} />

      <Card>
        <h2 className="mb-1 text-sm font-semibold">{t('Language & Units')}</h2>
        <Row icon={Globe} title={t('App language')} desc={t('Multilingual support for Indian languages')}>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as AppLanguage)}
            className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm outline-none"
          >
            {languages.map((l) => (
              <option key={l} value={l}>
                {label(l)}
              </option>
            ))}
          </select>
        </Row>
        <Row icon={Ruler} title={t('Temperature unit')} desc={t('Display readings in Celsius or Fahrenheit')}>
          <div className="flex overflow-hidden rounded-lg border border-border">
            {(['C', 'F'] as const).map((u) => (
              <button
                key={u}
                onClick={() => setUnit(u)}
                className={cn(
                  'px-3 py-1.5 text-sm font-medium transition-colors',
                  unit === u ? 'bg-primary text-primary-foreground' : 'bg-background text-muted-foreground',
                )}
              >
                °{u}
              </button>
            ))}
          </div>
        </Row>
      </Card>

      <Card>
        <h2 className="mb-1 text-sm font-semibold">{t('Voice & Accessibility')}</h2>
        <Row icon={Mic} title={t('Voice input')} desc={t('Ask questions by speaking — ideal for rural accessibility')}>
          <Toggle on={voice} onChange={setVoice} label={t('Voice input')} />
        </Row>
        <Row icon={Bell} title={t('Read responses aloud')} desc={t('Text-to-speech for WeatherGPT replies')}>
          <Toggle on={autoRead} onChange={setAutoRead} label={t('Read responses aloud')} />
        </Row>
      </Card>

      <Card>
        <h2 className="mb-1 text-sm font-semibold">{t('Notifications')}</h2>
        <Row icon={TriangleAlert} title={t('Severe weather alerts')} desc={t('Push warnings for storms, floods & cyclones')}>
          <Toggle on={severe} onChange={changeAlertNotifications} label={t('Severe weather alerts')} />
        </Row>
        <Row icon={Bell} title={t('Daily forecast summary')} desc={t('A morning briefing at 7:00 AM')}>
          <Toggle on={daily} onChange={setDaily} label={t('Daily forecast summary')} />
        </Row>
      </Card>

      <Card>
        <h2 className="mb-1 text-sm font-semibold">{t('Appearance')}</h2>
        <Row icon={theme === 'dark' ? Moon : Sun} title={t('Dark mode')} desc={t('Switch between light and dark themes')}>
          <Toggle on={theme === 'dark'} onChange={toggle} label={t('Dark mode')} />
        </Row>
      </Card>

      <p className="pb-2 text-center text-xs text-muted-foreground">
        WeatherGPT · SIH 2026 · PS-26068 · Data via IMD, GFS &amp; WRF
      </p>
    </div>
  )
}
