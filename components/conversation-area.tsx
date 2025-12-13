"use client"

import React from "react"
import ReactMarkdown from "react-markdown"
import { Card } from "@/components/ui/card"
import { Loader2, Zap } from "lucide-react"

interface Message {
  id: string
  type: "user" | "assistant"
  content: string
  sources?: string[]
}

interface ConversationAreaProps {
  messages: Message[]
  isLoading: boolean
}

export default function ConversationArea({ messages, isLoading }: ConversationAreaProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const agents = ["Market", "Patents", "Trials", "EXIM", "Web", "Internal"]

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex items-start ${message.type === "user" ? "justify-end" : "justify-start"}`}
        >
          {/* Assistant avatar on the left */}
          {message.type === "assistant" && (
            <img
              src="/repurpo.ico"
              alt="Repurpo AI"
              className="w-10 h-10 rounded-full mr-4 flex-shrink-0 object-cover"
            />
          )}

          <div
            className={`max-w-2xl rounded-xl px-5 py-4 ${
              message.type === "user"
                ? "bg-pharma-teal/5 border border-pharma-teal/20 rounded-br-none shadow-sm"
                : "bg-card border border-border rounded-bl-none shadow-md"
            }`}
          >
            {message.type === "assistant" && (
              <div className="flex items-center gap-2 mb-3 pb-3 border-b border-border/50">
                <Zap className="w-4 h-4 text-pharma-teal" />
                <span className="text-xs font-semibold text-foreground/70">Master Agent Summary</span>
              </div>
            )}

            {message.type === "assistant" ? (
              <div className="text-sm text-foreground prose prose-sm max-w-none">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            ) : (
              <p className="text-sm whitespace-pre-wrap text-foreground">{message.content}</p>
            )}

            {message.type === "assistant" && message.sources && (
              <div className="mt-4 pt-3 border-t border-border/50 flex items-center gap-2">
                <span className="text-xs font-medium text-foreground/60">Sources Queried:</span>
                <div className="flex flex-wrap gap-2">
                  {message.sources.map((source) => (
                    <span key={source} className="text-xs px-2 py-1 bg-pharma-teal/10 text-pharma-teal rounded-full">
                      {source}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* User avatar on the right */}
          {message.type === "user" && (
            <img
              src="/placeholder-user.jpg"
              alt="You"
              className="w-10 h-10 rounded-full ml-4 flex-shrink-0 object-cover"
            />
          )}
        </div>
      ))}

      {isLoading && (
        <div className="flex justify-start">
          <Card className="p-4 bg-card border border-border shadow-md">
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-pharma-teal" />
                <span className="text-sm font-medium text-foreground">Analyzing with multi-agent intelligence...</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {agents.map((agent) => (
                  <div
                    key={agent}
                    className="flex items-center gap-1 px-2.5 py-1.5 bg-muted rounded-md text-xs text-foreground/70 border border-border/50"
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-pharma-teal animate-pulse" />
                    {agent}
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}
