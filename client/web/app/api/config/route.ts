import { NextResponse } from "next/server"
import { auth } from "@/lib/auth"
import { prisma } from "@/lib/prisma"

export async function GET() {
  const session = await auth()
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const config = await prisma.userConfig.findUnique({
    where: { userId: session.user.id },
  })

  return NextResponse.json({ config: config?.config ?? {} })
}

export async function PUT(req: Request) {
  const session = await auth()
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const body = await req.json()
  const config = body.config

  if (!config || typeof config !== "object") {
    return NextResponse.json({ error: "Config must be a JSON object" }, { status: 400 })
  }

  const result = await prisma.userConfig.upsert({
    where: { userId: session.user.id },
    update: { config },
    create: {
      userId: session.user.id,
      config,
    },
  })

  return NextResponse.json({ config: result.config })
}
