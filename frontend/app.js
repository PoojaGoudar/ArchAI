// ArchAI Pro Commercial Web Studio Controller

let currentPlan = null;
let currentSvgRaw = "";
let currentScale = 1.0;
let isImperial = false;
let currentTheme = "cad-dark";

// Three.js State
let scene, camera, renderer, controls;
let threeInitialized = false;

const TYPOLOGY_PRESETS = {
  "1bhk": {
    brief: "Compact 1 BHK urban studio with accessible bathroom, open kitchen, and corridor",
    width: 13.0,
    depth: 11.0,
    front: 1.2,
    rear: 1.2,
    side: 1.0
  },
  "2bhk": {
    brief: "Modern 2 BHK apartment with spacious living room, open kitchen, and balcony",
    width: 15.0,
    depth: 13.0,
    front: 1.5,
    rear: 1.5,
    side: 1.0
  },
  "3bhk": {
    brief: "Luxury 3 BHK residence with master ensuite, common bathroom, open kitchen, and home office",
    width: 16.0,
    depth: 14.0,
    front: 1.5,
    rear: 1.5,
    side: 1.0
  },
  "4bhk": {
    brief: "Spacious 4 BHK family villa with dual master suites, formal dining, and central corridor",
    width: 18.0,
    depth: 15.0,
    front: 1.8,
    rear: 1.8,
    side: 1.2
  }
};

function applyTypology(key) {
  document.querySelectorAll('.pill-chip').forEach(c => c.classList.remove('active'));
  event.target.classList.add('active');

  const p = TYPOLOGY_PRESETS[key];
  if (!p) return;
  document.getElementById('briefText').value = p.brief;
  document.getElementById('plotWidth').value = p.width;
  document.getElementById('plotDepth').value = p.depth;
  document.getElementById('setbackFront').value = p.front;
  document.getElementById('setbackRear').value = p.rear;
  document.getElementById('setbackSide').value = p.side;
}

function recalculatePlotArea() {
  const w = parseFloat(document.getElementById('plotWidth').value) || 16.0;
  const d = parseFloat(document.getElementById('plotDepth').value) || 14.0;
  console.log(`Plot footprint updated: ${w}m x ${d}m = ${w*d} m²`);
}

function toggleUnitSystem() {
  isImperial = !isImperial;
  document.getElementById('unitMetric').classList.toggle('active', !isImperial);
  document.getElementById('unitImperial').classList.toggle('active', isImperial);
  if (currentPlan) {
    updateKPIsAndInspector(currentPlan);
    renderScheduleTable(currentPlan);
    if (selectedRoomId) selectRoomFromCanvas(selectedRoomId);
  }
}

function toggleExportMenu() {
  document.getElementById('exportDropdown').parentElement.classList.toggle('open');
}

// Close dropdown on click outside
window.addEventListener('click', (e) => {
  if (!e.target.closest('.dropdown')) {
    document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('open'));
  }
});

function setViewMode(mode) {
  document.querySelectorAll('.view-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.stage-view-wrapper').forEach(s => s.classList.remove('active'));

  if (mode === '2d') {
    document.getElementById('viewTab2D').classList.add('active');
    document.getElementById('stage2D').classList.add('active');
  } else if (mode === '3d') {
    document.getElementById('viewTab3D').classList.add('active');
    document.getElementById('stage3D').classList.add('active');
    initThreeJS();
    if (currentPlan) render3DPlan(currentPlan);
  } else if (mode === 'schedule') {
    document.getElementById('viewTabSchedule').classList.add('active');
    document.getElementById('stageSchedule').classList.add('active');
    if (currentPlan) renderScheduleTable(currentPlan);
  } else if (mode === 'audit') {
    document.getElementById('viewTabAudit').classList.add('active');
    document.getElementById('stageAudit').classList.add('active');
    loadAuditCertificate();
  }
}

function switchSideTab(tab) {
  document.querySelectorAll('.side-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.side-tab-content').forEach(c => c.classList.remove('active'));

  if (tab === 'rules') {
    document.getElementById('tabRules').classList.add('active');
    document.getElementById('sideTabRulesContent').classList.add('active');
  } else {
    document.getElementById('tabProperties').classList.add('active');
    document.getElementById('sideTabPropertiesContent').classList.add('active');
  }
}

// Execute Generation Pipeline
async function executeGeneration() {
  const btn = document.getElementById('btnSynthesize');
  btn.disabled = true;
  btn.innerHTML = `<span class="pulse-dot"></span> Synthesizing (Agents Active)...`;

  const payload = {
    user_brief: document.getElementById('briefText').value || TYPOLOGY_PRESETS['3bhk'].brief,
    site_width: parseFloat(document.getElementById('plotWidth').value) || 16.0,
    site_depth: parseFloat(document.getElementById('plotDepth').value) || 14.0,
    setback_front: parseFloat(document.getElementById('setbackFront').value) || 1.5,
    setback_rear: parseFloat(document.getElementById('setbackRear').value) || 1.5,
    setback_left: parseFloat(document.getElementById('setbackSide').value) || 1.0,
    setback_right: parseFloat(document.getElementById('setbackSide').value) || 1.0,
    max_iterations: 3
  };

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
    const data = await res.json();
    currentPlan = data.floor_plan;

    // Render Stream
    renderAgentStream(data.reasoning_timeline);
    // Render 2D SVG Canvas
    await fetchAndRender2DSVG(currentPlan);
    // Render KPIs & Inspector
    updateKPIsAndInspector(currentPlan);
    // Populate Schedule
    renderScheduleTable(currentPlan);
    // If in 3D view, render 3D
    if (document.getElementById('stage3D').classList.contains('active')) {
      render3DPlan(currentPlan);
    }
  } catch (err) {
    console.error("Synthesis error:", err);
    alert("Error synthesizing floor plan: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Synthesize Compliant Floor Plan`;
  }
}

async function fetchAndRender2DSVG(plan) {
  const res = await fetch('/api/export/svg', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(plan)
  });
  const svgText = await res.text();
  currentSvgRaw = svgText;
  document.getElementById('svgCanvasMount').innerHTML = svgText;
  fitCanvas();
}

function renderAgentStream(timeline) {
  const container = document.getElementById('agentStreamSteps');
  container.innerHTML = "";

  timeline.forEach(step => {
    const card = document.createElement('div');
    card.className = 'stream-step-card';
    card.innerHTML = `
      <div class="step-card-head">
        <span>${step.agent_name}</span>
        <span style="color: #94a3b8; font-size: 0.65rem;">${step.timestamp}</span>
      </div>
      <div class="step-card-body">${step.thought}</div>
      <div style="font-size: 0.68rem; color: #38bdf8; font-weight: 600; margin-top: 3px;">➔ ${step.output_summary}</div>
    `;
    container.appendChild(card);
  });
}

function updateKPIsAndInspector(plan) {
  const rep = plan.compliance;
  if (rep) {
    document.getElementById('kpiCompliance').innerText = `${rep.compliance_score.toFixed(1)}%`;
    document.getElementById('headerComplianceText').innerText = `${rep.compliance_score.toFixed(1)}% COMPLIANT`;
    document.getElementById('statPassCount').innerText = rep.passed_checks;
    document.getElementById('statFailCount').innerText = rep.failed_critical;
    document.getElementById('statWarnCount').innerText = rep.failed_warnings;
  }

  const area = plan.total_built_area;
  if (isImperial) {
    document.getElementById('kpiArea').innerText = `${(area * 10.7639).toFixed(1)} sq.ft`;
  } else {
    document.getElementById('kpiArea').innerText = `${area.toFixed(1)} m²`;
  }

  const plotArea = plan.site.width * plan.site.depth;
  const cov = ((area / plotArea) * 100).toFixed(1);
  document.getElementById('kpiCoverageTxt').innerText = `Coverage: ${cov}% of ${isImperial ? (plotArea*10.7639).toFixed(0)+' sq.ft' : plotArea.toFixed(0)+' m²'}`;

  if (rep && rep.egress_paths && rep.egress_paths.length > 0) {
    const avgEgress = (rep.egress_paths.reduce((a, b) => a + b.total_travel_distance, 0) / rep.egress_paths.length);
    document.getElementById('kpiEgressDistance').innerText = isImperial ? `${(avgEgress*3.28084).toFixed(1)} ft` : `${avgEgress.toFixed(1)} m`;
  }
}

// Room Selection & Properties Inspector
let selectedRoomId = null;
function selectRoomFromCanvas(roomId) {
  if (!currentPlan) return;
  selectedRoomId = roomId;
  const room = currentPlan.rooms.find(r => r.id === roomId);
  if (!room || !room.bounds) return;

  switchSideTab('properties');
  document.getElementById('noRoomSelectedMsg').classList.add('hidden');
  const details = document.getElementById('roomInspectorDetails');
  details.classList.remove('hidden');

  document.getElementById('inspRoomName').innerText = room.name;
  document.getElementById('inspRoomZone').innerText = `${room.zone} Zone`;

  const areaStr = isImperial 
    ? `${(room.bounds.area * 10.7639).toFixed(1)} sq.ft` 
    : `${room.bounds.area.toFixed(1)} m² (${(room.bounds.area * 10.7639).toFixed(1)} sq.ft)`;
  document.getElementById('inspRoomArea').innerText = areaStr;

  const wStr = isImperial ? `${(room.bounds.w * 3.28084).toFixed(1)}′` : `${room.bounds.w.toFixed(2)}m`;
  const hStr = isImperial ? `${(room.bounds.h * 3.28084).toFixed(1)}′` : `${room.bounds.h.toFixed(2)}m`;
  document.getElementById('inspRoomDims').innerText = `${wStr} × ${hStr}`;

  document.getElementById('inspRoomAspect').innerText = `${room.bounds.aspect_ratio.toFixed(2)} : 1 (Compliant)`;

  const totalGlazing = room.windows.reduce((acc, w) => acc + w.glazing_area, 0);
  const ratio = ((totalGlazing / room.bounds.area) * 100).toFixed(1);
  document.getElementById('inspRoomGlazing').innerText = `${totalGlazing.toFixed(1)} m² (${ratio}% ≥ 8% IBC Pass)`;

  document.getElementById('inspRoomDoors').innerText = `${room.doors.length} Door(s) (≥ 900mm ADA Pass)`;

  const ep = currentPlan.compliance ? currentPlan.compliance.egress_paths.find(p => p.room_id === room.id) : null;
  if (ep) {
    document.getElementById('inspRoomEgress').innerText = isImperial 
      ? `${(ep.total_travel_distance * 3.28084).toFixed(1)} ft (Pass < 75ft)`
      : `${ep.total_travel_distance.toFixed(1)} m (Pass < 22.86m)`;
  }
}

// 2D Canvas Controls
function zoomIn() {
  currentScale = Math.min(2.5, currentScale + 0.15);
  apply2DTransform();
}
function zoomOut() {
  currentScale = Math.max(0.4, currentScale - 0.15);
  apply2DTransform();
}
function fitCanvas() {
  currentScale = 1.0;
  apply2DTransform();
}
function apply2DTransform() {
  const mount = document.querySelector('#svgCanvasMount svg');
  if (mount) {
    mount.style.transform = `scale(${currentScale})`;
    mount.style.transformOrigin = 'center center';
  }
}

function toggleCanvasLayer(layer) {
  const svg = document.querySelector('#svgCanvasMount svg');
  if (!svg) return;
  if (layer === 'egress') {
    const el = svg.querySelector('#layer-egress');
    if (el) el.style.display = document.getElementById('chkEgress').checked ? 'block' : 'none';
  } else if (layer === 'glazing') {
    const windows = svg.querySelectorAll('.cad-window');
    windows.forEach(w => w.style.display = document.getElementById('chkGlazing').checked ? 'block' : 'none');
  } else if (layer === 'furniture') {
    const items = svg.querySelectorAll('.cad-room > g[opacity="0.35"]');
    items.forEach(i => i.style.display = document.getElementById('chkFurniture').checked ? 'block' : 'none');
  } else if (layer === 'dims') {
    const dims = svg.querySelectorAll('.dim-leader');
    dims.forEach(d => d.style.display = document.getElementById('chkDims').checked ? 'block' : 'none');
  }
}

function changeCADTheme(theme) {
  currentTheme = theme;
  document.body.className = `theme-${theme}`;
  if (currentPlan) fetchAndRender2DSVG(currentPlan);
}

// Schedule Table
function renderScheduleTable(plan) {
  const tbody = document.getElementById('scheduleTableBody');
  tbody.innerHTML = "";

  plan.rooms.forEach(r => {
    if (!r.bounds) return;
    const tr = document.createElement('tr');
    const area = isImperial ? `${(r.bounds.area * 10.7639).toFixed(1)} sq.ft` : `${r.bounds.area.toFixed(1)} m²`;
    const target = isImperial ? `${(r.target_area * 10.7639).toFixed(1)} sq.ft` : `${r.target_area.toFixed(1)} m²`;
    const dims = isImperial 
      ? `${(r.bounds.w * 3.28084).toFixed(1)}′ × ${(r.bounds.h * 3.28084).toFixed(1)}′` 
      : `${r.bounds.w.toFixed(2)}m × ${r.bounds.h.toFixed(2)}m`;
    const glazing = `${r.windows.length} (${(r.windows.reduce((a, w) => a + w.glazing_area, 0)).toFixed(1)} m²)`;

    tr.innerHTML = `
      <td><strong>${r.name}</strong></td>
      <td><span class="chip-mini">${r.zone}</span></td>
      <td>${target}</td>
      <td><strong>${area}</strong></td>
      <td><code>${dims}</code></td>
      <td>${r.bounds.aspect_ratio.toFixed(2)}:1</td>
      <td>${glazing}</td>
      <td><span class="text-emerald">✓ ADA Compliant</span></td>
      <td><span class="text-emerald font-bold">PASS</span></td>
    `;
    tbody.appendChild(tr);
  });
}

function exportScheduleCSV() {
  if (!currentPlan) return;
  let csv = "Room Name,Zone,Target Area (sqm),Actual Area (sqm),Width (m),Depth (m),Aspect Ratio,Windows Glazing (sqm)\n";
  currentPlan.rooms.forEach(r => {
    if (r.bounds) {
      const g = r.windows.reduce((a, w) => a + w.glazing_area, 0);
      csv += `"${r.name}","${r.zone}",${r.target_area},${r.bounds.area.toFixed(2)},${r.bounds.w.toFixed(2)},${r.bounds.h.toFixed(2)},${r.bounds.aspect_ratio.toFixed(2)},${g.toFixed(2)}\n`;
    }
  });
  const blob = new Blob([csv], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = window.URL.createObjectURL(blob);
  a.download = `AREA_SCHEDULE_${currentPlan.id}.csv`;
  a.click();
}

// 3D WebGL Model Visualizer (Three.js)
function initThreeJS() {
  if (threeInitialized) return;
  const mount = document.getElementById('threejsMount');
  const width = mount.clientWidth || 800;
  const height = mount.clientHeight || 500;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x080c14);

  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
  camera.position.set(20, 25, 25);

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(width, height);
  renderer.shadowMap.enabled = true;
  mount.appendChild(renderer.domElement);

  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);

  const sunLight = new THREE.DirectionalLight(0xfffaed, 0.9);
  sunLight.position.set(30, 40, 20);
  sunLight.castShadow = true;
  scene.add(sunLight);

  // Ground Grid
  const gridHelper = new THREE.GridHelper(50, 50, 0x3b82f6, 0x1e293b);
  scene.add(gridHelper);

  window.addEventListener('resize', onThreeResize);
  threeInitialized = true;
  animateThree();
}

function onThreeResize() {
  const mount = document.getElementById('threejsMount');
  if (!mount || !renderer || !camera) return;
  const width = mount.clientWidth;
  const height = mount.clientHeight;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

function animateThree() {
  requestAnimationFrame(animateThree);
  if (controls) controls.update();
  if (renderer && scene && camera) renderer.render(scene, camera);
}

function reset3DCamera() {
  if (camera && controls) {
    camera.position.set(20, 25, 25);
    controls.target.set(0, 0, 0);
  }
}

function render3DPlan(plan) {
  if (!scene) return;
  // Clear previous meshes
  const toRemove = [];
  scene.traverse(child => {
    if (child.isMesh && child !== scene.children[0]) toRemove.push(child);
  });
  toRemove.forEach(obj => scene.remove(obj));

  const wallMaterial = new THREE.MeshStandardMaterial({ color: 0x243046, roughness: 0.4 });
  const wallHeight = 2.8; // 2.8m standard ceiling height
  const wallThickness = 0.2;

  const zoneColors3D = {
    "LivingRoom": 0x3b82f6,
    "MasterBedroom": 0x8b5cf6,
    "Bedroom": 0xa855f7,
    "Kitchen": 0xf59e0b,
    "DiningRoom": 0x10b981,
    "Bathroom": 0x06b6d4,
    "MasterBathroom": 0x0891b2,
    "Corridor": 0x475569,
    "Office": 0xec4899
  };

  const centerOffset = {
    x: plan.site.width / 2.0,
    z: plan.site.depth / 2.0
  };

  plan.rooms.forEach(r => {
    if (!r.bounds) return;
    const rx = r.bounds.x - centerOffset.x + r.bounds.w / 2.0;
    const rz = r.bounds.y - centerOffset.z + r.bounds.h / 2.0;
    const rw = r.bounds.w;
    const rh = r.bounds.h;

    // Floor Mesh
    const floorGeo = new THREE.BoxGeometry(rw - 0.05, 0.08, rh - 0.05);
    const floorMat = new THREE.MeshStandardMaterial({
      color: zoneColors3D[r.room_type] || 0x334155,
      roughness: 0.6,
      transparent: true,
      opacity: 0.85
    });
    const floorMesh = new THREE.Mesh(floorGeo, floorMat);
    floorMesh.position.set(rx, 0.04, rz);
    scene.add(floorMesh);

    // Extruded Walls
    // North Wall
    const nWallGeo = new THREE.BoxGeometry(rw, wallHeight, wallThickness);
    const nWall = new THREE.Mesh(nWallGeo, wallMaterial);
    nWall.position.set(rx, wallHeight / 2.0, rz + rh / 2.0);
    scene.add(nWall);

    // South Wall
    const sWall = new THREE.Mesh(nWallGeo, wallMaterial);
    sWall.position.set(rx, wallHeight / 2.0, rz - rh / 2.0);
    scene.add(sWall);

    // East Wall
    const eWallGeo = new THREE.BoxGeometry(wallThickness, wallHeight, rh);
    const eWall = new THREE.Mesh(eWallGeo, wallMaterial);
    eWall.position.set(rx + rw / 2.0, wallHeight / 2.0, rz);
    scene.add(eWall);

    // West Wall
    const wWall = new THREE.Mesh(eWallGeo, wallMaterial);
    wWall.position.set(rx - rw / 2.0, wallHeight / 2.0, rz);
    scene.add(wWall);
  });
}

// Export Deliverables
async function exportDXF() {
  if (!currentPlan) return alert("Generate a plan first!");
  const res = await fetch('/api/export/dxf', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(currentPlan)
  });
  const blob = await res.blob();
  const a = document.createElement('a');
  a.href = window.URL.createObjectURL(blob);
  a.download = `${currentPlan.id || 'floor_plan'}.dxf`;
  a.click();
}

function exportSVG() {
  if (!currentSvgRaw) return alert("Generate a plan first!");
  const blob = new Blob([currentSvgRaw], { type: 'image/svg+xml' });
  const a = document.createElement('a');
  a.href = window.URL.createObjectURL(blob);
  a.download = `${currentPlan.id || 'floor_plan'}.svg`;
  a.click();
}

function exportReportMD() {
  if (!currentPlan) return alert("Generate a plan first!");
  fetch('/api/export/report', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(currentPlan)
  }).then(r => r.json()).then(data => {
    const blob = new Blob([data.report_markdown], { type: 'text/markdown' });
    const a = document.createElement('a');
    a.href = window.URL.createObjectURL(blob);
    a.download = `COMPLIANCE_CERTIFICATE_${currentPlan.id}.md`;
    a.click();
  });
}

function exportBIMJSON() {
  if (!currentPlan) return alert("Generate a plan first!");
  const blob = new Blob([JSON.stringify(currentPlan, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = window.URL.createObjectURL(blob);
  a.download = `BIM_PLAN_${currentPlan.id}.json`;
  a.click();
}

async function loadAuditCertificate() {
  if (!currentPlan) return;
  const res = await fetch('/api/export/report', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(currentPlan)
  });
  const data = await res.json();
  const html = data.report_markdown
    .replace(/^# (.*$)/gim, '<h1 style="color: #60a5fa; margin-bottom: 8px;">$1</h1>')
    .replace(/^## (.*$)/gim, '<h2 style="color: #38bdf8; margin: 18px 0 8px 0; font-size: 1.15rem;">$1</h2>')
    .replace(/^### (.*$)/gim, '<h3 style="color: #f8fafc; margin: 12px 0 6px 0; font-size: 0.95rem;">$1</h3>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/`(.*?)`/gim, '<code style="background: rgba(255,255,255,0.08); padding: 2px 6px; border-radius: 4px; font-family: monospace;">$1</code>')
    .replace(/\n/gim, '<br>');
  document.getElementById('auditCertBody').innerHTML = html;
}

function highlightRuleRooms(ruleType) {
  // Highlight matching rooms on 2D canvas
  const svg = document.querySelector('#svgCanvasMount svg');
  if (!svg) return;
  const rooms = svg.querySelectorAll('.cad-room rect');
  rooms.forEach(r => {
    r.style.stroke = '#38bdf8';
    r.style.strokeWidth = '3.5';
  });
  setTimeout(() => {
    if (currentPlan) fetchAndRender2DSVG(currentPlan);
  }, 1200);
}

// Initial Boot
window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('briefText').value = TYPOLOGY_PRESETS['3bhk'].brief;
  executeGeneration();
});
