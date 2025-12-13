"use client"

import { useState } from "react"
import { SettingsIcon, User, Bell, Database, Shield, Palette } from "lucide-react"
import Header from "@/components/header"
import Footer from "@/components/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function SettingsPage() {
  const [showAgentLogs, setShowAgentLogs] = useState(false)
  const [settings, setSettings] = useState({
    notifications: true,
    autoSave: true,
    darkMode: false,
    dataRetention: "90",
    defaultAgents: ["Market Agent", "Patent Agent", "Trials Agent", "EXIM Agent"],
  })

  return (
    <div className="flex flex-col h-screen bg-background">
      <Header onToggleLogs={() => setShowAgentLogs(!showAgentLogs)} showLogs={showAgentLogs} />

      <div className="flex-1 overflow-auto px-6 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header section */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <SettingsIcon className="w-6 h-6 text-pharma-teal" />
              <h1 className="text-3xl font-semibold text-foreground">Settings</h1>
            </div>
            <p className="text-muted-foreground">Manage your pharmaceutical intelligence assistant preferences</p>
          </div>

          {/* Settings sections */}
          <div className="space-y-6">
            {/* Profile Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="w-5 h-5 text-pharma-teal" />
                  Profile Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Full Name</label>
                  <input
                    type="text"
                    defaultValue="Dr. Sarah Johnson"
                    className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-pharma-teal/30 bg-background text-foreground"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Email</label>
                  <input
                    type="email"
                    defaultValue="sarah.johnson@pharma.com"
                    className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-pharma-teal/30 bg-background text-foreground"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Organization</label>
                  <input
                    type="text"
                    defaultValue="PharmaCorp Research"
                    className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-pharma-teal/30 bg-background text-foreground"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Notification Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="w-5 h-5 text-pharma-teal" />
                  Notifications
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-foreground">Email Notifications</p>
                    <p className="text-sm text-muted-foreground">Receive updates about completed analyses</p>
                  </div>
                  <button
                    onClick={() => setSettings({ ...settings, notifications: !settings.notifications })}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      settings.notifications ? "bg-pharma-teal" : "bg-muted"
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        settings.notifications ? "translate-x-6" : "translate-x-1"
                      }`}
                    />
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-foreground">Auto-save Queries</p>
                    <p className="text-sm text-muted-foreground">Automatically save queries to history</p>
                  </div>
                  <button
                    onClick={() => setSettings({ ...settings, autoSave: !settings.autoSave })}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      settings.autoSave ? "bg-pharma-teal" : "bg-muted"
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        settings.autoSave ? "translate-x-6" : "translate-x-1"
                      }`}
                    />
                  </button>
                </div>
              </CardContent>
            </Card>

            {/* Agent Configuration */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="w-5 h-5 text-pharma-teal" />
                  Agent Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Default Active Agents</label>
                  <p className="text-sm text-muted-foreground mb-3">
                    Select which agents should be enabled by default for new queries
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      "Market Agent",
                      "Patent Agent",
                      "Trials Agent",
                      "EXIM Agent",
                      "Web Intelligence",
                      "Internal RAG",
                    ].map((agent) => (
                      <label key={agent} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          defaultChecked={settings.defaultAgents.includes(agent)}
                          className="w-4 h-4 rounded border-border text-pharma-teal focus:ring-pharma-teal"
                        />
                        <span className="text-sm text-foreground">{agent}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Data & Privacy */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-pharma-teal" />
                  Data & Privacy
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Data Retention Period</label>
                  <select
                    value={settings.dataRetention}
                    onChange={(e) => setSettings({ ...settings, dataRetention: e.target.value })}
                    className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-pharma-teal/30 bg-background text-foreground"
                  >
                    <option value="30">30 days</option>
                    <option value="90">90 days</option>
                    <option value="180">180 days</option>
                    <option value="365">1 year</option>
                  </select>
                </div>
                <div className="pt-4 border-t border-border">
                  <Button
                    variant="outline"
                    className="text-destructive border-destructive hover:bg-destructive/10 bg-transparent"
                  >
                    Delete All Query History
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Appearance */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Palette className="w-5 h-5 text-pharma-teal" />
                  Appearance
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-foreground">Dark Mode</p>
                    <p className="text-sm text-muted-foreground">Switch to dark theme</p>
                  </div>
                  <button
                    onClick={() => setSettings({ ...settings, darkMode: !settings.darkMode })}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      settings.darkMode ? "bg-pharma-teal" : "bg-muted"
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        settings.darkMode ? "translate-x-6" : "translate-x-1"
                      }`}
                    />
                  </button>
                </div>
              </CardContent>
            </Card>

            {/* Save button */}
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="outline">Cancel</Button>
              <Button className="bg-pharma-teal hover:bg-pharma-teal/90">Save Changes</Button>
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  )
}
