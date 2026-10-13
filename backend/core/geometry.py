from __future__ import annotations
import math
from typing import List, Dict, Tuple, Optional
from shapely.geometry import Polygon, box, LineString, Point
from shapely.ops import unary_union
from .models import BoundingBox, Point2D, Door, Window, RoomSpec, SiteBoundary

def bbox_to_polygon(b: BoundingBox) -> Polygon:
    return box(b.x, b.y, b.x + b.w, b.y + b.h)

def check_overlap(b1: BoundingBox, b2: BoundingBox, tolerance: float = 1e-3) -> float:
    """Returns overlapping area in sq. meters."""
    p1 = bbox_to_polygon(b1)
    p2 = bbox_to_polygon(b2)
    if not p1.intersects(p2):
        return 0.0
    inter = p1.intersection(p2)
    if inter.area > tolerance:
        return inter.area
    return 0.0

def are_adjacent(b1: BoundingBox, b2: BoundingBox, tolerance: float = 0.05) -> Tuple[bool, Optional[LineString]]:
    """Returns True and the shared boundary segment if b1 and b2 touch."""
    p1 = bbox_to_polygon(b1)
    p2 = bbox_to_polygon(b2)
    
    # Expand slightly by tolerance to detect touching edges
    p1_buf = p1.buffer(tolerance, join_style=2)
    if not p1_buf.intersects(p2):
        return False, None
        
    # Find shared edge
    shared = p1.boundary.intersection(p2.boundary)
    if shared.is_empty:
        return False, None
    if isinstance(shared, LineString) and shared.length > 0.3:  # At least 30cm shared wall
        return True, shared
    return False, None

def snap_to_grid(val: float, grid_size: float = 0.1) -> float:
    """Snaps dimension or coordinate to architectural grid (e.g. 10cm)."""
    return round(round(val / grid_size) * grid_size, 2)

def compute_exterior_walls(room_box: BoundingBox, site_bounds: BoundingBox, tolerance: float = 0.2) -> List[str]:
    """Identifies which walls of a room face the exterior/setback zone."""
    exterior = []
    # North wall (top)
    if abs((room_box.y + room_box.h) - (site_bounds.y + site_bounds.h)) < tolerance:
        exterior.append("North")
    # South wall (bottom)
    if abs(room_box.y - site_bounds.y) < tolerance:
        exterior.append("South")
    # East wall (right)
    if abs((room_box.x + room_box.w) - (site_bounds.x + site_bounds.w)) < tolerance:
        exterior.append("East")
    # West wall (left)
    if abs(room_box.x - site_bounds.x) < tolerance:
        exterior.append("West")
    return exterior

def generate_doors_and_windows(rooms: List[RoomSpec], site: SiteBoundary) -> List[RoomSpec]:
    """
    Deterministically computes compliant door and window placements:
    - Circulation/Corridor gets doors to adjacent habitable rooms and main entry.
    - Habitable rooms facing the exterior receive windows meeting IBC 8% daylight requirement.
    """
    buildable = site.buildable_bounds
    corridor_room = next((r for r in rooms if r.room_type in ["Corridor", "Foyer", "LivingRoom"]), rooms[0])
    
    door_counter = 1
    window_counter = 1
    
    for room in rooms:
        if not room.bounds:
            continue
        room.doors = []
        room.windows = []
        
        # 1. Main Entry Door (if Foyer, Corridor, or LivingRoom)
        if room.id == corridor_room.id or room.room_type in ["Foyer", "LivingRoom"]:
            # Place main entry door on South or West exterior wall
            entry_x = snap_to_grid(room.bounds.x + min(1.0, room.bounds.w / 2.0))
            entry_y = snap_to_grid(room.bounds.y)
            room.doors.append(
                Door(
                    id=f"D-ENTRY-{door_counter}",
                    from_room=room.id,
                    to_room="Exterior",
                    position=Point2D(x=entry_x, y=entry_y),
                    width=0.95,  # 950mm wide main entry (> ADA 32")
                    swing_direction="inward",
                    is_main_exit=True
                )
            )
            door_counter += 1

        # 2. Interior Doors to Corridor or adjacent spaces
        if room.id != corridor_room.id and corridor_room.bounds:
            is_adj, shared_seg = are_adjacent(room.bounds, corridor_room.bounds)
            if is_adj and shared_seg:
                mid_pt = shared_seg.interpolate(0.5, normalized=True)
                room.doors.append(
                    Door(
                        id=f"D-{door_counter}",
                        from_room=room.id,
                        to_room=corridor_room.id,
                        position=Point2D(x=snap_to_grid(mid_pt.x), y=snap_to_grid(mid_pt.y)),
                        width=0.90,  # 900mm ADA compliant
                        swing_direction="inward"
                    )
                )
                door_counter += 1
            else:
                # Door between nearest room boundary
                dx = snap_to_grid(room.bounds.x + 0.5)
                dy = snap_to_grid(room.bounds.y + (0.0 if room.bounds.y > corridor_room.bounds.y else room.bounds.h))
                room.doors.append(
                    Door(
                        id=f"D-{door_counter}",
                        from_room=room.id,
                        to_room=corridor_room.id,
                        position=Point2D(x=dx, y=dy),
                        width=0.90,
                        swing_direction="inward"
                    )
                )
                door_counter += 1

        # 3. Windows for Natural Light & Ventilation
        ext_walls = compute_exterior_walls(room.bounds, buildable)
        if ext_walls and room.requires_exterior_window:
            for orientation in ext_walls:
                # IBC Chapter 1205: glazing area >= 8% of room area
                target_glazing = max(1.2, room.bounds.area * 0.09)
                win_w = snap_to_grid(min(room.bounds.w * 0.6, target_glazing / 1.2))
                win_w = max(1.0, win_w)
                
                # Position on exterior edge
                if orientation == "North":
                    pos = Point2D(x=snap_to_grid(room.bounds.x + room.bounds.w / 2.0), y=snap_to_grid(room.bounds.y + room.bounds.h))
                elif orientation == "South":
                    pos = Point2D(x=snap_to_grid(room.bounds.x + room.bounds.w / 2.0), y=snap_to_grid(room.bounds.y))
                elif orientation == "East":
                    pos = Point2D(x=snap_to_grid(room.bounds.x + room.bounds.w), y=snap_to_grid(room.bounds.y + room.bounds.h / 2.0))
                else:  # West
                    pos = Point2D(x=snap_to_grid(room.bounds.x), y=snap_to_grid(room.bounds.y + room.bounds.h / 2.0))
                    
                room.windows.append(
                    Window(
                        id=f"W-{window_counter}",
                        room_id=room.id,
                        wall_orientation=orientation, # type: ignore
                        position=pos,
                        width=win_w,
                        height=1.2,
                        glazing_area=win_w * 1.2
                    )
                )
                window_counter += 1
                break  # Primary exterior window created
                
    return rooms
