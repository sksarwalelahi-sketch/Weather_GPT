import { Suspense } from 'react'
import { ChatScreen } from '@/components/chat-screen'
import { ChatLoading } from '@/components/chat-loading'

export default function Page() {
  return (
    <Suspense fallback={<ChatLoading />}>
      <ChatScreen />
    </Suspense>
  )
}
