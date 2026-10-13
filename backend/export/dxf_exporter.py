from __future__ import annotations
import io
import ezdxf
from ..core.models import FloorPlan

class DXFExporter:
    """
    Exports production-ready AutoCAD DXF files with standardized architectural CAD layers.
    """
    
    @staticmethod
    def generate_dxf_string(floor_plan: FloorPlan) -> str:
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        
        # Setup CAD Layers with standard ACI colors
        doc.layers.add(name="SITE_BOUNDARY", color=1)    # Red
        doc.layers.add(name="SETBACK_ZONE", color=8)     # Gray dashed
        doc.layers.add(name="WALLS", color=7)            # White/Black
        doc.layers.add(name="DOORS", color=4)            # Cyan
        doc.layers.add(name="WINDOWS", color=5)          # Blue
        doc.layers.add(name="ROOM_LABELS", color=2)      # Yellow
        doc.layers.add(name="DIMENSIONS", color=3)       # Green
        doc.layers.add(name="EGRESS_PATH", color=6)      # Magenta
        
        site = floor_plan.site
        # 1. Draw Site Boundary
        msp.add_lwpolyline(
            [(0, 0), (site.width, 0), (site.width, site.depth), (0, site.depth), (0, 0)],
            dxfattribs={"layer": "SITE_BOUNDARY"}
        )
        
        # 2. Draw Setback Envelope
        b = site.buildable_bounds
        msp.add_lwpolyline(
            [(b.x, b.y), (b.x + b.w, b.y), (b.x + b.w, b.y + b.h), (b.x, b.y + b.h), (b.x, b.y)],
            dxfattribs={"layer": "SETBACK_ZONE"}
        )
        
        # 3. Draw Room Walls, Doors, Windows, Labels
        for r in floor_plan.rooms:
            if not r.bounds:
                continue
            bx, by, bw, bh = r.bounds.x, r.bounds.y, r.bounds.w, r.bounds.h
            
            # Walls
            msp.add_lwpolyline(
                [(bx, by), (bx + bw, by), (bx + bw, by + bh), (bx, by + bh), (bx, by)],
                dxfattribs={"layer": "WALLS"}
            )
            
            # Label
            center = r.bounds.center
            msp.add_text(
                f"{r.name}\n{r.bounds.area:.1f} sq.m",
                dxfattribs={"layer": "ROOM_LABELS", "height": 0.3}
            ).set_placement((center.x - 0.8, center.y))
            
            # Doors
            for d in r.doors:
                msp.add_circle(
                    (d.position.x, d.position.y),
                    radius=d.width / 2.0,
                    dxfattribs={"layer": "DOORS"}
                )
                
            # Windows
            for w in r.windows:
                msp.add_lwpolyline(
                    [(w.position.x - w.width / 2.0, w.position.y), (w.position.x + w.width / 2.0, w.position.y)],
                    dxfattribs={"layer": "WINDOWS"}
                )
                
        # 4. Draw Egress Paths
        if floor_plan.compliance and floor_plan.compliance.egress_paths:
            for ep in floor_plan.compliance.egress_paths:
                pts = [(p.x, p.y) for p in ep.path_points]
                if len(pts) >= 2:
                    msp.add_lwpolyline(pts, dxfattribs={"layer": "EGRESS_PATH"})
                    
        # Export to string stream
        stream = io.StringIO()
        doc.write(stream)
        return stream.getvalue()
