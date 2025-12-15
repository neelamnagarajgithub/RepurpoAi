"use client"
import { useState } from "react"

type FooterProps = {
  getReportContent: () => string | null
}

export default function Foot() {
 

  return (
    <footer className="border-t border-border bg-background px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="text-xs text-foreground/50">
          © 2025 RepurpoAI. Pharmaceutical analysis for research purposes.
        </div>

        
      </div>
    </footer>
  )
}
