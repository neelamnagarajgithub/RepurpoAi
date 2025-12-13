"use client"

import type React from "react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { ArrowUp, Paperclip } from "lucide-react"

interface PromptBoxProps {
  onSendMessage: (message: string) => void
  isLoading: boolean
}

export default function PromptBox({ onSendMessage, isLoading }: PromptBoxProps) {
  const [input, setInput] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim())
      setInput("")
    }
  }
  return (
    <form onSubmit={handleSubmit} className="px-2 pb-0 mt-10 flex flex-col gap-3">
      <div className="relative">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about innovation opportunities for molecule X... (market, patents, trials, trade)"
          disabled={isLoading}
          className="w-full min-h-[120px] max-h-[240px] p-4 pr-12 bg-card border border-border rounded-xl text-foreground placeholder:text-foreground/50 focus:outline-none focus:ring-2 focus:ring-pharma-teal focus:border-transparent resize-none shadow-sm"
        />
        <div className="absolute bottom-6 right-4 flex gap-2">
          <button
            type="button"
            className="p-2 hover:bg-muted rounded-lg transition-colors text-foreground/60 hover:text-foreground"
          >
            <Paperclip className="w-4 h-4" />
          </button>
          <Button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="p-2 h-auto bg-pharma-teal hover:bg-pharma-teal/90 text-white rounded-lg shadow-sm"
          >
            <ArrowUp className=" w-4 h-4" />
          </Button>
        </div>
      </div>
      
    </form>
  )
}
