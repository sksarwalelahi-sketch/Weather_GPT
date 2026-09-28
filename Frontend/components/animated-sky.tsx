import { Cloud } from 'lucide-react'
import type { Condition } from '@/lib/weather-data'

// Decorative animated backdrop that reflects the current condition.
export function AnimatedSky({ condition }: { condition: Condition }) {
  const rainy = ['rain', 'heavy-rain', 'thunderstorm'].includes(condition)
  const sunny = ['clear', 'partly-cloudy'].includes(condition)

  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      {sunny && (
        <div className="absolute -right-10 -top-16 size-56 rounded-full bg-warning/30 blur-2xl animate-float-slow" />
      )}
      <Cloud className="absolute right-8 top-6 size-24 text-primary-foreground/20 animate-float-slow" />
      <Cloud className="absolute right-40 top-16 size-16 text-primary-foreground/15 animate-float-slow [animation-delay:1.5s]" />
      <Cloud className="absolute left-10 top-24 size-14 text-primary-foreground/10 animate-float-slow [animation-delay:3s]" />

      {rainy && (
        <div className="absolute inset-0">
          {Array.from({ length: 24 }).map((_, i) => (
            <span
              key={i}
              className="absolute top-0 h-6 w-px bg-primary-foreground/30 animate-rain"
              style={{
                left: `${(i * 4.3) % 100}%`,
                animationDelay: `${(i % 8) * 0.15}s`,
                animationDuration: `${1 + (i % 5) * 0.12}s`,
              }}
            />
          ))}
        </div>
      )}
    </div>
  )
}
