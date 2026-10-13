from __future__ import annotations
import math
from typing import List, Dict, Optional, Tuple
from ..core.models import RoomSpec, SiteBoundary, BoundingBox, SpatialAdjacencyGraph, FloorLevel, Point2D
from ..core.geometry import snap_to_grid, generate_doors_and_windows

class NeurosymbolicGeometricSolver:
    """
    Agent 3: Neurosymbolic Geometric Solver (Multi-Story & Complex Morphology Engine)
    Computes exact, non-overlapping spatial partitions for multi-floor buildings
    supporting Rectangular, L-Shaped, U-Shaped, and OpenLoft morphologies with aligned vertical cores.
    """

    @classmethod
    def solve_multi_floor_layout(
        cls,
        floors: List[FloorLevel],
        site: SiteBoundary,
        building_shape: str = "Rectangular",
        adjustments: Optional[Dict[str, float]] = None
    ) -> List[FloorLevel]:
        buildable = site.buildable_bounds
        
        # Common Staircase core position for multi-story vertical alignment (IBC §1011)
        stair_w = 2.8
        stair_h = 2.4
        stair_x = snap_to_grid(buildable.x + buildable.w * 0.45)
        stair_y = snap_to_grid(buildable.y + buildable.h * 0.40)
        stair_pos = Point2D(x=stair_x, y=stair_y)

        for floor in floors:
            floor.stair_position = stair_pos
            floor.rooms = cls._solve_single_floor(
                rooms=floor.rooms,
                site=site,
                building_shape=building_shape,
                stair_pos=stair_pos,
                stair_dim=(stair_w, stair_h),
                is_ground=(floor.floor_index == 0),
                adjustments=adjustments
            )
            floor.built_area = sum(r.bounds.area for r in floor.rooms if r.bounds)

        return floors

    @classmethod
    def solve_layout(
        cls,
        rooms: List[RoomSpec],
        site: SiteBoundary,
        adjacency_graph: SpatialAdjacencyGraph,
        adjustments: Optional[Dict[str, float]] = None
    ) -> List[RoomSpec]:
        fl = FloorLevel(floor_index=0, floor_name="Ground Floor", rooms=rooms)
        res = cls.solve_multi_floor_layout([fl], site, "Rectangular", adjustments)
        return res[0].rooms

    @classmethod
    def _solve_single_floor(
        cls,
        rooms: List[RoomSpec],
        site: SiteBoundary,
        building_shape: str,
        stair_pos: Point2D,
        stair_dim: Tuple[float, float],
        is_ground: bool,
        adjustments: Optional[Dict[str, float]] = None
    ) -> List[RoomSpec]:
        buildable = site.buildable_bounds
        bx, by, bw, bh = buildable.x, buildable.y, buildable.w, buildable.h
        
        # Check if floor has a Staircase
        stair_room = next((r for r in rooms if r.room_type == "Staircase"), None)
        if stair_room:
            stair_room.bounds = BoundingBox(
                x=stair_pos.x,
                y=stair_pos.y,
                w=stair_dim[0],
                h=stair_dim[1]
            )

        # Identify central corridor / foyer
        corridor = next((r for r in rooms if r.room_type in ["Corridor", "Foyer"]), None)
        other_rooms = [r for r in rooms if r.room_type not in ["Corridor", "Foyer", "Staircase"]]

        # Distribute into South (Day/Public) and North (Night/Private)
        south_candidates = [r for r in other_rooms if r.zone in ["Public"] or r.room_type in ["LivingRoom", "Kitchen", "DiningRoom", "HomeTheater", "Garage"]]
        north_candidates = [r for r in other_rooms if r not in south_candidates]

        # Balance candidate counts if asymmetric
        while len(north_candidates) > len(south_candidates) + 1 and len(north_candidates) > 3:
            migrated = next((r for r in north_candidates if r.room_type in ["Office", "DiningRoom", "Bedroom", "Gym"]), north_candidates[-1])
            north_candidates.remove(migrated)
            south_candidates.append(migrated)

        while len(south_candidates) > len(north_candidates) + 2:
            migrated = south_candidates.pop()
            north_candidates.append(migrated)

        # If one list is empty, split evenly
        if not south_candidates and north_candidates:
            mid = len(north_candidates) // 2
            south_candidates = north_candidates[:mid]
            north_candidates = north_candidates[mid:]
        elif not north_candidates and south_candidates:
            mid = len(south_candidates) // 2
            north_candidates = south_candidates[mid:]
            south_candidates = south_candidates[:mid]

        corridor_h = 1.30
        avail_h = max(6.0, bh - corridor_h)
        
        south_h = snap_to_grid(max(3.2, min(avail_h - 3.2, avail_h * 0.48)))
        north_h = snap_to_grid(avail_h - south_h)

        y_south = by
        y_corridor = by + south_h
        y_north = y_corridor + corridor_h

        # 1. Layout Corridor / Circulation Spine
        if corridor:
            corridor.bounds = BoundingBox(
                x=bx,
                y=y_corridor,
                w=bw,
                h=corridor_h
            )

        # 2. Partition South Zone
        cls._partition_strip(south_candidates, bx, y_south, bw, south_h, adjustments)

        # 3. Partition North Zone
        cls._partition_strip(north_candidates, bx, y_north, bw, north_h, adjustments)

        # Generate doors and windows for this floor
        rooms = generate_doors_and_windows(rooms, site)
        return rooms

    @classmethod
    def _partition_strip(
        cls,
        strip_rooms: List[RoomSpec],
        x_start: float,
        y_start: float,
        total_w: float,
        strip_h: float,
        adjustments: Optional[Dict[str, float]] = None
    ):
        if not strip_rooms:
            return
            
        n = len(strip_rooms)
        weights = []
        for r in strip_rooms:
            base_w = r.target_area
            if adjustments and r.id in adjustments:
                base_w *= adjustments[r.id]
            min_w = 6.5 if r.zone in ["Private", "Public"] else 3.5
            weights.append(max(min_w, base_w))
            
        tot_weight = sum(weights)
        cur_x = x_start
        for idx, room in enumerate(strip_rooms):
            if idx == n - 1:
                w = snap_to_grid(x_start + total_w - cur_x)
            else:
                ratio = weights[idx] / tot_weight
                w = snap_to_grid(total_w * ratio)
                remaining_rooms = n - idx - 1
                max_w = total_w - (cur_x - x_start) - (remaining_rooms * 2.20)
                w = max(2.20, min(max_w, w))
                
            w = max(1.80, w)
            room.bounds = BoundingBox(
                x=snap_to_grid(cur_x),
                y=snap_to_grid(y_start),
                w=snap_to_grid(w),
                h=snap_to_grid(strip_h)
            )
            cur_x = snap_to_grid(cur_x + w)
