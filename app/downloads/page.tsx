"use client"

import { useState, useEffect } from "react"
import { Download, FileText, File, Trash2, Search } from "lucide-react"
import Header from "@/components/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import Foot from "@/components/foot"

interface DownloadItem {
  id: string
  name: string
  type: "PDF" | "Excel"
  size: string
  timestamp: Date
  queryRelated: string
  url: string
}

export default function DownloadsPage() {
  const [showAgentLogs, setShowAgentLogs] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [downloads, setDownloads] = useState<DownloadItem[]>([])

  useEffect(() => {
    let mounted = true
    ;(async () => {
      try {
        const token = localStorage.getItem("access_token")
        const res = await fetch("http://localhost:8001/api/downloads?limit=100", {
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        })
        if (!res.ok) throw new Error("Failed to fetch downloads")
        const data = await res.json()
        if (mounted) {
          // adapt backend response shape if needed
          setDownloads(
            data.map((d: any) => ({
              id: String(d.id),
              name: d.filename,
              type: d.filename?.toLowerCase().endsWith(".pdf") ? "PDF" : "Excel",
              size: d.size ?? "—",
              timestamp: d.created_at ? new Date(d.created_at) : new Date(),
              queryRelated: d.metadata?.queryRelated ?? "",
              url: d.url ?? "",
            })),
          )
        }
      } catch (err) {
        console.warn("Could not load downloads", err)
      }
    })()
    return () => {
      mounted = false
    }
  }, [])

  const filteredDownloads = downloads.filter(
    (item) =>
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.queryRelated.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  return (
    <div className="flex flex-col h-screen bg-background">
      <Header onToggleLogs={() => setShowAgentLogs(!showAgentLogs)} showLogs={showAgentLogs} />

      <div className="flex-1 overflow-auto px-6 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header section */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <Download className="w-6 h-6 text-pharma-teal" />
              <h1 className="text-3xl font-semibold text-foreground">Downloads</h1>
            </div>
            <p className="text-muted-foreground">Access your generated reports and exported data files</p>
          </div>

          {/* Search bar */}
          <div className="relative mb-6">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search downloads..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-pharma-teal/30 bg-background text-foreground"
            />
          </div>

          {/* Downloads list */}
          <div className="space-y-3">
            {filteredDownloads.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <Download className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground mb-4">No downloads available</p>
                  <p className="text-sm text-muted-foreground">Generate reports from your queries to see them here</p>
                </CardContent>
              </Card>
            ) : (
              filteredDownloads.map((item) => (
                <Card key={item.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-5">
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        {/* File icon */}
                        <div className="shrink-0 w-10 h-10 rounded-lg bg-pharma-teal/10 flex items-center justify-center">
                          {item.type === "PDF" ? (
                            <FileText className="w-5 h-5 text-pharma-teal" />
                          ) : (
                            <File className="w-5 h-5 text-pharma-teal" />
                          )}
                        </div>

                        {/* File info */}
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-foreground truncate mb-1">{item.name}</h3>
                          <div className="flex items-center gap-3 text-xs text-muted-foreground">
                            <span className="px-2 py-0.5 bg-muted rounded text-xs">{item.type}</span>
                            <span>{item.size}</span>
                            <span>
                              {item.timestamp.toLocaleDateString()} at {item.timestamp.toLocaleTimeString()}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1 truncate">Related: {item.queryRelated}</p>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2 shrink-0">
                        <Button
                          size="sm"
                          className="bg-pharma-teal hover:bg-pharma-teal/90"
                          onClick={() => {
                            if (item.url && item.url.trim() !== "") {
                              // open in new tab/window
                              window.open(item.url, "_blank", "noopener,noreferrer")
                            } else {
                              alert("No download URL available for this file.")
                            }
                          }}
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Download
                        </Button>
                        <Button variant="ghost" size="icon" title="Delete file">
                          <Trash2 className="w-4 h-4 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      </div>

      <Foot />
    </div>
  )
}
