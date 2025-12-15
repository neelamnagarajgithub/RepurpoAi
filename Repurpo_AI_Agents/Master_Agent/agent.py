"""
Master Pharmaceutical Intelligence Agent - updated to call sub_agents directly via their call_agent api
"""

from google.adk.agents.llm_agent import Agent
from typing import Dict, Any
import json, asyncio

# Import the agent modules (not their sync wrappers) so we can call async entrypoints
from Clinical_Agent import agent as Clinical_agent_mod
from competitive_landscape_agent import agent as Competitive_agent_mod
from Eximtrade_Agent import agent as Exim_agent_mod
from Literature_Agent import agent as Literature_agent_mod
from Patent_and_Regulatory_Agent import agent as Patent_agent_mod
from Pharma_Covigilance_Agent import agent as PV_agent_mod

AGENTS = {
    "clinical": Clinical_agent_mod,
    "competitive": Competitive_agent_mod,
    "exim": Exim_agent_mod,
    "literature": Literature_agent_mod,
    "patent": Patent_agent_mod,
    "pharmacovigilance": PV_agent_mod,
}

def get_agent(name: str):
    return AGENTS.get(name)

# Async-aware query wrappers call the agent module's async entrypoint when available
async def _call_agent_module_async(mod, *args, **kwargs):
    if mod is None:
        return {"status":"error","error":"agent module not available"}
    if hasattr(mod, "call_agent_async"):
        return await getattr(mod, "call_agent_async")(*args, **kwargs)
    # fallback: if module exposes sync call_agent, run in executor
    if hasattr(mod, "call_agent"):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: getattr(mod, "call_agent")(*args, **kwargs))
    return {"status":"error","error":"no callable entrypoint on agent module"}

async def query_clinical_trials_async(drug_name: str, condition: str = None, max_results: int = 10) -> Dict[str, Any]:
    mod = get_agent("clinical")
    return await _call_agent_module_async(mod, condition or drug_name, max_results=max_results)

async def query_competitive_landscape_async(drug_name: str) -> Dict[str, Any]:
    mod = get_agent("competitive")
    return await _call_agent_module_async(mod, drug_name)

async def query_exim_trade_async(product_description: str, exporter_country: str = "IN", importer_country: str = None, start_year: int = 2023) -> Dict[str, Any]:
    mod = get_agent("exim")
    return await _call_agent_module_async(mod, product_description, exporter_country=exporter_country, importer_country=importer_country, start_year=start_year)

async def query_literature_async(drug_name: str, topic: str = None, max_results: int = 10) -> Dict[str, Any]:
    mod = get_agent("literature")
    q = f"{drug_name} {topic}" if topic else drug_name
    return await _call_agent_module_async(mod, q, max_results=max_results)

async def query_patents_regulatory_async(drug_name: str) -> Dict[str, Any]:
    mod = get_agent("patent")
    return await _call_agent_module_async(mod, drug_name)

async def query_pharmacovigilance_async(drug_name: str) -> Dict[str, Any]:
    mod = get_agent("pharmacovigilance")
    return await _call_agent_module_async(mod, drug_name)

async def comprehensive_drug_analysis_async(drug_name: str, condition: str = None, include_trade: bool = True, exporter_country: str = "IN") -> Dict[str, Any]:
    tasks = {
        "clinical_trials": asyncio.create_task(query_clinical_trials_async(drug_name, condition)),
        "competitive_landscape": asyncio.create_task(query_competitive_landscape_async(drug_name)),
        "literature": asyncio.create_task(query_literature_async(drug_name)),
        "pharmacovigilance": asyncio.create_task(query_pharmacovigilance_async(drug_name)),
        "patents_regulatory": asyncio.create_task(query_patents_regulatory_async(drug_name)),
    }
    if include_trade:
        tasks["exim_trade"] = asyncio.create_task(query_exim_trade_async(product_description=drug_name, exporter_country=exporter_country))
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    report = {"drug_name": drug_name, "analysis_timestamp": None, "sections": {}}
    for k, v in zip(tasks.keys(), results):
        if isinstance(v, Exception):
            report["sections"][k] = {"status":"error","error":str(v)}
        else:
            report["sections"][k] = v
    report["summary"] = {
        "total_sections": len(report["sections"]),
        "successful_queries": sum(1 for s in report["sections"].values() if s.get("status") == "success"),
        "failed_queries": sum(1 for s in report["sections"].values() if s.get("status") == "error")
    }
    return report

def comprehensive_drug_analysis(drug_name: str, condition: str = None, include_trade: bool = True, exporter_country: str = "IN") -> Dict[str, Any]:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        # running inside event loop -> caller should use async API
        return {"status":"error","error":"event loop running; use comprehensive_drug_analysis_async(...) instead"}
    return asyncio.run(comprehensive_drug_analysis_async(drug_name, condition=condition, include_trade=include_trade, exporter_country=exporter_country))

master_pharma_agent = Agent(
        model="gemini-2.5-flash",
        name="master_pharma_intelligence_agent",
        description="Master Pharma agent orchestrating sub-agent modules for comprehensive pharmaceutical intelligence.",
        instruction="""You are a Master Pharmaceutical Intelligence Agent that coordinates specialized sub-agents to provide comprehensive drug analysis and market intelligence.

    CORE RESPONSIBILITIES:
    - Orchestrate requests across six specialized sub-agent modules
    - Synthesize multi-source pharmaceutical data into actionable insights
    - Ensure data consistency and identify correlations across domains

    SUB-AGENT CAPABILITIES:
    1. Clinical Trials (query_clinical_trials_async): Retrieve trial data, patient demographics, efficacy results
    2. Competitive Landscape (query_competitive_landscape_async): Analyze competitor drugs, market positioning, pricing
    3. Literature (query_literature_async): Search scientific publications, research findings, clinical evidence
    4. Patents & Regulatory (query_patents_regulatory_async): Patent status, regulatory approvals, exclusivity periods
    5. Pharmacovigilance (query_pharmacovigilance_async): Safety data, adverse events, risk profiles
    6. EXIM Trade (query_exim_trade_async): Import/export data, tariffs, trade flows

    INTERACTION GUIDELINES:
    - Use comprehensive_drug_analysis() for full reports on a drug
    - Use individual query functions for focused analysis on specific domains
    - Always await async functions; they return structured data with status indicators
    - Handle errors gracefully and report incomplete data transparently
    - Prioritize data from official regulatory databases when available

    OUTPUT STANDARDS:
    - Structure responses with clear sections for each domain
    - Include confidence levels and data recency
    - Flag conflicting information across sources
    - Provide actionable recommendations based on synthesis""",
        tools=[comprehensive_drug_analysis, comprehensive_drug_analysis_async, query_clinical_trials_async, query_competitive_landscape_async,
               query_exim_trade_async, query_literature_async, query_patents_regulatory_async, query_pharmacovigilance_async],
    )

root_agent = master_pharma_agent

__all__ = ["master_pharma_agent", "root_agent", "AGENTS", "get_agent",
           "comprehensive_drug_analysis", "comprehensive_drug_analysis_async"]