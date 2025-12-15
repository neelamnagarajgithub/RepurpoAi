"""
EXIM Trade Agent for Pharma (Google ADK)

This single-file module defines a production-friendly, ADK-compatible set of agents:
- fetch_trade_data tool (safe, retry/backoff)
- hs_classifier_agent (LLM-based with fallback rule engine)
- trade_data_agent (wraps fetch_trade_data)
- compliance_agent (country rules DB + LLM augmentation)
- report_generator_agent
- master_exim_agent (orchestrator)

Drop this file into your ADK application folder (e.g., finalagent/agent.py).
Expose `root_agent = master_exim_agent` at the bottom so ADK loader picks it up.

Requirements:
- google-adk (ADK library)
- requests
- tenacity (for retry/backoff)

Run: `adk run finalagent` (or your ADK workflow)

Design goals:
- Tools never raise — always return serializable dicts
- Robust HTTP handling for upstream APIs
- Clear structured outputs for LLM post-processing

"""

from typing import Any, Dict, Optional, List
import requests
import time
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.adk.agents.llm_agent import Agent
import asyncio, json, time, logging, requests
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Configuration ----------
COMTRADE_API = "https://comtrade.un.org/api/get"
DEFAULT_TIMEOUT = 15  # seconds
MAX_RETRIES = 3

# A small helper to build structured tool responses
def success(data: Any) -> Dict[str, Any]:
    return {"status": "success", "data": data}

def error(message: str, **kwargs) -> Dict[str, Any]:
    payload = {"status": "error", "message": message}
    payload.update(kwargs)
    return payload



def fetch_trade_data(hs_code: str,
                     reporter: str = "all",
                     partner: str = "all",
                     start_year: int = 2023,
                     end_year: Optional[int] = None) -> Dict[str, Any]:
    """Fetches trade data from UN Comtrade (safe wrapper).

    Parameters
    - hs_code: HS commodity code (e.g., "3004" or "3004%")
    - reporter: reporter country code or "all" (use numeric ISO if available, e.g., 356)
    - partner: partner country code or "all" (0 = world / all)
    - start_year: integer
    - end_year: integer (defaults to start_year)

    Returns structured dict with status and data or error info.
    """

    if end_year is None:
        end_year = start_year

    years = list(range(start_year, end_year + 1))
    results = {"years_requested": years, "queries": [], "responses": []}

    for yr in years:
        params = {
            "max": 5000,
            "type": "C",
            "freq": "A",
            "px": "HS",
            "ps": str(yr),
            # ADK/Comtrade uses numeric codes for reporter/partner in some endpoints;
            # if user passed a name like 'India' the agent can be extended to resolve it.
            "r": reporter if reporter != "all" else "0",
            "p": partner if partner != "all" else "0",
            "cc": hs_code,
        }

        try:
            # Use a retry strategy for transient errors
            @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(multiplier=1, min=1, max=10),
                   retry=retry_if_exception_type(Exception))
            def _get(params_inner):
                resp = requests.get(COMTRADE_API, params=params_inner, timeout=DEFAULT_TIMEOUT)
                return resp

            resp = _get(params)

            # Non-2xx HTTP codes — don't throw; return structured error
            if not resp.ok:
                results["queries"].append({"params": params, "http_status": resp.status_code})
                results["responses"].append({"status": "error", "http_status": resp.status_code, "raw": resp.text[:1000]})
                continue

            # Try to parse JSON safely
            try:
                j = resp.json()
                results["queries"].append({"params": params, "http_status": resp.status_code})
                results["responses"].append({"status": "ok", "body": j})
            except Exception as e_json:
                results["queries"].append({"params": params, "http_status": resp.status_code})
                results["responses"].append({"status": "error", "message": "invalid-json", "raw": resp.text[:1000]})

        except Exception as exc:
            logger.exception("fetch_trade_data exception")
            results["queries"].append({"params": params, "exception": str(exc)})
            results["responses"].append({"status": "error", "message": str(exc)})

    # If all responses are errors, surface as error for the agent to handle gracefully
    any_ok = any(r.get("status") == "ok" for r in results["responses"]) if results["responses"] else False
    if not any_ok:
        return error("no_valid_responses", details=results)

    return success(results)



def hs_classifier(description: str) -> Dict[str, Any]:
    """Predict HS code for a pharma product description.

    This is intentionally conservative: it returns a list of candidate HS codes with
    short justifications and a confidence score (0-1).
    """
    desc = (description or "").lower()

    # simple rule-based heuristics
    candidates = []

    # common pharma HS leading sections
    if any(tok in desc for tok in ["tablet", "capsule", "pill", "syrup", "suspension"]):
        candidates.append({"hs": "3004", "confidence": 0.7, "reason": "measured-dosage forms (tablet/capsule)"})

    if any(tok in desc for tok in ["active ingredient", "active pharmaceutical", "api", "bulk"]):
        candidates.append({"hs": "2933-2937", "confidence": 0.6, "reason": "chemical intermediates / active ingredients"})

    if any(tok in desc for tok in ["vaccine", "antiserum", "toxoid"]):
        candidates.append({"hs": "3002", "confidence": 0.9, "reason": "vaccines/antisera"})

    if "insulin" in desc or "hormone" in desc:
        candidates.append({"hs": "2937", "confidence": 0.75, "reason": "hormones / insulin"})

    # fallback: if nothing matched, propose HS 3003/3004 variants
    if not candidates:
        candidates.append({"hs": "3003/3004", "confidence": 0.45, "reason": "no deterministic match — needs LLM review"})

    return success({"description": description, "candidates": candidates})


COUNTRY_COMPLIANCE_DB = {
    # Minimal sample — extend as needed or connect to a real DB
    "IN": {
        "country_name": "India",
        "export_requirements": ["GST invoice", "IEC (Import Export Code)", "Quality certificate (CoPP)"],
        "reg_authority": "DCGI / CDSCO",
    },
    "US": {
        "country_name": "United States",
        "export_requirements": ["FDA Registration (if required)", "GMP certificate", "Free Sale Certificate"],
        "reg_authority": "FDA",
    },
    "GB": {
        "country_name": "United Kingdom",
        "export_requirements": ["MHRA registration", "GMP certificate"],
        "reg_authority": "MHRA",
    }
}



def compliance_lookup(hs_code: str, exporter_country: str = "IN", importer_country: Optional[str] = None) -> Dict[str, Any]:
    """Return compliance checklist and high-level guidance for exporting a pharma product.

    This is not legal advice. Use as starting point and validate with local counsel/regulators.
    """
    exporter = COUNTRY_COMPLIANCE_DB.get(exporter_country.upper())
    importer = COUNTRY_COMPLIANCE_DB.get(importer_country.upper()) if importer_country else None

    payload = {
        "hs_code": hs_code,
        "exporter_country": exporter_country,
        "importer_country": importer_country,
        "exporter": exporter,
        "importer": importer,
        "notes": []
    }

    # Add high-level notes
    if exporter:
        payload["notes"].append(f"Exporting from {exporter.get('country_name')}: check {exporter.get('reg_authority')}")
    if importer:
        payload["notes"].append(f"Importing to {importer.get('country_name')}: consult {importer.get('reg_authority')}")

    payload["notes"].append("Typical documents: Commercial Invoice, Packing List, Bill of Lading, Certificate of Analysis, GMP/CoPP, Free Sale Certificate (if required).")

    return success(payload)



def generate_report(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Takes combined analysis from sub-agents and returns a structured business report.

    Expected shape of `analysis`:
    {
        "hs_classification": {...},
        "trade_data": {...},
        "compliance": {...},
        "recommendation": str
    }
    """
    # Basic template — the LLM agent can also convert a similar object into natural language.
    report = {
        "title": f"EXIM Opportunity Report - HS {analysis.get('hs_classification',{}).get('best_hs','UNKNOWN')}",
        "summary": analysis.get("recommendation", "No recommendation provided"),
        "sections": []
    }

    report["sections"].append({"name": "HS Classification", "body": analysis.get("hs_classification")})
    report["sections"].append({"name": "Trade Data", "body": analysis.get("trade_data")})
    report["sections"].append({"name": "Compliance", "body": analysis.get("compliance")})

    return success(report)


exim_agent = Agent(
    model="gemini-2.5-flash",
    name="exim_agent",
    description="High level EXIM trade analytics agent tailored to pharmaceuticals.",
    instruction="""
You are an EXIM analytics assistant for pharmaceuticals.
When asked to analyze a product opportunity, follow these steps strictly:
1. Use hs_classifier tool to propose HS candidates from the product description.
2. Use fetch_trade_data to retrieve historical trade data for promising HS codes.
3. Use compliance_lookup for exporter/importer-specific regulatory guidance.
4. Produce a JSON object summarizing: best_hs, confidence, top_importers, trend_summary, risks, next_steps.
Output must be JSON-serializable and parsable by downstream tools.
""",
    tools=[fetch_trade_data, hs_classifier, compliance_lookup, generate_report],
)

hs_classifier_agent = Agent(
    model="gemini-2.5-flash",
    name="hs_classifier_agent",
    description="Agent that calls the hs_classifier tool and, if uncertain, asks the LLM to refine.",
    instruction="""
Given a product description, call the `hs_classifier` tool and return a single best HS candidate with confidence.
If the tool reports low confidence, use your model to reason and return an improved candidate and a one-line justification.
""",
    tools=[hs_classifier],
)

trade_data_agent = Agent(
    model="gemini-2.5-flash",
    name="trade_data_agent",
    description="Calls fetch_trade_data and synthesizes top importers, growth and unit price ranges.",
    instruction="""
Given an HS code and year range, call `fetch_trade_data` and extract:
- Top 10 importing countries by value
- 3-year CAGR (if data available)
- Typical unit value range (value/quantity) if quantity present
Return a structured JSON summary.
""",
    tools=[fetch_trade_data],
)

compliance_agent = Agent(
    model="gemini-2.5-flash",
    name="compliance_agent",
    description="Provides country-level compliance and document checklists using compliance_lookup.",
    instruction="""
Given hs_code, exporter country code and importer country code, call `compliance_lookup` and return a precise checklist and estimated timeline steps.
""",
    tools=[compliance_lookup],
)

report_generator_agent = Agent(
    model="gemini-2.5-flash",
    name="report_generator_agent",
    description="Converts structured analysis into a business-ready report and recommendation.",
    instruction="""
Take the structured analysis object and produce a concise report: title, executive summary, key metrics, and recommended go/no-go decision with reasons.
Return both JSON object and a plain-text summary (fields: json_report, text_summary).
""",
    tools=[generate_report],
)

master_exim_agent = Agent(
    model="gemini-2.5-flash",
    name="master_exim_agent",
    description="Orchestrates HS classification, trade fetch, compliance, and report generation for pharma EXIM.",
    instruction="""
You are the master orchestrator. Given a user request like: "Analyze export opportunity for <product description> from <exporter country> to <importer country> for years X-Y",
perform the following steps programmatically:
1. Ask hs_classifier_agent to get HS candidates for product.
2. Choose the top candidate(s) and call trade_data_agent to fetch UN Comtrade trade flows.
3. Call compliance_agent for regulatory checklist.
4. Aggregate results and call generate_report to produce final report.
5. Return a JSON object with all intermediate steps and the final report.

The output must be fully JSON-serializable.
""",
    tools=[fetch_trade_data, hs_classifier, compliance_lookup, generate_report],
)

# expose root_agent so ADK loader can import this module and find the agent
root_agent = master_exim_agent

APP_NAME = "exim_agent_app"
USER_ID = "exim_user"
SESSION_ID = f"session_exim_{int(time.time())}"

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

async def call_agent_async(product_description: str, exporter_country: str = "IN", importer_country: str = None, start_year: int = 2023, **kwargs) -> dict:
    try:
        runner = await _init_runner_once_async(APP_NAME, USER_ID, SESSION_ID)
        prompt = json.dumps({"product_description": product_description, "exporter_country": exporter_country, "importer_country": importer_country, "start_year": start_year, **kwargs})
        content = types.Content(role='user', parts=[types.Part(text=prompt)])
        loop = asyncio.get_running_loop()
        events = await loop.run_in_executor(None, lambda: runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content))
        for event in events:
            if event.is_final_response() and event.content:
                final = event.content.parts[0].text.strip()
                return {"status":"success","agent":"exim","response":final}
        return {"status":"error","agent":"exim","error":"no final response from agent"}
    except Exception as e:
        return {"status":"error","agent":"exim","error":str(e)}

def call_agent(product_description: str, exporter_country: str = "IN", importer_country: str = None, start_year: int = 2023, **kwargs) -> dict:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        return {"status":"error","agent":"exim","error":"event loop running; use call_agent_async(...) instead"}
    return asyncio.run(call_agent_async(product_description, exporter_country=exporter_country, importer_country=importer_country, start_year=start_year, **kwargs))