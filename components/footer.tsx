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
      // generate PDF via existing local route
      const res = await fetch("/api/report/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          markdown: content,
        }),
      })

      if (!res.ok) throw new Error("PDF generation failed")

      const blob = await res.blob()
      const filename = `RepurpoAI_Report_${Date.now()}.pdf`

      // Upload to server endpoint which will upload to Supabase using service role key
      let uploadedUrl: string | null = null
      try {
        const formData = new FormData()
        formData.append("file", new File([blob], filename, { type: "application/pdf" }))
        formData.append("filename", filename)

        const upRes = await fetch("/api/upload-report", {
          method: "POST",
          body: formData,
        })

        if (upRes.ok) {
          const upJson = await upRes.json()
          uploadedUrl = upJson?.url ?? null
        } else {
          console.warn("Upload endpoint returned non-OK", upRes.status)
          const txt = await upRes.text().catch(() => "")
          console.warn("upload response:", txt)
        }
      } catch (upErr) {
        console.warn("Upload to /api/upload-report failed:", upErr)
      }

      // Trigger client download (always do this regardless of upload result)
      try {
        const url = URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)
      } catch (dlErr) {
        console.warn("Client download failed:", dlErr)
      }

      // Register download with backend (send the URL if available)
      try {
        const token = localStorage.getItem("access_token")
        await fetch("http://localhost:8001/api/downloads", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            filename,
            url: uploadedUrl ?? "", // backend may require a URL; send empty string if not available
            meta: { uploadedTo: uploadedUrl ? "supabase" : "local" },
          }),
        })
      } catch (regErr) {
        console.warn("Failed to register download with backend", regErr)
      }
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
