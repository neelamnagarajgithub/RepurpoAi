# RepurpoAI — Multi-Agent Pharmaceutical Intelligence

![RepurpoAI Logo](logo.png)

## Summary
RepurpoAI is a **Next.js frontend + FastAPI backend** platform that orchestrates **specialized AI agents** (trade, literature, clinical, patents, pharmacovigilance, competitive landscape) to generate **multi-domain pharmaceutical intelligence** and **downloadable reports**.

---

## Quick References

- **Frontend (Chat UI & WS integration):** `app/page.tsx`  
  Key handler: `handleSendMessage`

- **PDF Generation (Server-side):** `app/api/report/pdf/route.ts`  
  Function: `buildHTMLFromMarkdown`

- **Report Upload (Supabase):** `app/api/upload-report/route.ts`

- **Backend Entry (FastAPI + WS runner):**  
  `Repurpo_AI_Agents/Backend/app.py`

- **Auth & Core API Routes:**  
  `Repurpo_AI_Agents/Backend/src/auth.py`

- **Master Agent / Orchestrator:**  
  `Repurpo_AI_Agents/Master_Agent/agent.py`  
  Function: `master_pharma_agent`

- **Individual Agents:**  
  `Repurpo_AI_Agents/*_Agent/agent.py`

- **Database Init & Models:**  
  `Repurpo_AI_Agents/Backend/src/db.py`  
  `Repurpo_AI_Agents/Backend/src/models.py`

- **API Schemas:**  
  `Repurpo_AI_Agents/Backend/src/schemas.py`

---

## Prerequisites

- **Node.js** (v18+ recommended)
- **npm** or **Yarn**
- **Python 3.11+** (backend & agents)
- **PostgreSQL** (local or Supabase)
- **Supabase Service Role Key** (for report uploads)

---

## Environment Setup

### Frontend

```bash
cp .env.example .env.local
```

- Refer: `Repurpo_AI_Agents/.env.example`
- Local override: `.env.local`

### Backend

Set the following in `Repurpo_AI_Agents/.env.example`:

- `SECRET_KEY`
- `DATABASE_URL`
- Agent API keys (Google GenAI, `NCBI_API_KEY`, etc.)

---

## Run Locally — Frontend

```bash
npm install
npm run dev
```

- Entry point: `app/page.tsx`

### Core UI Components

- Conversation UI: `components/conversation-area.tsx`
- Prompt Input: `components/prompt-box.tsx`
- Footer / Report Generation: `components/footer.tsx`  
  Handler: `handleGenerateReport`

---

## Run Locally — Backend & Agents

1. Create Python virtual environment
2. Install backend + agent dependencies
3. Ensure PostgreSQL is reachable
4. Start FastAPI server:

```bash
uvicorn Repurpo_AI_Agents.Backend.app:app \
  --host 0.0.0.0 \
  --port 8001 \
  --reload
```

- Backend entry: `Repurpo_AI_Agents/Backend/app.py`

---

## Backend API Endpoints

### Authentication

- `POST /api/auth/signup` — Create user  
  Schema: `UserCreate`

- `POST /api/auth/token` — OAuth2 token (form encoded)

### Messages & Conversations

- `POST /api/messages` — Store message, create conversation if missing  
  Schema: `MessageCreate`

- `GET /api/messages` — Fetch messages for current user

### Downloads

- `POST /api/downloads` — Register generated file  
  Schema: `DownloadCreate`

- `GET /api/downloads` — List downloads

---

## WebSocket & Conversation Flow

- Backend exposes a **WebSocket** for real-time agent streaming
- Frontend subscribes from `page.tsx`

### Important

When WS sends:

```json
{
  "type": "conversation_created",
  "conversation_id": "<uuid>"
}
```

You **must persist** `conversation_id` client-side and include it in all subsequent `POST /api/messages` calls.

This prevents **duplicate conversation creation**.

> ⚠️ Alternative: rely entirely on WS persistence and skip REST `/messages` calls (supported but not default).

---

## PDF Generation & Report Upload

### PDF

- Markdown → HTML → PDF using **Puppeteer**
- Builder: `buildHTMLFromMarkdown`
- Ensure logo/assets exist in `/public` (e.g., `logo.png`) for PDF rendering

### Upload

- Upload handled via: `app/api/upload-report/route.ts`
- Uses:
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`

---

## Agents & Orchestration

### Master Orchestrator

- `master_pharma_agent`
- Coordinates:
  - Clinical
  - Literature
  - Patents
  - Pharmacovigilance
  - EXIM Trade
  - Competitive Landscape

### Individual Agents

Each agent lives in its own module:

- **EXIM Agent**  
  Tools: `hs_classifier`, `fetch_trade_data`, `compliance_lookup`, `generate_report`

- **Literature Agent**
- **Clinical Agent**
- **Patent Agent**
- **Pharmacovigilance Agent**
- **Competitive Landscape Agent**

All agents return **JSON-serializable outputs** by design.

---

## Database Model Notes

- **Users** → `User`
- **Conversations**  
  Uses Postgres UUID via `gen_random_uuid()`

- **Messages**  
  Linked to `Conversation.id` and `User.id`

- **Downloads**  
  Persists metadata for generated reports

---

## Frontend Auth & Storage

- JWT stored in `localStorage` under `access_token`
- Token attached as:

```http
Authorization: Bearer <token>
```

Used for protected routes: messages, downloads

---

## Troubleshooting

### Puppeteer (Serverless / Docker)

Use launch args:

```bash
--no-sandbox --disable-setuid-sandbox
```

### Supabase Upload Failures

- Confirm `SUPABASE_SERVICE_ROLE_KEY`
- Ensure upload API route is reachable

### UUID / DB Errors

- Ensure `pgcrypto` extension exists
- DB init attempts auto-create via `init_db`

---

## Development Tips

- Frontend hot reload: `npm run dev`
- Backend hot reload: `uvicorn --reload`
- Agent testing: import and run agent modules standalone

---

## Contributing

- Add tests where possible
- Follow repo lint rules
- Keep agent tools deterministic
- Return structured JSON outputs

---

## Useful Files (Quick Index)

- Frontend entry: `app/page.tsx`
- Signup/Login: `app/login/page.tsx`
- Downloads UI: `app/downloads/page.tsx`
- PDF API: `app/api/report/pdf/route.ts`
- Upload API: `app/api/upload-report/route.ts`
- Backend app: `Repurpo_AI_Agents/Backend/app.py`
- Auth router: `auth.py`
- DB init: `db.py`
- Models: `models.py`
- Agent orchestrator: `Master_Agent/agent.py`

---

## License

**Proprietary / Internal**  
MIT