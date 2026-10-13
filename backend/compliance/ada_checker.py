from __future__ import annotations
from typing import List
from ..core.models import FloorPlan, Infraction

def check_ada_compliance(floor_plan: FloorPlan) -> List[Infraction]:
    infractions: List[Infraction] = []
    rooms = [r for r in floor_plan.rooms if r.bounds]
    
    # 1. ADA Section 404.2.3: Door Clear Opening Width (>= 32 inches / 0.813 m)
    for r in rooms:
        for d in r.doors:
            if d.width < 0.813:
                infractions.append(
                    Infraction(
                        code="ADA-404.2.3",
                        standard="ADA",
                        severity="CRITICAL",
                        room_id=r.id,
                        description=f"Door '{d.id}' clear width ({d.width * 1000:.0f} mm) is less than ADA minimum 813 mm (32 inches)",
                        current_value=d.width,
                        required_value=0.813,
                        unit="m",
                        remediation_advice="Widen door opening to at least 813 mm."
                    )
                )

    # 2. ADA Section 304.3.1: 60-inch (1.524 m) Wheelchair Turning Circle in Bathrooms & Kitchens
    accessible_wet_rooms = ["Bathroom", "MasterBathroom", "Kitchen"]
    for r in rooms:
        if r.room_type in accessible_wet_rooms and r.is_accessible:
            min_dim = r.bounds.min_dimension
            if min_dim < 1.524:
                infractions.append(
                    Infraction(
                        code="ADA-304.3.1",
                        standard="ADA",
                        severity="CRITICAL",
                        room_id=r.id,
                        description=f"Accessible room '{r.name}' minimum dimension {min_dim:.2f} m cannot accommodate a 1.524 m (60 inch) wheelchair turning diameter",
                        current_value=min_dim,
                        required_value=1.524,
                        unit="m",
                        remediation_advice="Enlarge room width to at least 1.524 m to provide circular wheelchair clearance."
                    )
                )

    # 3. ADA Section 403.5.1: Accessible Route Clear Width (>= 36 inches / 0.914 m)
    corridors = [r for r in rooms if r.room_type in ["Corridor", "Foyer"]]
    for c in corridors:
        if c.bounds.min_dimension < 0.914:
            infractions.append(
                Infraction(
                    code="ADA-403.5.1",
                    standard="ADA",
                    severity="CRITICAL",
                    room_id=c.id,
                    description=f"Circulation corridor '{c.name}' clear width {c.bounds.min_dimension:.2f} m is below ADA minimum 0.914 m (36 inches)",
                    current_value=c.bounds.min_dimension,
                    required_value=0.914,
                    unit="m",
                    remediation_advice="Widen corridor to at least 0.914 m continuous clear width."
                )
            )

    return infractions
