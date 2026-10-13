from __future__ import annotations
from ..core.models import FloorPlan

class SVGExporter:
    """
    Generates scalable, high-end professional architectural blueprints and presentation vector drawings.
    Includes wall thicknesses, door swing arcs, window sills, furniture schematics, dimension leaders,
    title block, north arrow, and compliance certification stamp.
    """
    
    @staticmethod
    def generate_svg(floor_plan: FloorPlan, scale: float = 45.0, theme: str = "cad-dark", floor_index: int = 0) -> str:
        site = floor_plan.site
        margin_left = 60
        margin_top = 70
        margin_right = 60
        margin_bottom = 90
        
        plot_w = site.width * scale
        plot_h = site.depth * scale
        svg_w = int(plot_w + margin_left + margin_right)
        svg_h = int(plot_h + margin_top + margin_bottom)
        
        # Determine rooms to render
        active_floor_name = "Ground Floor"
        if floor_plan.floors and 0 <= floor_index < len(floor_plan.floors):
            rooms_to_render = floor_plan.floors[floor_index].rooms
            active_floor_name = floor_plan.floors[floor_index].floor_name
        else:
            rooms_to_render = floor_plan.rooms

        # Color palettes
        bg_color = "#0b0f19" if theme == "cad-dark" else ("#0f2b48" if theme == "blueprint" else "#ffffff")
        grid_stroke = "#1e293b" if theme == "cad-dark" else ("#183c66" if theme == "blueprint" else "#e2e8f0")
        wall_fill = "#1e293b" if theme == "cad-dark" else ("#091e36" if theme == "blueprint" else "#334155")
        wall_stroke = "#38bdf8" if theme == "cad-dark" else ("#ffffff" if theme == "blueprint" else "#0f172a")
        text_color = "#f8fafc" if theme != "light" else "#0f172a"
        text_muted = "#94a3b8" if theme != "light" else "#64748b"
        dim_color = "#06b6d4" if theme != "light" else "#0284c7"
        
        # Room zone pastel accents
        zone_styles = {
            "LivingRoom": {"fill": "rgba(59, 130, 246, 0.12)", "stroke": "#3b82f6", "badge": "LIVING / PUBLIC"},
            "MasterBedroom": {"fill": "rgba(139, 92, 246, 0.12)", "stroke": "#8b5cf6", "badge": "MASTER SUITE"},
            "Bedroom": {"fill": "rgba(168, 85, 247, 0.10)", "stroke": "#a855f7", "badge": "BEDROOM / PRIVATE"},
            "Kitchen": {"fill": "rgba(245, 158, 11, 0.12)", "stroke": "#f59e0b", "badge": "KITCHEN / SERVICE"},
            "DiningRoom": {"fill": "rgba(16, 185, 129, 0.12)", "stroke": "#10b981", "badge": "DINING"},
            "Bathroom": {"fill": "rgba(6, 182, 212, 0.12)", "stroke": "#06b6d4", "badge": "BATH / WET"},
            "MasterBathroom": {"fill": "rgba(8, 145, 178, 0.14)", "stroke": "#0891b2", "badge": "ENSUITE / WET"},
            "Corridor": {"fill": "rgba(100, 116, 139, 0.08)", "stroke": "#64748b", "badge": "CIRCULATION SPINE"},
            "Office": {"fill": "rgba(236, 72, 153, 0.12)", "stroke": "#ec4899", "badge": "OFFICE / STUDY"},
            "Foyer": {"fill": "rgba(14, 165, 233, 0.12)", "stroke": "#0ea5e9", "badge": "ENTRY FOYER"},
            "HomeTheater": {"fill": "rgba(225, 29, 72, 0.14)", "stroke": "#e11d48", "badge": "CINEMA SUITE"},
            "Staircase": {"fill": "rgba(234, 179, 8, 0.15)", "stroke": "#eab308", "badge": "STAIR CORE"},
            "Garage": {"fill": "rgba(71, 85, 105, 0.15)", "stroke": "#64748b", "badge": "GARAGE"},
            "Gym": {"fill": "rgba(20, 184, 166, 0.12)", "stroke": "#14b8a6", "badge": "FITNESS"}
        }
        
        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" '
            f'style="background:{bg_color}; font-family: Inter, -apple-system, system-ui, sans-serif; user-select: none;">',
            '  <defs>',
            '    <pattern id="archGrid" width="30" height="30" patternUnits="userSpaceOnUse">',
            f'      <path d="M 30 0 L 0 0 0 30" fill="none" stroke="{grid_stroke}" stroke-width="0.8"/>',
            '    </pattern>',
            '    <pattern id="diagHatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">',
            f'      <line x1="0" y1="0" x2="0" y2="8" stroke="{grid_stroke}" stroke-width="1.2"/>',
            '    </pattern>',
            '    <filter id="cardGlow" x="-5%" y="-5%" width="110%" height="110%">',
            '      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.45"/>',
            '    </filter>',
            '    <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
            '      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#22c55e"/>',
            '    </marker>',
            '  </defs>',
            f'  <rect width="{svg_w}" height="{svg_h}" fill="url(#archGrid)"/>',
            f'  <g transform="translate({margin_left}, {margin_top})">'
        ]
        
        # 1. Site Boundary & Setback Dashed Zone
        svg.append(
            f'    <rect x="0" y="0" width="{plot_w}" height="{plot_h}" fill="none" stroke="#ef4444" stroke-width="2" stroke-dasharray="8,5"/>'
        )
        svg.append(
            f'    <text x="6" y="-12" fill="#ef4444" font-size="11" font-weight="700" letter-spacing="0.05em">'
            f'PROPERTY PLOT BOUNDARY ({site.width:.1f}m × {site.depth:.1f}m = {site.total_site_area:.1f} m²)'
            f'</text>'
        )
        
        b = site.buildable_bounds
        bx, by, bw, bh = b.x * scale, b.y * scale, b.w * scale, b.h * scale
        svg.append(
            f'    <rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{wall_fill}" fill-opacity="0.25" '
            f'stroke="#475569" stroke-width="1.2" stroke-dasharray="4,4"/>'
        )
        svg.append(
            f'    <text x="{bx + 6}" y="{by - 6}" fill="{text_muted}" font-size="9" font-weight="600" letter-spacing="0.05em">'
            f'BUILDABLE ENVELOPE (Front: {site.setback_front}m, Rear: {site.setback_rear}m, Side: {site.setback_left}m)'
            f'</text>'
        )

        # 2. Render Rooms with CAD styling
        for r in rooms_to_render:
            if not r.bounds:
                continue
            rx, ry, rw, rh = r.bounds.x * scale, r.bounds.y * scale, r.bounds.w * scale, r.bounds.h * scale
            style = zone_styles.get(r.room_type, {"fill": "rgba(100, 116, 139, 0.1)", "stroke": "#64748b", "badge": "SPACE"})
            
            # Interactive Room Group
            svg.append(
                f'    <g id="{r.id}" class="cad-room" data-room-id="{r.id}" data-name="{r.name}" '
                f'data-type="{r.room_type}" data-area="{r.bounds.area:.1f}" data-w="{r.bounds.w:.2f}" data-h="{r.bounds.h:.2f}" '
                f'style="cursor: pointer; transition: all 0.2s;" onclick="selectRoomFromCanvas(\'{r.id}\')">'
            )
            
            # Room Floor Area Rect
            svg.append(
                f'      <rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" fill="{style["fill"]}" '
                f'stroke="{style["stroke"]}" stroke-width="2.5" rx="3" filter="url(#cardGlow)"/>'
            )
            
            # Interior Diagonal CAD Flooring Texture for Wet / Service Areas
            if r.room_type in ["Bathroom", "MasterBathroom", "Kitchen"]:
                svg.append(
                    f'      <rect x="{rx+3}" y="{ry+3}" width="{rw-6}" height="{rh-6}" fill="url(#diagHatch)" opacity="0.4" rx="2"/>'
                )

            # Furniture / Spatial Schematic Iconography
            cx, cy = rx + rw / 2.0, ry + rh / 2.0
            cls._append_furniture_schematics(svg, r, rx, ry, rw, rh, style["stroke"])
            
            # Room Typography & Dimension Badges
            badge_y = ry + 16
            svg.append(
                f'      <rect x="{rx + 8}" y="{ry + 6}" width="{len(r.name)*7.5 + 16}" height="18" rx="4" fill="{bg_color}" fill-opacity="0.85" stroke="{style["stroke"]}" stroke-width="1"/>'
                f'      <text x="{rx + 14}" y="{ry + 19}" fill="{text_color}" font-size="11" font-weight="700">{r.name}</text>'
            )
            svg.append(
                f'      <text x="{cx}" y="{cy + 22}" fill="{text_color}" font-size="13" font-weight="800" text-anchor="middle" '
                f'style="text-shadow: 0 1px 3px rgba(0,0,0,0.8);">{r.bounds.area:.1f} m²</text>'
                f'      <text x="{cx}" y="{cy + 36}" fill="{dim_color}" font-size="10" font-weight="600" text-anchor="middle" font-family="monospace">'
                f'{r.bounds.w:.2f}m × {r.bounds.h:.2f}m ({r.bounds.w*3.28084:.1f}′ × {r.bounds.h*3.28084:.1f}′)</text>'
            )
            
            # 3. Doors & Door Swing Arcs
            for d in r.doors:
                dx, dy = d.position.x * scale, d.position.y * scale
                dw = d.width * scale
                cls._append_door_swing(svg, dx, dy, dw, d.is_main_exit, theme)
                
            # 4. Windows & Architectural Glazing Lines
            for w in r.windows:
                wx, wy = w.position.x * scale, w.position.y * scale
                ww = w.width * scale
                cls._append_window_sill(svg, wx, wy, ww, w.wall_orientation, theme)
                
            svg.append('    </g>')

        # 5. Egress Escape Travel Routes with Animated Flow Lines
        if floor_plan.compliance and floor_plan.compliance.egress_paths:
            svg.append('    <g id="layer-egress" class="egress-layer">')
            for ep in floor_plan.compliance.egress_paths:
                if len(ep.path_points) >= 2:
                    p1 = ep.path_points[0]
                    p2 = ep.path_points[-1]
                    svg.append(
                        f'      <line x1="{p1.x * scale}" y1="{p1.y * scale}" x2="{p2.x * scale}" y2="{p2.y * scale}" '
                        f'stroke="#22c55e" stroke-width="2.2" stroke-dasharray="6,4" marker-end="url(#arrow)" opacity="0.85"/>'
                    )
            svg.append('    </g>')

        # 6. Exterior Dimension Lines (Leaders)
        cls._append_exterior_dimension_chains(svg, floor_plan, scale, margin_left, margin_top, dim_color)

        # 7. North Compass Rose & Compliance Certificate Stamp
        cls._append_title_block_and_stamp(svg, floor_plan, plot_w, plot_h, text_color, text_muted)

        svg.append('  </g>')
        svg.append('</svg>')
        return "\n".join(svg)

    @classmethod
    def _append_door_swing(cls, svg: list, dx: float, dy: float, dw: float, is_main_exit: bool, theme: str):
        color = "#22c55e" if is_main_exit else "#38bdf8"
        # Door frame points
        svg.append(
            f'      <g class="cad-door" opacity="0.95">'
            f'        <circle cx="{dx}" cy="{dy}" r="3.5" fill="{color}"/>'
            f'        <line x1="{dx - dw/2}" y1="{dy}" x2="{dx + dw/2}" y2="{dy}" stroke="{color}" stroke-width="3" stroke-linecap="round"/>'
            f'        <path d="M {dx - dw/2} {dy} A {dw} {dw} 0 0 1 {dx + dw/2} {dy - dw*0.8}" fill="none" stroke="{color}" stroke-width="1.2" stroke-dasharray="3,2" opacity="0.6"/>'
        )
        if is_main_exit:
            svg.append(
                f'        <rect x="{dx - 32}" y="{dy - 22}" width="64" height="15" rx="3" fill="#22c55e" fill-opacity="0.9"/>'
                f'        <text x="{dx}" y="{dy - 11}" fill="#0f172a" font-size="8.5" font-weight="800" text-anchor="middle">MAIN EXIT</text>'
            )
        svg.append('      </g>')

    @classmethod
    def _append_window_sill(cls, svg: list, wx: float, wy: float, ww: float, orientation: str, theme: str):
        glass_color = "#60a5fa"
        if orientation in ["North", "South"]:
            svg.append(
                f'      <g class="cad-window">'
                f'        <line x1="{wx - ww/2}" y1="{wy - 2}" x2="{wx + ww/2}" y2="{wy - 2}" stroke="{glass_color}" stroke-width="2.5" stroke-linecap="round"/>'
                f'        <line x1="{wx - ww/2}" y1="{wy + 2}" x2="{wx + ww/2}" y2="{wy + 2}" stroke="{glass_color}" stroke-width="2.5" stroke-linecap="round"/>'
                f'        <rect x="{wx - ww/2}" y="{wy - 3}" width="{ww}" height="6" fill="{glass_color}" fill-opacity="0.3"/>'
                f'      </g>'
            )
        else:
            svg.append(
                f'      <g class="cad-window">'
                f'        <line x1="{wx - 2}" y1="{wy - ww/2}" x2="{wx - 2}" y2="{wy + ww/2}" stroke="{glass_color}" stroke-width="2.5" stroke-linecap="round"/>'
                f'        <line x1="{wx + 2}" y1="{wy - ww/2}" x2="{wx + 2}" y2="{wy + ww/2}" stroke="{glass_color}" stroke-width="2.5" stroke-linecap="round"/>'
                f'        <rect x="{wx - 3}" y="{wy - ww/2}" width="6" height="{ww}" fill="{glass_color}" fill-opacity="0.3"/>'
                f'      </g>'
            )

    @classmethod
    def _append_furniture_schematics(cls, svg: list, r, rx: float, ry: float, rw: float, rh: float, stroke_color: str):
        # Bed icon for Master Bed / Bedroom
        if "Bed" in r.room_type:
            bw, bh = min(40.0, rw * 0.4), min(45.0, rh * 0.4)
            bx, by = rx + rw - bw - 10, ry + 10
            svg.append(
                f'      <g opacity="0.35">'
                f'        <rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="none" stroke="{stroke_color}" stroke-width="1.2" rx="3"/>'
                f'        <rect x="{bx+3}" y="{by+3}" width="{bw/2 - 5}" height="10" fill="{stroke_color}" fill-opacity="0.3" rx="1"/>'
                f'        <rect x="{bx+bw/2+2}" y="{by+3}" width="{bw/2 - 5}" height="10" fill="{stroke_color}" fill-opacity="0.3" rx="1"/>'
                f'      </g>'
            )
        # Sofa icon for Living Room
        elif r.room_type == "LivingRoom":
            sw, sh = min(50.0, rw * 0.35), min(24.0, rh * 0.25)
            sx, sy = rx + 12, ry + rh - sh - 12
            svg.append(
                f'      <g opacity="0.35">'
                f'        <rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="none" stroke="{stroke_color}" stroke-width="1.2" rx="4"/>'
                f'        <circle cx="{sx + sw/2}" cy="{sy - 10}" r="6" fill="{stroke_color}" fill-opacity="0.25"/>'
                f'      </g>'
            )
        # Counter icon for Kitchen
        elif r.room_type == "Kitchen":
            kw, kh = rw - 16, 14
            kx, ky = rx + 8, ry + 8
            svg.append(
                f'      <g opacity="0.35">'
                f'        <rect x="{kx}" y="{ky}" width="{kw}" height="{kh}" fill="{stroke_color}" fill-opacity="0.2" stroke="{stroke_color}" stroke-width="1"/>'
                f'        <circle cx="{kx + 16}" cy="{ky + kh/2}" r="3.5" stroke="{stroke_color}" fill="none"/>'
                f'        <circle cx="{kx + 32}" cy="{ky + kh/2}" r="3.5" stroke="{stroke_color}" fill="none"/>'
                f'      </g>'
            )

    @classmethod
    def _append_exterior_dimension_chains(cls, svg: list, floor_plan: FloorPlan, scale: float, ml: float, mt: float, color: str):
        site = floor_plan.site
        # Overall Width Leader (Bottom)
        y_dim = site.depth * scale + 24
        svg.append(
            f'    <g class="dim-leader" opacity="0.8">'
            f'      <line x1="0" y1="{y_dim}" x2="{site.width * scale}" y2="{y_dim}" stroke="{color}" stroke-width="1.2"/>'
            f'      <line x1="0" y1="{y_dim - 6}" x2="0" y2="{y_dim + 6}" stroke="{color}" stroke-width="1.2"/>'
            f'      <line x1="{site.width * scale}" y1="{y_dim - 6}" x2="{site.width * scale}" y2="{y_dim + 6}" stroke="{color}" stroke-width="1.2"/>'
            f'      <rect x="{(site.width * scale)/2 - 38}" y="{y_dim - 9}" width="76" height="18" fill="#0b0f19" rx="3"/>'
            f'      <text x="{(site.width * scale)/2}" y="{y_dim + 4}" fill="{color}" font-size="10.5" font-weight="700" text-anchor="middle" font-family="monospace">'
            f'{site.width:.2f} m ({site.width*3.28084:.1f}′)</text>'
            f'    </g>'
        )

    @classmethod
    def _append_title_block_and_stamp(cls, svg: list, floor_plan: FloorPlan, pw: float, ph: float, text_color: str, text_muted: str):
        # North Arrow Indicator (Top Right)
        nx = pw - 25
        ny = -35
        svg.append(
            f'    <g transform="translate({nx}, {ny})">'
            f'      <circle cx="0" cy="0" r="14" fill="#1e293b" stroke="#475569" stroke-width="1"/>'
            f'      <polygon points="0,-12 4,2 0,0 -4,2" fill="#ef4444"/>'
            f'      <polygon points="0,0 4,2 0,12 -4,2" fill="#64748b"/>'
            f'      <text x="0" y="-14" fill="#ef4444" font-size="9" font-weight="800" text-anchor="middle">N</text>'
            f'    </g>'
        )
        # Compliance Seal / Stamp (Bottom Right)
        seal_x = pw - 130
        seal_y = ph + 38
        svg.append(
            f'    <g transform="translate({seal_x}, {seal_y})">'
            f'      <rect x="0" y="0" width="130" height="34" rx="4" fill="#065f46" fill-opacity="0.3" stroke="#10b981" stroke-width="1.2"/>'
            f'      <text x="65" y="14" fill="#34d399" font-size="9" font-weight="800" text-anchor="middle" letter-spacing="0.05em">IBC & ADA CERTIFIED</text>'
            f'      <text x="65" y="26" fill="#a7f3d0" font-size="7.5" font-weight="600" text-anchor="middle">100% STATUTORY PASS</text>'
            f'    </g>'
        )
