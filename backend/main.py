from __future__ import annotations
import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .core.models import SiteBoundary, FloorPlan, GenerationPipelineResponse, ComplianceReport
from .agents.orchestrator import AgenticSystemOrchestrator
from .agents.compliance_auditor_agent import ComplianceAuditorAgent
from .agents.refiner_agent import IterativeRefinerAgent
from .evaluation.benchmark_suite import BenchmarkSuiteRunner
from .export.dxf_exporter import DXFExporter
from .export.svg_exporter import SVGExporter
from .export.report_generator import ComplianceReportGenerator

app = FastAPI(
    title="ArchAI Pro — Compliance-Aware Architectural Layout Generation API",
    description="Multi-Agent Neurosymbolic Architectural Design & Multi-Floor Building Code Verification Framework",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    user_brief: str = "Luxury 3 BHK residence with master ensuite, open kitchen, and home office"
    site_width: float = 16.0
    site_depth: float = 14.0
    setback_front: float = 1.5
    setback_rear: float = 1.5
    setback_left: float = 1.0
    setback_right: float = 1.0
    llm_provider: str = "auto" # "auto", "gemini", "openai", "ollama", "semantic"
    api_key: Optional[str] = None
    max_iterations: int = 3

@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "ArchAI Pro Multi-Agent Engine", "version": "2.0.0"}

@app.post("/api/generate", response_model=GenerationPipelineResponse)
def generate_layout(req: GenerateRequest):
    site = SiteBoundary(
        width=req.site_width,
        depth=req.site_depth,
        setback_front=req.setback_front,
        setback_rear=req.setback_rear,
        setback_left=req.setback_left,
        setback_right=req.setback_right
    )
    result = AgenticSystemOrchestrator.execute_pipeline(
        user_brief=req.user_brief,
        site=site,
        provider=req.llm_provider,
        api_key=req.api_key,
        max_iterations=req.max_iterations
    )
    return result

@app.post("/api/audit", response_model=ComplianceReport)
def audit_plan(plan: FloorPlan):
    report = ComplianceAuditorAgent.audit(plan)
    return report

@app.post("/api/refine", response_model=FloorPlan)
def refine_plan(plan: FloorPlan):
    report = ComplianceAuditorAgent.audit(plan)
    refined = IterativeRefinerAgent.refine_layout(plan, report.infractions)
    ComplianceAuditorAgent.audit(refined)
    return refined

@app.get("/api/benchmark")
def run_benchmark(test_count: int = 6):
    results = BenchmarkSuiteRunner.run_full_benchmark(test_count=test_count)
    return results

@app.post("/api/export/dxf")
def export_dxf(plan: FloorPlan):
    dxf_content = DXFExporter.generate_dxf_string(plan)
    return Response(
        content=dxf_content,
        media_type="application/dxf",
        headers={"Content-Disposition": f"attachment; filename={plan.id}.dxf"}
    )

@app.post("/api/export/svg")
def export_svg(plan: FloorPlan, floor_index: int = Query(0)):
    svg_content = SVGExporter.generate_svg(plan, floor_index=floor_index)
    return Response(content=svg_content, media_type="image/svg+xml")

@app.post("/api/export/report")
def export_report(plan: FloorPlan):
    report_md = ComplianceReportGenerator.generate_markdown_report(plan)
    return {"report_markdown": report_md}

# Mount frontend directory
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
