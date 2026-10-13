from __future__ import annotations
from typing import List
from ..core.models import FloorPlan, Infraction

def check_zoning_compliance(floor_plan: FloorPlan) -> List[Infraction]:
    infractions: List[Infraction] = []
    site = floor_plan.site
    buildable = site.buildable_bounds
    
    rooms = [r for r in floor_plan.rooms if r.bounds]
    if not rooms:
        return infractions

    # 1. Setback Encroachment Check
    for r in rooms:
        # Check if room extends beyond buildable envelope
        if r.bounds.x < buildable.x - 1e-3:
            encroachment = round(buildable.x - r.bounds.x, 2)
            infractions.append(
                Infraction(
                    code="ZONE-SETBACK-LEFT",
                    standard="ZONING",
                    severity="CRITICAL",
                    room_id=r.id,
                    description=f"Room '{r.name}' encroaches into left side setback by {encroachment} m",
                    current_value=encroachment,
                    required_value=0.0,
                    unit="m",
                    remediation_advice=f"Shift room boundary rightward by at least {encroachment} m."
                )
            )
            
        if (r.bounds.x + r.bounds.w) > (buildable.x + buildable.w) + 1e-3:
            encroachment = round((r.bounds.x + r.bounds.w) - (buildable.x + buildable.w), 2)
            infractions.append(
                Infraction(
                    code="ZONE-SETBACK-RIGHT",
                    standard="ZONING",
                    severity="CRITICAL",
                    room_id=r.id,
                    description=f"Room '{r.name}' encroaches into right side setback by {encroachment} m",
                    current_value=encroachment,
                    required_value=0.0,
                    unit="m",
                    remediation_advice=f"Shrink or shift room boundary leftward."
                )
            )

        if r.bounds.y < buildable.y - 1e-3:
            encroachment = round(buildable.y - r.bounds.y, 2)
            infractions.append(
                Infraction(
                    code="ZONE-SETBACK-FRONT",
                    standard="ZONING",
                    severity="CRITICAL",
                    room_id=r.id,
                    description=f"Room '{r.name}' encroaches into front setback by {encroachment} m",
                    current_value=encroachment,
                    required_value=0.0,
                    unit="m",
                    remediation_advice=f"Shift room boundary inward from front plot line."
                )
            )

        if (r.bounds.y + r.bounds.h) > (buildable.y + buildable.h) + 1e-3:
            encroachment = round((r.bounds.y + r.bounds.h) - (buildable.y + buildable.h), 2)
            infractions.append(
                Infraction(
                    code="ZONE-SETBACK-REAR",
                    standard="ZONING",
                    severity="CRITICAL",
                    room_id=r.id,
                    description=f"Room '{r.name}' encroaches into rear setback by {encroachment} m",
                    current_value=encroachment,
                    required_value=0.0,
                    unit="m",
                    remediation_advice=f"Shrink room height or move away from rear property boundary."
                )
            )

    # 2. Maximum Ground Coverage Ratio
    total_built_area = sum(r.bounds.area for r in rooms)
    coverage_ratio = total_built_area / site.total_site_area
    if coverage_ratio > site.max_ground_coverage:
        infractions.append(
            Infraction(
                code="ZONE-COVERAGE",
                standard="ZONING",
                severity="CRITICAL",
                description=f"Total ground coverage {coverage_ratio * 100:.1f}% exceeds maximum allowable {site.max_ground_coverage * 100:.1f}%",
                current_value=coverage_ratio,
                required_value=site.max_ground_coverage,
                unit="ratio",
                remediation_advice="Reduce footprint area of individual rooms or introduce courtyards."
            )
        )

    return infractions
