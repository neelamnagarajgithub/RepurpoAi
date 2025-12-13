"use client"

import { useState } from "react"
import { ChevronDown, ChevronRight, Zap, BookOpen, Beaker, Globe, Cloud, Database } from "lucide-react"

const agents = [
  {
    name: "Market Agent",
    icon: Globe,
    color: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800",
    status: "completed",
  },
  {
    name: "Patent Agent",
    icon: BookOpen,
    color: "bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-900/20 dark:text-teal-400 dark:border-teal-800",
    status: "completed",
  },
  {
    name: "Trials Agent",
    icon: Beaker,
    color: "bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800",
    status: "completed",
  },
  {
    name: "EXIM Agent",
    icon: Cloud,
    color: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-800",
    status: "completed",
  },
  {
    name: "Web Intelligence Agent",
    icon: Zap,
    color:
      "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-900/20 dark:text-purple-400 dark:border-purple-800",
    status: "running",
  },
  {
    name: "Internal RAG Agent",
    icon: Database,
    color:
      "bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-900/20 dark:text-orange-400 dark:border-orange-800",
    status: "pending",
  },
]

export default function AgentLogs() {
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null)

  return (
    <div className="w-80 bg-card border-l border-border flex flex-col overflow-hidden shadow-lg">
      <div className="px-4 py-3 border-b border-border">
        <h3 className="font-semibold text-sm text-foreground">Agent Logs</h3>
        <p className="text-xs text-foreground/50 mt-1">Real-time analysis pipeline</p>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        {agents.map((agent) => {
          const Icon = agent.icon
          return (
            <div key={agent.name} className="space-y-1">
              <button
                onClick={() => setExpandedAgent(expandedAgent === agent.name ? null : agent.name)}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg border ${agent.color} text-xs font-medium transition-colors hover:opacity-80`}
              >
                {expandedAgent === agent.name ? (
                  <ChevronDown className="w-3 h-3 flex-shrink-0" />
                ) : (
                  <ChevronRight className="w-3 h-3 flex-shrink-0" />
                )}
                <Icon className="w-3 h-3 flex-shrink-0" />
                <span>{agent.name}</span>
                <span className="ml-auto text-xs opacity-70">
                  {agent.status === "completed" && "✓"}
                  {agent.status === "running" && "⟳"}
                  {agent.status === "pending" && "○"}
                </span>
              </button>

              {expandedAgent === agent.name && (
                <div className="ml-6 px-3 py-2 text-xs text-foreground/60 bg-muted/30 rounded border border-border/50 space-y-1">
                  <p>• Querying pharmaceutical databases</p>
                  <p>• Analyzing patent landscapes</p>
                  <p>• Processing clinical trial data</p>
                  <p className="text-foreground/40">Timestamp: {new Date().toLocaleTimeString()}</p>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
