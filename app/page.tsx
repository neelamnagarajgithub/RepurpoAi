"use client"

import { useEffect, useRef, useState } from "react"
import Header from "@/components/header"
import ConversationArea from "@/components/conversation-area"
import HeroSection from "@/components/hero-section"
import PromptBox from "@/components/prompt-box"
import AgentLogs from "@/components/agent-logs"
import Footer from "@/components/footer"
import React from "react"

/* ------------------ Types ------------------ */

type Message = {
  id: string
  type: "user" | "assistant"
  content: string
  sources?: string[]
}

type WSEventPayload = {
  text?: string
  is_final?: boolean
  _done?: boolean
  error?: string
}

type WSEvent = {
  type: string
  conversation_id?: string
  payload?: WSEventPayload
}

/* ------------------ Helpers ------------------ */

const stripMarkdown = (md: string) => {
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
  const messagesRef = useRef<Message[]>(messages)
  const [isLoading, setIsLoading] = useState(false)
  const [showAgentLogs, setShowAgentLogs] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const assistantMsgIdRef = useRef<string | null>(null)

  // Keep messagesRef in sync for async closures
  useEffect(() => {
    messagesRef.current = messages
  }, [messages])

  /* ------------------ WebSocket lifecycle ------------------ */
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
      } catch (e) {
        console.warn("Invalid WS JSON", e)
        return
      }

      // If server created a conversation and notifies us, store it
      if (data?.type === "conversation_created" && data.conversation_id) {
        setConversationId(String(data.conversation_id))
        return
      }

      // streaming event payloads
      if (data.type !== "event" || !data.payload) {
        return
      }

      const { text, is_final, _done, error } = data.payload
      const assistantId = assistantMsgIdRef.current

      // Append streaming text to the assistant message in UI
      if (text && assistantId) {
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, content: m.content + text } : m)),
        )
      }

      // When assistant finalizes its response, persist it to backend
      if ((is_final || _done) && assistantId) {
        // Trim final assistant message content in state
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, content: m.content.trim() } : m)),
        )

        // Persist assistant final message (non-blocking)
        ;(async () => {
          try {
            const token = localStorage.getItem("access_token")
            // read the latest assistant content from the ref (safe in async)
            const assistantMsg = messagesRef.current.find((m) => m.id === assistantId)
            const assistantContent = assistantMsg?.content ?? ""

            const res = await fetch("http://localhost:8001/api/messages", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
              },
              body: JSON.stringify({
                conversation_id: conversationId,
                role: "assistant",
                content: assistantContent,
                meta: null,
              }),
            })

            if (res.ok) {
              const json = await res.json().catch(() => ({}))
              // backend may return conversation_id (if created server-side)
              if (json?.conversation_id) {
                setConversationId(String(json.conversation_id))
              }
            } else {
              console.warn("Failed to persist assistant message", res.status)
            }
          } catch (err) {
            console.warn("Failed to store assistant message on backend", err)
          }
        })()
      }

      if (error) {
        console.error("[Agent error]", error)
        setIsLoading(false)
      }

      if (is_final || _done) {
        setIsLoading(false)
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
      try {
        ws.close()
      } catch {
        // ignore
      }
      wsRef.current = null
    }
    // Intentionally don't re-create ws on conversationId changes; keep stable connection.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* ------------------ Send message ------------------ */

  async function handleSendMessage(text: string) {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      alert("Realtime connection is not open. Try reloading the page.")
      return
    }

    // Create user + assistant placeholders in UI immediately
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

    // Persist user message so backend can create conversation (if needed).
    // We POST and capture conversation_id returned by backend, if any.
    ;(async () => {
      try {
        const token = localStorage.getItem("access_token")
        const res = await fetch("http://localhost:8001/api/messages", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            conversation_id: conversationId,
            role: "user",
            content: text,
            meta: null,
          }),
        })

        if (res.ok) {
          const json = await res.json().catch(() => ({}))
          if (json?.conversation_id) {
            setConversationId(String(json.conversation_id))
          }
        } else {
          console.warn("Failed to store user message", res.status)
        }
      } catch (err) {
        console.warn("Failed to store user message", err)
      }
    })()

    // Send the user message to the WS for real-time agent processing.
    // Include conversation_id if we have one (backend will create if missing).
    try {
      ws.send(
        JSON.stringify({
          type: "user_message",
          content: text,
          conversation_id: conversationId ?? undefined,
        }),
      )
    } catch (err) {
      console.warn("Failed to send WS message", err)
      setIsLoading(false)
    }
  }

  function getLastAssistantMessage(): string | null {
    const lastAssistantMsg = [...messages].reverse().find((m) => m.type === "assistant")
    return lastAssistantMsg?.content ?? null
  }

  /* ------------------ UI ------------------ */

  return (
    <div className="flex flex-col h-screen bg-background">
      <Header onToggleLogs={() => setShowAgentLogs(!showAgentLogs)} showLogs={showAgentLogs} />

      <div className="flex flex-1 overflow-hidden gap-4 p-4">
        <div className="flex flex-col flex-1 overflow-hidden">
          {messages.length === 0 ? (
            <HeroSection onSendMessage={handleSendMessage} isLoading={isLoading} />
          ) : (
            <>
              <ConversationArea messages={messages} isLoading={isLoading} />
              <div className="border-t border-border" />
            </>
          )}

          <PromptBox onSendMessage={handleSendMessage} isLoading={isLoading} />
        </div>

        {showAgentLogs && <AgentLogs />}
      </div>

      <Footer getReportContent={getLastAssistantMessage} />
    </div>
  )
}