"use client"

import { useState, useEffect, useCallback } from "react"
import { Save } from "lucide-react"

interface BrainConfig {
  llmEndpoint?: string
  llmModel?: string
  embeddingEndpoint?: string
  embeddingModel?: string
  githubToken?: string
  githubRepository?: string
  slackToken?: string
  slackChannels?: string
  neo4jUrl?: string
  neo4jUsername?: string
  neo4jPassword?: string
  [key: string]: string | undefined
}

const defaultConfig: BrainConfig = {
  llmEndpoint: "http://localhost:11434/v1",
  llmModel: "llama3.2:3b",
  embeddingEndpoint: "http://localhost:11434/v1",
  embeddingModel: "nomic-embed-text",
  githubToken: "",
  githubRepository: "",
  slackToken: "",
  slackChannels: "",
  neo4jUrl: "",
  neo4jUsername: "",
  neo4jPassword: "",
}

export default function SettingsPage() {
  const [config, setConfig] = useState<BrainConfig>(defaultConfig)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const fetchConfig = useCallback(async () => {
    const res = await fetch("/api/config")
    if (res.ok) {
      const data = await res.json()
      setConfig({ ...defaultConfig, ...data.config })
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    fetchConfig()
  }, [fetchConfig])

  async function saveConfig() {
    setSaving(true)
    setSaved(false)

    const res = await fetch("/api/config", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ config }),
    })

    if (res.ok) {
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    }
    setSaving(false)
  }

  function updateField(key: string, value: string) {
    setConfig((prev) => ({ ...prev, [key]: value }))
  }

  if (loading) {
    return <div className="text-sm text-muted-foreground">Loading...</div>
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">
          Settings
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Configure how your brain connects to LLMs and data sources.
        </p>
      </div>

      <section className="space-y-4">
        <h2 className="font-medium text-foreground border-b border-border pb-2">
          LLM Configuration
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              LLM Endpoint
            </label>
            <input
              type="text"
              value={config.llmEndpoint || ""}
              onChange={(e) => updateField("llmEndpoint", e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              LLM Model
            </label>
            <input
              type="text"
              value={config.llmModel || ""}
              onChange={(e) => updateField("llmModel", e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              Embedding Endpoint
            </label>
            <input
              type="text"
              value={config.embeddingEndpoint || ""}
              onChange={(e) => updateField("embeddingEndpoint", e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              Embedding Model
            </label>
            <input
              type="text"
              value={config.embeddingModel || ""}
              onChange={(e) => updateField("embeddingModel", e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="font-medium text-foreground border-b border-border pb-2">
          GitHub Connector
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              GitHub Token
            </label>
            <input
              type="password"
              value={config.githubToken || ""}
              onChange={(e) => updateField("githubToken", e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              Repository
            </label>
            <input
              type="text"
              value={config.githubRepository || ""}
              onChange={(e) => updateField("githubRepository", e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="owner/repo"
            />
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="font-medium text-foreground border-b border-border pb-2">
          Slack Connector
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              Slack Bot Token
            </label>
            <input
              type="password"
              value={config.slackToken || ""}
              onChange={(e) => updateField("slackToken", e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              Channels
            </label>
            <input
              type="text"
              value={config.slackChannels || ""}
              onChange={(e) => updateField("slackChannels", e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="engineering,general"
            />
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="font-medium text-foreground border-b border-border pb-2">
          Graph Database (Neo4j)
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              Neo4j URL
            </label>
            <input
              type="text"
              value={config.neo4jUrl || ""}
              onChange={(e) => updateField("neo4jUrl", e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="bolt://localhost:7687"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              Username
            </label>
            <input
              type="text"
              value={config.neo4jUsername || ""}
              onChange={(e) => updateField("neo4jUsername", e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              Password
            </label>
            <input
              type="password"
              value={config.neo4jPassword || ""}
              onChange={(e) => updateField("neo4jPassword", e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>
      </section>

      <button
        onClick={saveConfig}
        disabled={saving}
        className="flex items-center gap-1 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50"
      >
        <Save className="w-4 h-4" />
        {saving ? "Saving..." : saved ? "Saved!" : "Save settings"}
      </button>
    </div>
  )
}
