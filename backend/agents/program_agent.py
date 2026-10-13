from __future__ import annotations
from typing import List, Dict, Any, Tuple
from ..core.models import RoomSpec, SiteBoundary, FloorLevel
from .llm_client import LLMArchitectClient

class ArchitectProgramAgent:
    """
    Agent 1: Architect Program Agent
    Interprets natural language design briefs and site boundaries using LLMs (Gemini, GPT-4o, Ollama)
    or the advanced semantic reasoning engine to synthesize structured multi-story room programs.
    """
    
    @classmethod
    def formulate_program(
        cls,
        user_brief: str,
        site: SiteBoundary,
        provider: str = "auto",
        api_key: str = None
    ) -> Tuple[List[FloorLevel], str, int, str]:
        """
        Returns (floors_data, building_shape, stories_count, llm_provider_used)
        """
        parsed = LLMArchitectClient.parse_architectural_brief(
            user_brief=user_brief,
            site_width=site.width,
            site_depth=site.depth,
            provider=provider,
            api_key=api_key
        )

        floors_out: List[FloorLevel] = []
        for fl_data in parsed.get("floors", []):
            f_idx = fl_data.get("floor_index", 0)
            f_name = fl_data.get("floor_name", f"Level {f_idx + 1}")
            rooms_list: List[RoomSpec] = []
            
            for r in fl_data.get("rooms", []):
                rooms_list.append(
                    RoomSpec(
                        id=r.get("id", f"room_{len(rooms_list)}"),
                        name=r.get("name", "Custom Space"),
                        room_type=r.get("type", "LivingRoom"),
                        zone=r.get("zone", "Public"),
                        target_area=float(r.get("target_area", 12.0)),
                        min_area=6.5 if r.get("zone") in ["Public", "Private"] else 3.5,
                        min_width=2.13 if r.get("zone") in ["Public", "Private"] else 1.5,
                        requires_exterior_window=r.get("requires_exterior_window", True),
                        is_accessible=True,
                        floor_index=f_idx
                    )
                )
                
            floors_out.append(
                FloorLevel(
                    floor_index=f_idx,
                    floor_name=f_name,
                    rooms=rooms_list,
                    built_area=sum(rm.target_area for rm in rooms_list)
                )
            )

        if not floors_out:
            # Fallback
            floors_out.append(
                FloorLevel(
                    floor_index=0,
                    floor_name="Ground Floor",
                    rooms=[
                        RoomSpec(id="living_0", name="Living Room", room_type="LivingRoom", zone="Public", target_area=24.0),
                        RoomSpec(id="kitchen_0", name="Kitchen", room_type="Kitchen", zone="Service", target_area=12.0),
                        RoomSpec(id="corridor_0", name="Corridor", room_type="Corridor", zone="Circulation", target_area=8.0),
                        RoomSpec(id="master_0", name="Master Bedroom", room_type="MasterBedroom", zone="Private", target_area=18.0),
                        RoomSpec(id="bath_0", name="Bathroom", room_type="Bathroom", zone="Service", target_area=5.0)
                    ]
                )
            )

        shape = parsed.get("building_shape", "Rectangular")
        stories = parsed.get("stories_count", len(floors_out))
        llm_used = parsed.get("llm_provider", "ArchAI Neurosymbolic Engine")

        return floors_out, shape, stories, llm_used
