from __future__ import annotations
from typing import List, Tuple
from ..core.models import FloorPlan, ComplianceReport, Infraction
from ..compliance.engine import ComplianceAuditEngine

class ComplianceAuditorAgent:
    """
    Agent 4: Compliance Auditor Agent
    Executes exhaustive deterministic verification against IBC 2024, ADA 2010,
    and municipal zoning rules. Generates structured critique and mathematical infraction vectors.
    """
    
    @staticmethod
    def audit(floor_plan: FloorPlan) -> ComplianceReport:
        report = ComplianceAuditEngine.audit_floor_plan(floor_plan)
        return report
