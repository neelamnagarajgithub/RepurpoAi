"use client"

import { useState } from "react"
import { Clock, MessageSquare, Trash2, Search } from "lucide-react"
import Header from "@/components/header"
import Footer from "@/components/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import Link from "next/link"

interface HistoryItem {
  id: string
  query: string
  timestamp: Date
  responsePreview: string
  agentsUsed: string[]
}

export default function HistoryPage() {
  const [showAgentLogs, setShowAgentLogs] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")

  // Mock history data
  const [historyItems] = useState<HistoryItem[]>([
    {
      id: "1",
      query: "Identify innovation opportunities for Aspirin across market, patents, trials, and trade",
      timestamp: new Date("2025-01-15T10:30:00"),
      responsePreview:
        "Market analysis shows $500M opportunity in cardiovascular segment. 3 key patents expiring in 2026...",
      agentsUsed: ["Market Agent", "Patent Agent", "Trials Agent", "EXIM Agent"],
    },
    {
      id: "2",
      query: "Analyze Metformin repurposing potential for oncology indications",
      timestamp: new Date("2025-01-14T15:45:00"),
      responsePreview: "12 active clinical trials investigating Metformin in breast cancer and colorectal cancer...",
      agentsUsed: ["Trials Agent", "Web Intelligence", "Internal RAG"],
    },
    {
      id: "3",
      query: "Patent landscape for GLP-1 agonists in diabetes treatment",
      timestamp: new Date("2025-01-13T09:20:00"),
      responsePreview: "45 active patents identified. Key players: Novo Nordisk, Eli Lilly. Expiration timeline...",
      agentsUsed: ["Patent Agent", "Market Agent"],
    },
  ])

  const filteredHistory = historyItems.filter((item) => item.query.toLowerCase().includes(searchQuery.toLowerCase()))

  return (
    <div className="flex flex-col h-screen bg-background">
      <Header onToggleLogs={() => setShowAgentLogs(!showAgentLogs)} showLogs={showAgentLogs} />

      <div className="flex-1 overflow-auto px-6 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header section */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <Clock className="w-6 h-6 text-pharma-teal" />
              <h1 className="text-3xl font-semibold text-foreground">Query History</h1>
            </div>
            <p className="text-muted-foreground">View and manage your past pharmaceutical intelligence queries</p>
          </div>

          {/* Search bar */}
          <div className="relative mb-6">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search your query history..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-pharma-teal/30 bg-background text-foreground"
            />
          </div>

          {/* History items */}
          <div className="space-y-4">
            {filteredHistory.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground mb-4">No query history found</p>
                  <Link href="/">
                    <Button>Start New Query</Button>
                  </Link>
                </CardContent>
              </Card>
            ) : (
              filteredHistory.map((item) => (
                <Card key={item.id} className="hover:shadow-lg transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex justify-between items-start gap-4">
                      <div className="flex-1">
                        {/* Query text */}
                        <Link href={`/?resumeQuery=${item.id}`}>
                          <h3 className="text-lg font-medium text-foreground mb-2 hover:text-pharma-teal transition-colors cursor-pointer">
                            {item.query}
                          </h3>
                        </Link>

                        {/* Response preview */}
                        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{item.responsePreview}</p>

                        {/* Metadata */}
                        <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {item.timestamp.toLocaleDateString()} at {item.timestamp.toLocaleTimeString()}
                          </span>
                          <div className="flex flex-wrap gap-1">
                            {item.agentsUsed.map((agent, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-0.5 bg-pharma-teal/10 text-pharma-teal rounded-full text-xs"
                              >
                                {agent}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* Actions */}
                      <Button variant="ghost" size="icon" className="shrink-0" title="Delete query">
                        <Trash2 className="w-4 h-4 text-destructive" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      </div>

      <Footer />
    </div>
  )
}
