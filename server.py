import json
import os
import socket
import tempfile
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from algo_engine import run_algorithm
from os_server import HTML_CONTENT as OS_HTML_CONTENT
from vision_parser import extract_graph

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8050"))

LATEST_SHARED_GRAPH = {"nodes": [], "edges": [], "parser_used": "None yet"}
GRAPH_LOCK = threading.Lock()


def get_local_ip() -> str:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_phone_url() -> str:
    public_url = os.environ.get("PUBLIC_URL", "").strip().rstrip("/")
    if public_url:
        return public_url
    return f"http://{get_local_ip()}:{PORT}"


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>AlgoCanvas Studio — Graph Vision & Algorithm Visualizer</title>
<style>
  :root {
    --bg: #ede9e0;
    --surface: #faf8f5;
    --surface-2: #e4dfd4;
    --border: rgba(17, 17, 16, 0.2);
    --border-strong: rgba(45, 74, 62, 0.65);
    --text: #111110;
    --muted: #2b2926;
    --accent: #2d4a3e;
    --accent-soft: rgba(45, 74, 62, 0.14);
    --terracotta: #b04a2e;
    --ochre: #9e630c;
    --sage: #143d2b;
  }

  * { box-sizing: border-box; }

  body {
    margin: 0;
    font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    -webkit-font-smoothing: antialiased;
  }

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 14px 24px;
    background: var(--surface);
    border-bottom: 1.5px solid var(--border);
    flex-wrap: wrap;
  }

  .brand { display: flex; align-items: center; gap: 12px; }

  .logo {
    width: 36px; height: 36px; border-radius: 9px;
    background: var(--accent);
    display: grid; place-items: center;
    font-weight: 800; font-size: 14px; color: #faf8f5;
  }

  .brand-title { font-size: 18px; font-weight: 700; margin: 0; letter-spacing: -0.01em; color: #111110; }
  .brand-sub { font-size: 13px; font-weight: 500; color: var(--muted); }

  .header-pills { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

  .layout {
    display: grid;
    grid-template-columns: 335px minmax(0, 1fr) 350px;
    gap: 14px;
    padding: 16px 24px 22px;
    flex: 1;
    transition: grid-template-columns 0.25s ease;
  }

  .layout.left-collapsed { grid-template-columns: 0px minmax(0, 1fr) 350px; }
  .layout.right-collapsed { grid-template-columns: 335px minmax(0, 1fr) 0px; }
  .layout.left-collapsed.right-collapsed { grid-template-columns: 0px minmax(0, 1fr) 0px; }

  @media (max-width: 1120px) {
    .layout,
    .layout.left-collapsed,
    .layout.right-collapsed,
    .layout.left-collapsed.right-collapsed {
      grid-template-columns: 1fr;
      padding: 12px;
    }
    .panel.drawer-collapsed { display: none !important; }
  }

  .panel {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 14px;
    padding: 16px;
    display: flex; flex-direction: column; gap: 13px;
    box-shadow: 0 2px 10px rgba(17, 17, 16, 0.05);
    min-width: 0;
    overflow: hidden;
    transition: opacity 0.2s ease, padding 0.25s ease, border-width 0.25s ease;
  }

  .panel.drawer-collapsed {
    padding-left: 0; padding-right: 0;
    border-width: 0; opacity: 0; pointer-events: none;
  }

  .panel-title {
    font-size: 12.5px; font-weight: 800;
    text-transform: uppercase; letter-spacing: 0.07em;
    color: #111110; margin: 0;
    white-space: nowrap;
  }

  .divider { height: 1.5px; background: var(--border); margin: 2px 0; }

  label {
    display: block;
    font-size: 13.5px;
    font-weight: 700;
    color: #111110;
    margin-bottom: 6px;
  }

  select, input[type="text"], input[type="number"], input[type="file"] {
    width: 100%; padding: 9px 11px; border-radius: 8px;
    border: 1.5px solid var(--border); background: #f4f1ea;
    color: #111110; font-size: 14px; font-weight: 600; outline: none;
  }

  select:focus, input:focus { border-color: var(--accent); }

  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }

  button, a.nav-link-btn {
    padding: 9px 12px; border-radius: 8px;
    border: 1.5px solid var(--border); background: var(--surface-2);
    color: #111110; font-size: 13.5px; font-weight: 600;
    cursor: pointer; transition: all 0.14s ease;
    text-decoration: none; display: inline-flex; align-items: center; justify-content: center;
  }

  button:hover, a.nav-link-btn:hover {
    border-color: var(--border-strong);
    background: #d8d2c5;
  }

  button:active, a.nav-link-btn:active { transform: scale(0.99); }

  button.primary {
    background: var(--accent);
    border: 1.5px solid var(--accent);
    color: #ffffff;
    font-weight: 700;
  }

  button.primary:hover {
    background: #21382f;
    border-color: #21382f;
  }

  button.tool-active {
    border-color: var(--accent);
    background: var(--accent-soft);
    color: #1c332a;
    font-weight: 700;
  }

  .canvas-top {
    display: flex; justify-content: space-between;
    align-items: center; gap: 10px; flex-wrap: wrap;
  }

  .legend { display: flex; gap: 14px; flex-wrap: wrap; font-size: 13px; font-weight: 600; color: #111110; }
  .legend-item { display: inline-flex; align-items: center; gap: 6px; }
  .dot { width: 9px; height: 9px; border-radius: 50%; }

  .canvas-frame {
    position: relative;
    width: 100%;
    height: 540px;
    flex: none;
    border-radius: 10px;
    overflow: hidden;
    border: 1.5px solid var(--border);
    background: #eae4d7;
  }

  canvas { display: block; width: 100%; height: 100%; cursor: grab; touch-action: none; }
  canvas.c-add-node { cursor: crosshair; }
  canvas.c-pick { cursor: pointer; }

  .timeline-bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

  .progress-track {
    flex: 1; min-width: 110px; height: 6px; border-radius: 999px;
    background: var(--surface-2); overflow: hidden;
  }

  .progress-fill {
    height: 100%; width: 0%;
    background: var(--accent);
    transition: width 0.2s ease;
  }

  .callout {
    background: #f2eee6; border: 1.5px solid var(--border);
    border-left: 4px solid var(--accent); border-radius: 8px;
    padding: 13px; font-size: 14.5px; font-weight: 600; line-height: 1.55; color: #111110;
  }

  .chips { display: flex; flex-wrap: wrap; gap: 7px; min-height: 30px; }

  .chip {
    font-size: 13.5px; font-weight: 700; padding: 5px 10px;
    border-radius: 7px; background: var(--surface-2);
    border: 1.5px solid rgba(17, 17, 16, 0.25); color: #111110;
  }

  .chip.frontier {
    border-color: rgba(158, 99, 12, 0.65);
    color: #4a2c00;
    background: #f5e2ba;
  }

  .chip.visited {
    border-color: rgba(20, 61, 43, 0.55);
    color: #0f3323;
    background: #cfe6da;
  }

  .chip.dist {
    border-color: rgba(17, 17, 16, 0.28);
    color: #111110;
    background: #e6e1d6;
  }

  .status-text { font-size: 13px; font-weight: 500; color: var(--muted); line-height: 1.45; }

  .modal-backdrop {
    position: fixed; inset: 0; background: rgba(17, 17, 16, 0.5);
    backdrop-filter: blur(4px); display: none;
    align-items: center; justify-content: center; z-index: 50; padding: 16px;
  }
  .modal-backdrop.open { display: flex; }
  .modal-card {
    background: var(--surface); border: 1.5px solid var(--border);
    border-radius: 14px; padding: 22px; max-width: 380px; width: 100%;
    text-align: center; display: flex; flex-direction: column; gap: 12px;
    box-shadow: 0 18px 40px rgba(17, 17, 16, 0.18);
  }
  #qr-container {
    margin: 0 auto; border-radius: 10px; background: #ffffff; padding: 12px;
    border: 1.5px solid var(--border); display: inline-block;
  }
  #cam-video {
    width: 100%; max-height: 250px; border-radius: 10px;
    background: #111110; border: 1.5px solid var(--border); object-fit: cover;
  }
  .url-box {
    display: block; text-decoration: none;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 13px; font-weight: 600; padding: 9px 10px; border-radius: 8px;
    background: var(--bg); border: 1.5px solid var(--border);
    color: var(--accent); word-break: break-all;
  }
  .app-footer {
    text-align: center;
    padding: 10px 24px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.03em;
    color: var(--muted);
    background: var(--surface);
    border-top: 1.5px solid var(--border);
  }
</style>
</head>
<body>
<header>
  <div class="brand">
    <div class="logo">AC</div>
    <div>
      <h1 class="brand-title">AlgoCanvas Studio</h1>
      <div class="brand-sub">Hand-Drawn Graph Parser & Animated Algorithm Visualizer</div>
    </div>
  </div>
  <div class="header-pills">
    <button id="toggle-left-btn" class="tool-active" onclick="toggleDrawer('left')">Left Panel</button>
    <button id="toggle-right-btn" class="tool-active" onclick="toggleDrawer('right')">Right Panel</button>
    <a class="nav-link-btn" href="/os-algorithms">Operating System Algorithms</a>
  </div>
</header>

<div id="qr-modal" class="modal-backdrop" onclick="if(event.target===this)closeQrModal()">
  <div class="modal-card">
    <h2 class="panel-title">Phone Scanner Link</h2>
    <div class="status-text">Scan with your phone camera, snap your graph sketch, then tap <strong>Sync Phone Graph</strong> on PC.</div>
    <div id="qr-container"></div>
    <a id="phone-url-text" class="url-box" href="__PHONE_URL__" target="_blank" rel="noopener">__PHONE_URL__</a>
    <div class="status-text">Keep your phone on the same Wi-Fi network as this PC (and port 8050 allowed in Windows Firewall), or set <code>PUBLIC_URL</code>.</div>
    <button class="primary" onclick="closeQrModal()">Close</button>
  </div>
</div>

<div id="cam-modal" class="modal-backdrop" onclick="if(event.target===this)closeCamModal()">
  <div class="modal-card">
    <h2 class="panel-title">Phone / Webcam Sketch Scanner</h2>
    <video id="cam-video" autoplay playsinline></video>
    <div id="cam-hint" class="status-text">Align the full graph sketch inside the frame, then tap <strong>Snap & Parse</strong>.</div>
    <div class="grid-2">
      <button class="primary" onclick="captureCamPhoto()">Snap & Parse</button>
      <button onclick="closeCamModal()">Cancel</button>
    </div>
  </div>
</div>

<main id="main-layout" class="layout">
  <section id="left-panel" class="panel">
    <h2 class="panel-title">Sketch & Phone Scanner</h2>
    <div>
      <label for="photo-input">Choose or Snap Sketch Image</label>
      <input type="file" id="photo-input" accept="image/*" capture="environment" onchange="onPhotoSelected()" />
    </div>
    <div class="grid-2">
      <button onclick="openCamModal()">Snap Camera</button>
      <button class="primary" onclick="parsePhoto()">Parse File</button>
    </div>
    <div class="grid-2">
      <button onclick="openQrModal()">Phone QR</button>
      <button onclick="syncSharedGraph()">Sync Phone Graph</button>
    </div>
    <div>
      <label for="parse-mode">Parser Mode</label>
      <select id="parse-mode">
        <option value="auto" selected>Auto (Cloud -> Local)</option>
        <option value="offline">Offline (OpenCV + MNIST-12)</option>
        <option value="cloud">Cloud (Groq)</option>
      </select>
    </div>

    <div class="divider"></div>
    <h2 class="panel-title">Graph Canvas Tools</h2>
    <div class="grid-2">
      <button id="tool-move" class="tool-active" onclick="setTool('move')">Drag Node</button>
      <button id="tool-add-node" onclick="setTool('add-node')">+ Node</button>
      <button id="tool-rename-node" onclick="setTool('rename-node')">Rename Node</button>
      <button id="tool-add-edge" onclick="setTool('add-edge')">+ Edge</button>
      <button id="tool-set-weight" onclick="setTool('set-weight')">Set Weight</button>
      <button id="tool-delete" onclick="setTool('delete')">Delete</button>
    </div>

    <div class="grid-2">
      <div>
        <label for="new-node-id">Node ID / New Name</label>
        <input type="text" id="new-node-id" placeholder="Auto or name" />
      </div>
      <div>
        <label for="edge-weight">Edge Weight</label>
        <input type="number" id="edge-weight" value="1" min="1" />
      </div>
    </div>

    <div class="grid-2">
      <button onclick="loadSampleGraph()">Load Sample</button>
      <button onclick="clearGraph()">Clear Canvas</button>
    </div>

    <div id="status-msg" class="status-text">Tap Phone QR to scan on mobile, or Snap Camera / Parse File to scan a sketch.</div>
  </section>

  <section class="panel">
    <div class="canvas-top">
      <h2 class="panel-title">Animated Execution Stage</h2>
      <div class="legend">
        <span class="legend-item"><span class="dot" style="background:#4a6b5d;"></span>Unvisited</span>
        <span class="legend-item"><span class="dot" style="background:#c98a2e;"></span>Final Path / MST</span>
        <span class="legend-item"><span class="dot" style="background:#2d6a4f;"></span>Visited / Tree</span>
        <span class="legend-item"><span class="dot" style="background:#c86d51;"></span>Active & Traveler</span>
      </div>
    </div>

    <div class="canvas-frame">
      <canvas id="graph-canvas" width="920" height="540"></canvas>
    </div>

    <div class="timeline-bar">
      <button onclick="stepPrev()">Prev</button>
      <button id="play-btn" class="primary" onclick="togglePlay()">Play</button>
      <button onclick="stepNext()">Next</button>
      <button onclick="resetTrace()">Reset</button>
      <div class="progress-track"><div id="progress-fill" class="progress-fill"></div></div>
      <label for="speed-slider" style="margin:0; font-size:11px;">Speed</label>
      <input type="range" id="speed-slider" min="250" max="1500" step="50" value="700" style="width:96px;" />
    </div>
  </section>

  <section id="right-panel" class="panel">
    <h2 class="panel-title">Algorithm Inspector</h2>
    <div>
      <label for="algo-select">Algorithm</label>
      <select id="algo-select" onchange="toggleTarget()">
        <option value="Dijkstra">Dijkstra's Shortest Path</option>
        <option value="Bellman-Ford">Bellman-Ford Shortest Path</option>
        <option value="A*">A* Search</option>
        <option value="Greedy Best-First">Greedy Best-First Search</option>
        <option value="Prim's MST">Prim's Minimum Spanning Tree</option>
        <option value="Kruskal's MST">Kruskal's Minimum Spanning Tree</option>
        <option value="BFS">Breadth-First Search (BFS)</option>
        <option value="DFS">Depth-First Search (DFS)</option>
        <option value="Tarjan SCC">Tarjan's Strongly Connected Components</option>
        <option value="Topological Sort">Topological Sort (Kahn's)</option>
        <option value="Floyd-Warshall">Floyd-Warshall All-Pairs</option>
        <option value="Cycle Detection">Cycle Detection (Union-Find)</option>
      </select>
    </div>

    <div class="grid-2">
      <div>
        <label for="start-node">Start Node</label>
        <select id="start-node"></select>
      </div>
      <div id="target-box">
        <label for="target-node">Target Node</label>
        <select id="target-node"><option value="">All Nodes</option></select>
      </div>
    </div>

    <div id="heuristic-box" style="display:none;">
      <label for="custom-heuristics">Custom Heuristic h(n) (e.g. 2:5, 4:2, 6:0)</label>
      <input type="text" id="custom-heuristics" placeholder="Blank uses automatic canvas h(n)" />
    </div>

    <button class="primary" onclick="runAlgo()">Run & Animate</button>

    <div id="step-explanation" class="callout">
      Choose an algorithm and start node, then click <strong>Run & Animate</strong> to watch node transitions and edge travel.
    </div>

    <div>
      <label id="frontier-label">Frontier</label>
      <div id="frontier-chips" class="chips"></div>
    </div>

    <div>
      <label>Visited / Settled Nodes</label>
      <div id="visited-chips" class="chips"></div>
    </div>

    <div>
      <label>Distances / Weights</label>
      <div id="dist-chips" class="chips"></div>
    </div>
  </section>
</main>
<footer class="app-footer">Made by Vinit</footer>
<script>
const PHONE_URL = "__PHONE_URL__";
const canvas = document.getElementById("graph-canvas");
const ctx = canvas.getContext("2d");

let graph = { nodes: [], edges: [] };
let steps = [];
let stepIndex = 0;
let playing = false;
let timer = null;

let tool = "move";
let draggingNode = null;
let edgeSource = null;
let hoverNode = null;
let hoverEdge = null;
let animStart = performance.now();
let camStream = null;
let leftCollapsed = false;
let rightCollapsed = false;

function syncCanvasResolution() {
  const frame = document.querySelector(".canvas-frame");
  if (!frame) return;
  const targetW = Math.max(480, Math.round(frame.clientWidth));
  if (canvas.width !== targetW) {
    canvas.width = targetW;
  }
  canvas.height = 540;
}

function toggleDrawer(side) {
  const layout = document.getElementById("main-layout");
  if (side === "left") {
    leftCollapsed = !leftCollapsed;
    document.getElementById("left-panel").classList.toggle("drawer-collapsed", leftCollapsed);
    document.getElementById("toggle-left-btn").classList.toggle("tool-active", !leftCollapsed);
  } else {
    rightCollapsed = !rightCollapsed;
    document.getElementById("right-panel").classList.toggle("drawer-collapsed", rightCollapsed);
    document.getElementById("toggle-right-btn").classList.toggle("tool-active", !rightCollapsed);
  }
  layout.classList.toggle("left-collapsed", leftCollapsed);
  layout.classList.toggle("right-collapsed", rightCollapsed);
  setTimeout(syncCanvasResolution, 260);
}

function parseHeuristicInput(raw) {
  const out = {};
  if (!raw || !raw.trim()) return out;
  for (const part of raw.split(",")) {
    const idx = part.indexOf(":");
    if (idx === -1) continue;
    const key = part.slice(0, idx).trim();
    const val = parseFloat(part.slice(idx + 1).trim());
    if (key && !Number.isNaN(val)) out[key] = val;
  }
  return out;
}

function isMobileDevice() {
  return /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent || "");
}

function openQrModal() {
  const urlEl = document.getElementById("phone-url-text");
  const box = document.getElementById("qr-container");
  urlEl.textContent = PHONE_URL;
  urlEl.href = PHONE_URL;

  box.innerHTML = "";
  const img = document.createElement("img");
  img.width = 200;
  img.height = 200;
  img.alt = "QR code for " + PHONE_URL;
  img.style.display = "block";
  img.onerror = () => {
    box.innerHTML = `<div style="color:#090d16;font-size:12px;max-width:190px;padding:10px;">QR image offline — open <strong>${PHONE_URL}</strong> directly in your phone browser.</div>`;
  };
  img.src = "https://quickchart.io/qr?size=200&text=" + encodeURIComponent(PHONE_URL);
  box.appendChild(img);

  document.getElementById("qr-modal").classList.add("open");
}

function closeQrModal() {
  document.getElementById("qr-modal").classList.remove("open");
}

async function openCamModal() {
  const video = document.getElementById("cam-video");
  const hint = document.getElementById("cam-hint");
  document.getElementById("cam-modal").classList.add("open");
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      closeCamModal();
      document.getElementById("photo-input").click();
      setStatus("Opened device camera/photo picker.");
      return;
    }
    camStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: "environment" } },
      audio: false,
    });
    video.srcObject = camStream;
    hint.textContent = "Align the full graph sketch inside the frame, then tap Snap & Parse.";
  } catch (err) {
    closeCamModal();
    document.getElementById("photo-input").click();
    setStatus("Live camera preview blocked (" + err.message + ") — using photo/camera picker.");
  }
}

function closeCamModal() {
  document.getElementById("cam-modal").classList.remove("open");
  if (camStream) {
    camStream.getTracks().forEach(t => t.stop());
    camStream = null;
  }
}

function captureCamPhoto() {
  const video = document.getElementById("cam-video");
  if (!video.videoWidth || !video.videoHeight) {
    setStatus("Camera stream not ready yet.");
    return;
  }
  const snapCanvas = document.createElement("canvas");
  snapCanvas.width = video.videoWidth;
  snapCanvas.height = video.videoHeight;
  snapCanvas.getContext("2d").drawImage(video, 0, 0);
  closeCamModal();

  snapCanvas.toBlob(async (blob) => {
    if (!blob) return;
    await uploadImageBlob(blob, "phone_scan.jpg");
  }, "image/jpeg", 0.9);
}

async function onPhotoSelected() {
  const input = document.getElementById("photo-input");
  if (!input.files.length) return;
  if (isMobileDevice()) {
    await uploadImageBlob(input.files[0], input.files[0].name || "phone_scan.jpg");
  }
}

async function syncSharedGraph() {
  try {
    const res = await fetch("/api/graph");
    const data = await res.json();
    if (!data.nodes || !data.nodes.length) {
      setStatus("No scanned phone graph available yet. Scan a sketch on your phone first.");
      return;
    }
    applyParsedGraph(data, data.parser_used || "Synced");
    setStatus(`Synced ${graph.nodes.length} nodes and ${graph.edges.length} edges from phone scan.`);
  } catch (err) {
    setStatus("Sync failed: " + err.message);
  }
}

function applyParsedGraph(data, label) {
  stopPlay();
  steps = [];
  stepIndex = 0;
  graph = { nodes: data.nodes || [], edges: data.edges || [] };
  fitGraphToCanvas();
  syncDropdowns();
  renderStep(null);
}

function setTool(nextTool) {
  tool = nextTool;
  edgeSource = null;
  for (const id of ["move", "add-node", "rename-node", "add-edge", "set-weight", "delete"]) {
    document.getElementById("tool-" + id).classList.toggle("tool-active", id === nextTool);
  }
  canvas.className = "";
  if (nextTool === "add-node") canvas.classList.add("c-add-node");
  if (nextTool === "rename-node" || nextTool === "add-edge" || nextTool === "set-weight" || nextTool === "delete") {
    canvas.classList.add("c-pick");
  }
}

function toggleTarget() {
  const algo = document.getElementById("algo-select").value;
  const needsTarget = ["Dijkstra", "Bellman-Ford", "A*", "Greedy Best-First", "Floyd-Warshall"].includes(algo);
  const needsHeuristic = ["A*", "Greedy Best-First"].includes(algo);
  document.getElementById("target-box").style.display = needsTarget ? "block" : "none";
  document.getElementById("heuristic-box").style.display = needsHeuristic ? "block" : "none";
}

function setStatus(msg) {
  document.getElementById("status-msg").textContent = msg;
}

function syncDropdowns() {
  const startSel = document.getElementById("start-node");
  const targetSel = document.getElementById("target-node");
  const prevStart = startSel.value;
  const prevTarget = targetSel.value;

  startSel.innerHTML = "";
  targetSel.innerHTML = '<option value="">All Nodes</option>';

  for (const n of graph.nodes) {
    const o1 = document.createElement("option");
    o1.value = n.id; o1.textContent = n.id;
    startSel.appendChild(o1);

    const o2 = document.createElement("option");
    o2.value = n.id; o2.textContent = n.id;
    targetSel.appendChild(o2);
  }

  if (graph.nodes.some(n => n.id === prevStart)) startSel.value = prevStart;
  if (graph.nodes.some(n => n.id === prevTarget)) targetSel.value = prevTarget;
}

function fitGraphToCanvas() {
  if (!graph.nodes.length) return;
  const padX = 76, padY = 66;
  const xs = graph.nodes.map(n => n.x);
  const ys = graph.nodes.map(n => n.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const spanX = Math.max(1, maxX - minX);
  const spanY = Math.max(1, maxY - minY);

  graph.nodes.forEach(n => {
    n.x = Math.round(padX + ((n.x - minX) / spanX) * (canvas.width - padX * 2));
    n.y = Math.round(padY + ((n.y - minY) / spanY) * (canvas.height - padY * 2));
    n.r = n.r || 22;
  });
}

async function uploadImageBlob(blobOrFile, filename) {
  const mode = document.getElementById("parse-mode").value;
  const fd = new FormData();
  fd.append("image", blobOrFile, filename);
  fd.append("mode", mode);

  setStatus("Scanning & parsing sketch photo...");
  try {
    const res = await fetch("/api/parse", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok || data.error) {
      setStatus("Parse error: " + (data.error || res.statusText));
      return;
    }
    applyParsedGraph(data, data.parser_used || mode);
    const suffix = isMobileDevice() ? " Tap 'Sync Phone Graph' on your PC to load it there." : "";
    setStatus(`Parsed ${graph.nodes.length} nodes and ${graph.edges.length} edges.${suffix}`);
  } catch (err) {
    setStatus("Failed to parse photo: " + err.message);
  }
}

async function parsePhoto() {
  const input = document.getElementById("photo-input");
  if (!input.files.length) {
    setStatus("Choose a sketch image or click Snap Camera first.");
    return;
  }
  await uploadImageBlob(input.files[0], input.files[0].name || "sketch.jpg");
}

function loadSampleGraph() {
  stopPlay();
  steps = [];
  stepIndex = 0;
  graph = {
    nodes: [
      { id: "1", x: 150, y: 155, r: 22 },
      { id: "2", x: 365, y: 115, r: 22 },
      { id: "3", x: 365, y: 335, r: 22 },
      { id: "4", x: 590, y: 145, r: 22 },
      { id: "5", x: 590, y: 355, r: 22 },
      { id: "6", x: 780, y: 250, r: 22 },
    ],
    edges: [
      { source: "1", target: "2", weight: 4 },
      { source: "1", target: "3", weight: 2 },
      { source: "2", target: "3", weight: 1 },
      { source: "2", target: "4", weight: 5 },
      { source: "3", target: "5", weight: 8 },
      { source: "4", target: "5", weight: 2 },
      { source: "4", target: "6", weight: 6 },
      { source: "5", target: "6", weight: 3 },
    ],
  };
  syncDropdowns();
  renderStep(null);
  setStatus("Loaded weighted sample graph.");
}

function clearGraph() {
  stopPlay();
  steps = [];
  stepIndex = 0;
  graph = { nodes: [], edges: [] };
  syncDropdowns();
  renderStep(null);
  setStatus("Canvas cleared.");
}

function getCanvasPoint(evt) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: ((evt.clientX - rect.left) / rect.width) * canvas.width,
    y: ((evt.clientY - rect.top) / rect.height) * canvas.height,
  };
}

function hitNode(x, y) {
  for (let i = graph.nodes.length - 1; i >= 0; i--) {
    const n = graph.nodes[i];
    if (Math.hypot(x - n.x, y - n.y) <= (n.r || 22) + 6) return n;
  }
  return null;
}

function hitEdge(x, y) {
  for (const e of graph.edges) {
    const u = graph.nodes.find(n => n.id === e.source);
    const v = graph.nodes.find(n => n.id === e.target);
    if (!u || !v) continue;
    const mx = (u.x + v.x) / 2, my = (u.y + v.y) / 2;
    if (Math.hypot(x - mx, y - my) <= 13) return e;
    const dx = v.x - u.x, dy = v.y - u.y;
    const len2 = dx * dx + dy * dy;
    if (!len2) continue;
    const t = Math.max(0, Math.min(1, ((x - u.x) * dx + (y - u.y) * dy) / len2));
    const px = u.x + t * dx, py = u.y + t * dy;
    if (Math.hypot(x - px, y - py) <= 9) return e;
  }
  return null;
}

canvas.addEventListener("mousedown", (evt) => {
  const pt = getCanvasPoint(evt);
  const n = hitNode(pt.x, pt.y);

  if (tool === "move") {
    if (n) draggingNode = n;
  } else if (tool === "add-node") {
    let nid = document.getElementById("new-node-id").value.trim();
    if (!nid || graph.nodes.some(item => item.id === nid)) {
      let c = 1;
      while (graph.nodes.some(item => item.id === String(c))) c++;
      nid = String(c);
    }
    graph.nodes.push({ id: nid, x: Math.round(pt.x), y: Math.round(pt.y), r: 22 });
    syncDropdowns();
    setStatus(`Added node '${nid}'.`);
  } else if (tool === "rename-node") {
    if (!n) {
      setStatus("Click a node on the canvas to rename it.");
      return;
    }
    const typedName = document.getElementById("new-node-id").value.trim();
    const nextId = typedName || (window.prompt(`New name for node '${n.id}':`, n.id) || "").trim();
    if (!nextId || nextId === n.id) return;
    if (graph.nodes.some(item => item.id === nextId)) {
      setStatus(`Node ID '${nextId}' already exists.`);
      return;
    }
    const oldId = n.id;
    n.id = nextId;
    graph.edges.forEach(e => {
      if (e.source === oldId) e.source = nextId;
      if (e.target === oldId) e.target = nextId;
    });
    syncDropdowns();
    document.getElementById("start-node").value = nextId;
    setStatus(`Renamed node '${oldId}' to '${nextId}'.`);
  } else if (tool === "add-edge") {
    if (!n) return;
    if (!edgeSource) {
      edgeSource = n;
      setStatus(`Start '${n.id}' selected — click another node to connect.`);
    } else if (edgeSource.id !== n.id) {
      const w = Math.max(1, parseInt(document.getElementById("edge-weight").value || "1", 10));
      const dup = graph.edges.some(
        e => (e.source === edgeSource.id && e.target === n.id) ||
             (e.source === n.id && e.target === edgeSource.id)
      );
      if (!dup) {
        graph.edges.push({ source: edgeSource.id, target: n.id, weight: w });
        setStatus(`Connected '${edgeSource.id}' and '${n.id}' (w=${w}).`);
      }
      edgeSource = null;
    }
  } else if (tool === "set-weight") {
    const e = hitEdge(pt.x, pt.y);
    if (e) {
      const w = Math.max(1, parseInt(document.getElementById("edge-weight").value || "1", 10));
      e.weight = w;
      setStatus(`Updated edge (${e.source} — ${e.target}) weight to ${w}.`);
    } else {
      setStatus("Click on an edge line or weight badge to update its weight.");
    }
  } else if (tool === "delete") {
    if (n) {
      graph.nodes = graph.nodes.filter(item => item.id !== n.id);
      graph.edges = graph.edges.filter(e => e.source !== n.id && e.target !== n.id);
      syncDropdowns();
      setStatus(`Removed node '${n.id}'.`);
    } else {
      const e = hitEdge(pt.x, pt.y);
      if (e) {
        graph.edges = graph.edges.filter(item => item !== e);
        setStatus(`Removed edge (${e.source} - ${e.target}).`);
      }
    }
  }
});

canvas.addEventListener("mousemove", (evt) => {
  const pt = getCanvasPoint(evt);
  if (draggingNode) {
    draggingNode.x = Math.max(32, Math.min(canvas.width - 32, Math.round(pt.x)));
    draggingNode.y = Math.max(32, Math.min(canvas.height - 32, Math.round(pt.y)));
    return;
  }
  hoverNode = hitNode(pt.x, pt.y);
  hoverEdge = hoverNode ? null : hitEdge(pt.x, pt.y);
});

window.addEventListener("mouseup", () => { draggingNode = null; });

async function runAlgo() {
  if (!graph.nodes.length) {
    setStatus("Add or parse nodes first.");
    return;
  }
  const algo = document.getElementById("algo-select").value;
  const startId = document.getElementById("start-node").value;
  const targetId = document.getElementById("target-node").value || null;
  const heuristics = parseHeuristicInput(document.getElementById("custom-heuristics").value);

  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ graph, algorithm: algo, start_id: startId, target_id: targetId, heuristics }),
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      setStatus("Error: " + (data.error || res.statusText));
      return;
    }
    steps = data.steps || [];
    stepIndex = 0;
    animStart = performance.now();
    renderStep(steps[0] || null);
    startPlay();
  } catch (err) {
    setStatus("Request failed: " + err.message);
  }
}

function stepNext() {
  if (!steps.length) return;
  if (stepIndex < steps.length - 1) {
    stepIndex++;
    animStart = performance.now();
    renderStep(steps[stepIndex]);
  } else {
    stopPlay();
  }
}

function stepPrev() {
  stopPlay();
  if (!steps.length) return;
  if (stepIndex > 0) {
    stepIndex--;
    animStart = performance.now();
    renderStep(steps[stepIndex]);
  }
}

function resetTrace() {
  stopPlay();
  if (!steps.length) return;
  stepIndex = 0;
  animStart = performance.now();
  renderStep(steps[0]);
}

function togglePlay() {
  if (playing) stopPlay();
  else startPlay();
}

function startPlay() {
  if (!steps.length) return;
  if (stepIndex >= steps.length - 1) stepIndex = 0;
  playing = true;
  document.getElementById("play-btn").textContent = "Pause";
  clearInterval(timer);
  const delay = parseInt(document.getElementById("speed-slider").value, 10);
  timer = setInterval(() => {
    if (stepIndex < steps.length - 1) {
      stepIndex++;
      animStart = performance.now();
      renderStep(steps[stepIndex]);
    } else {
      stopPlay();
    }
  }, delay);
}

function stopPlay() {
  playing = false;
  document.getElementById("play-btn").textContent = "Play";
  clearInterval(timer);
}

function renderStep(st) {
  const fill = document.getElementById("progress-fill");
  const exp = document.getElementById("step-explanation");
  const fLabel = document.getElementById("frontier-label");
  const fChips = document.getElementById("frontier-chips");
  const vChips = document.getElementById("visited-chips");
  const dChips = document.getElementById("dist-chips");

  if (!st) {
    fill.style.width = "0%";
    fChips.innerHTML = "";
    vChips.innerHTML = "";
    dChips.innerHTML = "";
    return;
  }

  const pct = steps.length > 1 ? ((stepIndex + 1) / steps.length) * 100 : 100;
  fill.style.width = `${pct}%`;

  exp.textContent = st.explanation || "";
  fLabel.textContent = st.frontier_label || "Frontier";

  fChips.innerHTML = (st.frontier || []).map(x => `<span class="chip frontier">${x}</span>`).join("");
  vChips.innerHTML = (st.visited || []).map(x => `<span class="chip visited">${x}</span>`).join("");

  const distItems = [];
  if (st.distances && Object.keys(st.distances).length) {
    for (const [k, v] of Object.entries(st.distances)) {
      distItems.push(`<span class="chip dist">${k}: ${v}</span>`);
    }
  }
  dChips.innerHTML = distItems.join("");
}

function edgeMatch(e, pair) {
  if (!pair || pair.length !== 2) return false;
  return (e.source === pair[0] && e.target === pair[1]) ||
         (e.source === pair[1] && e.target === pair[0]);
}

function drawScene(now) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = "rgba(38, 37, 34, 0.2)";
  for (let gx = 24; gx < canvas.width; gx += 36) {
    for (let gy = 24; gy < canvas.height; gy += 36) {
      ctx.fillRect(gx, gy, 1.8, 1.8);
    }
  }

  const st = steps[stepIndex] || null;
  const isComplete = !!(st && st.action === "complete");
  const visitedSet = new Set(st ? (st.visited || []) : []);
  const pathSet = new Set(st ? (st.path_nodes || []) : []);
  const treeEdges = st ? (st.tree_edges || []) : [];
  const activeEdge = st ? st.active_edge : null;

  const nodeMap = {};
  for (const n of graph.nodes) nodeMap[n.id] = n;

  for (const e of graph.edges) {
    const u = nodeMap[e.source], v = nodeMap[e.target];
    if (!u || !v) continue;

    const isTree = treeEdges.some(te => edgeMatch(e, te));
    const isActive = edgeMatch(e, activeEdge);
    const isHovered = hoverEdge === e;
    const isFinalPathEdge =
      isComplete &&
      pathSet.has(e.source) &&
      pathSet.has(e.target) &&
      isTree;

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(u.x, u.y);
    ctx.lineTo(v.x, v.y);
    if (isActive) {
      ctx.strokeStyle = "#b04a2e";
      ctx.lineWidth = 6;
    } else if (isFinalPathEdge) {
      ctx.strokeStyle = "#a66c14";
      ctx.lineWidth = 5.5;
    } else if (isTree) {
      ctx.strokeStyle = "#1d4ed8";
      ctx.strokeStyle = "#1e4d38";
      ctx.lineWidth = 4.8;
    } else if (isHovered) {
      ctx.strokeStyle = "#2c443a";
      ctx.lineWidth = 4.2;
    } else {
      ctx.strokeStyle = "#6e695f";
      ctx.lineWidth = 3;
    }
    ctx.stroke();
    ctx.restore();

    const mx = (u.x + v.x) / 2, my = (u.y + v.y) / 2;
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(mx, my, 14.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = isActive ? "#b04a2e" : (isFinalPathEdge ? "#a66c14" : (isTree ? "#1e4d38" : "#4a463f"));
    ctx.lineWidth = 2.2;
    ctx.stroke();

    ctx.fillStyle = "#141413";
    ctx.font = "800 13px Inter, Segoe UI, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(String(e.weight ?? 1), mx, my);
  }

  if (st && activeEdge && activeEdge.length === 2) {
    const u = nodeMap[activeEdge[0]], v = nodeMap[activeEdge[1]];
    if (u && v) {
      const duration = Math.max(240, parseInt(document.getElementById("speed-slider").value, 10) * 0.72);
      const t = Math.min(1.0, (now - animStart) / duration);
      const px = u.x + (v.x - u.x) * t;
      const py = u.y + (v.y - u.y) * t;

      const glow = ctx.createRadialGradient(px, py, 2, px, py, 20);
      glow.addColorStop(0, "#ffffff");
      glow.addColorStop(0.45, "#b04a2e");
      glow.addColorStop(1, "rgba(176, 74, 46, 0)");
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(px, py, 20, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  const pulse = 0.5 + 0.5 * Math.sin(now / 180);
  for (const n of graph.nodes) {
    const r = n.r || 22;
    const isCurrent = !!(st && st.current_node === n.id);
    const isPicked = !!(edgeSource && edgeSource.id === n.id);
    const isHovered = hoverNode === n;
    const isVisited = visitedSet.has(n.id);
    const isFinalPathNode = isComplete && pathSet.has(n.id);

    let fill = "#f7f4ed";
    let stroke = "#2f483e";
    if (isCurrent || isPicked) {
      stroke = "#b04a2e";
      fill = "#efd3ca";
    } else if (isFinalPathNode) {
      stroke = "#a66c14";
      fill = "#f2dfb9";
    } else if (isVisited) {
      stroke = "#1e4d38";
      fill = "#cfe2d8";
    }

    if (isCurrent) {
      ctx.save();
      ctx.beginPath();
      ctx.arc(n.x, n.y, r + 6 + pulse * 4, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(176, 74, 46, 0.55)";
      ctx.lineWidth = 2.6;
      ctx.stroke();
      ctx.restore();
    }

    ctx.beginPath();
    ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
    ctx.fillStyle = fill;
    ctx.fill();
    ctx.lineWidth = isHovered ? 4.8 : 3.8;
    ctx.strokeStyle = isHovered ? "#141413" : stroke;
    ctx.stroke();

    ctx.fillStyle = "#141413";
    ctx.font = "800 14.5px Inter, Segoe UI, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(n.id, n.x, n.y);

    if (st && st.distances && st.distances[n.id] !== undefined) {
      ctx.fillStyle = "#2e2c28";
      ctx.font = "700 12px Inter, Segoe UI, sans-serif";
      ctx.fillText(`d=${st.distances[n.id]}`, n.x, n.y - r - 11);
    }
  }
  requestAnimationFrame(drawScene);
}

loadSampleGraph();
toggleTarget();
requestAnimationFrame(drawScene);
</script>
</body>
</html>
"""


class AlgoCanvasHandler(BaseHTTPRequestHandler):
    def to_json_safe(self, obj):
        if isinstance(obj, dict):
            return {str(k): self.to_json_safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self.to_json_safe(v) for v in obj]
        type_name = type(obj).__name__
        if hasattr(obj, "item") and callable(obj.item) and (
            "int" in type_name or "float" in type_name or "bool" in type_name
        ):
            return obj.item()
        if hasattr(obj, "tolist") and callable(obj.tolist):
            return obj.tolist()
        return obj

    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(self.to_json_safe(payload)).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_str: str, status: int = 200):
        body = html_str.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = self.path.split("?", 1)[0]
        if route in ("/", "/index.html"):
            self._send_html(HTML_TEMPLATE.replace("__PHONE_URL__", get_phone_url()), 200)
        elif route in ("/os-algorithms", "/os", "/kernelpulse"):
            self._send_html(OS_HTML_CONTENT, 200)
        elif route == "/api/graph":
            with GRAPH_LOCK:
                self._send_json(LATEST_SHARED_GRAPH, 200)
        else:
            self.send_error(404)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length)

            if self.path == "/api/parse":
                ctype = self.headers.get("Content-Type", "")
                mode = "auto"
                img_bytes = None

                if "multipart/form-data" in ctype and "boundary=" in ctype:
                    boundary = ctype.split("boundary=", 1)[1].strip().strip('"').encode("utf-8")
                    parts = raw_body.split(b"--" + boundary)
                    for part in parts:
                        if b"Content-Disposition" not in part:
                            continue
                        header_part, _, content = part.partition(b"\r\n\r\n")
                        content = content.rstrip(b"\r\n")
                        if content.endswith(b"--"):
                            content = content[:-2].rstrip(b"\r\n")
                        headers_str = header_part.decode("utf-8", errors="ignore")
                        if 'name="mode"' in headers_str:
                            mode = content.decode("utf-8", errors="ignore").strip() or "auto"
                        elif 'name="image"' in headers_str:
                            img_bytes = content

                if not img_bytes:
                    self._send_json({"error": "No image uploaded."}, 400)
                    return

                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    tmp.write(img_bytes)
                    tmp_path = tmp.name

                try:
                    parsed = extract_graph(tmp_path, mode=mode, save_debug=False)
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

                with GRAPH_LOCK:
                    LATEST_SHARED_GRAPH.clear()
                    LATEST_SHARED_GRAPH.update(parsed)

                self._send_json(parsed, 200)
                return

            if self.path == "/api/run":
                req = json.loads(raw_body.decode("utf-8"))
                steps = run_algorithm(
                    req.get("graph", {}),
                    req.get("algorithm", "Dijkstra"),
                    req.get("start_id", ""),
                    target_id=req.get("target_id") or None,
                    heuristics=req.get("heuristics") or None,
                )
                self._send_json({"steps": steps}, 200)
                return

            self.send_error(404)
        except Exception as exc:
            self._send_json({"error": str(exc)}, 500)

    def log_message(self, format, *args):
        return


def main():
    server = ThreadingHTTPServer((HOST, PORT), AlgoCanvasHandler)
    local_url = f"http://127.0.0.1:{PORT}"
    phone_url = get_phone_url()
    print(f"AlgoCanvas Studio (PC):    {local_url}")
    print(f"OS Algorithms Page:        {local_url}/os-algorithms")
    print(f"AlgoCanvas Studio (Phone): {phone_url}")
    threading.Timer(0.6, lambda: webbrowser.open(local_url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down AlgoCanvas Studio.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()