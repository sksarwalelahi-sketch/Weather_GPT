'use client'

import { createContext, useCallback, useContext, useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextValue {
  theme: Theme
  toggle: () => void
}

const ThemeContext = createContext<ThemeContextValue>({ theme: 'light', toggle: () => {} })

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // Keep the first server and browser render identical. The saved preference
  // is applied immediately after hydration.
  const [theme, setTheme] = useState<Theme>('light')

  useEffect(() => {
    const stored = window.localStorage.getItem('wgpt-theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const initial: Theme = stored === 'dark' || stored === 'light'
      ? stored
      : prefersDark ? 'dark' : 'light'
    setTheme(initial)
  }, [])

  useEffect(() => {
    const root = document.documentElement
    root.classList.toggle('dark', theme === 'dark')
    root.classList.toggle('light', theme === 'light')
    window.localStorage.setItem('wgpt-theme', theme)
  }, [theme])

  const toggle = useCallback(() => setTheme((t) => (t === 'dark' ? 'light' : 'dark')), [])

  return <ThemeContext.Provider value={{ theme, toggle }}>{children}</ThemeContext.Provider>
}

export const useTheme = () => useContext(ThemeContext)
