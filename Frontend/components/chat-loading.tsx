'use client'

import { useLanguage } from '@/components/language-provider'

export function ChatLoading() {
  const { t } = useLanguage()
  return <div className="p-8 text-sm text-muted-foreground">{t('Loading WeatherGPT…')}</div>
}
