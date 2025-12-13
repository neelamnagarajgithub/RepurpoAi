"use client"

import { Button } from "@/components/ui/button"
import { FileDown } from "lucide-react"
import { useState } from "react"

type FooterProps = {
  getReportContent: () => string | null
}

export default function Footer({ getReportContent }: FooterProps) {
  const [loading, setLoading] = useState(false)

  const handleGenerateReport = async () => {
    const content = getReportContent()

    if (!content) {
      alert("No analysis available to generate report.")
      return
    }

    setLoading(true)

    try {
      const res = await fetch("/api/report/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          markdown: content,
        }),
      })

      if (!res.ok) throw new Error("PDF generation failed")

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)

      const a = document.createElement("a")
      a.href = url
      a.download = "RepurpoAI_Report.pdf"
      document.body.appendChild(a)
      a.click()
      a.remove()

      URL.revokeObjectURL(url)
    } catch (err) {
      console.error(err)
      alert("Failed to generate report")
    } finally {
      setLoading(false)
    }
  }

  return (
    <footer className="border-t border-border bg-background px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="text-xs text-foreground/50">
          © 2025 RepurpoAI. Pharmaceutical analysis for research purposes.
        </div>

        <Button
          onClick={handleGenerateReport}
          disabled={loading}
          className="flex items-center gap-2 bg-pharma-teal hover:bg-pharma-teal/90 text-white shadow-lg"
          size="sm"
        >
          <FileDown className="w-4 h-4" />
          {loading ? "Generating..." : "Generate Full Report"}
        </Button>
      </div>
    </footer>
  )
}
