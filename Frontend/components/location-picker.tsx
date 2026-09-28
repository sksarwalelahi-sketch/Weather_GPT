'use client'

import { MapPin, Search, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { searchLocations, type LocationSearchResult } from '@/lib/live-api'
import { useDeviceLocation } from '@/components/location-provider'
import { useLanguage } from '@/components/language-provider'

export function LocationPicker() {
  const { setManualLocation, requestLocation, isManual } = useDeviceLocation()
  const { t } = useLanguage()
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<LocationSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const searchRequest = useRef(0)

  useEffect(() => {
    const requestId = ++searchRequest.current
    if (!open || query.trim().length < 2) {
      setResults([])
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    const timer = window.setTimeout(async () => {
      try {
        const response = await searchLocations(query.trim())
        // A previous partial-query request can finish after the current one.
        // Never let stale results replace the results for the visible query.
        if (requestId === searchRequest.current) {
          setResults(response.locations)
        }
      } catch (reason: unknown) {
        if (requestId === searchRequest.current) {
          setError(reason instanceof Error ? reason.message : t('Location search failed.'))
        }
      } finally {
        if (requestId === searchRequest.current) {
          setLoading(false)
        }
      }
    }, 350)
    return () => window.clearTimeout(timer)
  }, [open, query, t])

  const choose = (place: LocationSearchResult) => {
    if (!Number.isFinite(place.latitude) || !Number.isFinite(place.longitude)) {
      setError(t('This location does not have usable coordinates.'))
      return
    }
    const name = [place.name, place.admin2, place.admin1, place.country].filter(Boolean).join(', ')
    setManualLocation({ latitude: place.latitude, longitude: place.longitude, accuracy: 0 }, name)
    setOpen(false)
    setQuery('')
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-sm font-medium"
        aria-label={t('Choose a location')}
      >
        <Search className="size-4 text-primary" />
        {t('Choose location')}
      </button>
      {open && (
        <div className="fixed inset-0 z-[1000] grid place-items-start bg-black/30 p-4 pt-20" onClick={() => setOpen(false)}>
          <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-4 shadow-xl" onClick={(event) => event.stopPropagation()}>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold">{t('Choose a location')}</h2>
              <button type="button" onClick={() => setOpen(false)} aria-label={t('Close')}><X className="size-4" /></button>
            </div>
            <div className="flex items-center gap-2 rounded-lg border border-border px-3 py-2">
              <Search className="size-4 text-muted-foreground" />
              <input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder={t('Search city, district, or village')} className="min-w-0 flex-1 bg-transparent text-sm outline-none" />
            </div>
            {loading && <p className="py-3 text-sm text-muted-foreground">{t('Searching locations…')}</p>}
            {error && <p className="py-3 text-sm text-destructive">{error}</p>}
            <div className="mt-2 max-h-72 overflow-y-auto">
              {results.map((place) => (
                <button key={`${place.latitude}-${place.longitude}-${place.name}`} type="button" onClick={() => choose(place)} className="flex w-full items-start gap-3 rounded-lg px-3 py-3 text-left hover:bg-muted">
                  <MapPin className="mt-0.5 size-4 shrink-0 text-primary" />
                  <span>
                    <span className="block text-sm font-medium">{place.name}</span>
                    <span className="block text-xs text-muted-foreground">
                      {[place.admin2, place.admin1, place.country].filter(Boolean).join(', ')}
                    </span>
                  </span>
                </button>
              ))}
            </div>
            {isManual && <button type="button" onClick={() => { setOpen(false); requestLocation() }} className="mt-3 text-xs font-medium text-primary">{t('Use current device location')}</button>}
          </div>
        </div>
      )}
    </>
  )
}
