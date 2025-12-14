
import { NextResponse } from "next/server"
import puppeteer from "puppeteer"
import { marked } from "marked"

/* ------------------ HTML Builder ------------------ */


function buildHTMLFromMarkdown(md: string) {
  const contentHTML = marked.parse(md)

  return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>RepurpoAI Report</title>
  <style>
    body {
      font-family: Inter, Arial, sans-serif;
      color: #111;
      margin: 0;
      padding: 0;
    }
    header {
      padding: 32px 40px;
      border-bottom: 3px solid #0b3c5d;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 12px;
      text-align: center;
    }
    header img {
      width: 72px;
      height: 72px;
      display: block;
    }
    .brand {
      font-size: 22px;
      font-weight: 700;
      color: #0b3c5d;
      margin: 0;
    }
    .subtitle {
      font-size: 14px;
      color: #555;
      margin: 0;
      line-height: 1.35;
    }
    main {
      padding: 40px;
      line-height: 1.6;
      font-size: 14px;
    }
    h1, h2, h3 {
      color: #0b3c5d;
      margin-top: 28px;
    }
    h2 {
      border-left: 4px solid #328cc1;
      padding-left: 10px;
    }
    ul {
      padding-left: 20px;
    }
    footer {
      border-top: 1px solid #ddd;
      padding: 14px;
      text-align: center;
      font-size: 11px;
      color: #666;
    }
  </style>
</head>

<body>
  <header>
    <!-- Use public asset path (will resolve from /public/icon.png) -->
    <img src="http://localhost:3000/icon.png" alt="RepurpoAI logo" />
    <div>
      <div class="brand">RepurpoAI</div>
      <div class="subtitle">
        Drug Repurposing Intelligence Report,Multi-Agent Scientific &amp; Market Analysis
      </div>
    </div>
  </header>

  <main>
    ${contentHTML}
  </main>

  <footer>
    © RepurpoAI – Confidential | Generated ${new Date().toLocaleDateString()}
  </footer>
</body>
</html>
`
}

/* ------------------ API Route ------------------ */

export async function POST(req: Request) {
  try {
    const { markdown } = await req.json()

    if (!markdown || typeof markdown !== "string") {
      return NextResponse.json(
        { error: "Invalid markdown input" },
        { status: 400 }
      )
    }

    const browser = await puppeteer.launch({
      headless: true,
      args: ["--no-sandbox", "--disable-setuid-sandbox"], // IMPORTANT for prod
    })

    const page = await browser.newPage()

    await page.setContent(buildHTMLFromMarkdown(markdown), {
      waitUntil: "networkidle0",
    })

    const pdfBuffer = await page.pdf({
      format: "A4",
      printBackground: true,
      margin: {
        top: "20mm",
        bottom: "20mm",
        left: "15mm",
        right: "15mm",
      },
    })

    await browser.close()

    return new NextResponse(pdfBuffer, {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition":
          'attachment; filename="RepurpoAI_Report.pdf"',
      },
    })
  } catch (err) {
    console.error("[PDF ERROR]", err)
    return NextResponse.json(
      { error: "PDF generation failed" },
      { status: 500 }
    )
  }
}
