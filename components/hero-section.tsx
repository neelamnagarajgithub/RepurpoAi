"use client"

import { Button } from "@/components/ui/button"
import { Beaker, Globe, BookOpen, Microscope, TrendingUp, PackageSearch } from "lucide-react"

interface HeroSectionProps {
  onSendMessage: (message: string) => void
  isLoading: boolean
}

export default function HeroSection({ onSendMessage, isLoading }: HeroSectionProps) {
  const quickPrompts = [
    {
      icon: Microscope,
      label: "Find new indications",
      query: "Identify new therapeutic indications for molecule X across market, patents, and clinical data",
    },
    {
      icon: BookOpen,
      label: "Check patent landscape",
      query: "Analyze the patent landscape for compound X, including expiration dates and competitive threats",
    },
    {
      icon: Beaker,
      label: "View clinical trials",
      query: "What are the active clinical trials related to molecule X and its developmental stage?",
    },
    {
      icon: Globe,
      label: "Check market opportunities",
      query: "Assess market opportunities and competitive positioning for molecule X in target indications",
    },
    {
      icon: TrendingUp,
      label: "Explore repurposing cases",
      query: "Find recent examples of successful drug repurposing similar to molecule X",
    },
    {
      icon: PackageSearch,
      label: "Trade & supply analysis",
      query: "Analyze import/export trends and supply chain data for molecule X",
    },
  ]

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 py-12 overflow-y-auto">
      <div className="max-w-2xl text-center">
        <h1 className="text-4xl font-bold text-foreground mb-3">
          Discover new indications, market opportunities, patents, and clinical insights for any molecule—instantly.
        </h1>
        <p className="text-lg text-foreground/60 mb-8">Powered by multi-agent pharmaceutical intelligence.</p>

        {/* Quick prompt buttons */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-12">
          {quickPrompts.map((prompt) => {
            const Icon = prompt.icon
            return (
              <Button
                key={prompt.label}
                onClick={() => onSendMessage(prompt.query)}
                disabled={isLoading}
                variant="outline"
                className="justify-start h-auto py-3 px-4 border-border hover:border-pharma-teal hover:bg-pharma-teal/5 transition-all"
              >
                <Icon className="w-5 h-5 text-pharma-teal mr-3 flex-shrink-0" />
                <span className="text-sm font-medium">{prompt.label}</span>
              </Button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
