from google.adk.agents.llm_agent import Agent
from google.adk.tools import google_search
import requests, time, asyncio, json
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# # ----------------------------- PATENT SEARCH TOOLS -------------------------------- #

# def search_uspto_patents(drug_name: str, limit: int = 50) -> list:
#     """
#     Searches US patents related to the drug.
#     Returns a list of patent dictionaries.
#     """
#     url = "https://api.patentsview.org/patents/query"
#     query = {"_text_any": {"patent_title": drug_name}}
#     try:
#         r = requests.get(url, params={"q": query, "f": "patent_number,patent_title,patent_status,patent_date"})
#         patents = r.json().get("patents", [])
#         return patents[:limit]
#     except:
#         return []

# def search_epo_patents(drug_name: str, limit: int = 50) -> list:
#     """
#     Searches EU patents related to the drug.
#     Returns a list of patent dictionaries.
#     """
#     url = f"https://ops.epo.org/3.2/rest-services/published-data/search"
#     params = {"q": f"ti={drug_name}"}
#     try:
#         r = requests.get(url, params=params)
#         return r.json().get("ops:world-patent-data", {}).get("ops:patent", [])[:limit]
#     except:
#         return []

# def fetch_additional_patent_links(drug_name: str, limit: int = 5) -> list:
#     """
#     Uses Google search to find additional patents or references online.
#     """
#     try:
#         results = google_search(query=f"{drug_name} patent", num_results=limit)
#         if isinstance(results, list):
#             return [{"title": r.get("title", ""), "link": r.get("link", "")} for r in results]
#         return []
#     except:
#         return []

# # ----------------------------- ANALYSIS -------------------------------- #

# def analyze_patents(drug_name: str) -> dict:
#     """
#     Combines US, EU, and web search results into a structured format.
#     """
#     us_patents = search_uspto_patents(drug_name)
#     eu_patents = search_epo_patents(drug_name)
#     web_links = fetch_additional_patent_links(drug_name)

#     structured_result = {
#         "drug_name": drug_name,
#         "us_patents": [{"number": p.get("patent_number"),
#                         "title": p.get("patent_title"),
#                         "status": p.get("patent_status"),
#                         "date": p.get("patent_date")} for p in us_patents],
#         "eu_patents": eu_patents,  # raw data as returned by EPO API
#         "additional_online_references": web_links,
#         "summary": {
#             "us_active": len([p for p in us_patents if p.get("patent_status") == "Active"]),
#             "us_expired": len([p for p in us_patents if p.get("patent_status") == "Expired"]),
#             "eu_total": len(eu_patents),
#             "additional_online_links": len(web_links)
#         }
#     }

#     return structured_result

# # ----------------------------- AGENT -------------------------------- #

# root_agent = Agent(
#     model="gemini-2.5-flash",
#     name="patent_regulatory_agent",
#     description="Fetches and analyzes all patents related to a given drug, including US, EU, and online references.",
#     instruction="""
# You are a Patent & Regulatory Intelligence Agent.
# - Understand the drug name.
# - Use the analyze_patents tool to fetch US/EU patents and online references.
# - Return a detailed, structured response with all patents, including status, titles, dates, and links.
# - Provide a concise summary of total active/expired patents.
# """,
#     tools=[analyze_patents]
# )



root_agent = Agent(
    model="gemini-2.5-flash",
    name="patent_regulatory_agent",
    description="Fetches and analyzes patents for a drug.",
    instruction="You are a Patent & Regulatory Intelligence Agent...",
    tools=[google_search]
)

APP_NAME = "patent_agent_app"
USER_ID = "patent_user"
SESSION_ID = f"session_patent_{int(time.time())}"

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

async def call_agent_async(query: str, num_results: int = 5) -> dict:
    try:
        runner = await _init_runner_once_async(APP_NAME, USER_ID, SESSION_ID)
        prompt = json.dumps({"query": query, "num_results": num_results})
        content = types.Content(role='user', parts=[types.Part(text=prompt)])
        loop = asyncio.get_running_loop()
        events = await loop.run_in_executor(None, lambda: runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content))
        for event in events:
            if event.is_final_response() and event.content:
                final = event.content.parts[0].text.strip()
                return {"status":"success","agent":"patent_regulatory","response":final}
        return {"status":"error","agent":"patent_regulatory","error":"no final response from agent"}
    except Exception as e:
        return {"status":"error","agent":"patent_regulatory","error":str(e)}

def call_agent(query: str, num_results: int = 5) -> dict:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        return {"status":"error","agent":"patent_regulatory","error":"event loop running; use call_agent_async(...) instead"}
    return asyncio.run(call_agent_async(query, num_results=num_results))
