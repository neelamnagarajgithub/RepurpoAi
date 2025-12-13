"use client"

import { Menu, Settings, BarChart3 } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"

interface HeaderProps {
  onToggleLogs: () => void
  showLogs: boolean
}

export default function Header({ onToggleLogs, showLogs }: HeaderProps) {
  return (
    <header className="border-b border-border bg-background sticky top-0 z-50">
      <div className="px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Sidebar toggle */}
          <Button
            variant="ghost"
            size="sm"
            className="p-2 h-auto hover:bg-muted transition-colors"
            title="Toggle sidebar"
          >
            <Menu className="w-5 h-5 text-foreground/60" />
          </Button>

          <img src="/logo.png" alt="RepurpoAi" className="w-12 h-12 rounded-lg object-cover" />
          <h1 className="text-xl font-semibold text-foreground">RepurpoAi</h1>
        </div>

        <nav className="hidden md:flex items-center gap-8">
          <Link href="/" className="text-sm text-foreground/70 hover:text-foreground transition-colors">
            Home
          </Link>
          <Link href="/history" className="text-sm text-foreground/70 hover:text-foreground transition-colors">
            History
          </Link>
          <Link href="/downloads" className="text-sm text-foreground/70 hover:text-foreground transition-colors">
            Downloads
          </Link>
          <Link href="/settings" className="text-sm text-foreground/70 hover:text-foreground transition-colors">
            Settings
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleLogs}
            className={`flex items-center gap-2 ${showLogs ? "bg-muted" : ""}`}
            title="Toggle agent logs"
          >
            <BarChart3 className="w-4 h-4" />
            <span className="hidden sm:inline text-sm">Agents</span>
          </Button>
          <Button variant="ghost" size="icon" className="w-9 h-9" title="Settings">
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </header>
  )
}
