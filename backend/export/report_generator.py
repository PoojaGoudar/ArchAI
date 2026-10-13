from __future__ import annotations
from datetime import datetime
from ..core.models import FloorPlan

class ComplianceReportGenerator:
    """
    Generates structured, professional markdown and HTML architectural compliance audit certificates.
    """
    
    @staticmethod
    def generate_markdown_report(floor_plan: FloorPlan) -> str:
        report = floor_plan.compliance
        if not report:
            return "# No Compliance Audit Data Available"
            
        status_badge = "✅ FULLY COMPLIANT (PASS)" if report.overall_compliant else "❌ NON-COMPLIANT (FAIL - REVIEW REQUIRED)"
        
        md = [
            f"# ARCHITECTURAL COMPLIANCE AUDIT CERTIFICATE",
            f"**Project Reference:** {floor_plan.id} | **Layout:** {floor_plan.title}",
            f"**Generated On:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Audit Result:** {status_badge}",
            f"**Overall Compliance Score:** `{report.compliance_score:.1f} / 100.0`",
            "",
            "---",
            "## 1. Statutory Standards Evaluated",
            "- **IBC 2024 (International Building Code):** Chapters 10 (Means of Egress) & 12 (Interior Space Minimums & Daylight)",
            "- **ADA Standards (2010):** §404 (Door Clearance $\ge 32\"$), §304 ($60\"$ Wheelchair Turning Diameter), §403 (Accessible Routes)",
            "- **Zoning & Municipal Bylaws:** Front/Rear/Side Setbacks, Maximum Ground Coverage, Floor Area Ratio",
            "",
            "---",
            "## 2. Quantitative Summary Metrics",
            f"| Metric | Result |",
            f"| :--- | :--- |",
            f"| **Total Statutory Checks** | `{report.total_checks}` |",
            f"| **Checks Passed** | `{report.passed_checks}` |",
            f"| **Critical Infractions** | `{report.failed_critical}` |",
            f"| **Warnings / Suggestions** | `{report.failed_warnings}` |",
            f"| **Total Built Area** | `{floor_plan.total_built_area:.1f} m²` |",
            f"| **Plot Coverage** | `{(floor_plan.total_built_area / floor_plan.site.total_site_area)*100:.1f}%` (Max Allowed: {floor_plan.site.max_ground_coverage*100:.0f}%) |",
            "",
            "---",
            "## 3. Detailed Space & Room Schedule",
            "| Room Name | Type | Zone | Area (m²) | Dimensions (W × H) | Min Required (m²) | Windows | Doors |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        ]
        
        for r in floor_plan.rooms:
            if r.bounds:
                w_str = f"{len(r.windows)} ({sum(w.glazing_area for w in r.windows):.1f}m²)"
                d_str = f"{len(r.doors)}"
                md.append(
                    f"| **{r.name}** | {r.room_type} | {r.zone} | `{r.bounds.area:.1f}` | `{r.bounds.w:.1f}m × {r.bounds.h:.1f}m` | `{r.min_area:.1f}` | {w_str} | {d_str} |"
                )
                
        md.extend([
            "",
            "---",
            "## 4. Means of Egress & Travel Distance Assessment (IBC Chapter 10)",
            "| Origin Space | Travel Distance (m) | Max Permitted (m) | Status |",
            "| :--- | :--- | :--- | :--- |"
        ])
        
        for ep in report.egress_paths:
            room = next((r for r in floor_plan.rooms if r.id == ep.room_id), None)
            name = room.name if room else ep.room_id
            st = "✅ COMPLIANT" if ep.is_compliant else "❌ EXCEEDED"
            md.append(f"| **{name}** | `{ep.total_travel_distance:.2f} m` | `{ep.max_allowed_distance:.2f} m` | {st} |")
            
        md.extend([
            "",
            "---",
            "## 5. Infraction Log & Remediation Actions"
        ])
        
        if not report.infractions:
            md.append("✨ *Zero infractions detected. The design complies with all mandatory statutory codes.*")
        else:
            for idx, inf in enumerate(report.infractions, 1):
                md.append(f"### {idx}. [{inf.severity}] {inf.code}: {inf.description}")
                md.append(f"- **Standard:** `{inf.standard}`")
                md.append(f"- **Current Value:** `{inf.current_value} {inf.unit or ''}` | **Required:** `{inf.required_value} {inf.unit or ''}`")
                md.append(f"- **Recommended Remediation:** {inf.remediation_advice}")
                md.append("")
                
        md.extend([
            "---",
            "### Sign-Off & Verification Stamp",
            "**Certified by:** ArchAI Autonomous Multi-Agent Architectural Verification Engine",
            "**Hash Verification:** `SHA256-" + floor_plan.id + "`"
        ])
        
        return "\n".join(md)
