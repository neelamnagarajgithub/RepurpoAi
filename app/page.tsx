"use client"

import { useEffect, useRef, useState } from "react"
import Header from "@/components/header"
import ConversationArea from "@/components/conversation-area"
import HeroSection from "@/components/hero-section"
import PromptBox from "@/components/prompt-box"
import AgentLogs from "@/components/agent-logs"
import Footer from "@/components/footer"

/* ------------------ Types ------------------ */

type Message = {
  id: string
  type: "user" | "assistant"
  content: string
  sources?: string[]
}

type WSEvent = {
  type: "event"
  payload?: {
    text?: string
    is_final?: boolean
    _done?: boolean
    error?: string
  }
}

const stripMarkdown = (md: string) => {
  // Remove headers, bold, italics, code blocks, links, images, etc.
  return md
    .replace(/(!?\[.*?\]\(.*?\))/g, "") // links/images
    .replace(/([*_]{1,3})(\S.*?\S)\1/g, "$2") // bold/italic
    .replace(/```[\s\S]*?```/g, "") // code blocks
    .replace(/`([^`]*)`/g, "$1") // inline code
    .replace(/#+\s/g, "") // headers
    .replace(/>\s?/g, "") // blockquotes
    .replace(/[-*]\s/g, "") // list bullets
    .trim()
}


/* ------------------ Component ------------------ */

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showAgentLogs, setShowAgentLogs] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const assistantMsgIdRef = useRef<string | null>(null)

  /* ------------------ WebSocket lifecycle ------------------ */
  const getLastAssistantMessage = () => {
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].type === "assistant" && messages[i].content.trim()) {
      return messages[i].content
    }
  }
  return null
}

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8001/ws/master")
    wsRef.current = ws

    ws.onopen = () => {
      console.log("[WS] connected")
    }

    ws.onmessage = (event) => {
      let data: WSEvent
      try {
        data = JSON.parse(event.data)
      } catch {
        return
      }

      if (data.type !== "event" || !data.payload) return

      const { text, is_final, _done, error } = data.payload

      // Capture assistant ID safely
      const assistantId = assistantMsgIdRef.current

      if (text && assistantId) {
        // Append raw text for streaming
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: m.content + text }
              : m
          )
        )
      }

      // When final text arrives we may trim whitespace (do not strip markdown)
      if ((is_final || _done) && assistantId) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: m.content.trim() } : m
          )
        )
      }



      // Errors from backend
      if (error) {
        console.error("[Agent error]", error)
        setIsLoading(false)
      }

      // Final marker (DO NOT clear ID immediately)
      if (is_final || _done) {
        setIsLoading(false)

        // Let React flush state first
        setTimeout(() => {
          assistantMsgIdRef.current = null
        }, 0)
      }
    }

    ws.onerror = (err) => {
      console.error("[WS] error", err)
      setIsLoading(false)
    }

    ws.onclose = () => {
      console.log("[WS] closed")
    }

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [])

  /* ------------------ Send message ------------------ */

  const handleSendMessage = (text: string) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return

    const userMsg: Message = {
      id: crypto.randomUUID(),
      type: "user",
      content: text,
    }

    const assistantId = crypto.randomUUID()
    assistantMsgIdRef.current = assistantId

    const assistantMsg: Message = {
      id: assistantId,
      type: "assistant",
      content: "",
    }

    setMessages((prev) => [...prev, userMsg, assistantMsg])
    setIsLoading(true)

    ws.send(
      JSON.stringify({
        type: "user_message",
        content: text,
      })
    )
  }

  /* ------------------ UI (UNCHANGED) ------------------ */

  return (
    <div className="flex flex-col h-screen bg-background">
      <Header
        onToggleLogs={() => setShowAgentLogs(!showAgentLogs)}
        showLogs={showAgentLogs}
      />

      <div className="flex flex-1 overflow-hidden gap-4 p-4">
        <div className="flex flex-col flex-1 overflow-hidden">
          {messages.length === 0 ? (
            <HeroSection
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
            />
          ) : (
            <>
              <ConversationArea
                messages={messages}
                isLoading={isLoading}
              />
              <div className="border-t border-border" />
            </>
          )}
          <PromptBox
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
          />
        </div>

        {showAgentLogs && <AgentLogs />}
      </div>

      <Footer getReportContent={getLastAssistantMessage} />

    </div>
  )
}
