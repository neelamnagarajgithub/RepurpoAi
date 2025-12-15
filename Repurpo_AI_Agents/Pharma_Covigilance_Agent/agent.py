# ----------------------------- IMPORTS -------------------------------- #
from google.adk.agents.llm_agent import Agent
import requests, asyncio, json
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

FAERS_URL = "https://api.fda.gov/drug/event.json"


# ----------------------------- TOOLS --------------------------------- #

def fetch_adverse_events(drug_name: str, limit: int = 20) -> dict:
    """
    Fetches adverse event reports from the FDA FAERS database for a given drug.
    """
    params = {
        "search": f"patient.drug.medicinalproduct:{drug_name}",
        "limit": limit
    }

    try:
        response = requests.get(
            FAERS_URL,
            params=params,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        data = response.json()
    except Exception as e:
        return {"error": f"FAERS API error: {e}"}

    if "results" not in data:
        return {"error": "No AE reports found for this drug"}

    return data["results"]


def analyze_adverse_events(events: list) -> dict:
    """
    Analyzes FAERS adverse event reports:
    - Seriousness distribution
    - Outcome distribution
    - Most common reactions
    - Demographics
    """
    if isinstance(events, dict) and "error" in events:
        return events

    seriousness = {"serious": 0, "nonserious": 0}
    outcomes = {}
    reactions = {}
    genders = {"male": 0, "female": 0, "unknown": 0}
    ages = []

    for e in events:
        # Seriousness
        if e.get("serious", "0") == "1":
            seriousness["serious"] += 1
        else:
            seriousness["nonserious"] += 1

        # Outcomes
        outcome = e.get("seriousnessoutcome", "unknown")
        outcomes[outcome] = outcomes.get(outcome, 0) + 1

        # Reactions
        for r in e.get("patient", {}).get("reaction", []):
            term = r.get("reactionmeddrapt", "Unknown")
            reactions[term] = reactions.get(term, 0) + 1

        # Gender
        gender = e.get("patient", {}).get("patientsex", "0")
        gender_map = {"1": "male", "2": "female", "0": "unknown"}
        genders[gender_map.get(gender, "unknown")] += 1

        # Ages
        age = e.get("patient", {}).get("patientonsetage")
        if age:
            try:
                ages.append(float(age))
            except:
                pass

    return {
        "seriousness": seriousness,
        "outcomes": outcomes,
        "top_reactions": sorted(reactions.items(), key=lambda x: x[1], reverse=True)[:10],
        "gender_distribution": genders,
        "mean_age": sum(ages) / len(ages) if ages else "NA"
    }


def generate_safety_summary(drug_name: str) -> dict:
    """
    Full pipeline:
    1. Fetch AE data from FAERS
    2. Analyze patterns
    3. Provide a concise safety insight summary
    """
    events = fetch_adverse_events(drug_name=drug_name, limit=30)
    analysis = analyze_adverse_events(events)

    # Only send a summarized version to the LLM to avoid token limits
    summary_text = f"""
Drug: {drug_name}
Serious vs Non-Serious: {analysis['seriousness']}
Top Reactions: {analysis['top_reactions']}
Outcomes: {analysis['outcomes']}
Gender Distribution: {analysis['gender_distribution']}
Mean Age: {analysis['mean_age']}
"""

    return {
        "drug": drug_name,
        "summary": summary_text
    }


# ----------------------------- AGENT --------------------------------- #

root_agent = Agent(
    model="gemini-2.5-flash",
    name="pharmacovigilance_agent",
    description="Tracks drug safety signals using FAERS.",
    instruction="""
You are a Pharmacovigilance Intelligence Agent.

Responsibilities:
- Understand the drug name.
- Only use the summarized output from 'generate_safety_summary'.
- Analyze serious vs non-serious cases, top reactions, outcomes, and demographics.
- Provide concise, medically-safe insights.
- Do not process raw FAERS events directly.
- Ask clarifying questions if the drug name is ambiguous.
""",
    tools=[generate_safety_summary]
)

# Runner/session lazy init (reuse pattern)
APP_NAME = "pharmacovigilance_agent_app"
USER_ID = "pv_user"
SESSION_ID = f"session_pv_default"

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

def _init_runner_once(app_name: str, user_id: str, session_id: str):
    if _runner is not None:
        return _runner
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        raise RuntimeError("Event loop already running; use call_agent_async(...) instead.")
    return asyncio.run(_init_runner_once_async(app_name, user_id, session_id))

async def call_agent_async(drug_name: str) -> dict:
    try:
        runner = await _init_runner_once_async(APP_NAME, USER_ID, SESSION_ID)
        prompt = json.dumps({"drug_name": drug_name})
        content = types.Content(role='user', parts=[types.Part(text=prompt)])
        loop = asyncio.get_running_loop()
        events = await loop.run_in_executor(None, lambda: runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content))
        for event in events:
            if event.is_final_response() and event.content:
                final = event.content.parts[0].text.strip()
                return {"status":"success","agent":"pharmacovigilance","response":final}
        return {"status":"error","agent":"pharmacovigilance","error":"no final response from agent"}
    except Exception as e:
        return {"status":"error","agent":"pharmacovigilance","error":str(e)}

def call_agent(drug_name: str) -> dict:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        return {"status":"error","agent":"pharmacovigilance","error":"event loop running; use call_agent_async(...) instead"}
    return asyncio.run(call_agent_async(drug_name))
