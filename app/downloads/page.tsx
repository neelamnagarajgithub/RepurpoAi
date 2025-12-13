"use client"

import { useState } from "react"
import { Download, FileText, File, Trash2, Search } from "lucide-react"
import Header from "@/components/header"
import Footer from "@/components/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

interface DownloadItem {
  id: string
  name: string
  type: "PDF" | "Excel"
  size: string
  timestamp: Date
  queryRelated: string
}

export default function DownloadsPage() {
  const [showAgentLogs, setShowAgentLogs] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")

  // Mock downloads data
  const [downloads] = useState<DownloadItem[]>([
    {
      id: "1",
      name: "Aspirin_Market_Analysis_Report.pdf",
      type: "PDF",
      size: "2.4 MB",
      timestamp: new Date("2025-01-15T10:35:00"),
      queryRelated: "Identify innovation opportunities for Aspirin",
    },
    {
      id: "2",
      name: "Metformin_Clinical_Trials_Data.xlsx",
      type: "Excel",
      size: "1.8 MB",
      timestamp: new Date("2025-01-14T15:50:00"),
      queryRelated: "Analyze Metformin repurposing potential",
    },
    {
      id: "3",
      name: "GLP1_Patent_Landscape.pdf",
      type: "PDF",
      size: "3.1 MB",
      timestamp: new Date("2025-01-13T09:25:00"),
      queryRelated: "Patent landscape for GLP-1 agonists",
    },
  ])

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
                        <Button size="sm" className="bg-pharma-teal hover:bg-pharma-teal/90">
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

      <Footer />
    </div>
  )
}
