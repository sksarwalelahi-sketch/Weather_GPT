'use client'

import { useEffect, useRef, useState } from 'react'
import { getActiveAlerts, type LiveAlert, websocketUrl } from '@/lib/live-api'

const preferenceKey = 'weathergpt.alert-notifications'
const preferenceEvent = 'weathergpt:alert-notification-preference'

export type NotificationSetupResult = 'enabled' | 'denied' | 'unsupported'

export function alertNotificationsEnabled() {
  return typeof window !== 'undefined' && window.localStorage.getItem(preferenceKey) === 'true'
}

export async function setAlertNotifications(enabled: boolean): Promise<NotificationSetupResult> {
  if (!('Notification' in window)) return 'unsupported'

  if (!enabled) {
    window.localStorage.setItem(preferenceKey, 'false')
    window.dispatchEvent(new Event(preferenceEvent))
    return 'enabled'
  }

  const permission = Notification.permission === 'default'
    ? await Notification.requestPermission()
    : Notification.permission

  if (permission !== 'granted') return 'denied'
  window.localStorage.setItem(preferenceKey, 'true')
  window.dispatchEvent(new Event(preferenceEvent))
  return 'enabled'
}

function alertText(alert: LiveAlert) {
  return alert.description ?? `${alert.severity} weather alert${alert.area ? ` for ${alert.area}` : ''}.`
}

export function AlertNotificationProvider({ children }: { children: React.ReactNode }) {
  const [enabled, setEnabled] = useState(false)
  const knownAlertIds = useRef(new Set<string>())

  useEffect(() => {
    const syncPreference = () => setEnabled(alertNotificationsEnabled())
    syncPreference()
    window.addEventListener(preferenceEvent, syncPreference)
    return () => window.removeEventListener(preferenceEvent, syncPreference)
  }, [])

  useEffect(() => {
    if (!enabled || !('Notification' in window) || Notification.permission !== 'granted') return

    let disposed = false
    let socket: WebSocket | null = null

    const notify = (alert: LiveAlert) => {
      if (!alert.alert_id || knownAlertIds.current.has(alert.alert_id)) return
      knownAlertIds.current.add(alert.alert_id)
      const notification = new Notification(alert.title || 'WeatherGPT alert', {
        body: alertText(alert),
        tag: `weathergpt-alert-${alert.alert_id}`,
        icon: '/favicon.ico',
      })
      notification.onclick = () => {
        window.focus()
        window.location.assign('/alerts')
        notification.close()
      }
    }

    const loadExistingAlerts = async () => {
      try {
        const { alerts } = await getActiveAlerts()
        if (!disposed) alerts.forEach((alert) => knownAlertIds.current.add(alert.alert_id))
      } catch {
        // The WebSocket may still deliver live alerts when the initial request fails.
      }
    }

    void loadExistingAlerts()
    try {
      socket = new WebSocket(websocketUrl('/ws/alerts'))
      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as { type?: string; data?: LiveAlert }
          if (message.type === 'alert' && message.data) notify(message.data)
        } catch {
          // Ignore malformed live-update messages.
        }
      }
    } catch {
      // Polling still provides notifications while the app is open.
    }

    const poll = window.setInterval(async () => {
      try {
        const { alerts } = await getActiveAlerts()
        alerts.forEach(notify)
      } catch {
        // The next polling interval will retry.
      }
    }, 60_000)

    return () => {
      disposed = true
      socket?.close()
      window.clearInterval(poll)
    }
  }, [enabled])

  return <>{children}</>
}
