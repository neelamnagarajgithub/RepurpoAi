import fs from "fs";
import path from "path";
import puppeteer from "puppeteer";
import { marked } from "marked";

function buildHTMLFromMarkdown(md:any) {
  const contentHTML = marked.parse(md);

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
      align-items: center;
      gap: 16px;
    }
    header img {
      width: 60px;
      height: 60px;
    }
    .brand {
      font-size: 22px;
      font-weight: 700;
      color: #0b3c5d;
    }
    .subtitle {
      font-size: 14px;
      color: #555;
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
    <img src="repurpoai_logo.png" />
    <div>
      <div class="brand">RepurpoAI</div>
      <div class="subtitle">
        Drug Repurposing Intelligence Report<br/>
        Multi-Agent Scientific & Market Analysis
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
`;
}


/**
 * Generate RepurpoAI PDF from agent markdown response
 * @param {string} mdResponse - Raw markdown from agent
 * @returns {Promise<string>} - Path to generated PDF
 */
export async function generateRepurpoAIPDF(mdResponse:any) {
  const htmlContent = buildHTMLFromMarkdown(mdResponse);

  const outputDir = path.join(process.cwd(), "reports");
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir);

  const pdfPath = path.join(
    outputDir,
    `RepurpoAI_Report_${Date.now()}.pdf`
  );

  const browser = await puppeteer.launch({
    headless: true
  });

  const page = await browser.newPage();

  await page.setContent(htmlContent, {
    waitUntil: "networkidle0"
  });

  await page.pdf({
    path: pdfPath,
    format: "A4",
    printBackground: true,
    margin: {
      top: "20mm",
      bottom: "20mm",
      left: "15mm",
      right: "15mm"
    }
  });

  await browser.close();
  return pdfPath;
}
