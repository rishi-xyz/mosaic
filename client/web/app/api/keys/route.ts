import { NextResponse } from "next/server"
import { auth } from "@/lib/auth"
import { prisma } from "@/lib/prisma"
import bcrypt from "bcryptjs"
import crypto from "crypto"

function generateApiKey(): { fullKey: string; hash: string; prefix: string } {
  const random = crypto.randomBytes(24).toString("hex")
  const fullKey = `mosaic_${random}`
  const hash = bcrypt.hashSync(fullKey, 10)
  const prefix = fullKey.slice(0, 12)
  return { fullKey, hash, prefix }
}

export async function GET() {
  const session = await auth()
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const keys = await prisma.apiKey.findMany({
    where: { userId: session.user.id },
    select: {
      id: true,
      name: true,
      keyPrefix: true,
      isActive: true,
      lastUsedAt: true,
      createdAt: true,
    },
    orderBy: { createdAt: "desc" },
  })

  return NextResponse.json({ keys })
}

export async function POST(req: Request) {
  const session = await auth()
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { name } = await req.json()
  if (!name) {
    return NextResponse.json({ error: "Name is required" }, { status: 400 })
  }

  const { fullKey, hash, prefix } = generateApiKey()

  await prisma.apiKey.create({
    data: {
      userId: session.user.id,
      keyHash: hash,
      keyPrefix: prefix,
      name,
    },
  })

  return NextResponse.json({ key: fullKey, prefix }, { status: 201 })
}
