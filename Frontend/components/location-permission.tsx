'use client'

import { LoaderCircle, MapPin } from 'lucide-react'
import { useDeviceLocation } from '@/components/location-provider'

export function LocationPermission() {
  const { status, error, requestLocation } = useDeviceLocation()

  if (status === 'granted') return null

  const isRequesting = status === 'requesting'
  const message =
    error ??
    (isRequesting
      ? 'Waiting for your browser location permission…'
      : 'Allow location access to see live weather for where you are.')

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-primary/25 bg-primary/5 p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex gap-3">
        <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-primary text-primary-foreground">
          <MapPin className="size-5" />
        </span>
        <div>
          <h2 className="text-sm font-semibold">Use your current location</h2>
          <p className="mt-0.5 text-sm text-muted-foreground">{message}</p>
        </div>
      </div>
      <button
        type="button"
        onClick={requestLocation}
        disabled={isRequesting}
        className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isRequesting && <LoaderCircle className="size-4 animate-spin" />}
        {isRequesting ? 'Requesting…' : 'Enable location'}
      </button>
    </div>
  )
}
