from __future__ import annotations
from typing import List
import networkx as nx
from ..core.models import RoomSpec, SpatialAdjacencyGraph, AdjacencyEdge

class SpatialTopologyGraphAgent:
    """
    Agent 2: Spatial Topology Planner
    Constructs a topologically valid functional adjacency graph with a central circulation hub
    and functional clustering (Public vs Private vs Service zones).
    """
    
    @staticmethod
    def construct_topology(rooms: List[RoomSpec]) -> SpatialAdjacencyGraph:
        edges: List[AdjacencyEdge] = []
        node_ids = [r.id for r in rooms]
        
        corridor = next((r for r in rooms if r.room_type == "Corridor"), None)
        living = next((r for r in rooms if r.room_type == "LivingRoom"), None)
        kitchen = next((r for r in rooms if r.room_type == "Kitchen"), None)
        master_bed = next((r for r in rooms if r.room_type == "MasterBedroom"), None)
        master_bath = next((r for r in rooms if r.room_type == "MasterBathroom"), None)
        common_bath = next((r for r in rooms if r.room_type == "Bathroom"), None)
        
        # 1. Central Hub Connections
        if corridor:
            for r in rooms:
                if r.id != corridor.id:
                    # Connect all rooms to circulation corridor except private ensuite
                    if r.id != (master_bath.id if master_bath else ""):
                        edges.append(
                            AdjacencyEdge(
                                source=corridor.id,
                                target=r.id,
                                relation_type="direct_door",
                                weight=1.0
                            )
                        )
                        
        # 2. Living Room to Kitchen adjacency (Open or semi-open plan)
        if living and kitchen:
            edges.append(
                AdjacencyEdge(
                    source=living.id,
                    target=kitchen.id,
                    relation_type="shared_wall",
                    weight=0.9
                )
            )
            
        # 3. Master Bedroom to Master Ensuite (Direct private door)
        if master_bed and master_bath:
            edges.append(
                AdjacencyEdge(
                    source=master_bed.id,
                    target=master_bath.id,
                    relation_type="direct_door",
                    weight=1.0
                )
            )
            
        return SpatialAdjacencyGraph(nodes=node_ids, edges=edges)
