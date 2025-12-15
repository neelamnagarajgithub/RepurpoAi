import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
import requests, xml.etree.ElementTree as ET, os, json
from google.adk.agents.llm_agent import Agent
from google.genai import types

APP_NAME = "literature_agent_app"
USER_ID = "1234"
SESSION_ID = "session1234"

# Get API key from environment (optional)
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")

# Helper function: Search PubMed
def search_pubmed(query: str, retmax: int = 10, api_key: str = "") -> str:
    """
    Search PubMed database for articles matching the query.
    
    Args:
        query: Search term for PubMed
        retmax: Maximum number of results to return
        api_key: NCBI API key (optional but recommended)
    
    Returns:
        XML response containing PMIDs, WebEnv, and QueryKey
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": retmax,
        "usehistory": "y"
    }
    if api_key:
        params["api_key"] = api_key

    response = requests.get(base_url, params=params)
    return response.text


def fetch_summaries(webenv: str, query_key: str, retmax: int = 10, api_key: str = "") -> dict:
    """
    Fetch article summaries from PubMed using WebEnv and QueryKey.
    
    Args:
        webenv: Web environment from search results
        query_key: Query key from search results
        retmax: Maximum number of summaries to fetch
        api_key: NCBI API key (optional but recommended)
    
    Returns:
        JSON response with article metadata
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {
        "db": "pubmed",
        "query_key": query_key,
        "WebEnv": webenv,
        "retmax": retmax,
        "retmode": "json"
    }
    if api_key:
        params["api_key"] = api_key

    response = requests.get(base_url, params=params)
    return response.json()


def get_literature_summary(query: str) -> list:
    """
    Search PubMed and fetch top article summaries.
    
    Args:
        query: Research query to search in PubMed
    
    Returns:
        List of article summaries with title, journal, publication date, and authors
    """
    try:
        # Step 1: Search PubMed
        search_result = search_pubmed(query, retmax=10, api_key=NCBI_API_KEY)

        # Extract WebEnv and QueryKey from XML response
        root = ET.fromstring(search_result)
        webenv_element = root.find("WebEnv")
        query_key_element = root.find("QueryKey")
        
        if webenv_element is None or query_key_element is None:
            return [{"error": "No results found for the given query"}]
        
        webenv = webenv_element.text
        query_key = query_key_element.text

        # Step 2: Fetch summaries
        summaries = fetch_summaries(webenv, query_key, retmax=10, api_key=NCBI_API_KEY)

        # Step 3: Format output
        results = []
        if "result" in summaries:
            for uid, article in summaries['result'].items():
                if uid == 'uids':  # Skip metadata
                    continue
                results.append({
                    "title": article.get("title", "N/A"),
                    "journal": article.get("fulljournalname", "N/A"),
                    "pub_date": article.get("pubdate", "N/A"),
                    "authors": [a['name'] for a in article.get("authors", [])]
                })

        return results if results else [{"message": "No article summaries found"}]

    except Exception as e:
        return [{"error": f"Error fetching literature: {str(e)}"}]


# Root agent configuration with tools
literature_agent = Agent(
    model='gemini-2.5-flash',
    name='literature_agent',
    description="Searches PubMed articles and provides summaries.",
    instruction="You are a research assistant. When a user asks about literature or research topics, search PubMed and provide latest 10 article summaries with titles, journals, publication dates, and authors.",
    tools=[get_literature_summary]
)

root_agent = literature_agent

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
    """Sync initializer. If an event loop is already running, ask caller to use the async API."""
    global _runner, _session_service
    if _runner is not None:
        return _runner

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Running inside an event loop — caller must use call_agent_async.
        raise RuntimeError("Event loop already running; use call_agent_async(...) instead.")
    # safe to use asyncio.run for sync callers
    return asyncio.run(_init_runner_once_async(app_name, user_id, session_id))


async def call_agent_async(query: str, max_results: int = 10) -> dict:
    try:
        runner = await _init_runner_once_async(APP_NAME, USER_ID, SESSION_ID)
        content = types.Content(role='user', parts=[types.Part(text=query)])
        loop = asyncio.get_running_loop()
        events = await loop.run_in_executor(None, lambda: runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content))
        for event in events:
            if event.is_final_response() and event.content:
                final_answer = event.content.parts[0].text.strip()
                return {"status":"success","agent":"literature","response":final_answer}
        return {"status":"error","agent":"literature","error":"no final response from agent"}
    except Exception as e:
        return {"status":"error","agent":"literature","error":str(e)}

def call_agent(query: str, max_results: int = 10) -> dict:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        return {"status":"error","agent":"literature","error":"event loop running; use call_agent_async(...) instead"}
    return asyncio.run(call_agent_async(query, max_results=max_results))