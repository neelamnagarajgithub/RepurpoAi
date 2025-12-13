"use client"

import { Button } from "@/components/ui/button"
import { FileDown } from "lucide-react"
import { useState } from "react"

export default function Footer() {
  const [showToast, setShowToast] = useState(false)

  const handleGenerateReport = () => {
    setShowToast(true)
    setTimeout(() => setShowToast(false), 3000)
  }

  return (
    <footer className="border-t border-border bg-background px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="text-xs text-foreground/50">
          © 2025 RepurpoAi. Pharmaceutical analysis for research purposes.
        </div>
        <div className="relative">
          <Button
            onClick={handleGenerateReport}
            className="flex items-center gap-2 bg-pharma-teal hover:bg-pharma-teal/90 text-white shadow-lg hover:shadow-xl transition-all font-medium"
            size="sm"
          >
            <FileDown className="w-4 h-4" />
            Generate Full Report
          </Button>
          {showToast && (
            <div className="absolute bottom-full right-0 mb-2 px-3 py-2 bg-foreground text-background text-xs rounded-lg whitespace-nowrap shadow-lg">
              Report generation started...
            </div>
          )}
        </div>
      </div>
    </footer>
  )
}
