import httpx
from urllib.parse import urlencode
from google.adk.agents import Agent
import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import json

def fetch_trials_tool(condition: str, max_results: int = 10) -> dict:
    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {"query.term": condition, "pageSize": max_results}
    resp = httpx.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()

root_agent = Agent(
    name="clinical_trials_intel_agent",
    model="gemini-2.5-flash",
    instruction="You are a clinical trials intelligence assistant...",
    description="Agent that summarizes clinical trial data",
    tools=[fetch_trials_tool],
)

# Runner/session lazy init
APP_NAME = "clinical_agent_app"
USER_ID = "clinical_user"
SESSION_ID = "session_clinical"

_runner = None
_session_service = None

async def _init_runner_once_async(app_name: str, user_id: str, session_id: str):
    global _runner, _session_service
    if _runner is not None:
        return _runner
    _session_service = InMemorySessionService()
    await _session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    _runner = Runner(agent=root_agent, app_name=app_name, session_service=_session_service)
    return _runner

async def call_agent_async(query: str, max_results: int = 10) -> dict:
    try:
        runner = await _init_runner_once_async(APP_NAME, USER_ID, SESSION_ID)
        prompt = query if isinstance(query, str) else json.dumps(query)
        prompt += f"\n\nmax_results={max_results}"
        content = types.Content(role='user', parts=[types.Part(text=prompt)])
        loop = asyncio.get_running_loop()
        events = await loop.run_in_executor(None, lambda: runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content))
        for event in events:
            if event.is_final_response() and event.content:
                final = event.content.parts[0].text.strip()
                return {"status": "success", "agent": "clinical", "response": final}
        return {"status": "error", "agent": "clinical", "error": "no final response from agent"}
    except Exception as e:
        return {"status": "error", "agent": "clinical", "error": str(e)}

def call_agent(query: str, max_results: int = 10) -> dict:
    """
    Sync wrapper: if an event loop is running, caller should use call_agent_async.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        # Running inside an existing event loop — instruct caller to use async API
        return {"status":"error","agent":"clinical","error":"event loop running; use call_agent_async(...) instead"}
    return asyncio.run(call_agent_async(query, max_results=max_results))