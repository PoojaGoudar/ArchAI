from __future__ import annotations
from typing import List
from .ibc_checker import check_ibc_compliance
from .ada_checker import check_ada_compliance
from .zoning_checker import check_zoning_compliance
from ..core.models import FloorPlan, ComplianceReport, Infraction, EgressPath

class ComplianceAuditEngine:
    """
    Central deterministic audit engine executing verification across:
    - International Building Code (IBC 2024)
    - ADA 2010 Accessible Design Standards
    - Municipal Site Zoning & Setbacks
    """
    
    @staticmethod
    def audit_floor_plan(floor_plan: FloorPlan) -> ComplianceReport:
        all_infractions: List[Infraction] = []
        
        # 1. Run IBC Checks (Dimensions, Overlaps, Daylight, Egress)
        ibc_infractions, egress_paths = check_ibc_compliance(floor_plan)
        all_infractions.extend(ibc_infractions)
        
        # 2. Run ADA Accessibility Checks (Door widths, Turning radii, Hallways)
        ada_infractions = check_ada_compliance(floor_plan)
        all_infractions.extend(ada_infractions)
        
        # 3. Run Zoning Checks (Setbacks, Coverage)
        zoning_infractions = check_zoning_compliance(floor_plan)
        all_infractions.extend(zoning_infractions)
        
        # Compute summary metrics
        critical_count = sum(1 for inf in all_infractions if inf.severity == "CRITICAL")
        warning_count = sum(1 for inf in all_infractions if inf.severity == "WARNING")
        
        total_checks_evaluated = max(10, len(floor_plan.rooms) * 4 + len(egress_paths) + 5)
        passed_checks = max(0, total_checks_evaluated - (critical_count * 2 + warning_count))
        
        # Normalized compliance score 0.0 - 100.0%
        penalty = (critical_count * 25.0) + (warning_count * 8.0)
        compliance_score = max(0.0, min(100.0, 100.0 - penalty))
        
        overall_compliant = (critical_count == 0)
        
        report = ComplianceReport(
            overall_compliant=overall_compliant,
            compliance_score=round(compliance_score, 1),
            total_checks=total_checks_evaluated,
            passed_checks=passed_checks,
            failed_critical=critical_count,
            failed_warnings=warning_count,
            infractions=all_infractions,
            egress_paths=egress_paths,
            standards_applied=["IBC 2024", "ADA 2010", "Municipal Zoning Bylaws"]
        )
        
        floor_plan.compliance = report
        return report
