"use client"

import { useState, useEffect, useCallback } from "react"
import { Copy, Trash2, Plus, Eye, EyeOff } from "lucide-react"

interface ApiKey {
  id: string
  name: string
  keyPrefix: string
  isActive: boolean
  lastUsedAt: string | null
  createdAt: string
}

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [newKeyName, setNewKeyName] = useState("")
  const [newKeyValue, setNewKeyValue] = useState<string | null>(null)
  const [showKey, setShowKey] = useState(false)

  const fetchKeys = useCallback(async () => {
    const res = await fetch("/api/keys")
    if (res.ok) {
      const data = await res.json()
      setKeys(data.keys)
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    fetchKeys()
  }, [fetchKeys])

  async function createKey() {
    if (!newKeyName.trim()) return

    const res = await fetch("/api/keys", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newKeyName.trim() }),
    })

    if (res.ok) {
      const data = await res.json()
      setNewKeyValue(data.key)
      setShowKey(true)
      setNewKeyName("")
      setShowCreate(false)
      fetchKeys()
    }
  }

  async function revokeKey(id: string) {
    if (!confirm("Revoke this API key? This cannot be undone.")) return

    const res = await fetch(`/api/keys/${id}`, { method: "DELETE" })
    if (res.ok) {
      fetchKeys()
    }
  }

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">
            API Keys
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Keys used by AI coding agents to connect to your brain.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1 px-3 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90"
        >
          <Plus className="w-4 h-4" />
          New Key
        </button>
      </div>

      {showCreate && (
        <div className="border border-border rounded-lg p-4 bg-card space-y-3">
          <h2 className="font-medium text-foreground">Create API Key</h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="e.g., Claude Code, OpenCode"
              className="flex-1 px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              onKeyDown={(e) => e.key === "Enter" && createKey()}
            />
            <button
              onClick={createKey}
              className="px-3 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90"
            >
              Create
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="px-3 py-2 border border-border rounded-md text-sm text-muted-foreground hover:bg-accent"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {newKeyValue && (
        <div className="border border-border rounded-lg p-4 bg-card space-y-3">
          <h2 className="font-medium text-foreground">Key created</h2>
          <p className="text-sm text-muted-foreground">
            Copy this key now. You won&apos;t be able to see it again.
          </p>
          <div className="flex gap-2">
            <code className="flex-1 px-3 py-2 bg-muted rounded-md text-sm font-mono overflow-x-auto">
              {showKey ? newKeyValue : `${newKeyValue.slice(0, 12)}...`}
            </code>
            <button
              onClick={() => copyToClipboard(newKeyValue)}
              className="p-2 border border-border rounded-md hover:bg-accent"
              title="Copy"
            >
              <Copy className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowKey(!showKey)}
              className="p-2 border border-border rounded-md hover:bg-accent"
              title={showKey ? "Hide" : "Show"}
            >
              {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          <button
            onClick={() => { setNewKeyValue(null); setShowKey(false) }}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Done
          </button>
        </div>
      )}

      {loading ? (
        <div className="text-sm text-muted-foreground">Loading...</div>
      ) : keys.length === 0 ? (
        <div className="text-sm text-muted-foreground py-8 text-center">
          No API keys yet. Create one to connect your AI agents.
        </div>
      ) : (
        <div className="space-y-2">
          {keys.map((key) => (
            <div
              key={key.id}
              className="flex items-center justify-between border border-border rounded-lg p-3 bg-card"
            >
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm text-foreground">
                    {key.name}
                  </span>
                  {!key.isActive && (
                    <span className="text-xs bg-muted text-muted-foreground px-1.5 py-0.5 rounded">
                      Revoked
                    </span>
                  )}
                </div>
                <code className="text-xs text-muted-foreground font-mono">
                  {key.keyPrefix}...
                </code>
                <div className="text-xs text-muted-foreground">
                  Created {new Date(key.createdAt).toLocaleDateString()}
                  {key.lastUsedAt && ` · Last used ${new Date(key.lastUsedAt).toLocaleDateString()}`}
                </div>
              </div>
              {key.isActive && (
                <button
                  onClick={() => revokeKey(key.id)}
                  className="p-2 text-muted-foreground hover:text-destructive rounded-md hover:bg-destructive/10"
                  title="Revoke"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
