import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { chatApi, chatHistoryApi } from '../api'
import type { ConversationOut } from '../api'
import type { Message } from '../components/ChatPanel'

export interface KbChatContextValue {
  kbId: number
  conversations: ConversationOut[]
  currentConversationId: number | null
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  loading: boolean
  createNewChat: () => Promise<number | null>
  selectConversation: (conversationId: number) => Promise<void>
  deleteConversation: (conversationId: number) => Promise<void>
  appendToCurrent: (conversationId: number, userMsg: Message, assistantMsg: Message) => Promise<void>
  refreshConversations: () => Promise<void>
}

const KbChatContext = createContext<KbChatContextValue | null>(null)

export function useKbChat() {
  const ctx = useContext(KbChatContext)
  return ctx
}

function historyMsgToMessage(m: { id: string; role: string; content: string; tool_calls?: Array<{ name?: string; arguments?: string }> | null }): Message {
  return {
    id: m.id,
    role: m.role as 'user' | 'assistant',
    content: m.content,
    tool_calls: m.tool_calls ?? undefined,
  }
}

export function KbChatProvider({ children }: { children: React.ReactNode }) {
  const { kbId: kbIdParam } = useParams<{ kbId: string }>()
  const kbId = kbIdParam ? parseInt(kbIdParam, 10) : NaN
  const [conversations, setConversations] = useState<ConversationOut[]>([])
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)

  const refreshConversations = useCallback(async () => {
    if (Number.isNaN(kbId)) return
    try {
      const list = await chatHistoryApi.listConversations(kbId)
      setConversations(list)
    } catch {
      setConversations([])
    }
  }, [kbId])

  useEffect(() => {
    refreshConversations()
  }, [refreshConversations])

  const createNewChat = useCallback(async (): Promise<number | null> => {
    if (Number.isNaN(kbId)) return null
    try {
      const conv = await chatHistoryApi.createConversation(kbId, null)
      setCurrentConversationId(conv.id)
      setMessages([])
      await refreshConversations()
      return conv.id
    } catch {
      return null
    }
  }, [kbId, refreshConversations])

  const selectConversation = useCallback(async (conversationId: number) => {
    if (Number.isNaN(kbId)) return
    setLoading(true)
    try {
      const msgs = await chatHistoryApi.getMessages(kbId, conversationId)
      setCurrentConversationId(conversationId)
      setMessages(msgs.map(historyMsgToMessage))
    } catch {
      setMessages([])
    } finally {
      setLoading(false)
    }
  }, [kbId])

  const deleteConversation = useCallback(async (conversationId: number) => {
    if (Number.isNaN(kbId)) return
    try {
      await chatHistoryApi.deleteConversation(kbId, conversationId)
      if (currentConversationId === conversationId) {
        setCurrentConversationId(null)
        setMessages([])
      }
      await refreshConversations()
    } catch {
      // ignore
    }
  }, [kbId, currentConversationId, refreshConversations])

  const appendToCurrent = useCallback(
    async (conversationId: number, userMsg: Message, assistantMsg: Message) => {
      if (Number.isNaN(kbId)) return
      try {
        await chatHistoryApi.appendMessages(kbId, conversationId, [
          { role: userMsg.role, content: userMsg.content },
          {
            role: assistantMsg.role,
            content: assistantMsg.content,
            tool_calls: assistantMsg.tool_calls ?? null,
          },
        ])
        await refreshConversations()
      } catch {
        // ignore
      }
    },
    [kbId, refreshConversations]
  )

  const value: KbChatContextValue = {
    kbId,
    conversations,
    currentConversationId,
    messages,
    setMessages,
    loading,
    createNewChat,
    selectConversation,
    deleteConversation,
    appendToCurrent,
    refreshConversations,
  }

  return (
    <KbChatContext.Provider value={value}>
      {children}
    </KbChatContext.Provider>
  )
}
