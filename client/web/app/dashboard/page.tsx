import { auth } from "@/lib/auth"
import { prisma } from "@/lib/prisma"
import { Key, Settings } from "lucide-react"
import Link from "next/link"

export default async function DashboardPage() {
  const session = await auth()
  if (!session?.user) return null

  const apiKeyCount = await prisma.apiKey.count({
    where: { userId: session.user.id, isActive: true },
  })

  const config = await prisma.userConfig.findUnique({
    where: { userId: session.user.id },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">
          Welcome{session.user.name ? `, ${session.user.name}` : ""}
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Your engineering brain is ready.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="border border-border rounded-lg p-4 bg-card">
          <div className="flex items-center gap-2 text-foreground mb-2">
            <Key className="w-4 h-4" />
            <h2 className="font-medium">API Keys</h2>
          </div>
          <p className="text-sm text-muted-foreground mb-3">
            {apiKeyCount} active key{apiKeyCount !== 1 ? "s" : ""}
          </p>
          <Link
            href="/dashboard/api-keys"
            className="text-sm font-medium text-foreground hover:underline"
          >
            Manage keys →
          </Link>
        </div>

        <div className="border border-border rounded-lg p-4 bg-card">
          <div className="flex items-center gap-2 text-foreground mb-2">
            <Settings className="w-4 h-4" />
            <h2 className="font-medium">Configuration</h2>
          </div>
          <p className="text-sm text-muted-foreground mb-3">
            {config ? "Brain configured" : "Not yet configured"}
          </p>
          <Link
            href="/dashboard/settings"
            className="text-sm font-medium text-foreground hover:underline"
          >
            {config ? "Edit settings →" : "Configure brain →"}
          </Link>
        </div>
      </div>
    </div>
  )
}
