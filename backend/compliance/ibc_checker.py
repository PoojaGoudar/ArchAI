from __future__ import annotations
from typing import List, Tuple
import networkx as nx
from ..core.models import FloorPlan, Infraction, EgressPath, Point2D
from ..core.geometry import check_overlap

def check_ibc_compliance(floor_plan: FloorPlan) -> Tuple[List[Infraction], List[EgressPath]]:
    infractions: List[Infraction] = []
    egress_paths: List[EgressPath] = []
    
    # 1. Non-Overlap & Geometry Integrity
    rooms = [r for r in floor_plan.rooms if r.bounds]
    for i in range(len(rooms)):
        for j in range(i + 1, len(rooms)):
            r1, r2 = rooms[i], rooms[j]
            overlap = check_overlap(r1.bounds, r2.bounds)
            if overlap > 0.05:  # Overlap greater than 0.05 sqm
                infractions.append(
                    Infraction(
                        code="GEOM-OVERLAP",
                        standard="IBC",
                        severity="CRITICAL",
                        room_id=r1.id,
                        description=f"Physical collision detected: '{r1.name}' overlaps with '{r2.name}' by {overlap:.2f} m²",
                        current_value=overlap,
                        required_value=0.0,
                        unit="m²",
                        remediation_advice="Separate room boundaries along orthogonal cut plane."
                    )
                )

    # 2. IBC Chapter 12: Habitable Room Areas & Dimensions
    # IBC 1207.1: Habitable spaces shall have not less than 70 sq ft (6.50 m2)
    # IBC 1207.2: Habitable spaces shall not be less than 7 ft (2.13 m) in any dimension
    habitable_types = ["LivingRoom", "MasterBedroom", "Bedroom", "DiningRoom", "Office"]
    
    for room in rooms:
        if room.room_type in habitable_types:
            area = room.bounds.area
            min_dim = room.bounds.min_dimension
            aspect = room.bounds.aspect_ratio
            
            if area < 6.50:
                infractions.append(
                    Infraction(
                        code="IBC-1207.1",
                        standard="IBC",
                        severity="CRITICAL",
                        room_id=room.id,
                        description=f"Habitable room '{room.name}' area {area:.2f} m² is below IBC minimum 6.50 m² (70 sq.ft)",
                        current_value=area,
                        required_value=6.50,
                        unit="m²",
                        remediation_advice=f"Expand room width or depth to attain at least 6.50 m²."
                    )
                )
            
            if min_dim < 2.13:
                infractions.append(
                    Infraction(
                        code="IBC-1207.2",
                        standard="IBC",
                        severity="CRITICAL",
                        room_id=room.id,
                        description=f"Habitable room '{room.name}' minimum dimension {min_dim:.2f} m is below IBC minimum 2.13 m (7.0 ft)",
                        current_value=min_dim,
                        required_value=2.13,
                        unit="m",
                        remediation_advice="Widen the narrowest wall dimension of the room."
                    )
                )
                
            if aspect > 2.5:
                infractions.append(
                    Infraction(
                        code="ARCH-ASPECT",
                        standard="IBC",
                        severity="WARNING",
                        room_id=room.id,
                        description=f"Room '{room.name}' aspect ratio {aspect:.2f}:1 is excessively elongated (recommended < 2.5:1)",
                        current_value=aspect,
                        required_value=2.5,
                        unit="ratio",
                        remediation_advice="Adjust room proportions towards a squarer bounding box."
                    )
                )

        # 3. IBC Chapter 1205: Natural Light & Ventilation (8% Glazing Rule)
        if room.requires_exterior_window:
            total_glazing = sum(w.glazing_area for w in room.windows)
            req_glazing = room.bounds.area * 0.08
            if total_glazing < req_glazing:
                infractions.append(
                    Infraction(
                        code="IBC-1205.2",
                        standard="IBC",
                        severity="WARNING",
                        room_id=room.id,
                        description=f"Room '{room.name}' window glazing area {total_glazing:.2f} m² is less than 8% required daylight ({req_glazing:.2f} m²)",
                        current_value=total_glazing,
                        required_value=req_glazing,
                        unit="m²",
                        remediation_advice="Add or expand exterior wall windows."
                    )
                )

    # 4. IBC Chapter 10: Egress Travel Distance Calculation
    # Find Main Exit
    main_exit_door = None
    for r in rooms:
        for d in r.doors:
            if d.is_main_exit or d.to_room == "Exterior":
                main_exit_door = d
                break
        if main_exit_door:
            break
            
    if not main_exit_door and rooms:
        # Fallback to corner of first room
        exit_pos = Point2D(x=rooms[0].bounds.x, y=rooms[0].bounds.y)
    else:
        exit_pos = main_exit_door.position if main_exit_door else Point2D(x=0, y=0)
        
    # Build circulation navigation graph
    G = nx.Graph()
    for r in rooms:
        c = r.bounds.center
        G.add_node(r.id, pos=(c.x, c.y))
        for d in r.doors:
            if d.to_room != "Exterior" and any(other.id == d.to_room for other in rooms):
                # Add edge between connected rooms
                other_room = next(other for other in rooms if other.id == d.to_room)
                other_c = other_room.bounds.center
                # Euclidean distance between centers through door
                dist = ((c.x - d.position.x)**2 + (c.y - d.position.y)**2)**0.5 + \
                       ((other_c.x - d.position.x)**2 + (other_c.y - d.position.y)**2)**0.5
                G.add_edge(r.id, d.to_room, weight=dist)

    # Calculate egress for each room
    for r in rooms:
        c = r.bounds.center
        path_pts = [Point2D(x=c.x, y=c.y)]
        
        # Approximate distance to exit
        dist_direct = ((c.x - exit_pos.x)**2 + (c.y - exit_pos.y)**2)**0.5
        # Add Manhattan routing multiplier (1.25x for interior walls)
        egress_dist = round(dist_direct * 1.25, 2)
        
        path_pts.append(exit_pos)
        max_allowed = 22.86 # 75 ft IBC 1017.2 for residential
        is_comp = egress_dist <= max_allowed
        
        egress_paths.append(
            EgressPath(
                room_id=r.id,
                path_points=path_pts,
                total_travel_distance=egress_dist,
                max_allowed_distance=max_allowed,
                is_compliant=is_comp
            )
        )
        
        if not is_comp:
            infractions.append(
                Infraction(
                    code="IBC-1017.2",
                    standard="IBC",
                    severity="CRITICAL",
                    room_id=r.id,
                    description=f"Egress travel distance from '{r.name}' ({egress_dist:.1f} m) exceeds IBC maximum 22.86 m (75 ft)",
                    current_value=egress_dist,
                    required_value=max_allowed,
                    unit="m",
                    remediation_advice="Provide a secondary egress exit or shorten circulation corridor."
                )
            )

    return infractions, egress_paths
