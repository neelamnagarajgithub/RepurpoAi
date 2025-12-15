# competitive_landscape_agent.py
# Realistic Competitive Landscape Agent using free sources (ChEMBL, PatentsView, OpenFDA, PubChem)
from google.adk.agents.llm_agent import Agent
import requests, time, json, asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Optional: ADK web search helper (only if available in your ADK build)
try:
    from google.adk.tools import google_search
    HAS_WEB_SEARCH = True
except Exception:
    HAS_WEB_SEARCH = False

# ---------------------- Helpers / APIs -------------------------------- #
CH_EMBL_SEARCH = "https://www.ebi.ac.uk/chembl/api/data/compound"
CHEMBL_SIMILAR = "https://www.ebi.ac.uk/chembl/api/data/similarity/"

PATENTSVIEW_API = "https://api.patentsview.org/patents/query"
OPENFDA_LABEL = "https://api.fda.gov/drug/label.json"
PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/property/Title/JSON"
PUBCHEM_SYNONYMS = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/synonyms/JSON"
RXNAV_RXCUI = "https://rxnav.nlm.nih.gov/REST/rxcui.json"
RXNAV_PROP = "https://rxnav.nlm.nih.gov/REST/rxcui/{}/property.json"
DAILYMED_SPLS = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json"
CTGOV_STUDY_FIELDS = "https://clinicaltrials.gov/api/query/study_fields"

HEADERS = {"User-Agent": "RepurpoAI-Agent/1.0"}

def safe_get(url, params=None, timeout=8):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ---------------------- Tools (functions) -------------------------------- #
def lookup_chembl(drug_name: str, limit: int = 5):
    """
    Query ChEMBL for compound info and similar molecules (best-effort).
    """
    # ChEMBL compound search by pref_name or exact match via /search endpoint
    params = {"format": "json", "pref_name": drug_name}
    resp = safe_get("https://www.ebi.ac.uk/chembl/api/data/molecule", params=params)
    if isinstance(resp, dict) and resp.get("error"):
        return []  # soft-fail instead of raising
    # Return top molecules (trimmed)
    try:
        compounds = resp.get("molecules", [])[:limit]
        out = []
        for c in compounds:
            out.append({
                "chembl_id": c.get("molecule_chembl_id"),
                "pref_name": c.get("pref_name"),
                "molecule_type": c.get("molecule_type"),
            })
        return out
    except Exception:
        return []

def lookup_pubchem(drug_name: str):
    """
    Query PubChem for basic compound metadata (Title) as a quick check.
    """
    try:
        url = PUBCHEM_BASE.format(requests.utils.quote(drug_name))
        resp = safe_get(url)
        props = resp.get("PropertyTable", {}).get("Properties", [])
        return props[0] if props else {}
    except Exception:
        return {}


def lookup_pubchem_synonyms(drug_name: str, limit: int = 10):
    """Fetch PubChem synonyms to seed competitor/brand names."""
    try:
        url = PUBCHEM_SYNONYMS.format(requests.utils.quote(drug_name))
        resp = safe_get(url)
        syns = resp.get("InformationList", {}).get("Information", [])
        if not syns:
            return []
        synonyms = syns[0].get("Synonym", [])
        return synonyms[:limit]
    except Exception:
        return []

def lookup_openfda_manufacturers(drug_name: str, limit: int = 5):
    """
    Query OpenFDA labels to find manufacturers and product names.
    """
    try:
        params = {"search": f"openfda.brand_name:\"{drug_name}\"", "limit": limit}
        resp = safe_get(OPENFDA_LABEL, params=params)
        results = resp.get("results", [])
        manufacturers = []
        for r in results:
            mf = r.get("openfda", {}).get("manufacturer_name")
            bn = r.get("openfda", {}).get("brand_name")
            manufacturers.append({"brand_name": bn, "manufacturer": mf})
        # de-dup
        unique = []
        seen = set()
        for m in manufacturers:
            key = (m.get("brand_name"), m.get("manufacturer"))
            if key not in seen:
                seen.add(key)
                unique.append(m)
        return unique
    except Exception:
        return []


def lookup_rxnav_brands(drug_name: str):
    """Use RxNav to fetch RxCUI and brand names (BN)."""
    try:
        rxcui_resp = safe_get(RXNAV_RXCUI, params={"name": drug_name})
        rxcui = rxcui_resp.get("idGroup", {}).get("rxnormId", [])
        rxcui_id = rxcui[0] if rxcui else None
        brands = []
        if rxcui_id:
            prop_resp = safe_get(RXNAV_PROP.format(rxcui_id), params={"propName": "BN"})
            prop = prop_resp.get("propConceptGroup", {}).get("propConcept", [])
            for p in prop:
                bn = p.get("propValue")
                if bn:
                    brands.append({"brand_name": bn, "source": "RxNav", "rxcui": rxcui_id})
        return {"rxcui": rxcui_id, "brands": brands}
    except Exception:
        return {"rxcui": None, "brands": []}


def lookup_dailymed_labels(drug_name: str, limit: int = 5):
    """DailyMed SPLs to get labels and manufacturers."""
    try:
        resp = safe_get(DAILYMED_SPLS, params={"drug_name": drug_name, "pagesize": limit})
        data = resp.get("data", [])
        out = []
        for item in data:
            out.append({
                "title": item.get("title"),
                "manufacturer": item.get("manufacturerName"),
                "setid": item.get("setid")
            })
        return out
    except Exception:
        return []


def lookup_clinical_trials_sponsors(drug_name: str, limit: int = 10):
    """ClinicalTrials.gov sponsors as competitor signals."""
    try:
        params = {
            "expr": drug_name,
            "fields": "SponsorName,BriefTitle",
            "min_rnk": 1,
            "max_rnk": limit,
            "fmt": "json"
        }
        resp = safe_get(CTGOV_STUDY_FIELDS, params=params)
        studies = resp.get("StudyFieldsResponse", {}).get("StudyFields", [])
        sponsors = []
        for s in studies:
            names = s.get("SponsorName", [])
            for n in names:
                sponsors.append({"name": n, "source": "ClinicalTrials.gov"})
        return sponsors
    except Exception:
        return []

def web_search_fallback(query: str, limit: int = 5):
    """
    Use ADK web search tool if available, else return empty list.
    """
    if not HAS_WEB_SEARCH:
        return []
    try:
        results = google_search(query=query, num_results=limit)
        # convert to simplified dicts if needed
        out = []
        for r in results:
            # r might be dict with 'title' and 'link'
            if isinstance(r, dict):
                out.append({"title": r.get("title"), "link": r.get("link")})
            else:
                out.append({"text": str(r)})
        return out
    except Exception:
        return []

# ---------------------- Composite analysis tool --------------------------- #
def analyze_competitive_landscape_real(drug_name: str, limits: dict = None) -> dict:
    """
    Realistic competitive landscape using free, public sources.
    Returns a structured dictionary.
    """
    limits = limits or {}
    chembl_limit = limits.get("chembl", 5)
    web_limit = limits.get("web", 5)
    synonym_limit = limits.get("synonyms", 10)
    rxnav_limit = limits.get("rxnav_brands", 10)
    ct_limit = limits.get("clinical_trials", 10)

    pubchem = lookup_pubchem(drug_name)
    chembl = lookup_chembl(drug_name, limit=chembl_limit)
    pubchem_synonyms = lookup_pubchem_synonyms(drug_name, limit=synonym_limit)
    manufacturers = lookup_openfda_manufacturers(drug_name)
    dailymed = lookup_dailymed_labels(drug_name, limit=rxnav_limit)
    rxnav = lookup_rxnav_brands(drug_name)
    web_competitors = web_search_fallback(f"{drug_name} competitor product", limit=web_limit)
    web_pricing = web_search_fallback(f"{drug_name} price pharmacy", limit=web_limit)
    trial_sponsors = lookup_clinical_trials_sponsors(drug_name, limit=ct_limit)

    # 5) Build competitor list from ChEMBL similar molecules (pref_name) + web hits
    competitors = []
    # Ensure chembl is a list of dicts, not an error dict
    if isinstance(chembl, list):
        for c in chembl:
            if isinstance(c, dict):
                name = c.get("pref_name")
                if name and name.lower() != drug_name.lower():
                    competitors.append({"name": name, "source": "ChEMBL", "chembl_id": c.get("chembl_id")})
    # Synonyms as soft competitor/alias signals
    for syn in pubchem_synonyms:
        competitors.append({"name": syn, "source": "PubChem synonym"})
    # add manufacturer brand names as competitors sometimes (same molecule marketed by others)
    if isinstance(manufacturers, list):
        for m in manufacturers:
            if isinstance(m, dict):
                bn = m.get("brand_name")
                mf = m.get("manufacturer")
                if bn:
                    competitors.append({"name": bn, "source": "OpenFDA", "manufacturer": mf})
    for label in dailymed:
        title = label.get("title")
        manu = label.get("manufacturer")
        if title:
            competitors.append({"name": title, "source": "DailyMed", "manufacturer": manu})
    for brand in rxnav.get("brands", []):
        bn = brand.get("brand_name")
        if bn:
            competitors.append({"name": bn, "source": "RxNav", "rxcui": rxnav.get("rxcui")})
    for sponsor in trial_sponsors:
        nm = sponsor.get("name")
        if nm:
            competitors.append({"name": nm, "source": sponsor.get("source")})

    # dedupe competitors by name
    seen = set()
    deduped_competitors = []
    for comp in competitors:
        key = comp.get("name")
        if key and key not in seen:
            seen.add(key)
            deduped_competitors.append(comp)

    # 6) Basic differentiation data using web search
    differentiation = {
        "mechanism_info": web_search_fallback(f"{drug_name} mechanism of action", limit=2),
        "safety_info": web_search_fallback(f"{drug_name} safety profile adverse effects", limit=2),
    }

    # 7) Final structured result
    chembl_status = "ok" if isinstance(chembl, list) else "unavailable"

    result = {
        "drug": drug_name,
        "pubchem": pubchem,
        "pubchem_synonyms": pubchem_synonyms,
        "chembl_matches": chembl if isinstance(chembl, list) else [],
        "chembl_status": chembl_status,
        "manufacturers_brands": manufacturers if isinstance(manufacturers, list) else [],
        "dailymed_labels": dailymed,
        "rxnav": rxnav,
        "clinical_trial_sponsors": trial_sponsors,
        "competitors": deduped_competitors,
        "web_pricing_samples": web_pricing,
        "web_competitor_hits": web_competitors,
        "differentiation": differentiation,
        "summary": {
            "competitors_found": len(deduped_competitors),
            "manufacturers_found": len(manufacturers) if isinstance(manufacturers, list) else 0,
            "chembl_status": chembl_status,
            "rxnav_rxcui": rxnav.get("rxcui"),
            "web_hits_competitors": len(web_competitors) if isinstance(web_competitors, list) else 0,
            "web_hits_pricing": len(web_pricing) if isinstance(web_pricing, list) else 0,
            "dailymed_labels": len(dailymed),
            "clinical_trial_sponsors": len(trial_sponsors),
            "note": "ChemBL unavailable" if chembl_status == "unavailable" else ""
        }
    }
    return result
# ------------------ end analyze_competitive_landscape_real -----------------

# --------------------------- ADK AGENT ----------------------------------- #
competitive_landscape_agent = Agent(
    model="gemini-2.5-flash",
    name="competitive_landscape_agent",
    description="Analyzes the competitive environment for a drug.",
    instruction="You are a Competitive Landscape Agent...",
    tools=[analyze_competitive_landscape_real]
)

root_agent = competitive_landscape_agent

APP_NAME = "competitive_agent_app"
USER_ID = "competitive_user"
SESSION_ID = f"session_{int(time.time())}"

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

async def call_agent_async(drug_name: str, limits: dict = None) -> dict:
    try:
        runner = await _init_runner_once_async(APP_NAME, USER_ID, SESSION_ID)
        prompt = json.dumps({"drug_name": drug_name, "limits": limits or {}})
        content = types.Content(role='user', parts=[types.Part(text=prompt)])
        loop = asyncio.get_running_loop()
        events = await loop.run_in_executor(None, lambda: runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content))
        for event in events:
            if event.is_final_response() and event.content:
                final = event.content.parts[0].text.strip()
                return {"status":"success","agent":"competitive_landscape","response":final}
        return {"status":"error","agent":"competitive_landscape","error":"no final response from agent"}
    except Exception as e:
        return {"status":"error","agent":"competitive_landscape","error":str(e)}

def call_agent(drug_name: str, limits: dict = None) -> dict:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        return {"status":"error","agent":"competitive_landscape","error":"event loop running; use call_agent_async(...) instead"}
    return asyncio.run(call_agent_async(drug_name, limits=limits))