'use client'

import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { CloudSun, Mic, Send, Sparkles, StopCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { chatSuggestions, type ChatMessage } from '@/lib/weather-data'
import { askWeather, transcribeVoice, type AskResponse, type ChatWeatherData } from '@/lib/live-api'
import { useDeviceLocation } from '@/components/location-provider'
import { useLanguage } from '@/components/language-provider'

function DataChips({ data }: { data: NonNullable<ChatMessage['data']> }) {
  const { t } = useLanguage()
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {data.map((d) => (
        <div key={d.label} className="rounded-lg border border-border bg-background px-2.5 py-1.5">
          <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{t(d.label)}</div>
          <div className="font-mono text-sm font-semibold tabular-nums">{d.value}</div>
        </div>
      ))}
    </div>
  )
}

function Bubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'
  return (
    <div className={cn('flex gap-2.5', isUser ? 'flex-row-reverse' : 'flex-row')}>
      {!isUser && (
        <span className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg sky-gradient text-primary-foreground">
          <CloudSun className="size-4" />
        </span>
      )}
      <div
        className={cn(
          'max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed md:max-w-[75%]',
          isUser
            ? 'rounded-br-md bg-primary text-primary-foreground'
            : 'rounded-bl-md border border-border bg-card',
        )}
      >
        <p className="text-pretty">{message.content}</p>
        {message.data && <DataChips data={message.data} />}
      </div>
    </div>
  )
}

function TypingDots({ label }: { label: string }) {
  return (
    <div className="flex gap-2.5">
      <span className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg sky-gradient text-primary-foreground">
        <CloudSun className="size-4" />
      </span>
      <div className="flex items-center gap-2 rounded-2xl rounded-bl-md border border-border bg-card px-4 py-3.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="size-1.5 animate-bounce rounded-full bg-muted-foreground"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
    </div>
  )
}

function formatValue(value: number | undefined, unit: string) {
  return typeof value === 'number' && Number.isFinite(value) ? `${value}${unit}` : null
}

function weatherChips(result: AskResponse) {
  const data: ChatWeatherData | undefined = result.tool_result?.data
  if (!data) return undefined

  const temperature = formatValue(data.temperature_c ?? data.temperature_max_c, '°C')
  const lowTemperature = formatValue(data.temperature_min_c, '°C')
  const humidity = formatValue(data.humidity, '%')
  const wind = formatValue(data.wind_speed_kmh, ' km/h')
  const rainfall = formatValue(data.rainfall_mm ?? data.precipitation_mm, ' mm')
  const rainChance = formatValue(data.rain_probability, '%')
  const risk = result.intelligence?.risk?.level
    ?? (typeof result.intelligence?.maximum_risk_level === 'string' ? result.intelligence.maximum_risk_level : null)

  const chips = [
    temperature && { label: data.temperature_c === undefined && lowTemperature ? 'High' : 'Temperature', value: temperature },
    lowTemperature && { label: 'Low', value: lowTemperature },
    humidity && { label: 'Humidity', value: humidity },
    wind && { label: 'Wind', value: wind },
    rainfall && { label: 'Rainfall', value: rainfall },
    rainChance && { label: 'Rain chance', value: rainChance },
    risk && { label: 'Risk', value: risk },
  ].filter((chip): chip is { label: string; value: string } => Boolean(chip))

  return chips.length ? chips : undefined
}

const voiceLocales: Record<string, string> = {
  English: 'en-IN', Assamese: 'as-IN', Bengali: 'bn-IN', Gujarati: 'gu-IN', Hindi: 'hi-IN',
  Kannada: 'kn-IN', Malayalam: 'ml-IN', Marathi: 'mr-IN', Nepali: 'ne-NP', Odia: 'or-IN',
  Punjabi: 'pa-IN', Tamil: 'ta-IN', Telugu: 'te-IN', Urdu: 'ur-IN',
}

function speechLanguage(text: string, preferredLanguage?: string, detectedLanguage?: string) {
  if (preferredLanguage && voiceLocales[preferredLanguage]) return voiceLocales[preferredLanguage]
  if (detectedLanguage === 'Hinglish') return 'hi-IN'
  if (detectedLanguage && voiceLocales[detectedLanguage]) return voiceLocales[detectedLanguage]
  if (/\p{Script=Devanagari}/u.test(text)) return 'hi-IN'
  if (/\p{Script=Bengali}/u.test(text)) return 'bn-IN'
  if (/\p{Script=Gujarati}/u.test(text)) return 'gu-IN'
  if (/\p{Script=Gurmukhi}/u.test(text)) return 'pa-IN'
  if (/\p{Script=Oriya}/u.test(text)) return 'or-IN'
  if (/\p{Script=Tamil}/u.test(text)) return 'ta-IN'
  if (/\p{Script=Telugu}/u.test(text)) return 'te-IN'
  if (/\p{Script=Kannada}/u.test(text)) return 'kn-IN'
  if (/\p{Script=Malayalam}/u.test(text)) return 'ml-IN'
  if (/\p{Script=Arabic}/u.test(text)) return 'ur-IN'
  return navigator.language || 'en-IN'
}

function speakAnswer(text: string, preferredLanguage?: string, detectedLanguage?: string) {
  if (!('speechSynthesis' in window) || !text.trim()) return

  const lang = speechLanguage(text, preferredLanguage, detectedLanguage)
  const speak = () => {
    const synthesis = window.speechSynthesis
    const voices = synthesis.getVoices()
    const languagePrefix = lang.split('-')[0].toLowerCase()
    const voice = voices.find((candidate) => candidate.lang.toLowerCase() === lang.toLowerCase())
      ?? voices.find((candidate) => candidate.lang.toLowerCase().startsWith(`${languagePrefix}-`))
      ?? voices.find((candidate) => candidate.lang.toLowerCase().startsWith(languagePrefix))

    synthesis.cancel()
    // Keep chunks short because Chromium can stop speaking long Indian-language
    // utterances before reaching the end.
    const chunks = text.match(/[^.!?।॥]+[.!?।॥]*/gu) ?? [text]
    chunks.forEach((chunk, index) => {
      const utterance = new SpeechSynthesisUtterance(chunk.trim())
      utterance.lang = lang
      if (voice) utterance.voice = voice
      if (index > 0) utterance.rate = 0.95
      synthesis.speak(utterance)
    })
  }

  // Some browsers populate their voice list asynchronously after page load.
  if (window.speechSynthesis.getVoices().length > 0) {
    speak()
  } else {
    window.setTimeout(speak, 250)
  }
}

export function ChatScreen() {
  const params = useSearchParams()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const [thinkingLabel, setThinkingLabel] = useState('Checking live weather…')
  const [listening, setListening] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const [voiceLanguage, setVoiceLanguage] = useState('en-IN')
  const { location, locationName } = useDeviceLocation()
  const { language, t } = useLanguage()
  const scrollRef = useRef<HTMLDivElement>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const recordingTimeoutRef = useRef<number | null>(null)
  const silenceMonitorRef = useRef<number | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const recordingFailedRef = useRef(false)
  const seededRef = useRef(false)

  useEffect(() => {
    if (messages.length === 0 || (messages.length === 1 && messages[0]?.id === 'greet')) {
      setMessages((current) => [{
        id: 'greet',
        role: 'assistant',
        content: t('Namaste! I am WeatherGPT, your conversational weather assistant. Ask me about forecasts, rainfall, storms, air quality, travel safety, or sector advisories — in plain language.'),
      }, ...current.filter((message) => message.id !== 'greet')])
    }
  }, [language, messages.length, t])

  const send = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || thinking) return
    const userMsg: ChatMessage = { id: Math.random().toString(36).slice(2), role: 'user', content: trimmed }
    setMessages((m) => [...m, userMsg])
    setInput('')
    setThinking(true)
    setThinkingLabel(t('Checking live weather…'))
    const phaseTimer = window.setTimeout(() => setThinkingLabel(t('Preparing your answer…')), 2500)
    try {
      const result = await askWeather(trimmed, {
        locationName,
        latitude: location?.latitude,
        longitude: location?.longitude,
        language,
        history: messages.slice(-8).map(({ role, content }) => ({ role, content })),
      })
      const answer = result.answer?.trim() || result.intelligence?.advisory?.message?.trim() || 'I could not find a live answer.'
      setMessages((m) => [...m, {
        id: Math.random().toString(36).slice(2),
        role: 'assistant',
        content: answer,
        data: weatherChips(result),
      }])
      speakAnswer(answer, language, result.analysis?.language)
    } catch (error) {
      setMessages((m) => [...m, {
        id: Math.random().toString(36).slice(2),
        role: 'assistant',
        content: error instanceof Error
          ? t(error.message)
          : t('The live assistant is unavailable.'),
      }])
    } finally {
      window.clearTimeout(phaseTimer)
      setThinking(false)
    }
  }

  // Seed from ?q= (e.g. tapped a prompt on the home screen)
  useEffect(() => {
    const q = params.get('q')
    if (q && !seededRef.current) {
      seededRef.current = true
      send(q)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, thinking])

  useEffect(() => {
    const savedLanguage = window.localStorage.getItem('weathergpt.voice-language')
    if (savedLanguage && Object.values(voiceLocales).includes(savedLanguage)) setVoiceLanguage(savedLanguage)
  }, [])

  useEffect(() => {
    const appVoiceLanguage = voiceLocales[language]
    if (appVoiceLanguage) {
      setVoiceLanguage(appVoiceLanguage)
      window.localStorage.setItem('weathergpt.voice-language', appVoiceLanguage)
    }
  }, [language])

  useEffect(() => () => {
    if (recordingTimeoutRef.current !== null) window.clearTimeout(recordingTimeoutRef.current)
    if (silenceMonitorRef.current !== null) window.clearInterval(silenceMonitorRef.current)
    if (recorderRef.current?.state === 'recording') {
      recorderRef.current.ondataavailable = null
      recorderRef.current.onstop = null
      recorderRef.current.onerror = null
      recorderRef.current.stop()
    }
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop())
    void audioContextRef.current?.close()
  }, [])

  const toggleMic = async () => {
    if (listening) {
      recorderRef.current?.stop()
      return
    }
    if (transcribing) return
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setMessages((messages) => [...messages, {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Voice recording is not supported in this browser. Use a current browser over HTTPS or localhost.',
      }])
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const supportedMimeType = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/mp4',
      ].find((mimeType) => MediaRecorder.isTypeSupported(mimeType))
      const recorder = supportedMimeType
        ? new MediaRecorder(stream, { mimeType: supportedMimeType })
        : new MediaRecorder(stream)
      mediaStreamRef.current = stream
      recorderRef.current = recorder
      audioChunksRef.current = []
      recordingFailedRef.current = false
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data)
      }
      recorder.onerror = () => {
        recordingFailedRef.current = true
        if (recordingTimeoutRef.current !== null) window.clearTimeout(recordingTimeoutRef.current)
        if (silenceMonitorRef.current !== null) window.clearInterval(silenceMonitorRef.current)
        recordingTimeoutRef.current = null
        silenceMonitorRef.current = null
        void audioContextRef.current?.close()
        audioContextRef.current = null
        stream.getTracks().forEach((track) => track.stop())
        mediaStreamRef.current = null
        recorderRef.current = null
        setListening(false)
        setMessages((messages) => [...messages, {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: 'Microphone recording failed. Check microphone access and try again.',
        }])
      }
      recorder.onstop = async () => {
        if (recordingTimeoutRef.current !== null) window.clearTimeout(recordingTimeoutRef.current)
        if (silenceMonitorRef.current !== null) window.clearInterval(silenceMonitorRef.current)
        recordingTimeoutRef.current = null
        silenceMonitorRef.current = null
        void audioContextRef.current?.close()
        audioContextRef.current = null
        stream.getTracks().forEach((track) => track.stop())
        mediaStreamRef.current = null
        recorderRef.current = null
        setListening(false)
        if (recordingFailedRef.current) {
          audioChunksRef.current = []
          return
        }
        setTranscribing(true)
        const audio = new Blob(audioChunksRef.current, { type: recorder.mimeType || 'audio/webm' })
        audioChunksRef.current = []
        try {
          const result = await transcribeVoice(audio, voiceLanguage)
          if (!result.text.trim()) {
            throw new Error('No speech was recognized. Speak clearly and try again.')
          }
          setInput(result.text.trim())
        } catch (error) {
          setMessages((messages) => [...messages, {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: error instanceof Error ? error.message : 'Voice transcription failed. Please try again.',
          }])
        } finally {
          setTranscribing(false)
        }
      }
      setInput('')
      setListening(true)
      recorder.start()
      if (typeof AudioContext !== 'undefined') {
        const audioContext = new AudioContext()
        const analyser = audioContext.createAnalyser()
        analyser.fftSize = 512
        audioContext.createMediaStreamSource(stream).connect(analyser)
        audioContextRef.current = audioContext
        const samples = new Uint8Array(analyser.fftSize)
        const recordingStartedAt = Date.now()
        let speechStartedAt: number | null = null
        let lastSpeechAt: number | null = null
        silenceMonitorRef.current = window.setInterval(() => {
          analyser.getByteTimeDomainData(samples)
          let squareTotal = 0
          for (const sample of samples) {
            const amplitude = (sample - 128) / 128
            squareTotal += amplitude * amplitude
          }
          const volume = Math.sqrt(squareTotal / samples.length)
          const now = Date.now()
          if (volume >= 0.015) {
            speechStartedAt ??= now
            lastSpeechAt = now
          }
          if (
            speechStartedAt !== null
            && lastSpeechAt !== null
            && now - recordingStartedAt >= 700
            && now - lastSpeechAt >= 1700
            && recorder.state === 'recording'
          ) {
            recorder.stop()
          }
        }, 120)
      }
      recordingTimeoutRef.current = window.setTimeout(() => {
        if (recorder.state === 'recording') recorder.stop()
      }, 30_000)
    } catch (error) {
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop())
      mediaStreamRef.current = null
      recorderRef.current = null
      setListening(false)
      setMessages((messages) => [...messages, {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: error instanceof Error
          ? `Could not access the microphone: ${error.message}`
          : 'Could not access the microphone. Allow microphone access and try again.',
      }])
    }
  }

  return (
    <div className="mx-auto flex h-[calc(100svh-8.5rem)] max-w-3xl flex-col lg:h-[calc(100svh-6.5rem)]">
      <div className="mb-3 flex items-center gap-2.5">
        <span className="grid size-10 place-items-center rounded-xl bg-primary/10 text-primary">
          <Sparkles className="size-5" />
        </span>
        <div>
          <h1 className="text-lg font-semibold tracking-tight">WeatherGPT</h1>
          <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="size-1.5 rounded-full bg-success" /> {t('Online · Multilingual')}
          </p>
        </div>
      </div>

      <div ref={scrollRef} className="no-scrollbar flex-1 space-y-4 overflow-y-auto rounded-2xl border border-border bg-muted/30 p-4">
        {messages.map((m) => (
          <Bubble key={m.id} message={m} />
        ))}
        {thinking && <TypingDots label={thinkingLabel} />}
      </div>

      {messages.length <= 1 && (
        <div className="no-scrollbar mt-3 flex gap-2 overflow-x-auto">
          {chatSuggestions.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="shrink-0 rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:border-primary/40 hover:text-primary"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault()
          send(input)
        }}
        className="mt-3 flex items-center gap-2 rounded-2xl border border-border bg-card p-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing && e.keyCode !== 229) {
              e.preventDefault()
              send(input)
            }
          }}
          placeholder={listening ? t('Listening…') : transcribing ? t('Transcribing voice…') : t('Ask WeatherGPT…')}
          className="flex-1 bg-transparent px-3 text-sm outline-none placeholder:text-muted-foreground"
        />
        <button
          type="button"
          onClick={toggleMic}
          aria-label={listening ? 'Stop voice input' : transcribing ? 'Transcribing voice input' : 'Start voice input'}
          disabled={transcribing}
          className={cn(
            'grid size-9 place-items-center rounded-xl border border-border text-muted-foreground transition-colors',
            listening ? 'animate-pulse border-destructive/40 bg-destructive/10 text-destructive' : 'hover:text-foreground',
          )}
        >
          {listening ? <StopCircle className="size-4" /> : <Mic className="size-4" />}
        </button>
        <label className="sr-only" htmlFor="voice-language">Voice input language</label>
        <select
          id="voice-language"
          value={voiceLanguage}
          onChange={(event) => {
            setVoiceLanguage(event.target.value)
            window.localStorage.setItem('weathergpt.voice-language', event.target.value)
          }}
          disabled={listening || transcribing}
          className="max-w-20 bg-transparent text-xs text-muted-foreground outline-none disabled:opacity-50"
        >
          {Object.entries(voiceLocales).map(([language, locale]) => (
            <option key={locale} value={locale}>{language}</option>
          ))}
        </select>
        <button
          type="submit"
          aria-label="Send message"
          disabled={!input.trim() || listening || transcribing}
          className="grid size-9 place-items-center rounded-xl bg-primary text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          <Send className="size-4" />
        </button>
      </form>
      {(listening || transcribing) && (
        <p role="status" className="mt-2 text-center text-xs text-muted-foreground">
          {listening
            ? t('Listening — speak now. I will transcribe after you pause, or tap stop.')
            : t('Transcribing your voice… please wait.')}
        </p>
      )}
    </div>
  )
}
