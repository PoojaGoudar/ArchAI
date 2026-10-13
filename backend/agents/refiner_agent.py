from __future__ import annotations
from typing import List, Dict, Optional
from ..core.models import FloorPlan, Infraction
from ..core.geometry import generate_doors_and_windows
from .neurosymbolic_solver import NeurosymbolicGeometricSolver

class IterativeRefinerAgent:
    """
    Agent 5: Iterative Refiner Agent
    Executes constraint-guided symbolic parameter updates (re-weighting and boundary shifting)
    to eliminate infractions across all floor levels while maintaining multi-story alignment.
    """
    
    @classmethod
    def refine_layout(cls, floor_plan: FloorPlan, infractions: List[Infraction]) -> FloorPlan:
        if not infractions:
            return floor_plan
            
        adjustments: Dict[str, float] = {}
        
        # 1. Compute scaling adjustments from infractions
        for inf in infractions:
            if not inf.room_id:
                continue
                
            if inf.code in ["IBC-1207.1", "IBC-1207.2", "ADA-304.3.1"]:
                adjustments[inf.room_id] = adjustments.get(inf.room_id, 1.0) * 1.25
            elif inf.code == "ARCH-ASPECT":
                adjustments[inf.room_id] = adjustments.get(inf.room_id, 1.0) * 0.90
                
        # 2. Re-solve multi-floor layout with adjusted weights
        if floor_plan.floors:
            floor_plan.floors = NeurosymbolicGeometricSolver.solve_multi_floor_layout(
                floors=floor_plan.floors,
                site=floor_plan.site,
                building_shape=floor_plan.building_shape,
                adjustments=adjustments
            )
            floor_plan.rooms = floor_plan.floors[0].rooms
            floor_plan.total_built_area = round(sum(f.built_area for f in floor_plan.floors), 1)

        # 3. Direct window & door compliance remediation across all rooms
        all_rooms = []
        if floor_plan.floors:
            for f in floor_plan.floors:
                all_rooms.extend(f.rooms)
        else:
            all_rooms = floor_plan.rooms

        for r in all_rooms:
            if not r.bounds:
                continue
            if r.requires_exterior_window and r.windows:
                req_glaze = r.bounds.area * 0.09
                for w in r.windows:
                    w.width = max(1.0, round(req_glaze / 1.2, 2))
                    w.glazing_area = round(w.width * 1.2, 2)
                    
            for d in r.doors:
                d.width = max(0.90, d.width)
                
        floor_plan.iteration_step += 1
        return floor_plan
