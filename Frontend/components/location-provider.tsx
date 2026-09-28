'use client'

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { reverseLocation } from '@/lib/live-api'

export type LocationStatus = 'idle' | 'requesting' | 'granted' | 'denied' | 'unavailable' | 'error'

export type DeviceLocation = {
  latitude: number
  longitude: number
  accuracy: number
}

export type SelectedLocation = {
  latitude: number
  longitude: number
  accuracy: number
}

type LocationContextValue = {
  location: DeviceLocation | null
  locationName: string | null
  status: LocationStatus
  error: string | null
  requestLocation: () => void
  setManualLocation: (location: SelectedLocation, name: string) => void
  isManual: boolean
}

const LocationContext = createContext<LocationContextValue>({
  location: null,
  locationName: null,
  status: 'idle',
  error: null,
  requestLocation: () => {},
  setManualLocation: () => {},
  isManual: false,
})

function readableLocationError(error: GeolocationPositionError) {
  if (error.code === error.PERMISSION_DENIED) return 'Location permission was denied. Enable it in your browser settings, then try again.'
  if (error.code === error.POSITION_UNAVAILABLE) return 'Your location is currently unavailable. Check your device location services and try again.'
  if (error.code === error.TIMEOUT) return 'Location request timed out. Please try again.'
  return 'We could not get your location. Please try again.'
}

export function LocationProvider({ children }: { children: React.ReactNode }) {
  const [location, setLocation] = useState<DeviceLocation | null>(null)
  const [locationName, setLocationName] = useState<string | null>(null)
  const [status, setStatus] = useState<LocationStatus>('idle')
  const [error, setError] = useState<string | null>(null)
  const [isManual, setIsManual] = useState(false)
  const watchId = useRef<number | null>(null)
  const manualMode = useRef(false)
  const hasLocation = useRef(false)
  const lastReportedLocation = useRef<{ latitude: number; longitude: number } | null>(null)

  const requestLocation = useCallback(() => {
    if (!('geolocation' in navigator)) {
      setStatus('unavailable')
      setError('This browser does not support location access.')
      return
    }

    setStatus('requesting')
    setIsManual(false)
    manualMode.current = false
    setError(null)
    window.localStorage.removeItem('weathergpt.manual-location')
    const updateLocation = ({ coords }: GeolocationPosition) => {
      // A GPS callback may already be queued when a manual location is
      // selected. Never let that stale callback overwrite the selection.
      if (manualMode.current) return
      // GPS accuracy changes frequently even when the user has not moved.
      // Do not restart every weather request for those insignificant updates.
      const latitude = Number(coords.latitude.toFixed(4))
      const longitude = Number(coords.longitude.toFixed(4))
      const previous = lastReportedLocation.current
      if (previous && previous.latitude === latitude && previous.longitude === longitude) {
        hasLocation.current = true
        setStatus('granted')
        setError(null)
        return
      }
      lastReportedLocation.current = { latitude, longitude }
      setLocation({ latitude, longitude, accuracy: coords.accuracy })
      hasLocation.current = true
      setStatus('granted')
      setError(null)
    }
    const handleError = (geolocationError: GeolocationPositionError) => {
      if (manualMode.current) return
      if (geolocationError.code === geolocationError.PERMISSION_DENIED) {
        setLocation(null)
        setLocationName(null)
        hasLocation.current = false
        setStatus('denied')
      } else if (hasLocation.current) {
        setStatus('granted')
      } else {
        setStatus('error')
      }
      setError(readableLocationError(geolocationError))
    }

    if (watchId.current !== null) navigator.geolocation.clearWatch(watchId.current)
    navigator.geolocation.getCurrentPosition(
      updateLocation,
      handleError,
      { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 },
    )
    watchId.current = navigator.geolocation.watchPosition(
      updateLocation,
      handleError,
      { enableHighAccuracy: true, timeout: 20000, maximumAge: 60000 },
    )
  }, [])

  const setManualLocation = useCallback((selected: SelectedLocation, name: string) => {
    if (
      !Number.isFinite(selected.latitude)
      || !Number.isFinite(selected.longitude)
      || selected.latitude < -90
      || selected.latitude > 90
      || selected.longitude < -180
      || selected.longitude > 180
    ) {
      setStatus('error')
      setError('The selected location has invalid coordinates. Please choose another result.')
      return
    }
    manualMode.current = true
    if (watchId.current !== null) {
      navigator.geolocation.clearWatch(watchId.current)
      watchId.current = null
    }
    const normalized = {
      latitude: Number(selected.latitude.toFixed(4)),
      longitude: Number(selected.longitude.toFixed(4)),
      accuracy: selected.accuracy,
    }
    lastReportedLocation.current = normalized
    setLocation(normalized)
    setLocationName(name)
    setIsManual(true)
    setStatus('granted')
    setError(null)
    window.localStorage.setItem('weathergpt.manual-location', JSON.stringify({ ...normalized, name }))
  }, [])

  useEffect(() => {
    const saved = window.localStorage.getItem('weathergpt.manual-location')
    if (saved) {
      try {
        const parsed = JSON.parse(saved) as SelectedLocation & { name?: string }
        if (typeof parsed.latitude === 'number' && typeof parsed.longitude === 'number' && parsed.name) {
          setManualLocation(parsed, parsed.name)
          return
        }
      } catch {
        window.localStorage.removeItem('weathergpt.manual-location')
      }
    }
    requestLocation()
    return () => {
      if (watchId.current !== null) navigator.geolocation.clearWatch(watchId.current)
    }
  }, [requestLocation, setManualLocation])

  useEffect(() => {
    if (!location) return
    let cancelled = false
    const timer = window.setTimeout(async () => {
      try {
        const place = await reverseLocation(location.latitude, location.longitude)
        if (!cancelled && !manualMode.current) {
          setLocationName(place.name || place.display_name || 'Your location')
        }
      } catch {
        if (!cancelled && !manualMode.current) setLocationName('Your location')
      }
    }, 300)
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [location])

  const value = useMemo(
    () => ({ location, locationName, status, error, requestLocation, setManualLocation, isManual }),
    [error, isManual, location, locationName, requestLocation, setManualLocation, status],
  )

  return <LocationContext.Provider value={value}>{children}</LocationContext.Provider>
}

export const useDeviceLocation = () => useContext(LocationContext)
