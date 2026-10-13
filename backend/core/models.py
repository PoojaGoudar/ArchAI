from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Literal, Any
from pydantic import BaseModel, Field

RoomType = str  # Dynamic room types: LivingRoom, MasterBedroom, Bedroom, Kitchen, DiningRoom, Bathroom, MasterBathroom, Corridor, Foyer, Balcony, Utility, Office, HomeTheater, Staircase, Garage, Gym, Conference, Reception, Pantry, ServerRoom, Courtyard, etc.

ZoneCategory = Literal["Public", "Private", "Service", "Circulation"]

class Point2D(BaseModel):
    x: float
    y: float

class BoundingBox(BaseModel):
    x: float
    y: float
    w: float
    h: float

    @property
    def area(self) -> float:
        return self.w * self.h

    @property
    def min_dimension(self) -> float:
        return min(self.w, self.h)

    @property
    def aspect_ratio(self) -> float:
        if self.min_dimension == 0:
            return float('inf')
        return max(self.w, self.h) / self.min_dimension

    @property
    def center(self) -> Point2D:
        return Point2D(x=self.x + self.w / 2.0, y=self.y + self.h / 2.0)

class Door(BaseModel):
    id: str
    from_room: str
    to_room: str  # Can be "Exterior" or room id
    position: Point2D
    width: float = 0.9  # standard 900mm / ~35.4 inches (> 32" ADA)
    swing_direction: Literal["inward", "outward", "sliding"] = "inward"
    is_main_exit: bool = False

class Window(BaseModel):
    id: str
    room_id: str
    wall_orientation: Literal["North", "South", "East", "West"]
    position: Point2D
    width: float = 1.2  # meters
    height: float = 1.2  # meters
    glazing_area: float = 1.44  # sq meters

class RoomSpec(BaseModel):
    id: str
    name: str
    room_type: str = "LivingRoom"
    zone: ZoneCategory = "Public"
    target_area: float  # sq meters
    min_area: float = 6.5  # IBC default minimum (70 sqft = 6.5m2)
    min_width: float = 2.13  # IBC default minimum (7ft = 2.13m)
    requires_exterior_window: bool = True
    is_accessible: bool = True
    floor_index: int = 0
    bounds: Optional[BoundingBox] = None
    doors: List[Door] = Field(default_factory=list)
    windows: List[Window] = Field(default_factory=list)

class SiteBoundary(BaseModel):
    width: float = 16.0  # meters
    depth: float = 14.0  # meters
    setback_front: float = 1.5  # meters
    setback_rear: float = 1.5   # meters
    setback_left: float = 1.0   # meters
    setback_right: float = 1.0  # meters
    max_ground_coverage: float = 0.75  # 75% max coverage
    max_far: float = 2.5

    @property
    def total_site_area(self) -> float:
        return self.width * self.depth

    @property
    def buildable_width(self) -> float:
        return max(0.0, self.width - (self.setback_left + self.setback_right))

    @property
    def buildable_depth(self) -> float:
        return max(0.0, self.depth - (self.setback_front + self.setback_rear))

    @property
    def buildable_bounds(self) -> BoundingBox:
        return BoundingBox(
            x=self.setback_left,
            y=self.setback_front,
            w=self.buildable_width,
            h=self.buildable_depth
        )

class AdjacencyEdge(BaseModel):
    source: str
    target: str
    relation_type: Literal["direct_door", "shared_wall", "circulation_connected"] = "shared_wall"
    weight: float = 1.0

class SpatialAdjacencyGraph(BaseModel):
    nodes: List[str]  # Room IDs
    edges: List[AdjacencyEdge]

class Infraction(BaseModel):
    code: str  # e.g., "IBC-1207.1", "ADA-404.2.3", "ZONING-SETBACK"
    standard: Literal["IBC", "ADA", "ZONING", "NBC", "TOPOLOGY"]
    severity: Literal["CRITICAL", "WARNING", "SUGGESTION"]
    room_id: Optional[str] = None
    description: str
    current_value: Optional[float] = None
    required_value: Optional[float] = None
    unit: Optional[str] = None
    remediation_advice: str

class EgressPath(BaseModel):
    room_id: str
    floor_index: int = 0
    path_points: List[Point2D]
    total_travel_distance: float  # meters
    max_allowed_distance: float  # meters
    is_compliant: bool

class ComplianceReport(BaseModel):
    overall_compliant: bool
    compliance_score: float  # 0.0 to 100.0%
    total_checks: int
    passed_checks: int
    failed_critical: int
    failed_warnings: int
    infractions: List[Infraction] = Field(default_factory=list)
    egress_paths: List[EgressPath] = Field(default_factory=list)
    standards_applied: List[str] = ["IBC 2024", "ADA 2010", "Zoning Bylaws"]

class FloorLevel(BaseModel):
    floor_index: int
    floor_name: str
    rooms: List[RoomSpec] = Field(default_factory=list)
    built_area: float = 0.0
    stair_position: Optional[Point2D] = None

class FloorPlan(BaseModel):
    id: str
    title: str
    site: SiteBoundary
    building_shape: str = "Rectangular" # "Rectangular", "L-Shape", "U-Shape", "OpenLoft", "CommercialCore"
    stories_count: int = 1
    active_floor_index: int = 0
    floors: List[FloorLevel] = Field(default_factory=list)
    rooms: List[RoomSpec] = Field(default_factory=list) # Flattened or current floor rooms
    adjacency_graph: SpatialAdjacencyGraph
    compliance: Optional[ComplianceReport] = None
    total_built_area: float = 0.0
    iteration_step: int = 0
    llm_provider: str = "ArchAI Neurosymbolic Engine"
    generation_metadata: Dict[str, str] = Field(default_factory=dict)

class AgentReasoningStep(BaseModel):
    agent_name: str
    stage: str
    status: Literal["RUNNING", "COMPLETED", "FAILED"]
    thought: str
    actions_taken: List[str]
    output_summary: str
    timestamp: str

class GenerationPipelineResponse(BaseModel):
    success: bool
    floor_plan: FloorPlan
    reasoning_timeline: List[AgentReasoningStep]
    compliance_history: List[float]  # scores across iterations
    iterations_run: int
    execution_time_seconds: float
