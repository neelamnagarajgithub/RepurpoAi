import { NextResponse } from "next/server"
import { createClient } from "@supabase/supabase-js"

export const runtime = "nodejs"

export async function POST(req: Request) {
  try {
    const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL
    const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY

    if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
      return NextResponse.json({ error: "Missing Supabase server config" }, { status: 500 })
    }

    // Server-side Supabase client with service role key (do NOT expose this key to clients)
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    const formData = await req.formData()
    const file = formData.get("file") as File | null
    const filename = (formData.get("filename") as string) || `report_${Date.now()}.pdf`

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 })
    }

    const arrayBuffer = await file.arrayBuffer()
    const buffer = Buffer.from(arrayBuffer)

    const filePath = `reports/${Date.now()}_${filename}`

    const { data, error } = await supabase.storage
      .from("reports")
      .upload(filePath, buffer, {
        contentType: "application/pdf",
        upsert: false,
      })

    if (error) {
      console.error("Supabase upload error:", error)
      return NextResponse.json({ error: error.message }, { status: 500 })
    }

    // Because your bucket is public, getPublicUrl should return a usable URL
    const { data: urlData } = supabase.storage.from("reports").getPublicUrl(filePath)
    const publicUrl = urlData?.publicUrl ?? null

    return NextResponse.json({ url: publicUrl, path: filePath, data })
  } catch (err: any) {
    console.error("[upload-report] error:", err)
    return NextResponse.json({ error: "Upload failed" }, { status: 500 })
  }
}