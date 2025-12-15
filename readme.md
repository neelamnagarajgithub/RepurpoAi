<div align="center">
  <img src="public/icon.png" alt="RepurpoAI Logo" width="120" height="120">
  
  # RepurpoAI
  
  **AI-Powered Drug Repurposing Platform**
  
  Accelerating the discovery of new therapeutic uses for existing molecules through intelligent multi-agent analysis.
  
  [![Next.js](https://img.shields.io/badge/Next.js-16.0-black?logo=next.js)](https://nextjs.org/)
  [![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
</div>

---

##  About RepurpoAI

RepurpoAI is an advanced drug repurposing platform that leverages artificial intelligence to identify new therapeutic applications for existing pharmaceutical molecules. Using a sophisticated multi-agent architecture, RepurpoAI autonomously analyzes: 

-  **Clinical Trials Data** - Comprehensive trial outcomes and patient data
-  **Scientific Literature** - Research papers and medical publications
-  **Patent Information** - Intellectual property and competitive landscape
-  **Safety Profiles** - Adverse events and pharmacovigilance data
-  **Market Intelligence** - Commercial viability and market dynamics

Through an intuitive conversational interface, RepurpoAI delivers consolidated, actionable reports that help pharmaceutical teams move from hypothesis to decision in **weeks instead of months**.

---

##  Key Features

-  **Multi-Agent Intelligence** - Specialized AI agents working in concert
-  **Conversational Interface** - Natural language interaction for complex queries
-  **Automated Report Generation** - Comprehensive PDF reports with citations
-  **Real-time Streaming** - WebSocket-based live updates
-  **Secure Authentication** - JWT-based user authentication
-  **Document Management** - Download and archive generated reports
-  **Modern UI/UX** - Built with shadcn/ui and Tailwind CSS

---

##  Architecture

RepurpoAI uses a **multi-agent orchestration** pattern:

```
┌─────────────────────────────────────────────────────────┐
│                    Master Agent                         │
│              (Orchestrator & Coordinator)               │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Clinical     │  │ Literature   │  │ Safety       │
│ Trials Agent │  │ Agent        │  │ Agent        │
└──────────────┘  └──────────────┘  └──────────────┘
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Patent       │  │ Market       │  │ Report       │
│ Agent        │  │ Agent        │  │ Generator    │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

##  Tech Stack

### Frontend
- **Framework:** Next.js 16.0 (React 19.2)
- **Language:** TypeScript 5
- **Styling:** Tailwind CSS 4.1
- **UI Components:** Radix UI + shadcn/ui
- **Charts:** Recharts
- **Markdown:** react-markdown
- **PDF Generation:** Puppeteer, jsPDF
- **Storage:** Supabase

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.x
- **AI/ML:** Google ADK (Agent Development Kit)
- **Database:** PostgreSQL with pgcrypto
- **ORM:** SQLAlchemy (async)
- **Authentication:** JWT (OAuth2)
- **WebSockets:** Native FastAPI WebSocket support

---

##  Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- PostgreSQL database
- Supabase account (for file storage)
- Google AI API credentials

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/neelamnagarajgithub/RepurpoAi.git
cd RepurpoAi
```

#### 2. Frontend Setup

```bash
# Install dependencies
npm install

# Create .env. local file
cp .env.example .env. local

# Configure environment variables
# Add your Supabase, API endpoints, etc.

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

#### 3. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd Repurpo_AI_Agents
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your database, API keys, etc.

# Start FastAPI server
uvicorn Backend.app:app --host 0.0.0.0 --port 8001 --reload
```

The backend API will be available at `http://localhost:8001`

---

##  Environment Variables

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### Backend (.env)

```env
DATABASE_URL=postgresql://user:password@localhost:5432/repurpoai
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
GOOGLE_API_KEY=your_google_ai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

---

##  API Documentation

### Authentication Endpoints

#### POST `/api/auth/signup`
Create a new user account
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```

#### POST `/api/auth/token`
Obtain JWT access token (OAuth2 form-encoded)

### Message & Conversation Endpoints

#### POST `/api/messages`
Store user/assistant messages and create conversations

#### GET `/api/messages`
Retrieve conversation history for authenticated user

### Download Management

#### POST `/api/downloads`
Register generated report for user

#### GET `/api/downloads`
List all downloadable reports for user

### WebSocket

#### WS `/ws/master`
Real-time streaming connection to Master Agent

**Client → Server Messages:**
```json
{"type": "user_message", "content": "Analyze aspirin for cardiovascular uses"}
{"type": "human_reply", "content": "Yes, continue analysis"}
{"type": "interrupt"}
```

**Server → Client Messages:**
```json
{"type": "event", "payload": {... }}
{"type": "error", "message": "... "}
{"type": "done"}
```

---

##  Project Structure

```
RepurpoAi/
├── app/                          # Next.js app directory
│   ├── page.tsx                  # Main chat interface
│   ├── login/page.tsx            # Authentication page
│   ├── history/page.tsx          # Conversation history
│   ├── downloads/page.tsx        # Report downloads
│   └── api/                      # API routes
│       ├── report/pdf/route.ts   # PDF generation
│       └── upload-report/route.ts # Supabase upload
├── components/                    # React components
│   ├── conversation-area.tsx     # Chat UI
│   ├── prompt-box.tsx            # Input component
│   ├── footer.tsx                # Report generation
│   └── ui/                       # shadcn/ui components
├── Repurpo_AI_Agents/            # Backend & AI agents
│   ├── Backend/
│   │   ├── app.py                # FastAPI entry point
│   │   └── src/
│   │       ├── auth. py           # Authentication router
│   │       ├── db.py             # Database initialization
│   │       └── models.py         # SQLAlchemy models
│   ├── Master_Agent/
│   │   └── agent.py              # Master orchestrator agent
│   ├── Clinical_Agent/           # Clinical trials analysis
│   ├── Literature_Agent/         # Scientific literature mining
│   ├── Safety_Agent/             # Safety & pharmacovigilance
│   ├── Patent_Agent/             # Patent landscape analysis
│   └── Market_Agent/             # Market intelligence
├── public/
│   └── icon.png                  # RepurpoAI logo
├── styles/                       # Global styles
├── lib/                          # Utility functions
└── package.json                  # Frontend dependencies
```

---

##  Key Components

### Frontend

- **`app/page.tsx`** - Main entry point with WebSocket connection and chat interface
- **`components/conversation-area.tsx`** - Message display with markdown rendering
- **`components/prompt-box.tsx`** - User input component
- **`app/api/report/pdf/route.ts`** - Server-side PDF generation using Puppeteer

### Backend

- **`Backend/app.py`** - FastAPI application with WebSocket support
- **`Backend/src/auth.py`** - JWT authentication and protected routes
- **`Backend/src/db.py`** - Database models and initialization
- **`Master_Agent/agent.py`** - ADK-based orchestrator agent

---

##  Usage Example

1. **Sign up / Log in** to your RepurpoAI account
2. **Ask a question** in natural language: 
   ```
   "What are potential repurposing opportunities for metformin in neurodegenerative diseases?"
   ```
3. **Watch real-time** as agents analyze data sources
4. **Receive consolidated report** with citations and recommendations
5. **Download PDF** for offline review and sharing

---

##  Security

- JWT-based authentication with secure token storage
- OAuth2 password flow implementation
- Password hashing with industry-standard algorithms
- CORS configuration for controlled access
- Environment-based secrets management
- PostgreSQL `pgcrypto` extension for UUID generation

---

##  Troubleshooting

### Puppeteer Issues (Docker/Serverless)

If PDF generation fails, add launch arguments: 

```typescript
await puppeteer.launch({
  args: ['--no-sandbox', '--disable-setuid-sandbox']
})
```

### Database Connection Errors

Ensure PostgreSQL is running and `pgcrypto` extension is enabled:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

### WebSocket Connection Failures

Check that: 
- Backend is running on specified port
- CORS origins include your frontend URL
- Firewall allows WebSocket connections

---

##  Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Add tests for new features
- Follow existing code style and linting rules
- Keep agent tools deterministic and well-documented
- Return structured JSON outputs from agents
- Update documentation for API changes

---

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

##  Authors

- **Neelam Nagaraj** - [@neelamnagarajgithub](https://github.com/neelamnagarajgithub), Role: Web Development, API Integeration
- **Shatakshi Palli** - [@Shatakshipalli](https://github.com/Shatakshi Palli), ROle: Agent Development

---

##  Acknowledgments

- Google ADK for agent orchestration framework
- FastAPI for high-performance async API
- Next.js team for the amazing React framework
- shadcn/ui for beautiful UI components
- Supabase for backend services

---

##  Support

For questions, issues, or feature requests, please [open an issue](https://github.com/neelamnagarajgithub/RepurpoAi/issues) on GitHub.

---

<div align="center">
  Made with ❤️ for accelerating pharmaceutical innovation
</div>
